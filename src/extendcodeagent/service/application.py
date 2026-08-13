"""Versioned host-neutral Project Intelligence query application."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from extendcodeagent.analysis import (
    GraphAnalysisService,
    ImpactQuery,
    PathQuery,
    PythonCanonicalReferenceResolver,
)
from extendcodeagent.core.config.schema import CapabilityName, RolloutMode
from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.graph import GraphSnapshot
from extendcodeagent.graph.analyzers import PythonGraphAnalyzer
from extendcodeagent.storage import SqliteGraphStore
from extendcodeagent.twin import TwinService

INTERFACE_VERSION = "extendcodeagent.local.v1"


class CapabilityUnavailable(RuntimeError):
    pass


class ProjectIntelligenceApplication:
    """Own one project store and expose bounded JSON-compatible operations."""

    def __init__(
        self,
        root: str | Path,
        database: str | Path,
        policy: CapabilityPolicy,
        *,
        max_items: int = 100,
        max_depth: int = 6,
    ) -> None:
        self.root = Path(root).resolve()
        self.database = Path(database)
        self.policy = policy
        self.max_items = max_items
        self.max_depth = max_depth
        digest = hashlib.sha256(str(self.root).encode()).hexdigest()[:12]
        self.project = ProjectRef(f"{self.root.name}-{digest}", "default", self.root.as_uri())
        self._store: SqliteGraphStore | None = None
        self._twin: TwinService | None = None

    def __enter__(self) -> ProjectIntelligenceApplication:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._store is not None:
            self._store.close()
            self._store = None
            self._twin = None

    def status(self) -> dict[str, Any]:
        mode = self.policy.mode(CapabilityName.GRAPH)
        if mode is RolloutMode.OFF:
            return {
                "interface": INTERFACE_VERSION,
                "readiness": "disabled",
                "mode": mode.value,
                "revision_id": None,
                "nodes": 0,
                "edges": 0,
            }
        snapshot = self._ensure_twin().snapshot(self.project)
        return {
            "interface": INTERFACE_VERSION,
            "readiness": "ready" if snapshot.revision else "absent",
            "mode": mode.value,
            "revision_id": snapshot.revision.revision_id if snapshot.revision else None,
            "nodes": len(snapshot.nodes),
            "edges": len(snapshot.edges),
        }

    def process_event(self, paths: tuple[str, ...], kind: str) -> dict[str, Any]:
        if not all(
            self.policy.computes_automatically(capability)
            for capability in (CapabilityName.GRAPH, CapabilityName.TWIN, CapabilityName.SEMANTIC)
        ):
            return {"accepted": False, "kind": kind, "revision_id": None}
        twin = self._ensure_twin()
        current = twin.snapshot(self.project).revision
        result = (
            twin.refresh(self.project, changed_paths=tuple(sorted(set(paths))))
            if current and paths
            else twin.open(self.project)
        )
        return {
            "accepted": True,
            "kind": kind,
            "revision_id": result.revision.revision_id if result.revision else None,
            "affected_paths": list(result.affected_paths),
            "diagnostics": [item.code for item in result.diagnostics],
        }

    def symbol(self, query: str) -> dict[str, Any]:
        snapshot = self._explicit_snapshot(CapabilityName.SEMANTIC)
        lowered = query.casefold()
        items = [
            _node_json(node)
            for node in snapshot.nodes
            if lowered in node.canonical_ref.value.casefold()
            or lowered in str(node.properties.get("name", "")).casefold()
        ][: self.max_items]
        return _result(snapshot, items=items)

    def references(self, canonical_ref: str) -> dict[str, Any]:
        snapshot = self._explicit_snapshot(CapabilityName.SEMANTIC)
        items = [_edge_json(edge) for edge in snapshot.edges if edge.target.value == canonical_ref][
            : self.max_items
        ]
        return _result(snapshot, items=items)

    def path(
        self,
        source_ref: str,
        target_ref: str | None = None,
        *,
        allowed_edge_types: tuple[str, ...] = (),
        min_confidence: float = 0.0,
        max_depth: int | None = None,
        max_paths: int = 20,
    ) -> dict[str, Any]:
        snapshot = self._explicit_snapshot(CapabilityName.IMPACT)
        result = GraphAnalysisService(snapshot, PythonCanonicalReferenceResolver()).trace_path(
            PathQuery(
                source_ref,
                target_ref,
                allowed_edge_types,
                min_confidence=min_confidence,
                max_depth=min(max_depth or self.max_depth, self.max_depth),
                max_paths=min(max_paths, self.max_items),
            )
        )
        return _result(
            snapshot,
            paths=[_path_json(item) for item in result.paths],
            truncated=result.truncated,
            diagnostics=[item.code for item in result.diagnostics],
        )

    def impact(
        self,
        changed_refs: tuple[str, ...],
        *,
        min_confidence: float = 0.0,
        max_depth: int | None = None,
        include_historical: bool = False,
    ) -> dict[str, Any]:
        snapshot = self._explicit_snapshot(CapabilityName.IMPACT)
        report = self._impact_report(
            snapshot,
            changed_refs,
            min_confidence=min_confidence,
            max_depth=max_depth,
            include_historical=include_historical,
        )
        return _result(
            snapshot,
            direct=[_impact_json(item) for item in report.direct_impacts],
            transitive=[_impact_json(item) for item in report.transitive_impacts],
            requirements=[_impact_json(item) for item in report.affected_requirements],
            side_effects=[_impact_json(item) for item in report.side_effects],
            tests=[_impact_json(item) for item in report.recommended_tests],
            historical_risks=[_impact_json(item) for item in report.historical_risks],
            uncertainty=[_impact_json(item) for item in report.uncertainty],
            explanation_paths=[_path_json(item) for item in report.explanation_paths],
            diagnostics=[item.code for item in report.diagnostics],
        )

    def tests(self, changed_refs: tuple[str, ...]) -> dict[str, Any]:
        snapshot = self._explicit_snapshot(CapabilityName.TEST_SELECTION)
        report = self._impact_report(snapshot, changed_refs)
        return _result(
            snapshot,
            items=[_impact_json(item) for item in report.recommended_tests],
            fallback="full_suite" if not report.recommended_tests else None,
        )

    def _impact_report(
        self,
        snapshot: GraphSnapshot,
        changed_refs: tuple[str, ...],
        *,
        min_confidence: float = 0.0,
        max_depth: int | None = None,
        include_historical: bool = False,
    ) -> Any:
        return GraphAnalysisService(snapshot, PythonCanonicalReferenceResolver()).assess_impact(
            ImpactQuery(
                changed_refs,
                min_confidence=min_confidence,
                max_depth=min(max_depth or self.max_depth, self.max_depth),
                include_historical=include_historical,
            )
        )

    def _explicit_snapshot(self, capability: CapabilityName) -> GraphSnapshot:
        if not self.policy.allows_explicit_use(capability):
            raise CapabilityUnavailable(f"{capability.value} is not available for explicit use")
        return self._snapshot(open_if_missing=True)

    def _snapshot(self, *, open_if_missing: bool) -> GraphSnapshot:
        if self._twin is None:
            if not open_if_missing:
                return GraphSnapshot(self.project, None)
            twin = self._ensure_twin()
        else:
            twin = self._twin
        snapshot = twin.snapshot(self.project)
        if open_if_missing and snapshot.revision is None:
            twin.open(self.project)
            snapshot = twin.snapshot(self.project)
        return snapshot

    def _ensure_twin(self) -> TwinService:
        if self._twin is None:
            self.database.parent.mkdir(parents=True, exist_ok=True)
            self._store = SqliteGraphStore(self.database)
            self._twin = TwinService(self._store, analyzer=PythonGraphAnalyzer())
        return self._twin


def _result(snapshot: GraphSnapshot, **values: Any) -> dict[str, Any]:
    return {
        "interface": INTERFACE_VERSION,
        "revision_id": snapshot.revision.revision_id if snapshot.revision else None,
        **values,
    }


def _node_json(node: Any) -> dict[str, Any]:
    return {
        "canonical_ref": node.canonical_ref.value,
        "type": node.node_type,
        "source_ref": node.source_ref,
        "confidence": node.confidence.value,
        "status": node.status.value,
        "properties": dict(node.properties),
    }


def _edge_json(edge: Any) -> dict[str, Any]:
    return {
        "source": edge.source.value,
        "target": edge.target.value,
        "type": edge.edge_type,
        "source_ref": edge.source_ref,
        "confidence": edge.confidence.value,
        "status": edge.status.value,
    }


def _impact_json(item: Any) -> dict[str, Any]:
    return {
        "canonical_ref": item.canonical_ref,
        "type": item.item_type,
        "source_ref": item.source_ref,
        "confidence": item.confidence,
        "path_confidence": item.path_confidence,
        "status": item.status.value,
        "reason": item.reason,
    }


def _path_json(item: Any) -> dict[str, Any]:
    return {
        "node_refs": list(item.node_refs),
        "edge_types": list(item.edge_types),
        "min_confidence": item.min_confidence,
        "contains_inferred": item.contains_inferred,
        "explanation": item.explanation,
    }
