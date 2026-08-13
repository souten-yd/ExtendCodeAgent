# OpenCode adapter

This package targets the stable OpenCode 1.18.18 plugin interface. It keeps OpenCode and MCP SDK
types outside the host-neutral Python core. Both the plugin tools and standalone MCP server call the
same authenticated, versioned local sidecar.

Install and build:

```bash
npm ci
npm run build
```

Stable OpenCode configuration shape:

```json
{
  "plugin": [
    "file:///absolute/path/to/ExtendCodeAgent/adapters/opencode/dist/src/plugin.js"
  ],
  "mcp": {
    "extendcodeagent": {
      "type": "local",
      "command": [
        "node",
        "/absolute/path/to/ExtendCodeAgent/adapters/opencode/dist/src/mcp.js"
      ],
      "enabled": true,
      "environment": {
        "PYTHONPATH": "/absolute/path/to/ExtendCodeAgent/src",
        "EXTENDCODEAGENT_ROOT": "/absolute/path/to/project",
        "EXTENDCODEAGENT_PYTHON": "/absolute/path/to/ExtendCodeAgent/.venv/bin/python",
        "EXTENDCODEAGENT_MODE": "advisory"
      }
    }
  }
}
```

The plugin-side `EXTENDCODEAGENT_MODE` is a command/session override passed to the central Python
Config Resolver. Supported values are `off`, `shadow`, `advisory`, and `active`. Off starts no
filesystem watcher and performs no graph computation. Shadow refreshes the Twin but rejects
explicit intelligence queries. Advisory permits the six `pi_*` tools without automatic context or
test effects. PR-D does not enable active behavior beyond the same explicit/event surfaces.

OpenCode 1.18.18 did not emit ordinary source changes through its documented watcher event in the
tested Linux environment. The adapter therefore also uses a bounded Chokidar watcher. Native and
fallback events share one coalescing queue, while `.git`, `.extendcodeagent`, dependencies, caches,
and build outputs are rejected before enqueue.

Run the model-free real-host smoke:

```bash
tools/local/opencode-smoke
```
