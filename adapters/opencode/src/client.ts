import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process"
import { createInterface } from "node:readline"

export const INTERFACE_VERSION = "extendcodeagent.local.v1"

export type RolloutMode = "off" | "shadow" | "advisory" | "active"

export type CapabilityImplementation = "implemented" | "not_implemented"

/** Capability depth: the cost axis, independent of `RolloutMode`. */
export type Depth = "D0" | "D1" | "D2" | "D3" | "D4"

/** One entry of the per-capability inventory reported by `pi_status`. */
export type CapabilityStatus = {
  readonly name: string
  readonly implementation: CapabilityImplementation
  readonly mode: RolloutMode
  readonly depth: Depth
  /** Confidence an inferred relation must clear at this depth. */
  readonly min_inferred_confidence: number
  /** Set when another capability's rollout mode governs this one. */
  readonly governed_by: string | null
}

export type PiResult = {
  readonly interface: string
  readonly revision_id: string | null
  /** Depth the answering capability ran at; null when no capability owns the result. */
  readonly depth: Depth | null
}

export type PiStatus = PiResult & {
  readonly readiness: "ready" | "absent" | "disabled"
  readonly mode: RolloutMode
  readonly nodes: number
  readonly edges: number
  readonly capabilities: readonly CapabilityStatus[]
}

export type SidecarClientOptions = {
  root: string
  database: string
  python?: string | undefined
  mode?: "off" | "shadow" | "advisory" | "active" | undefined
  userConfig?: string | undefined
  projectConfig?: string | undefined
  startupTimeoutMs?: number
}

type Ready = {
  event: "ready"
  interface: string
  url: string
  token: string
}

export class SidecarClient {
  private process: ChildProcessWithoutNullStreams | undefined
  private ready: Ready | undefined
  private starting: Promise<Ready> | undefined

  constructor(private readonly options: SidecarClientOptions) {}

  async request(operation: string, params: Record<string, unknown> = {}): Promise<unknown> {
    const ready = await this.start()
    try {
      return await requestJson(ready, operation, params)
    } catch (error) {
      if (!isRetryable(error)) throw error
      await this.stop()
      return requestJson(await this.start(), operation, params)
    }
  }

  async stop(): Promise<void> {
    const child = this.process
    this.process = undefined
    this.ready = undefined
    this.starting = undefined
    if (!child || child.exitCode !== null) return
    child.stdin.end()
    child.kill("SIGTERM")
    await Promise.race([
      new Promise<void>((resolve) => child.once("exit", () => resolve())),
      new Promise<void>((resolve) => setTimeout(resolve, 2_000)),
    ])
    if (child.exitCode === null) child.kill("SIGKILL")
  }

  private async start(): Promise<Ready> {
    if (this.ready) return this.ready
    if (this.starting) return this.starting
    this.starting = this.spawnSidecar()
    try {
      this.ready = await this.starting
      return this.ready
    } finally {
      this.starting = undefined
    }
  }

  private async spawnSidecar(): Promise<Ready> {
    const args = [
      "-m",
      "extendcodeagent.adapters.local_sidecar",
      "--root",
      this.options.root,
      "--database",
      this.options.database,
    ]
    if (this.options.mode) args.push("--mode", this.options.mode)
    if (this.options.userConfig) args.push("--user-config", this.options.userConfig)
    if (this.options.projectConfig) args.push("--project-config", this.options.projectConfig)
    args.push("--parent-stdin-lifecycle")
    const child = spawn(this.options.python ?? "python3", args, {
      cwd: this.options.root,
      stdio: ["pipe", "pipe", "pipe"],
      env: process.env,
    })
    this.process = child
    let stderr = ""
    child.stderr.setEncoding("utf8")
    child.stderr.on("data", (chunk: string) => {
      stderr = `${stderr}${chunk}`.slice(-8_192)
    })
    const timeoutMs = this.options.startupTimeoutMs ?? 15_000
    const lines = createInterface({ input: child.stdout })
    return new Promise<Ready>((resolve, reject) => {
      const timeout = setTimeout(() => {
        child.kill("SIGKILL")
        reject(new Error(`sidecar startup timed out after ${timeoutMs}ms: ${stderr}`))
      }, timeoutMs)
      const fail = (error: Error) => {
        clearTimeout(timeout)
        lines.close()
        reject(error)
      }
      child.once("error", fail)
      child.once("exit", (code) => {
        if (!this.ready) fail(new Error(`sidecar exited before ready (${code}): ${stderr}`))
      })
      lines.once("line", (line) => {
        try {
          const value = JSON.parse(line) as Ready
          if (
            value.event !== "ready" ||
            value.interface !== INTERFACE_VERSION ||
            !value.url ||
            !value.token
          ) {
            throw new Error("sidecar returned an incompatible ready envelope")
          }
          clearTimeout(timeout)
          lines.close()
          resolve(value)
        } catch (error) {
          fail(error instanceof Error ? error : new Error(String(error)))
        }
      })
    })
  }
}

async function requestJson(
  ready: Ready,
  operation: string,
  params: Record<string, unknown>,
): Promise<unknown> {
  const response = await fetch(`${ready.url}/v1/request`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${ready.token}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({ interface: INTERFACE_VERSION, operation, params }),
    signal: AbortSignal.timeout(30_000),
  })
  const envelope = (await response.json()) as {
    ok: boolean
    result?: unknown
    error?: string
    message?: string
  }
  if (!response.ok || !envelope.ok) {
    throw new SidecarRequestError(
      response.status,
      envelope.error ?? "sidecar_error",
      envelope.message ?? response.statusText,
    )
  }
  return envelope.result
}

export class SidecarRequestError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
  ) {
    super(`${code}: ${message}`)
  }
}

function isRetryable(error: unknown): boolean {
  return !(error instanceof SidecarRequestError) || error.status >= 500
}
