import type { Part, UserMessage } from "@opencode-ai/sdk"

export type RuntimeCapabilityStatus = "supported" | "degraded" | "unavailable"

export type RuntimeCapabilityDeclaration = {
  readonly name: string
  readonly status: RuntimeCapabilityStatus
  readonly reason?: string
}

export type RuntimeConnect = {
  readonly runtime_name: "OpenCode"
  readonly runtime_version: string
  readonly capabilities: readonly RuntimeCapabilityDeclaration[]
}

export type RuntimeSignal = {
  readonly signal_id: string
  readonly kind: "task" | "session" | "model" | "advisory_delivery"
  readonly observed_at: string
  readonly producer: "opencode_adapter"
  readonly producer_version: string
  readonly runtime_session_id?: string
  readonly task_text?: string
  readonly lifecycle_state?: string
  readonly model_provider?: string
  readonly model_id?: string
  readonly delivery_channel?: "tool"
  readonly tool?: string
  readonly paths: readonly string[]
}

export const OPEN_CODE_RUNTIME: RuntimeConnect = {
  runtime_name: "OpenCode",
  runtime_version: "1.18.18",
  capabilities: [
    { name: "observe_task", status: "supported" },
    { name: "observe_session", status: "supported" },
    {
      name: "observe_file_mutation",
      status: "degraded",
      reason: "native file events use a bounded filesystem watcher fallback when absent",
    },
    { name: "observe_tool_execution", status: "supported" },
    { name: "observe_model_route", status: "supported" },
    {
      name: "observe_verification",
      status: "degraded",
      reason: "verification is authoritative only when tool metadata exposes an exit status",
    },
    {
      name: "deliver_context",
      status: "unavailable",
      reason: "automatic bounded context injection is not implemented in C0",
    },
    { name: "expose_tools", status: "supported" },
    {
      name: "request_model",
      status: "unavailable",
      reason: "model execution remains owned by OpenCode",
    },
    { name: "session_lifecycle", status: "supported" },
    { name: "reconnect", status: "supported" },
    { name: "mcp", status: "supported" },
  ],
}

const COMMON = {
  producer: "opencode_adapter" as const,
  producer_version: "0.1.0",
  paths: [] as const,
}

export function taskAndModelSignals(
  input: { sessionID: string; model?: { providerID: string; modelID: string } },
  message: UserMessage,
  parts: readonly Part[],
): RuntimeSignal[] {
  const observedAt = new Date(message.time.created).toISOString()
  const taskText = parts
    .filter(
      (part): part is Extract<Part, { type: "text" }> =>
        part.type === "text" && !part.synthetic && !part.ignored,
    )
    .map((part) => part.text.trim())
    .filter(Boolean)
    .join("\n")
  const signals: RuntimeSignal[] = []
  if (taskText) {
    signals.push({
      ...COMMON,
      signal_id: `opencode:task:${message.id}`,
      kind: "task",
      observed_at: observedAt,
      runtime_session_id: input.sessionID,
      task_text: taskText,
    })
  }
  const model = input.model ?? message.model
  if (model?.providerID && model.modelID) {
    signals.push({
      ...COMMON,
      signal_id: `opencode:model:${message.id}`,
      kind: "model",
      observed_at: observedAt,
      runtime_session_id: input.sessionID,
      model_provider: model.providerID,
      model_id: model.modelID,
    })
  }
  return signals
}

export function sessionSignal(
  sessionID: string,
  lifecycleState: "created" | "idle" | "deleted",
  observedAt = new Date(),
): RuntimeSignal {
  return {
    ...COMMON,
    signal_id: `opencode:session:${sessionID}:${lifecycleState}:${observedAt.getTime()}`,
    kind: "session",
    observed_at: observedAt.toISOString(),
    runtime_session_id: sessionID,
    lifecycle_state: lifecycleState,
  }
}

export function advisoryDeliverySignal(
  sessionID: string,
  callID: string,
  tool: string,
  observedAt = new Date(),
): RuntimeSignal | undefined {
  if (!tool.startsWith("pi_")) return undefined
  return {
    ...COMMON,
    signal_id: `opencode:advisory:${sessionID}:${callID}`,
    kind: "advisory_delivery",
    observed_at: observedAt.toISOString(),
    runtime_session_id: sessionID,
    delivery_channel: "tool",
    tool,
  }
}
