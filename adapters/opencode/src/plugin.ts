import { join, relative, resolve } from "node:path"
import type { Plugin } from "@opencode-ai/plugin"

import { SidecarClient } from "./client.js"
import { CoalescingEventQueue } from "./queue.js"
import { createTools } from "./tools.js"

export const ExtendCodeAgentPlugin: Plugin = async ({ directory, worktree }) => {
  const root = resolve(worktree || directory)
  const client = new SidecarClient({
    root,
    database: join(root, ".extendcodeagent", "graph.db"),
    python: process.env.EXTENDCODEAGENT_PYTHON,
    mode: readMode(process.env.EXTENDCODEAGENT_MODE),
    userConfig: process.env.EXTENDCODEAGENT_USER_CONFIG,
    projectConfig: process.env.EXTENDCODEAGENT_PROJECT_CONFIG,
  })
  const queue = new CoalescingEventQueue(async (event) => {
    try {
      await client.request("event", event)
    } catch {
      // Expected adapter errors must not break native OpenCode behavior.
    }
  })

  return {
    event: async ({ event }) => {
      if (event.type === "file.edited" || event.type === "file.watcher.updated") {
        queue.enqueue(event.type, [workspacePath(root, event.properties.file)])
      } else if (
        event.type === "lsp.updated" ||
        event.type === "session.created" ||
        event.type === "session.idle"
      ) {
        queue.enqueue(event.type)
      }
    },
    "tool.execute.before": async (input) => {
      queue.enqueue("tool.execute.before")
    },
    "tool.execute.after": async (input) => {
      queue.enqueue("tool.execute.after")
    },
    tool: createTools((operation, params) => client.request(operation, params)),
    dispose: async () => {
      await queue.close()
      await client.stop()
    },
  }
}

function workspacePath(root: string, path: string): string {
  const absolute = resolve(root, path)
  const value = relative(root, absolute)
  if (value === ".." || value.startsWith(`..${process.platform === "win32" ? "\\" : "/"}`)) {
    return path
  }
  return value.replaceAll("\\", "/")
}

function readMode(
  value: string | undefined,
): "off" | "shadow" | "advisory" | "active" | undefined {
  if (value === undefined) return undefined
  if (value === "off" || value === "shadow" || value === "advisory" || value === "active") {
    return value
  }
  return undefined
}

export default ExtendCodeAgentPlugin
