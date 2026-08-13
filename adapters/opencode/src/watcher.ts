import { watch, type FSWatcher } from "chokidar"

import { workspacePath } from "./paths.js"

export type WorkspaceWatcher = Pick<FSWatcher, "close">

export async function startWorkspaceWatcher(
  root: string,
  onPath: (path: string) => void,
): Promise<WorkspaceWatcher> {
  const watcher = watch(".", {
    cwd: root,
    ignoreInitial: true,
    ignored: (path) => path !== "." && workspacePath(root, path) === undefined,
  })
  watcher.on("all", (event, path) => {
    if (event !== "add" && event !== "change" && event !== "unlink") return
    const normalized = workspacePath(root, path)
    if (normalized) onPath(normalized)
  })
  await new Promise<void>((resolve, reject) => {
    watcher.once("ready", resolve)
    watcher.once("error", reject)
  })
  return watcher
}
