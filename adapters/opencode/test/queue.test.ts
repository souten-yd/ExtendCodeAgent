import assert from "node:assert/strict"
import test from "node:test"

import { CoalescingEventQueue, type ProjectEvent } from "../src/queue.js"
import { workspacePath } from "../src/paths.js"

test("coalesces duplicate file events and serializes batches", async () => {
  const observed: ProjectEvent[] = []
  const queue = new CoalescingEventQueue(async (event) => {
    observed.push(event)
  }, 10_000)
  queue.enqueue("file.edited", ["b.py", "a.py"])
  queue.enqueue("file.edited", ["a.py"])
  queue.enqueue("session.idle")
  await queue.flush()
  assert.deepEqual(observed, [
    { kind: "file.edited", paths: ["a.py", "b.py"] },
    { kind: "session.idle", paths: [] },
  ])
})

test("filters paths that cannot affect the source snapshot", () => {
  const root = process.platform === "win32" ? "C:\\workspace" : "/workspace"
  assert.equal(workspacePath(root, `${root}/src/app.py`), "src/app.py")
  assert.equal(workspacePath(root, `${root}/.git/index.lock`), undefined)
  assert.equal(workspacePath(root, `${root}/.extendcodeagent/graph.db-wal`), undefined)
  assert.equal(workspacePath(root, `${root}/node_modules/pkg/index.js`), undefined)
  assert.equal(workspacePath(root, `${root}/../outside.py`), undefined)
})

test("falls back to a full refresh when a path batch exceeds its bound", async () => {
  const observed: ProjectEvent[] = []
  const queue = new CoalescingEventQueue(async (event) => {
    observed.push(event)
  }, 10_000, 2)
  queue.enqueue("file.watcher.updated", ["a.py", "b.py", "c.py"])
  queue.enqueue("file.watcher.updated", ["d.py"])
  await queue.flush()
  assert.deepEqual(observed, [{ kind: "file.watcher.updated", paths: [] }])
})
