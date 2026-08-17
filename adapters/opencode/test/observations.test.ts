import assert from "node:assert/strict"
import test from "node:test"

import { ToolObservationNormalizer } from "../src/observations.js"

test("unknown stable tool outcomes remain observed and do not capture output text", () => {
  const normalizer = new ToolObservationNormalizer()
  normalizer.before(
    { tool: "shell", sessionID: "session", callID: "call" },
    new Date("2026-08-13T00:00:00Z"),
  )
  const result = normalizer.after(
    {
      tool: "shell",
      sessionID: "session",
      callID: "call",
      args: { command: "python script.py" },
    },
    { title: "Run script", output: "secret source output", metadata: {} },
    new Date("2026-08-13T00:00:01Z"),
  )
  assert.equal(result?.status, "observed")
  assert.equal(result?.kind, "runtime")
  assert.equal(result?.summary, "Run script")
  assert.equal(JSON.stringify(result).includes("secret source output"), false)
})

test("explicit exit metadata classifies test success and lint failure", () => {
  const normalizer = new ToolObservationNormalizer()
  const passed = normalizer.after(
    {
      tool: "shell",
      sessionID: "session",
      callID: "test",
      args: { command: "pytest -q", ignored: "value" },
    },
    {
      title: "Tests",
      output: "",
      metadata: { exitCode: 0, observed_refs: ["py://service#leaf", 3] },
    },
  )
  const failed = normalizer.after(
    {
      tool: "shell",
      sessionID: "session",
      callID: "lint",
      args: { command: "ruff check" },
    },
    { title: "Lint", output: "", metadata: { exit_code: 1 } },
  )
  assert.equal(passed?.kind, "test")
  assert.equal(passed?.status, "passed")
  assert.deepEqual(passed?.observed_refs, ["py://service#leaf"])
  assert.equal(failed?.kind, "lint")
  assert.equal(failed?.status, "failed")
})

test("Project Intelligence tools do not recursively create runtime evidence", () => {
  const normalizer = new ToolObservationNormalizer()
  assert.equal(
    normalizer.after(
      { tool: "pi_context", sessionID: "session", callID: "pi", args: {} },
      { title: "Context", output: "", metadata: {} },
    ),
    undefined,
  )
})

test("missing runtime title degrades to a bounded non-secret summary", () => {
  const normalizer = new ToolObservationNormalizer()
  const result = normalizer.after(
    { tool: "bash", sessionID: "session", callID: "call", args: { command: "pytest -q" } },
    { title: undefined, output: "secret output", metadata: { exitCode: 0 } } as never,
  )

  assert.equal(result?.summary, "OpenCode bash execution")
  assert.equal(result?.status, "passed")
  assert.equal(JSON.stringify(result).includes("secret output"), false)
})
