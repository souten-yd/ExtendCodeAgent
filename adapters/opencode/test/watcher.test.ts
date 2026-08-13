import assert from "node:assert/strict"
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join } from "node:path"
import test from "node:test"

import { startWorkspaceWatcher } from "../src/watcher.js"

test("observes external source changes and ignores managed state", async () => {
  const root = await mkdtemp(join(tmpdir(), "extendcodeagent-watcher-"))
  const observed: string[] = []
  await mkdir(join(root, ".extendcodeagent"))
  const watcher = await startWorkspaceWatcher(root, (path) => observed.push(path))
  try {
    await writeFile(join(root, "service.py"), "value = 1\n", "utf8")
    await writeFile(join(root, ".extendcodeagent", "graph.db-wal"), "state", "utf8")
    await waitFor(() => observed.includes("service.py"))
    assert.equal(observed.includes(".extendcodeagent/graph.db-wal"), false)
  } finally {
    await watcher.close()
    await rm(root, { recursive: true, force: true })
  }
})

async function waitFor(predicate: () => boolean): Promise<void> {
  const deadline = Date.now() + 5_000
  while (!predicate()) {
    if (Date.now() >= deadline) throw new Error("watcher event timed out")
    await new Promise((resolve) => setTimeout(resolve, 20))
  }
}
