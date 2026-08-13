"""Minimal contract shared by Twin composition and language analyzers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from extendcodeagent.core.contracts import Diagnostic, ProjectRef
from extendcodeagent.graph.contracts import GraphEdge, GraphNode

if TYPE_CHECKING:
    from extendcodeagent.twin.source_snapshot import SourceSnapshot


@dataclass(frozen=True, slots=True)
class GraphAnalysis:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    diagnostics: tuple[Diagnostic, ...] = ()
    analyzer_versions: tuple[tuple[str, str], ...] = ()


class GraphAnalyzer(Protocol):
    @property
    def analyzer_versions(self) -> tuple[tuple[str, str], ...]: ...

    def analyze(
        self,
        project: ProjectRef,
        snapshot: SourceSnapshot,
        *,
        paths: tuple[str, ...] | None = None,
    ) -> GraphAnalysis: ...
