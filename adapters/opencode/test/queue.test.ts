import assert from "node:assert/strict"
import test from "node:test"

import { CoalescingEventQueue, type ProjectEvent } from "../src/queue.js"

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
