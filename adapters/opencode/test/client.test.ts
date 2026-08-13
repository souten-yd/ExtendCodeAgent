import assert from "node:assert/strict"
import { mkdtemp, rm, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join, resolve } from "node:path"
import test from "node:test"

import { SidecarClient } from "../src/client.js"

test("spawns, queries, stops, and reconnects to the Python sidecar", async () => {
  const root = await mkdtemp(join(tmpdir(), "extendcodeagent-client-"))
  await writeFile(join(root, "service.py"), "def leaf():\n    return 1\n", "utf8")
  const client = new SidecarClient({
    root,
    database: join(root, ".extendcodeagent", "graph.db"),
    python: resolve("../../.venv/bin/python"),
    mode: "advisory",
  })
  try {
    const first = (await client.request("symbol", { query: "leaf" })) as {
      revision_id: string
      items: Array<{ canonical_ref: string }>
    }
    assert.equal(first.items[0]?.canonical_ref, "py://service#leaf")
    await client.stop()
    const second = (await client.request("status")) as { revision_id: string }
    assert.equal(second.revision_id, first.revision_id)
  } finally {
    await client.stop()
    await rm(root, { recursive: true, force: true })
  }
})
