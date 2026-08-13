import { relative, resolve } from "node:path"

const IGNORED_WORKSPACE_NAMES = new Set([
  ".git",
  ".hg",
  ".svn",
  ".venv",
  "venv",
  "node_modules",
  "dist",
  "build",
  "__pycache__",
  ".pytest_cache",
  ".mypy_cache",
  ".ruff_cache",
  ".extendcodeagent",
])

export function workspacePath(root: string, path: string): string | undefined {
  const absolute = resolve(root, path)
  const value = relative(root, absolute)
  if (value === ".." || value.startsWith(`..${process.platform === "win32" ? "\\" : "/"}`)) {
    return undefined
  }
  const normalized = value.replaceAll("\\", "/")
  if (
    normalized
      .split("/")
      .some(
        (part) =>
          IGNORED_WORKSPACE_NAMES.has(part.toLowerCase()) ||
          part.toLowerCase().endsWith(".egg-info"),
      )
  ) {
    return undefined
  }
  return normalized
}
