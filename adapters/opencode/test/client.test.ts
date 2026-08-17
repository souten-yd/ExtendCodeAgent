import assert from "node:assert/strict"
import { mkdtemp, rm, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join, resolve } from "node:path"
import test from "node:test"

import { SidecarClient } from "../src/client.js"
import {
  OPEN_CODE_RUNTIME,
  advisoryDeliverySignal,
  sessionSignal,
  taskAndModelSignals,
} from "../src/runtime.js"

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

test("negotiates and transports the C0 host-neutral runtime contract", async () => {
  const root = await mkdtemp(join(tmpdir(), "extendcodeagent-runtime-contract-"))
  await writeFile(join(root, "service.py"), "def leaf():\n    return 1\n", "utf8")
  const client = new SidecarClient({
    root,
    database: join(root, ".extendcodeagent", "graph.db"),
    python: resolve("../../.venv/bin/python"),
    mode: "active",
  })
  try {
    await client.request("runtime_connect", OPEN_CODE_RUNTIME)
    const message = {
      id: "message",
      sessionID: "session",
      role: "user" as const,
      time: { created: Date.parse("2026-08-17T00:00:00Z") },
      agent: "build",
      model: { providerID: "local", modelID: "qwen" },
    }
    const parts = [
      {
        id: "part",
        sessionID: "session",
        messageID: "message",
        type: "text" as const,
        text: "fix leaf",
      },
    ]
    for (const signal of taskAndModelSignals({ sessionID: "session" }, message, parts)) {
      await client.request("runtime_signal", signal)
    }
    await client.request("runtime_signal", sessionSignal("session", "created", new Date(0)))
    await client.request(
      "runtime_signal",
      advisoryDeliverySignal("session", "call", "pi_symbol", new Date(0))!,
    )
    await client.request("event", { kind: "file.edited", paths: ["service.py"] })
    await client.request("runtime_ingest", {
      observation_id: "verification",
      kind: "test",
      status: "passed",
      started_at: "2026-08-17T00:00:00Z",
      finished_at: "2026-08-17T00:00:01Z",
      observed_refs: ["py://service#leaf"],
      command: "pytest",
      automatic: true,
      runtime_session_id: "session",
      runtime_call_id: "verification-call",
    })
    const contract = (await client.request("runtime_contract")) as {
      signals: Record<string, Record<string, unknown>>
      tool_execution_count: number
      verification_count: number
      diagnostics: string[]
    }
    assert.equal(contract.signals.task?.task_text, "fix leaf")
    assert.equal(contract.signals.session?.lifecycle_state, "created")
    assert.deepEqual(contract.signals.mutation?.paths, ["service.py"])
    assert.equal(contract.signals.model?.model_id, "qwen")
    assert.equal(contract.signals.advisory_delivery?.tool, "pi_symbol")
    assert.equal(contract.tool_execution_count, 1)
    assert.equal(contract.verification_count, 1)
    assert.equal(
      contract.diagnostics.some((item) => item.startsWith("observe_file_mutation:degraded:")),
      true,
    )
  } finally {
    await client.stop()
    await rm(root, { recursive: true, force: true })
  }
})
