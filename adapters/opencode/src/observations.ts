type ToolInput = {
  tool: string
  sessionID: string
  callID: string
  args?: unknown
}

type ToolOutput = {
  title: string
  output: string
  metadata: unknown
}

export type RuntimeIngest = {
  observation_id: string
  kind: "test" | "lint" | "build" | "typecheck" | "smoke" | "benchmark" | "runtime"
  status: "passed" | "failed" | "observed" | "unavailable"
  started_at: string
  finished_at: string
  observed_refs: string[]
  command?: string
  tool: string
  summary: string
  automatic: true
}

export class ToolObservationNormalizer {
  private readonly starts = new Map<string, string>()

  before(input: Omit<ToolInput, "args">, startedAt = new Date()): void {
    if (!input.tool.startsWith("pi_")) this.starts.set(input.callID, startedAt.toISOString())
  }

  after(
    input: ToolInput,
    output: ToolOutput,
    finishedAt = new Date(),
  ): RuntimeIngest | undefined {
    if (input.tool.startsWith("pi_")) return undefined
    const finished = finishedAt.toISOString()
    const started = this.starts.get(input.callID) ?? finished
    this.starts.delete(input.callID)
    const metadata = record(output.metadata)
    const command = record(input.args)?.command
    const refs = Array.isArray(metadata?.observed_refs)
      ? metadata.observed_refs.filter((item): item is string => typeof item === "string")
      : []
    return {
      observation_id: `opencode:${input.sessionID}:${input.callID}`,
      kind: observationKind(input.tool, typeof command === "string" ? command : ""),
      status: observationStatus(metadata),
      started_at: started,
      finished_at: finished,
      observed_refs: refs,
      ...(typeof command === "string" ? { command } : {}),
      tool: input.tool,
      summary: output.title.slice(0, 500),
      automatic: true,
    }
  }
}

function observationKind(tool: string, command: string): RuntimeIngest["kind"] {
  const value = `${tool} ${command}`.toLowerCase()
  if (/pytest|\btest\b/.test(value)) return "test"
  if (/ruff|eslint|\blint\b/.test(value)) return "lint"
  if (/mypy|pyright|tsc|typecheck/.test(value)) return "typecheck"
  if (/benchmark|\bbench\b/.test(value)) return "benchmark"
  if (/\bsmoke\b/.test(value)) return "smoke"
  if (/\bbuild\b/.test(value)) return "build"
  return "runtime"
}

function observationStatus(metadata: Record<string, unknown> | undefined): RuntimeIngest["status"] {
  const explicit = metadata?.status
  if (
    explicit === "passed" ||
    explicit === "failed" ||
    explicit === "observed" ||
    explicit === "unavailable"
  ) {
    return explicit
  }
  const exitCode = metadata?.exitCode ?? metadata?.exit_code
  if (typeof exitCode === "number") return exitCode === 0 ? "passed" : "failed"
  return "observed"
}

function record(value: unknown): Record<string, unknown> | undefined {
  return typeof value === "object" && value !== null ? (value as Record<string, unknown>) : undefined
}
