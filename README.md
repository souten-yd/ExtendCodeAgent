# ExtendCodeAgent

ExtendCodeAgent is a host-neutral Project Intelligence layer intended to integrate with
OpenCode through thin adapters without forking OpenCode. The current implementation includes the
PR-A foundation, durable Graph/Twin revisions, Python semantic/path/impact intelligence, and the
PR-D stable OpenCode/MCP adapter.

Local validation:

```bash
tools/local/bootstrap
tools/local/all-fast
tools/local/build
tools/local/test-integration
```

After installing stable OpenCode 1.18.18, run the model-free real-host check with
`tools/local/opencode-smoke`. Adapter configuration is documented in `adapters/opencode/README.md`.
