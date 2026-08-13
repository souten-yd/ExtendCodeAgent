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

    def equivalents(self, canonical_ref: str, snapshot: GraphSnapshot) -> tuple[str, ...]:
        if canonical_ref.startswith("py://") and "#" in canonical_ref:
            short_name = canonical_ref.rsplit("#", 1)[1].rsplit(".", 1)[-1]
            return (f"pyname://{short_name}",)
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
