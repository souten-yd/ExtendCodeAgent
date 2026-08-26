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


class CompositeCanonicalReferenceResolver:
    def __init__(self, resolvers: tuple[CanonicalReferenceResolver, ...]) -> None:
        self.resolvers = resolvers

    def equivalents(self, canonical_ref: str, snapshot: GraphSnapshot) -> tuple[str, ...]:
        values = {
            value
            for resolver in self.resolvers
            for value in resolver.equivalents(canonical_ref, snapshot)
        }
        values.discard(canonical_ref)
        return tuple(sorted(values))


class SourceFileReferenceResolver:
    """A file reference stands for the symbols that file defines.

    Developers change files; the graph relates symbols. Without this bridge a `file://`
    reference reaches nothing, because a file node carries containment edges rather than
    call or reference edges, so Impact and every consumer of equivalence answered a
    file-level question with silence.

    The expansion is bounded and deterministic: a very large file would otherwise seed a
    traversal with hundreds of roots, and truncating without order would make the answer
    depend on graph iteration.
    """

    def __init__(self, *, max_symbols: int = 200) -> None:
        if max_symbols <= 0:
            raise ValueError("max_symbols must be positive")
        self.max_symbols = max_symbols

    def equivalents(self, canonical_ref: str, snapshot: GraphSnapshot) -> tuple[str, ...]:
        if not canonical_ref.startswith("file://"):
            return ()
        source_ref = canonical_ref.removeprefix("file://")
        defined = sorted(
            node.canonical_ref.value
            for node in snapshot.nodes
            if node.source_ref == source_ref
            and node.node_type not in {"file", "directory", "repository"}
        )
        return tuple(defined[: self.max_symbols])


class JavaScriptTypeScriptCanonicalReferenceResolver:
    """Bridge file-qualified JS/TS symbols and explicit name-only ambiguity nodes."""

    def equivalents(self, canonical_ref: str, snapshot: GraphSnapshot) -> tuple[str, ...]:
        if canonical_ref.startswith("js://") and "#" in canonical_ref:
            short_name = canonical_ref.rsplit("#", 1)[-1].rsplit(".", 1)[-1]
            return (f"jsname://{short_name}",)
        if canonical_ref.startswith("jsname://"):
            short_name = canonical_ref.removeprefix("jsname://")
            return tuple(
                sorted(
                    node.canonical_ref.value
                    for node in snapshot.nodes
                    if node.canonical_ref.value.startswith("js://")
                    and node.canonical_ref.value.rsplit("#", 1)[-1].rsplit(".", 1)[-1] == short_name
                )
            )
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
