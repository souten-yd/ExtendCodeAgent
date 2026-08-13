"""Versioned host-neutral Project Intelligence query application."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from extendcodeagent.analysis import (
    CanonicalReferenceResolver,
    CompositeCanonicalReferenceResolver,
    GraphAnalysisService,
    ImpactQuery,
    JavaScriptTypeScriptCanonicalReferenceResolver,
    PathQuery,
    PythonCanonicalReferenceResolver,
)
from extendcodeagent.blueprint import (
    BlueprintElement,
    BlueprintService,
    BlueprintView,
)
from extendcodeagent.blueprint.storage import SqliteBlueprintRepository
from extendcodeagent.context import ContextProfile, ContextRequest, build_context
from extendcodeagent.convergence import (
    ActualSnapshot,
    ConvergenceRecommendation,
    ConvergenceReport,
    TargetElement,
    TargetSnapshot,
    VerificationEvidence,
    decide_convergence,
    evaluate_convergence,
)
from extendcodeagent.convergence.storage import SqliteConvergenceRepository
from extendcodeagent.core.config.schema import KNOWN_ANALYZERS, CapabilityName, RolloutMode
from extendcodeagent.core.contracts import (
    CanonicalRef,
    ProjectRef,
    Provenance,
    SourceRevision,
    TwinRevisionRef,
)
from extendcodeagent.core.policy import CapabilityPolicy
from extendcodeagent.graph import GraphSnapshot
from extendcodeagent.graph.analyzers import (
    CompositeGraphAnalyzer,
    GraphAnalyzer,
    JavaScriptTypeScriptGraphAnalyzer,
    PythonGraphAnalyzer,
)
from extendcodeagent.research import ResearchDepth, ResearchRequest, build_research_plan
from extendcodeagent.runtime import ObservationKind, ObservationStatus, RuntimeObservation
from extendcodeagent.storage import SqliteGraphStore
from extendcodeagent.testing import TestHealthSignals, evaluate_test_health, select_tests
from extendcodeagent.traceability import (
    ProjectRequirementReport,
    Requirement,
    RequirementEvidence,
    evaluate_project_requirements,
)
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
        analyzers: tuple[str, ...] = KNOWN_ANALYZERS,
    ) -> None:
        self.root = Path(root).resolve()
        self.database = Path(database)
        self.policy = policy
        self.max_items = max_items
        self.max_depth = max_depth
        self.analyzers = analyzers
        digest = hashlib.sha256(str(self.root).encode()).hexdigest()[:12]
        self.project = ProjectRef(f"{self.root.name}-{digest}", "default", self.root.as_uri())
        self._store: SqliteGraphStore | None = None
        self._twin: TwinService | None = None
        self._blueprints: BlueprintService | None = None

    def __enter__(self) -> ProjectIntelligenceApplication:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._store is not None:
            self._store.close()
            self._store = None
            self._twin = None
            self._blueprints = None

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
        result = GraphAnalysisService(snapshot, self._reference_resolver()).trace_path(
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
        selection = select_tests(report)
        observations = self._ensure_store().observations(
            self.project,
            refs=tuple(
                CanonicalRef(item)
                for item in (
                    *changed_refs,
                    *(candidate.canonical_ref.value for candidate in selection.candidates),
                )
            ),
            limit=self.max_items,
        )
        current_revision = snapshot.revision.source_revision if snapshot.revision else None
        health = (
            [
                _health_json(
                    evaluate_test_health(
                        TestHealthSignals(
                            candidate.canonical_ref,
                            target_refs=tuple(CanonicalRef(item) for item in changed_refs),
                            changed_refs=tuple(CanonicalRef(item) for item in changed_refs),
                            observations=observations,
                        ),
                        current_revision=current_revision,
                    )
                )
                for candidate in selection.candidates
            ]
            if current_revision
            else []
        )
        return _result(
            snapshot,
            items=[_impact_json(item) for item in report.recommended_tests],
            fallback=selection.fallback,
            health=health,
            diagnostics=list(selection.diagnostics),
        )

    def source_revision(self) -> str:
        return self._current_source_revision().value

    def _current_source_revision(self) -> SourceRevision:
        snapshot = self._snapshot(open_if_missing=True)
        if snapshot.revision is None:
            raise CapabilityUnavailable("no source revision is available")
        return snapshot.revision.source_revision

    def ingest_runtime(
        self,
        *,
        observation_id: str,
        kind: str,
        status: str,
        started_at: datetime,
        finished_at: datetime,
        observed_refs: tuple[str, ...] = (),
        command: str | None = None,
        tool: str | None = None,
        summary: str = "",
        source_revision: str | None = None,
        automatic: bool = True,
    ) -> dict[str, Any]:
        allowed = (
            self.policy.computes_automatically(CapabilityName.RUNTIME)
            if automatic
            else self.policy.allows_explicit_use(CapabilityName.RUNTIME)
        )
        if not allowed:
            return {"accepted": False, "observation_id": observation_id}
        current_revision = self._current_source_revision()
        revision = (
            current_revision
            if source_revision is None or source_revision == current_revision.value
            else SourceRevision(source_revision)
        )
        producer = tool or command or kind
        observation = RuntimeObservation(
            observation_id,
            ObservationKind(kind),
            self.project,
            revision,
            ObservationStatus(status),
            started_at,
            finished_at,
            Provenance("runtime", producer, "1", revision),
            tuple(CanonicalRef(item) for item in observed_refs),
            command,
            tool,
            summary=summary,
        )
        inserted = self._ensure_store().put_observation(observation)
        return {
            "accepted": True,
            "observation_id": observation_id,
            "inserted": inserted,
            "source_revision": revision.value,
        }

    def runtime_evidence(self, refs: tuple[str, ...] = ()) -> dict[str, Any]:
        if not self.policy.allows_explicit_use(CapabilityName.RUNTIME):
            raise CapabilityUnavailable("runtime is not available for explicit use")
        snapshot = self._snapshot(open_if_missing=True)
        observations = self._ensure_store().observations(
            self.project,
            refs=tuple(CanonicalRef(item) for item in refs),
            limit=self.max_items,
        )
        return _result(snapshot, items=[_observation_json(item) for item in observations])

    def context(
        self,
        objective: str,
        target_refs: tuple[str, ...] = (),
        *,
        profile: str = "standard",
        token_budget: int = 2_000,
    ) -> dict[str, Any]:
        snapshot = self._explicit_snapshot(CapabilityName.CONTEXT)
        package = build_context(
            snapshot,
            ContextRequest(
                objective,
                tuple(CanonicalRef(item) for item in target_refs),
                token_budget,
                self.max_items,
                profile=ContextProfile(profile),
            ),
        )
        return _result(
            snapshot,
            items=[_context_json(item) for item in package.items],
            used_tokens=package.used_tokens,
            token_budget=package.token_budget,
            truncated=package.truncated,
            excluded_count=package.excluded_count,
        )

    def create_blueprint(
        self,
        elements: tuple[BlueprintElement, ...],
        *,
        durable: bool = True,
    ) -> BlueprintView | None:
        if not self.policy.allows_explicit_use(CapabilityName.BLUEPRINT):
            raise CapabilityUnavailable("blueprint is not available for explicit use")
        return self._ensure_blueprints().create(self.project, elements, durable=durable)

    def review_blueprint(self, revision_id: str) -> BlueprintView:
        self._require_explicit(CapabilityName.BLUEPRINT)
        return self._ensure_blueprints().review(self.project, revision_id)

    def approve_blueprint(self, revision_id: str) -> BlueprintView:
        self._require_explicit(CapabilityName.BLUEPRINT)
        return self._ensure_blueprints().approve(self.project, revision_id)

    def activate_blueprint(self, revision_id: str) -> BlueprintView:
        self._require_explicit(CapabilityName.BLUEPRINT)
        return self._ensure_blueprints().activate(self.project, revision_id)

    def evaluate_task_convergence(
        self,
        blueprint_revision_id: str,
        actual: ActualSnapshot,
        verification: tuple[VerificationEvidence, ...] = (),
        *,
        unsafe: bool = False,
        decision_required: bool = False,
        target_invalid: bool = False,
        interface_changed: tuple[str, ...] = (),
    ) -> tuple[ConvergenceReport, ConvergenceRecommendation]:
        self._require_explicit(CapabilityName.CONVERGENCE)
        view = self._ensure_blueprints().get(self.project, blueprint_revision_id)
        target = TargetSnapshot(
            self.project,
            view.revision.revision_id,
            tuple(
                TargetElement(
                    item.element_id,
                    item.planned_ref,
                    item.expected_actual_refs,
                    item.mandatory,
                    item.requires_verification,
                    item.depends_on_element_ids,
                )
                for item in view.revision.elements
            ),
        )
        report = evaluate_convergence(target, actual, verification)
        recommendation = decide_convergence(
            report,
            unsafe=unsafe,
            decision_required=decision_required,
            target_invalid=target_invalid,
            interface_changed=interface_changed,
        )
        SqliteConvergenceRepository(self._ensure_store()).put(report, recommendation)
        return report, recommendation

    def research_plan(
        self, query: str, depth: ResearchDepth, facets: tuple[str, ...] = ()
    ) -> dict[str, Any]:
        self._require_explicit(CapabilityName.RESEARCH)
        plan = build_research_plan(
            ResearchRequest(
                hashlib.sha256(f"{self.project.project_id}\0{query}".encode()).hexdigest()[:20],
                self.project,
                query,
                depth,
            ),
            facets,
        )
        return {
            "request_id": plan.request_id,
            "queries": list(plan.queries),
            "max_queries": plan.max_queries,
            "max_sources": plan.max_sources,
            "max_time_seconds": plan.max_time_seconds,
        }

    def evaluate_project_requirements(
        self,
        requirement_revision_id: str,
        requirements: tuple[Requirement, ...],
        evidence: tuple[RequirementEvidence, ...],
    ) -> tuple[ConvergenceReport, ConvergenceRecommendation]:
        snapshot = self._explicit_snapshot(CapabilityName.TRACEABILITY)
        if snapshot.revision is None:
            raise CapabilityUnavailable("traceability requires a Twin revision")
        result: ProjectRequirementReport = evaluate_project_requirements(
            self.project,
            requirement_revision_id,
            requirements,
            tuple(node.canonical_ref for node in snapshot.nodes),
            TwinRevisionRef(snapshot.revision.revision_id, snapshot.revision.source_revision),
            evidence,
        )
        SqliteConvergenceRepository(self._ensure_store()).put(
            result.convergence, result.recommendation
        )
        return result.convergence, result.recommendation

    def _impact_report(
        self,
        snapshot: GraphSnapshot,
        changed_refs: tuple[str, ...],
        *,
        min_confidence: float = 0.0,
        max_depth: int | None = None,
        include_historical: bool = False,
    ) -> Any:
        return GraphAnalysisService(snapshot, self._reference_resolver()).assess_impact(
            ImpactQuery(
                changed_refs,
                min_confidence=min_confidence,
                max_depth=min(max_depth or self.max_depth, self.max_depth),
                include_historical=include_historical,
            )
        )

    def _explicit_snapshot(self, capability: CapabilityName) -> GraphSnapshot:
        self._require_explicit(capability)
        return self._snapshot(open_if_missing=True)

    def _require_explicit(self, capability: CapabilityName) -> None:
        if not self.policy.allows_explicit_use(capability):
            raise CapabilityUnavailable(f"{capability.value} is not available for explicit use")

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
            selected: list[GraphAnalyzer] = []
            if "python" in self.analyzers:
                selected.append(PythonGraphAnalyzer())
            if "javascript_typescript" in self.analyzers:
                selected.append(JavaScriptTypeScriptGraphAnalyzer())
            analyzer = CompositeGraphAnalyzer(tuple(selected)) if selected else None
            self._twin = TwinService(self._ensure_store(), analyzer=analyzer)
        return self._twin

    def _reference_resolver(self) -> CompositeCanonicalReferenceResolver:
        resolvers: list[CanonicalReferenceResolver] = []
        if "python" in self.analyzers:
            resolvers.append(PythonCanonicalReferenceResolver())
        if "javascript_typescript" in self.analyzers:
            resolvers.append(JavaScriptTypeScriptCanonicalReferenceResolver())
        return CompositeCanonicalReferenceResolver(tuple(resolvers))

    def _ensure_store(self) -> SqliteGraphStore:
        if self._store is None:
            self.database.parent.mkdir(parents=True, exist_ok=True)
            self._store = SqliteGraphStore(self.database)
        return self._store

    def _ensure_blueprints(self) -> BlueprintService:
        if self._blueprints is None:
            self._blueprints = BlueprintService(SqliteBlueprintRepository(self._ensure_store()))
        return self._blueprints


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


def _health_json(item: Any) -> dict[str, Any]:
    return {
        "canonical_ref": item.test_ref.value,
        "state": item.state.value,
        "reasons": list(item.reasons),
        "evidence_ids": list(item.evidence_ids),
        "delete_recommended": item.delete_recommended,
    }


def _observation_json(item: Any) -> dict[str, Any]:
    return {
        "observation_id": item.observation_id,
        "kind": item.kind.value,
        "status": item.status.value,
        "source_revision": item.source_revision.value,
        "observed_refs": [ref.value for ref in item.observed_refs],
        "started_at": item.started_at.isoformat(),
        "finished_at": item.finished_at.isoformat(),
        "command": item.command,
        "tool": item.tool,
        "summary": item.summary,
    }


def _context_json(item: Any) -> dict[str, Any]:
    return {
        "canonical_ref": item.canonical_ref.value,
        "kind": item.kind,
        "summary": item.summary,
        "why_included": item.why_included,
        "confidence": item.confidence,
        "revision": item.revision.value,
        "provenance": {
            "source": item.provenance.source,
            "producer": item.provenance.producer,
            "producer_version": item.provenance.producer_version,
        },
        "token_estimate": item.token_estimate,
        "status": item.status,
    }
