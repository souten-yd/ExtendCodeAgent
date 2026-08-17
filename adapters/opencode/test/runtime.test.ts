import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"

import {
  OPEN_CODE_RUNTIME,
  advisoryDeliverySignal,
  sessionSignal,
  taskAndModelSignals,
} from "../src/runtime.js"

test("declares every C0 runtime capability with truthful gaps", async () => {
  const packageJson = JSON.parse(
    await readFile(new URL("../../package.json", import.meta.url), "utf8"),
  ) as { dependencies: Record<string, string> }
  assert.equal(
    OPEN_CODE_RUNTIME.runtime_version,
    packageJson.dependencies["@opencode-ai/plugin"],
  )
  assert.equal(OPEN_CODE_RUNTIME.capabilities.length, 12)
  assert.equal(new Set(OPEN_CODE_RUNTIME.capabilities.map((item) => item.name)).size, 12)
  assert.deepEqual(
    OPEN_CODE_RUNTIME.capabilities
      .filter((item) => item.status === "unavailable")
      .map((item) => item.name),
    ["deliver_context", "request_model"],
  )
  assert.equal(
    OPEN_CODE_RUNTIME.capabilities
      .filter((item) => item.status !== "supported")
      .every((item) => Boolean(item.reason)),
    true,
  )
})

test("maps task and model without exposing OpenCode message objects", () => {
  const signals = taskAndModelSignals(
    { sessionID: "session", model: { providerID: "local", modelID: "qwen" } },
    {
      id: "message",
      sessionID: "session",
      role: "user",
      time: { created: Date.parse("2026-08-17T00:00:00Z") },
      agent: "build",
      model: { providerID: "ignored", modelID: "ignored" },
    },
    [
      { id: "part", sessionID: "session", messageID: "message", type: "text", text: "fix leaf" },
    ],
  )
  assert.deepEqual(signals.map((item) => item.kind), ["task", "model"])
  assert.equal(signals[0]?.task_text, "fix leaf")
  assert.equal(signals[1]?.model_id, "qwen")
  assert.equal("message" in signals[0]!, false)
})

test("maps session lifecycle and advisory delivery independently", () => {
  assert.equal(sessionSignal("session", "idle", new Date(0)).lifecycle_state, "idle")
  assert.equal(advisoryDeliverySignal("session", "call", "shell"), undefined)
  assert.equal(
    advisoryDeliverySignal("session", "call", "pi_symbol", new Date(0))?.delivery_channel,
    "tool",
  )
})
