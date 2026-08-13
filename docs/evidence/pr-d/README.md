# PR-D real OpenCode evidence

`real-opencode-smoke.json` is the compact result of the reproducible, model-free
`tools/local/opencode-smoke` run against stable OpenCode 1.18.18.

The smoke starts a native `--pure` baseline and a plugin-enabled server on temporary local Git
projects. It verifies project bootstrap, the six plugin tools, an advisory MCP connection, an
OpenCode session-shell tool edit, a separate external edit, immutable Twin revision updates,
absence of a refresh loop, restart persistence, MCP reconnect, and an off-mode negative control.

The first native OpenCode watcher experiment observed `.git/index.lock` events but did not emit
ordinary tracked source edits even after its inotify backend was initialized. Processing the Git
events originally caused a refresh feedback loop. PR-D therefore filters ignored/managed paths and
uses a Chokidar fallback in the adapter. This is an ADAPT decision based on real-host behavior, not
a claim that OpenCode's documented watcher contract is permanently unavailable.

The recorded startup comparison uses three alternating-order samples per mode and reports the
median while retaining raw values, including one 1,609 ms native outlier. This small smoke sample
must not be presented as a statistically stable distribution or general performance claim.
