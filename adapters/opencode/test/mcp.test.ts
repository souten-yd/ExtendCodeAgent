import assert from "node:assert/strict"
import { mkdtemp, rm, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join, resolve } from "node:path"
import test from "node:test"
import { Client } from "@modelcontextprotocol/sdk/client/index.js"
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js"

test("MCP stdio handshake lists and calls the shared tools", async () => {
  const root = await mkdtemp(join(tmpdir(), "extendcodeagent-mcp-"))
  await writeFile(join(root, "service.py"), "def leaf():\n    return 1\n", "utf8")
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [resolve("dist/src/mcp.js")],
    cwd: resolve("../.."),
    env: {
      PATH: process.env.PATH ?? "",
      PYTHONPATH: resolve("../../src"),
      EXTENDCODEAGENT_ROOT: root,
      EXTENDCODEAGENT_PYTHON: resolve("../../.venv/bin/python"),
      EXTENDCODEAGENT_MODE: "active",
    },
    stderr: "pipe",
  })
  const client = new Client({ name: "integration-test", version: "1.0.0" })
  try {
    await client.connect(transport)
    const tools = await client.listTools()
    assert.deepEqual(
      tools.tools.map((item) => item.name).sort(),
      [
        "pi_context",
        "pi_impact",
        "pi_path",
        "pi_plan",
        "pi_references",
        "pi_research_plan",
        "pi_runtime_evidence",
        "pi_status",
        "pi_symbol",
        "pi_tests",
        "pi_verify",
      ],
    )
    const response = (await client.callTool({
      name: "pi_symbol",
      arguments: { query: "leaf" },
    })) as {
      isError?: boolean
      content: Array<{ type: string; text?: string }>
    }
    assert.equal(response.isError, undefined)
    const content = response.content[0]
    assert.equal(content?.type, "text")
    if (content?.type !== "text" || !content.text) throw new Error("expected text content")
    const result = JSON.parse(content.text) as { definition: string[]; view: string }
    assert.deepEqual(result.definition, ["service.py"])
    assert.equal(result.view, "compact")
    const statusResponse = (await client.callTool({
      name: "pi_status",
      arguments: {},
    })) as { content: Array<{ type: string; text?: string }> }
    const statusContent = statusResponse.content[0]
    if (statusContent?.type !== "text" || !statusContent.text) {
      throw new Error("expected status text content")
    }
    const status = JSON.parse(statusContent.text) as {
      mode: string
      capabilities: Array<{ name: string; mode: string }>
    }
    assert.equal(status.mode, "active")
    const modes = new Map(status.capabilities.map((item) => [item.name, item.mode]))
    for (const capability of ["blueprint", "convergence", "traceability", "strategy"]) {
      assert.equal(modes.get(capability), "active")
    }
    const planResponse = (await client.callTool({
      name: "pi_research_plan",
      arguments: { query: "SQLite durability", depth: "micro", facets: ["official docs"] },
    })) as { content: Array<{ type: string; text?: string }> }
    const planContent = planResponse.content[0]
    if (planContent?.type !== "text" || !planContent.text) throw new Error("expected plan text")
    const plan = JSON.parse(planContent.text) as { max_queries: number; queries: string[] }
    assert.equal(plan.max_queries, 2)
    assert.deepEqual(plan.queries, ["SQLite durability official docs"])
    const changeResponse = (await client.callTool({
      name: "pi_plan",
      arguments: { goal: "change leaf safely", target_refs: ["py://service#leaf"] },
    })) as { content: Array<{ type: string; text?: string }> }
    const changeContent = changeResponse.content[0]
    if (changeContent?.type !== "text" || !changeContent.text) {
      throw new Error("expected change plan text")
    }
    const changePlan = JSON.parse(changeContent.text) as {
      capabilities_used: string[]
      blueprint: { persisted: boolean }
    }
    assert.deepEqual(changePlan.capabilities_used, ["blueprint", "strategy"])
    assert.equal(changePlan.blueprint.persisted, false)
    const verifyResponse = (await client.callTool({
      name: "pi_verify",
      arguments: {
        requirements: [{
          requirement_id: "leaf-exists",
          description: "leaf remains present",
          expected_actual_refs: ["py://service#leaf"],
        }],
      },
    })) as { content: Array<{ type: string; text?: string }> }
    const verifyContent = verifyResponse.content[0]
    if (verifyContent?.type !== "text" || !verifyContent.text) {
      throw new Error("expected verification text")
    }
    const verification = JSON.parse(verifyContent.text) as {
      capabilities_used: string[]
      coverage_complete: boolean
    }
    assert.deepEqual(verification.capabilities_used, ["convergence", "traceability"])
    assert.equal(verification.coverage_complete, false)
  } finally {
    await client.close()
    await rm(root, { recursive: true, force: true })
  }
})
