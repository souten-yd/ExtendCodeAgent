import { join, resolve } from "node:path"
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js"
import { z } from "zod"

import { SidecarClient, type RolloutMode } from "./client.js"

const root = resolve(process.env.EXTENDCODEAGENT_ROOT ?? process.cwd())
const client = new SidecarClient({
  root,
  database:
    process.env.EXTENDCODEAGENT_DATABASE ?? join(root, ".extendcodeagent", "graph.db"),
  python: process.env.EXTENDCODEAGENT_PYTHON,
  mode: readMode(process.env.EXTENDCODEAGENT_MODE),
  userConfig: process.env.EXTENDCODEAGENT_USER_CONFIG,
  projectConfig: process.env.EXTENDCODEAGENT_PROJECT_CONFIG,
})

function readMode(value: string | undefined): RolloutMode | undefined {
  if (value === undefined) return undefined
  if (value === "off" || value === "shadow" || value === "advisory" || value === "active") {
    return value
  }
  return undefined
}

const server = new McpServer({ name: "extendcodeagent", version: "0.1.0" })

function result(value: unknown) {
  return { content: [{ type: "text" as const, text: JSON.stringify(value, null, 2) }] }
}

server.registerTool(
  "pi_status",
  { description: "Show compact Project Intelligence readiness and configured bounds." },
  async () => result(await client.request("status", { view: "compact" })),
)
server.registerTool(
  "pi_symbol",
  {
    description: "Find compact task-ready definition, export, caller, and test paths.",
    inputSchema: {
      query: z.string().min(1),
    },
  },
  async (args) => result(await client.request("symbol", { ...args, view: "compact" })),
)
server.registerTool(
  "pi_references",
  {
    description: "Find graph references to a canonical entity.",
    inputSchema: { canonical_ref: z.string().min(1) },
  },
  async (args) => result(await client.request("references", args)),
)
server.registerTool(
  "pi_path",
  {
    description: "Trace bounded explainable dependency paths.",
    inputSchema: {
      source_ref: z.string().min(1),
      target_ref: z.string().min(1).optional(),
      allowed_edge_types: z.array(z.string()).optional(),
      min_confidence: z.number().min(0).max(1).optional(),
      max_depth: z.number().int().min(0).optional(),
      max_paths: z.number().int().positive().optional(),
    },
  },
  async (args) => result(await client.request("path", args)),
)
server.registerTool(
  "pi_impact",
  {
    description: "Assess direct/transitive project impact.",
    inputSchema: {
      changed_refs: z.array(z.string()).min(1),
      min_confidence: z.number().min(0).max(1).optional(),
      max_depth: z.number().int().min(0).optional(),
      include_historical: z.boolean().optional(),
    },
  },
  async (args) => result(await client.request("impact", { ...args, view: "compact" })),
)
server.registerTool(
  "pi_tests",
  {
    description: "Select task-ready tests by verification objective and optional changed refs.",
    inputSchema: {
      objective: z.string().min(1),
      changed_refs: z.array(z.string()).optional(),
    },
  },
  async (args) => result(await client.request("tests", { ...args, view: "compact" })),
)
server.registerTool(
  "pi_context",
  {
    description:
      "Build a minimum task-relevant evidence envelope and expand only for an explicit gap.",
    inputSchema: {
      objective: z.string().min(1),
      target_refs: z.array(z.string()).optional(),
      profile: z.enum(["standard", "weak"]).optional(),
      token_budget: z.number().int().positive().optional(),
      scope: z
        .enum(["symbol", "neighborhood", "impact", "verification", "subsystem"])
        .optional(),
      prior_evidence_ids: z.array(z.string()).optional(),
      unresolved_gaps: z.array(z.string()).optional(),
    },
  },
  async (args) => result(await client.request("context", { ...args, view: "envelope" })),
)
server.registerTool(
  "pi_runtime_evidence",
  {
    description: "Show bounded revision-aware runtime evidence.",
    inputSchema: { refs: z.array(z.string()).optional() },
  },
  async (args) => result(await client.request("runtime_evidence", { ...args, view: "compact" })),
)
server.registerTool(
  "pi_research_plan",
  {
    description: "Build a bounded provider-neutral research retrieval plan.",
    inputSchema: {
      query: z.string().min(1),
      depth: z.enum(["micro", "standard", "deep"]).optional(),
      facets: z.array(z.string()).optional(),
    },
  },
  async (args) => result(await client.request("research_plan", args)),
)
server.registerTool(
  "pi_plan",
  {
    description: "Score Project Truth change alternatives and project a Blueprint draft.",
    inputSchema: {
      goal: z.string().min(1),
      target_refs: z.array(z.string()).min(1),
      constraints: z.array(z.string()).optional(),
      persist_blueprint: z.boolean().default(false),
    },
  },
  async (args) => result(await client.request("plan", args)),
)
server.registerTool(
  "pi_verify",
  {
    description: "Trace requirements to Project Truth and evaluate convergence gaps.",
    inputSchema: {
      requirement_revision_id: z.string().min(1).optional(),
      requirements: z.array(z.object({
        requirement_id: z.string().min(1),
        description: z.string().min(1),
        expected_actual_refs: z.array(z.string()).min(1),
        mandatory: z.boolean().default(true),
        requires_verification: z.boolean().default(true),
      })).min(1),
    },
  },
  async (args) => result(await client.request("verify", args)),
)

const stop = async () => {
  await client.stop()
  await server.close()
}
process.once("SIGINT", () => void stop())
process.once("SIGTERM", () => void stop())

await server.connect(new StdioServerTransport())
