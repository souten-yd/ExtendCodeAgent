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
      description:
        "Show compact ExtendCodeAgent readiness, graph revision, and configured capability bounds.",
      args: {},
      async execute() {
        return jsonResult(await request("status", { view: "compact" }))
      },
    }),
    pi_symbol: tool({
      description:
        "Find task-ready definition, export, caller, and test paths for a project symbol. " +
        "Use the returned compact fields directly instead of expanding them into explanation objects.",
      args: {
        query: z.string().min(1),
      },
      async execute(args) {
        return jsonResult(await request("symbol", { ...args, view: "compact" }))
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
      description:
        "Return task-ready definition, production methods, direct use count, focused tests, " +
        "and uncertainty. Copy compact scalar/path fields without enriching their schema.",
      args: {
        changed_refs: refs,
        min_confidence: z.number().min(0).max(1).optional(),
        max_depth: z.number().int().min(0).optional(),
        include_historical: z.boolean().optional(),
      },
      async execute(args) {
        return jsonResult(await request("impact", { ...args, view: "compact" }))
      },
    }),
    pi_tests: tool({
      description:
        "Select the smallest task-ready unit, integration, and architecture test obligations. " +
        "Copy selected_tests directly and preserve any explicit coverage gaps.",
      args: {
        objective: z.string().min(1),
        changed_refs: z.array(z.string()).optional(),
      },
      async execute(args) {
        return jsonResult(await request("tests", { ...args, view: "compact" }))
      },
    }),
    pi_context: tool({
      description:
        "Build a minimum task-relevant evidence envelope. Start at the inferred/explicit smallest " +
        "scope and request a broader scope only for an unresolved evidence gap.",
      args: {
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
      async execute(args) {
        return jsonResult(await request("context", { ...args, view: "envelope" }))
      },
    }),
    pi_runtime_evidence: tool({
      description: "Show bounded revision-aware runtime evidence.",
      args: { refs: z.array(z.string()).optional() },
      async execute(args) {
        return jsonResult(await request("runtime_evidence", { ...args, view: "compact" }))
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
    pi_plan: tool({
      description:
        "Score bounded change alternatives from Project Truth and project the selected " +
        "strategy into a Blueprint draft. Persistence is opt-in.",
      args: {
        goal: z.string().min(1),
        target_refs: refs,
        constraints: z.array(z.string()).optional(),
        persist_blueprint: z.boolean().default(false),
      },
      async execute(args) {
        return jsonResult(await request("plan", args))
      },
    }),
    pi_verify: tool({
      description:
        "Trace requirements to current Project Truth and report convergence, missing facts, " +
        "and verification gaps without claiming unobserved evidence.",
      args: {
        requirement_revision_id: z.string().min(1).optional(),
        requirements: z.array(z.object({
          requirement_id: z.string().min(1),
          description: z.string().min(1),
          expected_actual_refs: refs,
          mandatory: z.boolean().default(true),
          requires_verification: z.boolean().default(true),
        })).min(1),
      },
      async execute(args) {
        return jsonResult(await request("verify", args))
      },
    }),
  }
}
