import { tool, type ToolDefinition } from "@opencode-ai/plugin"
import { z } from "zod"

export type Requester = (
  operation: string,
  params?: Record<string, unknown>,
) => Promise<unknown>

const refs = z.array(z.string()).min(1)

function jsonResult(value: unknown): string {
  return JSON.stringify(value, null, 2)
}

export function createTools(request: Requester): Record<string, ToolDefinition> {
  return {
    pi_status: tool({
      description: "Show ExtendCodeAgent Project Intelligence status and graph revision.",
      args: {},
      async execute() {
        return jsonResult(await request("status"))
      },
    }),
    pi_symbol: tool({
      description: "Find bounded project symbols by name or canonical reference.",
      args: { query: z.string().min(1) },
      async execute(args) {
        return jsonResult(await request("symbol", args))
      },
    }),
    pi_references: tool({
      description: "Find graph facts that reference a canonical project entity.",
      args: { canonical_ref: z.string().min(1) },
      async execute(args) {
        return jsonResult(await request("references", args))
      },
    }),
    pi_path: tool({
      description: "Trace bounded explainable dependency paths between project entities.",
      args: {
        source_ref: z.string().min(1),
        target_ref: z.string().min(1).optional(),
        allowed_edge_types: z.array(z.string()).optional(),
        min_confidence: z.number().min(0).max(1).optional(),
        max_depth: z.number().int().min(0).optional(),
        max_paths: z.number().int().positive().optional(),
      },
      async execute(args) {
        return jsonResult(await request("path", args))
      },
    }),
    pi_impact: tool({
      description: "Assess direct/transitive project impact with confidence and explanations.",
      args: {
        changed_refs: refs,
        min_confidence: z.number().min(0).max(1).optional(),
        max_depth: z.number().int().min(0).optional(),
        include_historical: z.boolean().optional(),
      },
      async execute(args) {
        return jsonResult(await request("impact", args))
      },
    }),
    pi_tests: tool({
      description: "Recommend graph-linked tests for changed project references.",
      args: { changed_refs: refs },
      async execute(args) {
        return jsonResult(await request("tests", args))
      },
    }),
    pi_context: tool({
      description: "Build bounded revision-aware Project Intelligence context.",
      args: {
        objective: z.string().min(1),
        target_refs: z.array(z.string()).optional(),
        profile: z.enum(["standard", "weak"]).optional(),
        token_budget: z.number().int().positive().optional(),
      },
      async execute(args) {
        return jsonResult(await request("context", args))
      },
    }),
    pi_runtime_evidence: tool({
      description: "Show bounded revision-aware runtime evidence.",
      args: { refs: z.array(z.string()).optional() },
      async execute(args) {
        return jsonResult(await request("runtime_evidence", args))
      },
    }),
    pi_research_plan: tool({
      description: "Build a bounded provider-neutral research retrieval plan.",
      args: {
        query: z.string().min(1),
        depth: z.enum(["micro", "standard", "deep"]).optional(),
        facets: z.array(z.string()).optional(),
      },
      async execute(args) {
        return jsonResult(await request("research_plan", args))
      },
    }),
  }
}
