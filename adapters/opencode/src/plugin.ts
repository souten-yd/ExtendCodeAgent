import { join, resolve } from "node:path"
import type { Plugin } from "@opencode-ai/plugin"

import { SidecarClient, type PiStatus, type RolloutMode } from "./client.js"
import { ToolObservationNormalizer } from "./observations.js"
import { workspacePath } from "./paths.js"
import { CoalescingEventQueue } from "./queue.js"
import {
  OPEN_CODE_RUNTIME,
  advisoryDeliverySignal,
  sessionSignal,
  taskAndModelSignals,
} from "./runtime.js"
import { createTools } from "./tools.js"
import { startWorkspaceWatcher, type WorkspaceWatcher } from "./watcher.js"

const ExtendCodeAgentPlugin: Plugin = async ({ directory, worktree }) => {
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
  const observations = new ToolObservationNormalizer()
  await client.request("runtime_connect", OPEN_CODE_RUNTIME).catch(() => {
    // Capability negotiation is observable but must not break native OpenCode startup.
  })
  const watcher = startWatcher(client, root, queue)

  return {
    event: async ({ event }) => {
      if (event.type === "file.edited" || event.type === "file.watcher.updated") {
        const path = workspacePath(root, event.properties.file)
        if (path) queue.enqueue(event.type, [path])
      } else if (
        event.type === "lsp.updated"
      ) {
        queue.enqueue(event.type)
      } else if (event.type === "session.created") {
        await sendSignal(client, sessionSignal(event.properties.info.id, "created"))
      } else if (event.type === "session.idle") {
        await sendSignal(client, sessionSignal(event.properties.sessionID, "idle"))
      } else if (event.type === "session.deleted") {
        await sendSignal(client, sessionSignal(event.properties.info.id, "deleted"))
      }
    },
    "chat.message": async (input, output) => {
      for (const signal of taskAndModelSignals(input, output.message, output.parts)) {
        await sendSignal(client, signal)
      }
    },
    "tool.execute.before": async (input) => {
      observations.before(input)
      queue.enqueue("tool.execute.before")
    },
    "tool.execute.after": async (input, output) => {
      queue.enqueue("tool.execute.after")
      const delivery = advisoryDeliverySignal(input.sessionID, input.callID, input.tool)
      if (delivery) await sendSignal(client, delivery)
      const observation = observations.after(input, output)
      if (observation) {
        await client.request("runtime_ingest", observation).catch(() => {
          // Runtime evidence capture must not break native tool execution.
        })
      }
    },
    tool: createTools((operation, params) => client.request(operation, params)),
    dispose: async () => {
      await (await watcher)?.close()
      await queue.close()
      await client.stop()
    },
  }
}

async function sendSignal(
  client: SidecarClient,
  signal: ReturnType<typeof sessionSignal>,
): Promise<void> {
  await client.request("runtime_signal", signal).catch(() => {
    // Runtime signal capture must not break native OpenCode behavior.
  })
}

async function startWatcher(
  client: SidecarClient,
  root: string,
  queue: CoalescingEventQueue,
): Promise<WorkspaceWatcher | undefined> {
  try {
    const status = (await client.request("status")) as Partial<PiStatus>
    if (status.mode === "off") return undefined
    return await startWorkspaceWatcher(root, (path) =>
      queue.enqueue("file.watcher.updated", [path]),
    )
  } catch {
    return undefined
  }
}

function readMode(value: string | undefined): RolloutMode | undefined {
  if (value === undefined) return undefined
  if (value === "off" || value === "shadow" || value === "advisory" || value === "active") {
    return value
  }
  return undefined
}

export default ExtendCodeAgentPlugin
