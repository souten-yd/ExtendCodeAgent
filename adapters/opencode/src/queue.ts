export type ProjectEvent = {
  kind: string
  paths: string[]
}

export class CoalescingEventQueue {
  private readonly pending = new Map<string, Set<string>>()
  private timer: NodeJS.Timeout | undefined
  private chain = Promise.resolve()

  constructor(
    private readonly consume: (event: ProjectEvent) => Promise<void>,
    private readonly delayMs = 100,
  ) {}

  enqueue(kind: string, paths: string[] = []): void {
    const existing = this.pending.get(kind) ?? new Set<string>()
    for (const path of paths) existing.add(path)
    this.pending.set(kind, existing)
    if (!this.timer) this.timer = setTimeout(() => void this.flush(), this.delayMs)
  }

  async flush(): Promise<void> {
    if (this.timer) clearTimeout(this.timer)
    this.timer = undefined
    const batch = [...this.pending.entries()].map(([kind, paths]) => ({
      kind,
      paths: [...paths].sort(),
    }))
    this.pending.clear()
    this.chain = this.chain.then(async () => {
      for (const event of batch) await this.consume(event)
    })
    return this.chain
  }

  async close(): Promise<void> {
    await this.flush()
  }
}
