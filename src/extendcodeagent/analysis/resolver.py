"""Language-owned canonical reference equivalence."""

from __future__ import annotations

from typing import Protocol

from extendcodeagent.graph import GraphSnapshot


class CanonicalReferenceResolver(Protocol):
    def equivalents(self, canonical_ref: str, snapshot: GraphSnapshot) -> tuple[str, ...]: ...


class IdentityReferenceResolver:
    def equivalents(self, canonical_ref: str, snapshot: GraphSnapshot) -> tuple[str, ...]:
        del canonical_ref, snapshot
        return ()


class PythonCanonicalReferenceResolver:
    """Bridge concrete Python symbols and explicit name-only ambiguity nodes."""

    def __init__(self) -> None:
        self._snapshot_identity: int | None = None
        self._aliases_by_target: dict[str, set[str]] = {}
        self._targets_by_package_name: dict[tuple[str, str], set[str]] = {}

    def equivalents(self, canonical_ref: str, snapshot: GraphSnapshot) -> tuple[str, ...]:
        if canonical_ref.startswith("py://") and "#" in canonical_ref:
            self._index_imports(snapshot)
            module, symbol = canonical_ref.removeprefix("py://").split("#", 1)
            short_name = symbol.rsplit(".", 1)[-1]
            equivalents = {f"pyname://{short_name}"}
            normalized_module = _without_source_root(module)
            if normalized_module != module:
                equivalents.add(f"py://{normalized_module}#{symbol}")
            equivalents.update(self._aliases_by_target.get(canonical_ref, ()))
            equivalents.update(
                self._targets_by_package_name.get((normalized_module, short_name), ())
            )
            equivalents.discard(canonical_ref)
            return tuple(sorted(equivalents))
        if canonical_ref.startswith("pyname://"):
            short_name = canonical_ref.removeprefix("pyname://")
            return tuple(
                sorted(
                    node.canonical_ref.value
                    for node in snapshot.nodes
                    if node.canonical_ref.value.startswith("py://")
                    and node.canonical_ref.value.rsplit("#", 1)[-1].rsplit(".", 1)[-1] == short_name
                )
            )
        return ()

    def _index_imports(self, snapshot: GraphSnapshot) -> None:
        identity = id(snapshot)
        if self._snapshot_identity == identity:
            return
        aliases_by_target: dict[str, set[str]] = {}
        targets_by_package_name: dict[tuple[str, str], set[str]] = {}
        for edge in snapshot.edges:
            source = edge.source.value
            target = edge.target.value
            if (
                edge.edge_type != "imports"
                or not source.startswith("module://")
                or not target.startswith("py://")
                or "#" not in target
            ):
                continue
            _, target_symbol = target.removeprefix("py://").split("#", 1)
            short_name = target_symbol.rsplit(".", 1)[-1]
            package = source.removeprefix("module://")
            normalized_package = _without_source_root(package)
            aliases_by_target.setdefault(target, set()).update(
                {
                    f"py://{package}#{short_name}",
                    f"py://{normalized_package}#{short_name}",
                }
            )
            targets_by_package_name.setdefault((normalized_package, short_name), set()).add(target)
        self._snapshot_identity = identity
        self._aliases_by_target = aliases_by_target
        self._targets_by_package_name = targets_by_package_name


def _without_source_root(module: str) -> str:
    return module.removeprefix("src.")
