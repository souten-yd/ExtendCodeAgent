"""Small deterministic composition for independently selected language analyzers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from extendcodeagent.core.contracts import ProjectRef

from .contracts import GraphAnalysis, GraphAnalyzer

if TYPE_CHECKING:
    from extendcodeagent.twin.source_snapshot import SourceSnapshot


@dataclass(frozen=True, slots=True)
class CompositeGraphAnalyzer:
    analyzers: tuple[GraphAnalyzer, ...]
    analyzer_versions: tuple[tuple[str, str], ...] = field(init=False)

    def __post_init__(self) -> None:
        versions = [item for analyzer in self.analyzers for item in analyzer.analyzer_versions]
        if len(dict(versions)) != len(versions):
            raise ValueError("composed analyzer version keys must be unique")
        object.__setattr__(
            self,
            "analyzer_versions",
            tuple(
                sorted(item for analyzer in self.analyzers for item in analyzer.analyzer_versions)
            ),
        )

    def analyze(
        self,
        project: ProjectRef,
        snapshot: SourceSnapshot,
        *,
        paths: tuple[str, ...] | None = None,
    ) -> GraphAnalysis:
        results = tuple(
            analyzer.analyze(project, snapshot, paths=paths) for analyzer in self.analyzers
        )
        nodes = {item.node_id: item for result in results for item in result.nodes}
        edges = {item.edge_id: item for result in results for item in result.edges}
        return GraphAnalysis(
            tuple(sorted(nodes.values(), key=lambda item: item.canonical_ref.value)),
            tuple(sorted(edges.values(), key=lambda item: item.edge_id)),
            tuple(item for result in results for item in result.diagnostics),
            self.analyzer_versions,
        )
