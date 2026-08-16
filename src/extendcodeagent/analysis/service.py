"""Deterministic, revision-aware path and impact analysis."""

from __future__ import annotations

from collections import deque

from extendcodeagent.core.contracts import Diagnostic
from extendcodeagent.graph import FactStatus, GraphEdge, GraphSnapshot

from .contracts import (
    GraphPath,
    ImpactItem,
    ImpactQuery,
    ImpactReport,
    PathQuery,
    PathResult,
)
from .resolver import CanonicalReferenceResolver, IdentityReferenceResolver

_CONTAINER_TYPES = frozenset({"repository", "directory", "file", "module", "package"})
_SIDE_EFFECT_TYPES = frozenset({"side_effect", "resource", "api_call", "db_effect"})
_REQUIREMENT_TYPES = frozenset({"requirement"})
_TEST_TYPES = frozenset({"test"})
_HISTORICAL_TYPES = frozenset({"incident", "risk"})
_EXECUTABLE_TYPES = frozenset({"function", "method", "api_route", "handler"})
_UNCERTAIN_CONFIDENCE = 0.7


class GraphAnalysisService:
    def __init__(
        self,
        snapshot: GraphSnapshot,
        resolver: CanonicalReferenceResolver | None = None,
    ) -> None:
        self.snapshot = snapshot
        self.resolver = resolver or IdentityReferenceResolver()
        self.nodes = {node.canonical_ref.value: node for node in snapshot.nodes}
        self.forward: dict[str, list[GraphEdge]] = {}
        self.reverse: dict[str, list[GraphEdge]] = {}
        for edge in snapshot.edges:
            self.forward.setdefault(edge.source.value, []).append(edge)
            self.reverse.setdefault(edge.target.value, []).append(edge)
        for values in (*self.forward.values(), *self.reverse.values()):
            values.sort(key=lambda edge: (edge.edge_type, edge.source.value, edge.target.value))

    def trace_path(self, query: PathQuery) -> PathResult:
        allowed = frozenset(query.allowed_edge_types)
        statuses = frozenset(query.statuses)
        paths: list[GraphPath] = []
        stack: list[tuple[str, tuple[str, ...], tuple[GraphEdge, ...]]] = [
            (query.source_ref, (query.source_ref,), ())
        ]
        exhausted_more = False
        while stack:
            current, node_refs, path_edges = stack.pop()
            if query.target_ref is not None and current == query.target_ref and path_edges:
                if len(paths) >= query.max_paths:
                    exhausted_more = True
                    break
                paths.append(_path(node_refs, path_edges))
                continue
            if len(path_edges) >= query.max_depth:
                if query.target_ref is None and path_edges:
                    if len(paths) >= query.max_paths:
                        exhausted_more = True
                        break
                    paths.append(_path(node_refs, path_edges))
                continue
            candidates = [
                edge
                for edge in self.forward.get(current, ())
                if (not allowed or edge.edge_type in allowed)
                and edge.status in statuses
                and _edge_meets_confidence(
                    edge, query.min_confidence, query.min_inferred_confidence
                )
                and edge.target.value not in node_refs
            ]
            if not candidates and query.target_ref is None and path_edges:
                if len(paths) >= query.max_paths:
                    exhausted_more = True
                    break
                paths.append(_path(node_refs, path_edges))
            for edge in reversed(candidates):
                stack.append(
                    (edge.target.value, (*node_refs, edge.target.value), (*path_edges, edge))
                )
        diagnostics: tuple[Diagnostic, ...] = ()
        if not paths:
            diagnostics = (
                Diagnostic(
                    "no_path_found",
                    f"no path from {query.source_ref} to {query.target_ref or 'a leaf'}",
                    refs=tuple(item for item in (query.source_ref, query.target_ref) if item),
                ),
            )
        return PathResult(self.snapshot.revision, tuple(paths), exhausted_more, diagnostics)

    def assess_impact(self, query: ImpactQuery) -> ImpactReport:
        seeds = set(query.changed_refs)
        for ref in tuple(seeds):
            seeds.update(self.resolver.equivalents(ref, self.snapshot))

        implementation_refs: set[str] = set()
        implementation_queue: deque[tuple[str, tuple[str, ...], tuple[GraphEdge, ...]]] = deque(
            (seed, (seed,), ()) for seed in sorted(seeds)
        )
        seen_forward = set(seeds)
        while implementation_queue:
            current, refs, edges = implementation_queue.popleft()
            for edge in self.forward.get(current, ()):
                if (
                    edge.edge_type not in query.forward_implementation_edges
                    or not _edge_meets_confidence(
                        edge, query.min_confidence, query.min_inferred_confidence
                    )
                    or len(edges) >= query.max_depth
                ):
                    continue
                target = edge.target.value
                if target in seen_forward:
                    continue
                seen_forward.add(target)
                implementation_refs.add(target)
                implementation_queue.append((target, (*refs, target), (*edges, edge)))

        traversal_seeds = seeds | implementation_refs
        depth: dict[str, int] = {ref: 0 for ref in traversal_seeds}
        path_confidence: dict[str, float] = {ref: 1.0 for ref in traversal_seeds}
        inferred_path: dict[str, bool] = {ref: False for ref in traversal_seeds}
        paths: dict[str, tuple[tuple[str, ...], tuple[GraphEdge, ...]]] = {
            ref: ((ref,), ()) for ref in traversal_seeds
        }
        impact_queue: deque[str] = deque(sorted(traversal_seeds))
        while impact_queue:
            current = impact_queue.popleft()
            current_depth = depth[current]
            if current_depth >= query.max_depth:
                continue
            for edge in self.reverse.get(current, ()):
                if not _edge_meets_confidence(
                    edge, query.min_confidence, query.min_inferred_confidence
                ):
                    continue
                source = edge.source.value
                candidate_confidence = min(path_confidence[current], edge.confidence.value)
                candidate_depth = current_depth + 1
                if source in depth and (
                    depth[source] < candidate_depth
                    or (
                        depth[source] == candidate_depth
                        and path_confidence[source] >= candidate_confidence
                    )
                ):
                    continue
                depth[source] = candidate_depth
                path_confidence[source] = candidate_confidence
                inferred_path[source] = inferred_path[current] or edge.status is FactStatus.INFERRED
                current_refs, current_edges = paths[current]
                paths[source] = ((*current_refs, source), (*current_edges, edge))
                impact_queue.append(source)
                for equivalent in self.resolver.equivalents(source, self.snapshot):
                    if equivalent not in depth:
                        depth[equivalent] = candidate_depth
                        path_confidence[equivalent] = candidate_confidence
                        inferred_path[equivalent] = inferred_path[source]
                        paths[equivalent] = paths[source]
                        impact_queue.append(equivalent)

        reason = {ref: "implements_changed_entity" for ref in implementation_refs}
        items: list[tuple[int, ImpactItem]] = []
        for ref, item_depth in depth.items():
            if ref in traversal_seeds and ref not in implementation_refs:
                continue
            node = self.nodes.get(ref)
            if node is None or node.node_type in _CONTAINER_TYPES:
                continue
            status = FactStatus.INFERRED if inferred_path.get(ref, False) else node.status
            items.append(
                (
                    max(1, item_depth),
                    ImpactItem(
                        ref,
                        node.node_type,
                        status,
                        node.confidence.value,
                        path_confidence.get(ref, node.confidence.value),
                        node.source_ref,
                        reason.get(ref, f"reverse_dependency_depth_{max(1, item_depth)}"),
                    ),
                )
            )
        items.sort(key=lambda pair: (pair[0], pair[1].canonical_ref))
        direct = tuple(item for item_depth, item in items if item_depth <= 1)
        transitive = tuple(item for item_depth, item in items if item_depth > 1)
        requirements = tuple(item for _, item in items if item.item_type in _REQUIREMENT_TYPES)
        tests = tuple(item for _, item in items if item.item_type in _TEST_TYPES)
        history = (
            tuple(item for _, item in items if item.item_type in _HISTORICAL_TYPES)
            if query.include_historical
            else ()
        )
        uncertainty = tuple(
            item
            for _, item in items
            if item.status is FactStatus.INFERRED
            or item.confidence < 0.5
            or item.path_confidence < _UNCERTAIN_CONFIDENCE
        )

        effect_roots = traversal_seeds | {
            ref
            for ref in depth
            if ref in self.nodes and self.nodes[ref].node_type in _EXECUTABLE_TYPES
        }
        side_effects = self._side_effects(
            effect_roots,
            query.min_confidence,
            query.min_inferred_confidence,
            query.max_depth,
        )
        explanations = tuple(
            _reverse_path(*paths[item.canonical_ref])
            for _, item in items
            if item.canonical_ref in paths
        )
        diagnostics: tuple[Diagnostic, ...] = ()
        if not direct and not transitive and not side_effects:
            diagnostics = (
                Diagnostic("no_impact_found", "no impact found", refs=query.changed_refs),
            )
        return ImpactReport(
            self.snapshot.revision,
            direct,
            transitive,
            requirements,
            side_effects,
            tests,
            history,
            uncertainty,
            explanations,
            diagnostics,
        )

    def _side_effects(
        self,
        roots: set[str],
        min_confidence: float,
        min_inferred_confidence: float,
        max_depth: int,
    ) -> tuple[ImpactItem, ...]:
        found: dict[str, ImpactItem] = {}
        queue = deque((root, 0, 1.0, False) for root in sorted(roots))
        visited: dict[str, float] = {root: 1.0 for root in roots}
        while queue:
            current, depth, confidence, inferred = queue.popleft()
            if depth >= max_depth:
                continue
            for edge in self.forward.get(current, ()):
                if not _edge_meets_confidence(edge, min_confidence, min_inferred_confidence):
                    continue
                target = edge.target.value
                path_confidence = min(confidence, edge.confidence.value)
                path_inferred = inferred or edge.status is FactStatus.INFERRED
                node = self.nodes.get(target)
                if node and node.node_type in _SIDE_EFFECT_TYPES:
                    found[target] = ImpactItem(
                        target,
                        node.node_type,
                        FactStatus.INFERRED if path_inferred else node.status,
                        node.confidence.value,
                        path_confidence,
                        node.source_ref,
                        "side_effect_of_change",
                    )
                if visited.get(target, -1.0) < path_confidence:
                    visited[target] = path_confidence
                    queue.append((target, depth + 1, path_confidence, path_inferred))
        return tuple(found[key] for key in sorted(found))


def _edge_meets_confidence(
    edge: GraphEdge, min_confidence: float, min_inferred_confidence: float
) -> bool:
    """Apply the caller floor to all facts and the depth floor only to inferred facts."""

    required = max(
        min_confidence,
        min_inferred_confidence if edge.status is FactStatus.INFERRED else 0.0,
    )
    return edge.confidence.value >= required


def _path(node_refs: tuple[str, ...], edges: tuple[GraphEdge, ...]) -> GraphPath:
    confidence = min((edge.confidence.value for edge in edges), default=1.0)
    edge_types = tuple(edge.edge_type for edge in edges)
    return GraphPath(
        node_refs,
        edge_types,
        confidence,
        any(edge.status is FactStatus.INFERRED for edge in edges),
        " -> ".join(
            f"{node_refs[index]} =[{edge.edge_type}]=> {node_refs[index + 1]}"
            for index, edge in enumerate(edges)
        ),
    )


def _reverse_path(node_refs: tuple[str, ...], edges: tuple[GraphEdge, ...]) -> GraphPath:
    confidence = min((edge.confidence.value for edge in edges), default=1.0)
    return GraphPath(
        node_refs,
        tuple(f"reverse:{edge.edge_type}" for edge in edges),
        confidence,
        any(edge.status is FactStatus.INFERRED for edge in edges),
        " <- ".join(node_refs),
    )
