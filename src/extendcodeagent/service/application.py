"""Versioned host-neutral Project Intelligence query application."""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import UTC, datetime
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
from extendcodeagent.context import (
    ContextProfile,
    ContextRequest,
    EvidenceScope,
    WeakLocalEvidencePackage,
    WeakLocalEvidenceRequest,
    build_context,
    build_weak_local_evidence,
    stable_evidence_envelope,
)
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
from extendcodeagent.core.config.schema import (
    KNOWN_ANALYZERS,
    CapabilityName,
    Depth,
    RemoteCodePolicy,
    RolloutMode,
    governing_capability,
)
from extendcodeagent.core.contracts import (
    CanonicalRef,
    ProjectRef,
    Provenance,
    SourceRevision,
    TwinRevisionRef,
)
from extendcodeagent.core.policy import CapabilityPolicy, CapabilityUnavailable
from extendcodeagent.graph import FactStatus, GraphSnapshot
from extendcodeagent.graph.analyzers import (
    CompositeGraphAnalyzer,
    GraphAnalyzer,
    JavaScriptTypeScriptGraphAnalyzer,
    PythonGraphAnalyzer,
)
from extendcodeagent.orchestration import PlanOutcome, create_shadow_plan, project_task_signals
from extendcodeagent.research import ResearchDepth, ResearchRequest, build_research_plan
from extendcodeagent.runtime import (
    ObservationKind,
    ObservationStatus,
    RuntimeAdapterCapability,
    RuntimeCapabilities,
    RuntimeCapabilityDeclaration,
    RuntimeCapabilityStatus,
    RuntimeObservation,
    RuntimeSignal,
    RuntimeSignalKind,
    TaskSignalCollector,
)
from extendcodeagent.storage import SqliteGraphStore
from extendcodeagent.strategy import (
    ProposedAlternative,
    StrategyRequest,
    StrategySignals,
    build_strategy,
)
from extendcodeagent.testing import TestHealthSignals, evaluate_test_health, select_tests
from extendcodeagent.traceability import (
    ProjectRequirementReport,
    Requirement,
    RequirementEvidence,
    evaluate_project_requirements,
)
from extendcodeagent.twin import TwinService

INTERFACE_VERSION = "extendcodeagent.local.v1"

__all__ = ["CapabilityUnavailable", "ProjectIntelligenceApplication", "INTERFACE_VERSION"]


class _FixedStrategySynthesis:
    """Bounded adapter for alternatives derived from the current graph."""

    def __init__(self, alternatives: tuple[ProposedAlternative, ...]) -> None:
        self._alternatives = alternatives

    def propose(self, payload: dict[str, object]) -> tuple[ProposedAlternative, ...]:
        del payload
        return self._alternatives


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
        context_max_tokens: int = 8_192,
        privacy_policy: RemoteCodePolicy = RemoteCodePolicy.DENY,
        analyzers: tuple[str, ...] = KNOWN_ANALYZERS,
    ) -> None:
        self.root = Path(root).resolve()
        self.database = Path(database)
        self.policy = policy
        self.max_items = max_items
        self.max_depth = max_depth
        self.context_max_tokens = context_max_tokens
        self.privacy_policy = privacy_policy
        self.analyzers = analyzers
        digest = hashlib.sha256(str(self.root).encode()).hexdigest()[:12]
        self.project = ProjectRef(f"{self.root.name}-{digest}", "default", self.root.as_uri())
        self._task_signals = TaskSignalCollector(self.project)
        self._shadow_plan: PlanOutcome | None = None
        self._store: SqliteGraphStore | None = None
        self._twin: TwinService | None = None
        self._blueprints: BlueprintService | None = None
        self._request_timing: dict[str, float] | None = None
        self._cold_twin_build_ms = 0.0
        self._snapshot_cache: GraphSnapshot | None = None
        self._analysis_cache: tuple[str, GraphAnalysisService] | None = None
        self._symbol_index_cache: tuple[str, dict[str, tuple[Any, ...]]] | None = None

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
            self._invalidate_query_cache()

    def begin_timing(self) -> None:
        """Start one sidecar-request timing scope.

        The local sidecar is deliberately single-threaded, so request-local
        accumulation remains deterministic without leaking timing concerns into
        domain contracts.
        """

        self._request_timing = {
            "snapshot_load_ms": 0.0,
            "adjacency_index_build_ms": 0.0,
            "cold_twin_build_current_request_ms": 0.0,
        }

    def finish_timing(self, request_ms: float) -> dict[str, float]:
        current = self._request_timing or {}
        tracked = sum(current.values())
        result = {
            "cold_twin_build_ms": round(self._cold_twin_build_ms, 3),
            "snapshot_load_ms": round(current.get("snapshot_load_ms", 0.0), 3),
            "adjacency_index_build_ms": round(current.get("adjacency_index_build_ms", 0.0), 3),
            "query_execution_ms": round(max(0.0, request_ms - tracked), 3),
        }
        self._request_timing = None
        return result

    def _record_timing(self, name: str, started_ns: int) -> None:
        elapsed = (time.perf_counter_ns() - started_ns) / 1_000_000
        if name == "cold_twin_build_current_request_ms":
            self._cold_twin_build_ms += elapsed
        if self._request_timing is not None:
            self._request_timing[name] = self._request_timing.get(name, 0.0) + elapsed

    def status(self, *, view: str = "detail") -> dict[str, Any]:
        if view not in {"compact", "detail"}:
            raise ValueError("view must be compact or detail")
        mode = self.policy.mode(CapabilityName.GRAPH)
        if mode is RolloutMode.OFF:
            result = {
                "interface": INTERFACE_VERSION,
                "depth": None,
                "readiness": "disabled",
                "mode": mode.value,
                "revision_id": None,
                "nodes": 0,
                "edges": 0,
                "capabilities": self._capability_status(),
            }
            return self._compact_status(result) if view == "compact" else result
        snapshot = self._load_snapshot(self._ensure_twin())
        result = {
            "interface": INTERFACE_VERSION,
            "depth": None,
            "readiness": "ready" if snapshot.revision else "absent",
            "mode": mode.value,
            "revision_id": snapshot.revision.revision_id if snapshot.revision else None,
            "nodes": len(snapshot.nodes),
            "edges": len(snapshot.edges),
            "capabilities": self._capability_status(),
        }
        if view == "compact":
            return self._compact_status(result)
        if view != "detail":
            raise ValueError("view must be compact or detail")
        return result

    def _compact_status(self, result: dict[str, Any]) -> dict[str, Any]:
        capabilities = result["capabilities"]
        assert isinstance(capabilities, list)
        configured = [
            {
                "name": item["name"],
                "mode": item["mode"],
                "depth": item["depth"],
                "implementation": item["implementation"],
            }
            for item in capabilities
            if item["implementation"] == "implemented" and item["name"] != "call_graph"
        ]
        return {
            "interface": result["interface"],
            "readiness": result["readiness"],
            "mode": result["mode"],
            "revision_id": result["revision_id"],
            "nodes": result["nodes"],
            "edges": result["edges"],
            "capabilities": configured,
            "omitted_unimplemented_capabilities": sum(
                item["implementation"] != "implemented" for item in capabilities
            ),
        }

    def _capability_status(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for capability in CapabilityName:
            governed_by = governing_capability(capability)
            entries.append(
                {
                    "name": capability.value,
                    "implementation": self.policy.implementation(capability).value,
                    "mode": self.policy.mode(capability).value,
                    "depth": self.policy.depth(capability).value,
                    "min_inferred_confidence": self.policy.min_inferred_confidence(capability),
                    "governed_by": governed_by.value if governed_by is not capability else None,
                }
            )
        return entries

    def process_event(self, paths: tuple[str, ...], kind: str) -> dict[str, Any]:
        if kind in {"file.edited", "file.watcher.updated"}:
            collected = self._task_signals.collect(
                RuntimeSignal(
                    f"event:{kind}:{time.time_ns()}",
                    RuntimeSignalKind.MUTATION,
                    self.project,
                    datetime.now(UTC),
                    Provenance("runtime", kind, "1"),
                    paths=tuple(sorted(set(paths))),
                    source_category=kind,
                )
            )
            if collected:
                self._refresh_shadow_plan()
        if not all(
            self.policy.computes_automatically(capability)
            for capability in (CapabilityName.GRAPH, CapabilityName.TWIN, CapabilityName.SEMANTIC)
        ):
            return {
                "accepted": False,
                "kind": kind,
                "revision_id": None,
                "depth": self.policy.depth(CapabilityName.SEMANTIC).value,
            }
        twin = self._ensure_twin()
        current = self._load_snapshot(twin).revision
        started = time.perf_counter_ns()
        result = (
            twin.refresh(self.project, changed_paths=tuple(sorted(set(paths))))
            if current and paths
            else twin.open(self.project)
        )
        self._invalidate_query_cache()
        if current is None:
            self._record_timing("cold_twin_build_current_request_ms", started)
        return {
            "accepted": True,
            "kind": kind,
            "revision_id": result.revision.revision_id if result.revision else None,
            "depth": self.policy.depth(CapabilityName.SEMANTIC).value,
            "affected_paths": list(result.affected_paths),
            "diagnostics": [item.code for item in result.diagnostics],
        }

    def symbol(self, query: str, *, view: str = "detail") -> dict[str, Any]:
        snapshot = self._explicit_snapshot(CapabilityName.SEMANTIC)
        lowered = query.casefold()
        matches = self._symbol_matches(snapshot, lowered)
        if view == "compact":
            return self._compact_symbol(snapshot, matches)
        if view != "detail":
            raise ValueError("view must be compact or detail")
        return _result(
            snapshot,
            depth=self.policy.depth(CapabilityName.SEMANTIC),
            view=view,
            items=[_node_json(node) for node in matches],
        )

    def references(self, canonical_ref: str) -> dict[str, Any]:
        snapshot = self._explicit_snapshot(CapabilityName.SEMANTIC)
        inferred_floor = self.policy.min_inferred_confidence(CapabilityName.SEMANTIC)
        items = [
            _edge_json(edge)
            for edge in self._analysis_service(snapshot).reverse.get(canonical_ref, ())
            if edge.status is not FactStatus.INFERRED or edge.confidence.value >= inferred_floor
        ][: self.max_items]
        return _result(snapshot, depth=self.policy.depth(CapabilityName.SEMANTIC), items=items)

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
        result = self._analysis_service(snapshot).trace_path(
            PathQuery(
                source_ref,
                target_ref,
                allowed_edge_types,
                min_confidence=min_confidence,
                min_inferred_confidence=self.policy.min_inferred_confidence(CapabilityName.IMPACT),
                max_depth=min(max_depth or self.max_depth, self.max_depth),
                max_paths=min(max_paths, self.max_items),
            )
        )
        return _result(
            snapshot,
            depth=self.policy.depth(CapabilityName.IMPACT),
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
        view: str = "detail",
    ) -> dict[str, Any]:
        snapshot = self._explicit_snapshot(CapabilityName.IMPACT)
        report = self._impact_report(
            snapshot,
            changed_refs,
            min_confidence=min_confidence,
            max_depth=max_depth,
            include_historical=include_historical,
        )
        if view == "compact":
            return self._compact_impact(snapshot, changed_refs, report)
        if view != "detail":
            raise ValueError("view must be compact or detail")
        return _result(
            snapshot,
            depth=self.policy.depth(CapabilityName.IMPACT),
            view=view,
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

    def tests(
        self,
        changed_refs: tuple[str, ...] = (),
        *,
        objective: str = "",
        view: str = "detail",
    ) -> dict[str, Any]:
        snapshot = self._explicit_snapshot(CapabilityName.TEST_SELECTION)
        if not changed_refs and view == "detail":
            raise ValueError("changed_refs must not be empty for detail view")
        report = (
            self._impact_report(snapshot, changed_refs, capability=CapabilityName.TEST_SELECTION)
            if changed_refs
            else None
        )
        selection = select_tests(report) if report is not None else None
        candidates = selection.candidates if selection is not None else ()
        observations = self._ensure_store().observations(
            self.project,
            refs=tuple(
                CanonicalRef(item)
                for item in (
                    *changed_refs,
                    *(candidate.canonical_ref.value for candidate in candidates),
                )
            ),
            limit=self.max_items,
        )
        current_revision = snapshot.revision.source_revision if snapshot.revision else None
        # test_obsolescence is a separate capability: test selection stays available
        # when obsolescence classification is switched off for ablation.
        obsolescence = self.policy.allows_explicit_use(CapabilityName.TEST_OBSOLESCENCE)
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
                        policy=self.policy,
                    )
                )
                for candidate in candidates
            ]
            if current_revision and obsolescence
            else []
        )
        if view == "compact":
            nodes = {node.canonical_ref.value: node for node in snapshot.nodes}
            intent_architecture = _intent_architecture_test_paths(changed_refs, nodes)
            selected_candidates = [
                item
                for item in candidates
                if "architecture" not in Path(item.source_ref).parts
                or item.source_ref in intent_architecture
            ]
            objective_paths = _objective_test_paths(snapshot, objective)
            selected_paths = sorted(
                {item.source_ref for item in selected_candidates} | objective_paths
            )
            candidate_refs = {item.canonical_ref.value for item in selected_candidates}
            covered_obligations = sorted({_test_obligation(path) for path in selected_paths})
            required_obligations = {
                "architecture_boundary",
                "integration_boundary",
                "unit_behavior",
            }
            uncovered_obligations = sorted(required_obligations - set(covered_obligations))
            coverage_complete = not uncovered_obligations
            return _result(
                snapshot,
                depth=self.policy.depth(CapabilityName.TEST_SELECTION),
                view=view,
                selected_tests=selected_paths,
                candidate_refs=sorted(candidate_refs),
                covered_obligations=covered_obligations,
                coverage_complete=coverage_complete,
                uncovered_obligations=uncovered_obligations,
                fallback_search_required=not coverage_complete,
                fallback=(
                    None
                    if coverage_complete
                    else selection.fallback
                    if selection is not None
                    else "native_search"
                ),
                diagnostics=(
                    [*selection.diagnostics, "objective_intent_projection"]
                    if selection is not None and objective_paths
                    else ["objective_intent_projection"]
                    if objective_paths
                    else list(selection.diagnostics)
                    if selection is not None
                    else ["objective did not match test intent"]
                ),
            )
        if view != "detail":
            raise ValueError("view must be compact or detail")
        assert report is not None and selection is not None
        return _result(
            snapshot,
            depth=self.policy.depth(CapabilityName.TEST_SELECTION),
            view=view,
            items=[_impact_json(item) for item in report.recommended_tests],
            fallback=selection.fallback,
            health=health,
            diagnostics=list(selection.diagnostics),
        )

    def _compact_symbol(self, snapshot: GraphSnapshot, matches: list[Any]) -> dict[str, Any]:
        compact_limit = min(self.max_items, 24)
        definitions = [
            node
            for node in matches
            if node.node_type
            not in {"repository", "directory", "file", "module", "package", "dependency", "test"}
        ] or matches
        definitions = definitions[:compact_limit]
        refs = tuple(node.canonical_ref.value for node in definitions)
        analysis = self._analysis_service(snapshot)
        report = (
            analysis.assess_impact(
                ImpactQuery(
                    refs,
                    min_inferred_confidence=self.policy.min_inferred_confidence(
                        CapabilityName.SEMANTIC
                    ),
                    max_depth=self.max_depth,
                )
            )
            if refs
            else None
        )
        exports = sorted(
            {
                edge.source_ref
                for ref in refs
                for edge in analysis.reverse.get(ref, ())
                if edge.edge_type == "imports" and Path(edge.source_ref).name == "__init__.py"
            }
        )
        direct_production = sorted(
            {
                item.source_ref
                for item in (report.direct_impacts if report is not None else ())
                if item.item_type in {"function", "method", "api_route", "handler"}
            }
        )
        source_production = [path for path in direct_production if path.startswith("src/")]
        production_callers = source_production or direct_production
        candidate_tests = (
            {item.source_ref for item in report.recommended_tests} if report is not None else set()
        )
        nodes = {node.canonical_ref.value: node for node in snapshot.nodes}
        intent_architecture = _intent_architecture_test_paths(refs, nodes)
        tests = sorted(
            path
            for path in candidate_tests
            if "architecture" not in Path(path).parts or path in intent_architecture
        )
        fields = {
            "symbols": sorted(refs),
            "definition": sorted({node.source_ref for node in definitions}),
            "exports": exports,
            "production_callers": production_callers,
            "tests": tests,
        }
        bounded = {name: values[:compact_limit] for name, values in fields.items()}
        excluded = {name: len(values) - len(bounded[name]) for name, values in fields.items()}
        return _result(
            snapshot,
            depth=self.policy.depth(CapabilityName.SEMANTIC),
            view="compact",
            **bounded,
            coverage_complete=False,
            unresolved=["structural/architecture tests may not be represented by call relations"],
            projection_truncated=any(excluded.values()),
            excluded_counts=excluded,
        )

    def _compact_impact(
        self, snapshot: GraphSnapshot, changed_refs: tuple[str, ...], report: Any
    ) -> dict[str, Any]:
        nodes = {node.canonical_ref.value: node for node in snapshot.nodes}
        production = tuple(
            item
            for item in report.direct_impacts
            if item.item_type in {"function", "method", "api_route", "handler"}
        )
        intent_tests = _intent_architecture_test_paths(changed_refs, nodes)
        candidate_tests = sorted(
            {item.source_ref for item in report.recommended_tests} | intent_tests
        )
        candidate_refs = {item.canonical_ref for item in report.recommended_tests}
        structural_tests = _structural_test_paths(snapshot, candidate_refs) & intent_tests
        focused_tests = sorted(
            set(_focused_test_paths(changed_refs, nodes, candidate_tests))
            | structural_tests
            | intent_tests
        )
        counted_refs = set(changed_refs)
        for ref in changed_refs:
            counted_refs.update(self._reference_resolver().equivalents(ref, snapshot))
        return _result(
            snapshot,
            depth=self.policy.depth(CapabilityName.IMPACT),
            view="compact",
            changed_refs=list(changed_refs),
            definition=sorted({nodes[ref].source_ref for ref in changed_refs if ref in nodes}),
            production_methods=sorted(
                {
                    str(nodes[item.canonical_ref].properties.get("qualname", item.canonical_ref))
                    for item in production
                    if item.canonical_ref in nodes
                }
            ),
            direct_use_count=_direct_use_count(
                snapshot,
                counted_refs,
                {item.canonical_ref for item in production},
            ),
            affected_symbols=[
                item.canonical_ref for item in (*report.direct_impacts, *report.transitive_impacts)
            ],
            focused_tests=focused_tests,
            candidate_tests=candidate_tests,
            uncertainty=sorted({item.canonical_ref for item in report.uncertainty}),
            coverage_complete=False,
            unresolved=[
                "dynamic, structural, or repeated source-level uses may require native confirmation"
            ],
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
        runtime_session_id: str | None = None,
        runtime_call_id: str | None = None,
    ) -> dict[str, Any]:
        allowed = (
            self.policy.computes_automatically(CapabilityName.RUNTIME)
            if automatic
            else self.policy.allows_explicit_use(CapabilityName.RUNTIME)
        )
        if not allowed:
            return {
                "accepted": False,
                "observation_id": observation_id,
                "depth": self.policy.depth(CapabilityName.RUNTIME).value,
            }
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
            runtime_session_id=runtime_session_id,
            runtime_call_id=runtime_call_id,
        )
        inserted = self._ensure_store().put_observation(observation)
        collected = self._task_signals.collect_observation(observation)
        if collected:
            self._refresh_shadow_plan()
        return {
            "accepted": True,
            "observation_id": observation_id,
            "inserted": inserted,
            "source_revision": revision.value,
            "depth": self.policy.depth(CapabilityName.RUNTIME).value,
            "runtime_contract_collected": collected,
        }

    def connect_runtime(
        self,
        *,
        runtime_name: str,
        runtime_version: str,
        declarations: tuple[tuple[str, str, str], ...],
    ) -> dict[str, Any]:
        capabilities = RuntimeCapabilities(
            runtime_name,
            runtime_version,
            tuple(
                RuntimeCapabilityDeclaration(
                    RuntimeAdapterCapability(name),
                    RuntimeCapabilityStatus(status),
                    reason,
                )
                for name, status, reason in declarations
            ),
        )
        self._task_signals.connect(capabilities)
        return self.runtime_contract()

    def ingest_runtime_signal(
        self,
        *,
        signal_id: str,
        kind: str,
        observed_at: datetime,
        runtime_session_id: str | None = None,
        task_text: str | None = None,
        paths: tuple[str, ...] = (),
        source_category: str | None = None,
        lifecycle_state: str | None = None,
        model_provider: str | None = None,
        model_id: str | None = None,
        delivery_channel: str | None = None,
        tool: str | None = None,
        producer: str = "runtime_adapter",
        producer_version: str = "1",
    ) -> dict[str, Any]:
        signal = RuntimeSignal(
            signal_id,
            RuntimeSignalKind(kind),
            self.project,
            observed_at,
            Provenance("runtime", producer, producer_version),
            runtime_session_id,
            task_text,
            paths,
            source_category,
            lifecycle_state,
            model_provider,
            model_id,
            delivery_channel,
            tool,
        )
        accepted = self._task_signals.collect(signal)
        if accepted and signal.kind in {
            RuntimeSignalKind.TASK,
            RuntimeSignalKind.MUTATION,
            RuntimeSignalKind.MODEL,
        }:
            self._refresh_shadow_plan()
        return {
            "accepted": accepted,
            "signal_id": signal.signal_id,
            "kind": signal.kind.value,
            "diagnostics": list(self._task_signals.snapshot().diagnostics),
            "shadow_plan_id": self._shadow_plan.plan.plan_id if self._shadow_plan else None,
        }

    def runtime_contract(self) -> dict[str, Any]:
        payload = _runtime_snapshot_json(self._task_signals.snapshot())
        payload["shadow_plan"] = _plan_outcome_json(self._shadow_plan)
        return payload

    def _refresh_shadow_plan(self) -> None:
        signals = project_task_signals(
            self._task_signals.snapshot(),
            context_token_limit=self.context_max_tokens,
            max_items=self.max_items,
            max_depth=self.max_depth,
            privacy_policy=self.privacy_policy,
        )
        if signals is not None:
            self._shadow_plan = create_shadow_plan(signals, self.policy)

    def runtime_evidence(
        self, refs: tuple[str, ...] = (), *, view: str = "detail"
    ) -> dict[str, Any]:
        if not self.policy.allows_explicit_use(CapabilityName.RUNTIME):
            raise CapabilityUnavailable("runtime is not available for explicit use")
        snapshot = self._snapshot(open_if_missing=True)
        observations = self._ensure_store().observations(
            self.project,
            refs=tuple(CanonicalRef(item) for item in refs),
            limit=self.max_items,
        )
        if view == "compact":
            revision = snapshot.revision.source_revision.value if snapshot.revision else None
            return {
                "interface": INTERFACE_VERSION,
                "source_revision": revision,
                "depth": self.policy.depth(CapabilityName.RUNTIME).value,
                "items": [
                    {
                        "id": item.observation_id,
                        "kind": item.kind.value,
                        "status": item.status.value,
                        "refs": [ref.value for ref in item.observed_refs],
                        "tool": item.tool,
                        "summary": item.summary[:256],
                    }
                    for item in observations
                ],
                "selected_evidence_ids": [item.observation_id for item in observations],
                "unresolved_evidence_gaps": (
                    [] if observations else ["no_matching_runtime_evidence"]
                ),
            }
        if view != "detail":
            raise ValueError("view must be compact or detail")
        return _result(
            snapshot,
            depth=self.policy.depth(CapabilityName.RUNTIME),
            items=[_observation_json(item) for item in observations],
        )

    def context(
        self,
        objective: str,
        target_refs: tuple[str, ...] = (),
        *,
        profile: str = "standard",
        token_budget: int = 2_000,
        view: str = "detail",
        scope: str | None = None,
        prior_evidence_ids: tuple[str, ...] = (),
        unresolved_gaps: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        snapshot = self._explicit_snapshot(CapabilityName.CONTEXT)
        if view == "envelope":
            weak_package = build_weak_local_evidence(
                snapshot,
                WeakLocalEvidenceRequest(
                    objective,
                    tuple(CanonicalRef(item) for item in target_refs),
                    token_budget,
                    min(self.max_items, 32),
                    scope=EvidenceScope(scope) if scope is not None else None,
                    prior_evidence_ids=prior_evidence_ids,
                    unresolved_gaps=unresolved_gaps,
                ),
            )
            return _weak_local_evidence_json(weak_package)
        if view != "detail":
            raise ValueError("view must be detail or envelope")
        context_package = build_context(
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
            depth=self.policy.depth(CapabilityName.CONTEXT),
            items=[_context_json(item) for item in context_package.items],
            used_tokens=context_package.used_tokens,
            token_budget=context_package.token_budget,
            truncated=context_package.truncated,
            excluded_count=context_package.excluded_count,
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
            "depth": self.policy.depth(CapabilityName.RESEARCH).value,
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
        self._require_explicit(CapabilityName.CONVERGENCE)
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

    def plan_change(
        self,
        goal: str,
        target_refs: tuple[str, ...],
        constraints: tuple[str, ...] = (),
        *,
        persist_blueprint: bool = False,
    ) -> dict[str, Any]:
        """Project a bounded strategy into Blueprint-shaped change elements.

        Strategy selection is deterministic from current Project Truth.  The
        default route is read-only; callers must explicitly request persistence
        before a Blueprint revision is stored.
        """

        if not goal.strip():
            raise ValueError("goal must not be empty")
        if not target_refs:
            raise ValueError("target_refs must not be empty")
        snapshot = self._explicit_snapshot(CapabilityName.STRATEGY)
        self._require_explicit(CapabilityName.BLUEPRINT)
        report = self._impact_report(snapshot, target_refs, capability=CapabilityName.STRATEGY)
        nodes = {node.canonical_ref.value: node for node in snapshot.nodes}
        focused_files = tuple(
            sorted({nodes[ref].source_ref if ref in nodes else ref for ref in target_refs})
        )
        expanded_files = tuple(
            sorted(
                set(focused_files)
                | {
                    item.source_ref
                    for item in (*report.direct_impacts, *report.transitive_impacts)
                    if item.source_ref
                }
            )
        )[: self.max_items]
        proposals = [
            ProposedAlternative(
                "focused",
                focused_files,
                "Change only the requested project entities.",
                "Revert the bounded target changes.",
            )
        ]
        if expanded_files != focused_files:
            proposals.append(
                ProposedAlternative(
                    "impact_aware",
                    expanded_files,
                    "Include directly and transitively impacted project files.",
                    "Revert in reverse dependency order.",
                )
            )
        impact_by_file: dict[str, int] = {}
        for item in (*report.direct_impacts, *report.transitive_impacts):
            impact_by_file[item.source_ref] = impact_by_file.get(item.source_ref, 0) + 1
        tests_by_file: dict[str, int] = {}
        for item in report.recommended_tests:
            tests_by_file[item.source_ref] = tests_by_file.get(item.source_ref, 0) + 1
        uncertainty_by_file = {
            item.source_ref: 1.0 - item.confidence for item in report.uncertainty
        }
        strategy = build_strategy(
            StrategyRequest(goal, constraints),
            StrategySignals(
                impact_by_file=impact_by_file,
                tests_by_file=tests_by_file,
                uncertainty_by_file=uncertainty_by_file,
            ),
            _FixedStrategySynthesis(tuple(proposals)),
            policy=self.policy,
        )
        selected = next(
            (item for item in strategy.alternatives if item.alternative_id == strategy.selected_id),
            strategy.alternatives[0],
        )
        refs_by_source: dict[str, list[str]] = {}
        for node in snapshot.nodes:
            refs_by_source.setdefault(node.source_ref, []).append(node.canonical_ref.value)
        elements = tuple(
            BlueprintElement(
                f"change-{index}",
                CanonicalRef(f"planned://change/{index}"),
                "file",
                expected_actual_refs=(
                    CanonicalRef(_preferred_actual_ref(path, refs_by_source.get(path, []))),
                ),
                acceptance_criteria=(goal,),
            )
            for index, path in enumerate(selected.changed_files, 1)
        )
        blueprint = self.create_blueprint(elements, durable=persist_blueprint)
        return _result(
            snapshot,
            depth=self.policy.depth(CapabilityName.STRATEGY),
            capabilities_used=[CapabilityName.BLUEPRINT.value, CapabilityName.STRATEGY.value],
            goal=goal,
            selected_alternative=strategy.selected_id,
            decision_required=strategy.selected_id is None,
            alternatives=[_strategy_json(item) for item in strategy.alternatives],
            blueprint={
                "persisted": blueprint is not None,
                "revision_id": blueprint.revision.revision_id if blueprint else None,
                "status": blueprint.status.value if blueprint else "draft",
                "elements": [_blueprint_element_json(item) for item in elements],
            },
            unresolved=(
                ["strategy alternatives tied; agent decision is required"]
                if strategy.selected_id is None
                else []
            ),
        )

    def verify_requirements(
        self,
        requirements: tuple[Requirement, ...],
        evidence: tuple[RequirementEvidence, ...] = (),
        *,
        requirement_revision_id: str = "pi-verify",
    ) -> dict[str, Any]:
        """Trace requirements to current Twin facts and evaluate convergence."""

        report, recommendation = self.evaluate_project_requirements(
            requirement_revision_id, requirements, evidence
        )
        return {
            "interface": INTERFACE_VERSION,
            "revision_id": (
                report.actual_twin_revision.revision_id if report.actual_twin_revision else None
            ),
            "depth": self.policy.depth(CapabilityName.TRACEABILITY).value,
            "capabilities_used": [
                CapabilityName.CONVERGENCE.value,
                CapabilityName.TRACEABILITY.value,
            ],
            "decision": recommendation.decision.value,
            "reason_codes": list(recommendation.reason_codes),
            "requirements": [
                {
                    "requirement_id": item.element_id,
                    "state": item.state.value,
                    "matched_actual_refs": [ref.value for ref in item.matched_actual_refs],
                    "missing_actual_refs": [ref.value for ref in item.missing_actual_refs],
                    "diagnostics": list(item.diagnostics),
                }
                for item in report.elements
            ],
            "coverage_complete": recommendation.decision.value == "complete",
            "unresolved": [
                item.element_id
                for item in report.elements
                if item.state.value not in {"verified", "observed"}
            ],
        }

    def _impact_report(
        self,
        snapshot: GraphSnapshot,
        changed_refs: tuple[str, ...],
        *,
        min_confidence: float = 0.0,
        max_depth: int | None = None,
        include_historical: bool = False,
        capability: CapabilityName = CapabilityName.IMPACT,
    ) -> Any:
        return self._analysis_service(snapshot).assess_impact(
            ImpactQuery(
                changed_refs,
                min_confidence=min_confidence,
                min_inferred_confidence=self.policy.min_inferred_confidence(capability),
                max_depth=min(max_depth or self.max_depth, self.max_depth),
                include_historical=include_historical,
            )
        )

    def _explicit_snapshot(self, capability: CapabilityName) -> GraphSnapshot:
        self._require_explicit(capability)
        return self._snapshot(open_if_missing=True)

    def _require_explicit(self, capability: CapabilityName) -> None:
        self.policy.require_explicit_use(capability)

    def _snapshot(self, *, open_if_missing: bool) -> GraphSnapshot:
        if self._twin is None:
            if not open_if_missing:
                return GraphSnapshot(self.project, None)
            twin = self._ensure_twin()
        else:
            twin = self._twin
        snapshot = self._load_snapshot(twin)
        if open_if_missing and snapshot.revision is None:
            started = time.perf_counter_ns()
            twin.open(self.project)
            self._invalidate_query_cache()
            self._record_timing("cold_twin_build_current_request_ms", started)
            snapshot = self._load_snapshot(twin)
        return snapshot

    def _load_snapshot(self, twin: TwinService) -> GraphSnapshot:
        started = time.perf_counter_ns()
        current = twin.store.current_revision(self.project)
        cached = self._snapshot_cache
        if (
            cached is not None
            and cached.revision is not None
            and current is not None
            and cached.revision.revision_id == current.revision_id
        ):
            snapshot = cached
        else:
            snapshot = twin.snapshot(self.project, current.revision_id if current else None)
            self._snapshot_cache = snapshot if snapshot.revision is not None else None
            self._analysis_cache = None
            self._symbol_index_cache = None
        self._record_timing("snapshot_load_ms", started)
        return snapshot

    def _analysis_service(self, snapshot: GraphSnapshot) -> GraphAnalysisService:
        revision_id = snapshot.revision.revision_id if snapshot.revision is not None else None
        if (
            revision_id is not None
            and self._analysis_cache is not None
            and self._analysis_cache[0] == revision_id
        ):
            return self._analysis_cache[1]
        started = time.perf_counter_ns()
        service = GraphAnalysisService(snapshot, self._reference_resolver())
        self._record_timing("adjacency_index_build_ms", started)
        if revision_id is not None:
            self._analysis_cache = (revision_id, service)
        return service

    def _symbol_matches(self, snapshot: GraphSnapshot, lowered: str) -> list[Any]:
        revision_id = snapshot.revision.revision_id if snapshot.revision is not None else None
        cached = self._symbol_index_cache
        if revision_id is not None and (cached is None or cached[0] != revision_id):
            started = time.perf_counter_ns()
            buckets: dict[str, list[Any]] = {}
            for node in snapshot.nodes:
                keys = {
                    node.canonical_ref.value.casefold(),
                    str(node.properties.get("name", "")).casefold(),
                    str(node.properties.get("qualname", "")).casefold(),
                }
                for key in keys - {""}:
                    buckets.setdefault(key, []).append(node)
            cached = (
                revision_id,
                {
                    key: tuple(sorted(values, key=lambda item: item.canonical_ref.value))
                    for key, values in buckets.items()
                },
            )
            self._symbol_index_cache = cached
            self._record_timing("adjacency_index_build_ms", started)
        exact = cached[1].get(lowered, ()) if cached is not None else ()
        if exact:
            return list(exact[: self.max_items])
        return [
            node
            for node in snapshot.nodes
            if lowered in node.canonical_ref.value.casefold()
            or lowered in str(node.properties.get("name", "")).casefold()
        ][: self.max_items]

    def _invalidate_query_cache(self) -> None:
        self._snapshot_cache = None
        self._analysis_cache = None
        self._symbol_index_cache = None

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


def _result(
    snapshot: GraphSnapshot,
    *,
    depth: Depth | None = None,
    **values: Any,
) -> dict[str, Any]:
    return {
        "interface": INTERFACE_VERSION,
        "revision_id": snapshot.revision.revision_id if snapshot.revision else None,
        "depth": depth.value if depth is not None else None,
        **values,
    }


def _preferred_actual_ref(source_ref: str, candidates: list[str]) -> str:
    file_refs = sorted(item for item in candidates if item.startswith("file://"))
    if file_refs:
        return file_refs[0]
    if candidates:
        return sorted(candidates)[0]
    if "://" in source_ref:
        return source_ref
    return f"file://{source_ref}"


def _strategy_json(item: Any) -> dict[str, Any]:
    return {
        "alternative_id": item.alternative_id,
        "changed_files": list(item.changed_files),
        "explanation": item.explanation,
        "rollback_plan": item.rollback_plan,
        "score": item.score,
        "impact_size": item.impact_size,
        "test_burden": item.test_burden,
        "uncertainty": item.uncertainty,
        "metric_provenance": item.metric_provenance,
    }


def _blueprint_element_json(item: BlueprintElement) -> dict[str, Any]:
    return {
        "element_id": item.element_id,
        "planned_ref": item.planned_ref.value,
        "element_type": item.element_type,
        "expected_actual_refs": [ref.value for ref in item.expected_actual_refs],
        "acceptance_criteria": list(item.acceptance_criteria),
        "requires_verification": item.requires_verification,
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


def _focused_test_paths(
    changed_refs: tuple[str, ...], nodes: dict[str, Any], candidate_tests: list[str]
) -> list[str]:
    generic = {"src", "lib", "app", "service", "index", "main", "py", "extendcodeagent"}
    source_tokens = {
        token
        for ref in changed_refs
        if ref in nodes
        for part in Path(nodes[ref].source_ref).parts
        for token in Path(part).stem.casefold().split("_")
        if token and token not in generic
    }
    focused = [
        path
        for path in candidate_tests
        if source_tokens
        & {
            token
            for part in Path(path).parts
            for token in Path(part).stem.casefold().split("_")
            if token
        }
    ]
    return focused or candidate_tests


def _objective_test_paths(snapshot: GraphSnapshot, objective: str) -> set[str]:
    if not objective.strip():
        return set()
    ignored = {
        "and",
        "covers",
        "existing",
        "for",
        "its",
        "set",
        "smallest",
        "test",
        "tests",
        "the",
    }
    objective_tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", objective.casefold().replace("_", " "))
        if token not in ignored and len(token) > 2
    }
    by_path: dict[str, set[str]] = {}
    for node in snapshot.nodes:
        if node.node_type != "test":
            continue
        tokens = by_path.setdefault(node.source_ref, set())
        intent_tokens = node.properties.get("intent_tokens", ())
        if isinstance(intent_tokens, list | tuple | set):
            tokens.update(str(item).casefold() for item in intent_tokens)
        tokens.update(
            token
            for part in Path(node.source_ref).parts
            for token in re.findall(r"[a-z0-9]+", part.casefold().replace("_", " "))
        )
    selected: set[str] = set()
    for obligation in ("unit_behavior", "integration_boundary", "architecture_boundary"):
        ranked = sorted(
            (
                (len(objective_tokens & tokens), path)
                for path, tokens in by_path.items()
                if _test_obligation(path) == obligation
            ),
            key=lambda item: (-item[0], item[1]),
        )
        if ranked and ranked[0][0] > 0:
            selected.add(ranked[0][1])
    return selected


def _structural_test_paths(snapshot: GraphSnapshot, candidate_refs: set[str]) -> set[str]:
    return {
        edge.source_ref
        for edge in snapshot.edges
        if edge.edge_type == "structurally_covers" and edge.source.value in candidate_refs
    }


def _intent_architecture_test_paths(
    changed_refs: tuple[str, ...], nodes: dict[str, Any]
) -> set[str]:
    changed_tokens = {
        token
        for ref in changed_refs
        for value in (
            ref.rsplit("#", 1)[-1],
            nodes[ref].source_ref if ref in nodes else "",
        )
        for part in Path(value).parts
        for token in Path(part).stem.casefold().split("_")
        if len(token) >= 4 and token not in {"meets", "service", "source", "extendcodeagent"}
    }
    return {
        node.source_ref
        for node in nodes.values()
        if node.node_type == "test"
        and "architecture" in Path(node.source_ref).parts
        and changed_tokens
        & (
            set(node.properties.get("intent_tokens", ()))
            | set(Path(node.source_ref).stem.casefold().split("_"))
        )
    }


def _direct_use_count(
    snapshot: GraphSnapshot, changed_refs: set[str], production_refs: set[str]
) -> int:
    short_names = {ref.rsplit("#", 1)[-1].rsplit(".", 1)[-1] for ref in changed_refs}
    return sum(
        _edge_occurrences(edge)
        for edge in snapshot.edges
        if edge.source.value in production_refs
        and edge.edge_type in {"calls", "may_call", "references"}
        and (
            edge.target.value in changed_refs
            or edge.target.value.rsplit("#", 1)[-1].rsplit("/", 1)[-1] in short_names
        )
    )


def _edge_occurrences(edge: Any) -> int:
    value = edge.properties.get("occurrences", 1)
    return value if isinstance(value, int) else 1


def _test_obligation(path: str) -> str:
    parts = set(Path(path).parts)
    if "architecture" in parts:
        return "architecture_boundary"
    if "integration" in parts:
        return "integration_boundary"
    return "unit_behavior"


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
        "runtime_session_id": item.runtime_session_id,
        "runtime_call_id": item.runtime_call_id,
    }


def _runtime_signal_json(item: Any) -> dict[str, Any] | None:
    if item is None:
        return None
    return {
        "signal_id": item.signal_id,
        "kind": item.kind.value,
        "project": {
            "project_id": item.project.project_id,
            "workspace_id": item.project.workspace_id,
            "root_uri": item.project.root_uri,
            "worktree_fingerprint": item.project.worktree_fingerprint,
        },
        "observed_at": item.observed_at.isoformat(),
        "runtime_session_id": item.runtime_session_id,
        "task_text": item.task_text,
        "paths": list(item.paths),
        "source_category": item.source_category,
        "lifecycle_state": item.lifecycle_state,
        "model_provider": item.model_provider,
        "model_id": item.model_id,
        "delivery_channel": item.delivery_channel,
        "tool": item.tool,
        "provenance": {
            "source": item.provenance.source,
            "producer": item.provenance.producer,
            "producer_version": item.provenance.producer_version,
        },
    }


def _runtime_snapshot_json(item: Any) -> dict[str, Any]:
    capabilities = item.capabilities
    return {
        "project": {
            "project_id": item.project.project_id,
            "workspace_id": item.project.workspace_id,
            "root_uri": item.project.root_uri,
            "worktree_fingerprint": item.project.worktree_fingerprint,
        },
        "runtime": (
            None
            if capabilities is None
            else {
                "name": capabilities.runtime_name,
                "version": capabilities.runtime_version,
                "capabilities": [
                    {
                        "name": declaration.capability.value,
                        "status": declaration.status.value,
                        "reason": declaration.reason,
                    }
                    for declaration in capabilities.declarations
                ],
            }
        ),
        "signals": {
            "task": _runtime_signal_json(item.latest_task),
            "session": _runtime_signal_json(item.latest_session),
            "mutation": _runtime_signal_json(item.latest_mutation),
            "model": _runtime_signal_json(item.latest_model),
            "advisory_delivery": _runtime_signal_json(item.latest_advisory_delivery),
        },
        "tool_execution_count": item.tool_execution_count,
        "verification_count": item.verification_count,
        "latest_tool_observation_id": item.latest_tool_observation_id,
        "latest_verification_observation_id": item.latest_verification_observation_id,
        "diagnostics": list(item.diagnostics),
    }


def _plan_outcome_json(item: PlanOutcome | None) -> dict[str, Any] | None:
    if item is None:
        return None
    plan = item.plan
    return {
        "plan_id": plan.plan_id,
        "status": item.status,
        "recorded_at": item.recorded_at.isoformat(),
        "decision_latency_us": item.decision_latency_us,
        "behavior_changed": item.behavior_changed,
        "llm_calls": item.llm_calls,
        "intent": {
            "primary": plan.intent.primary.value,
            "secondary": [value.value for value in plan.intent.secondary],
            "uncertainty": plan.intent.uncertainty.value,
            "reasons": list(plan.intent.reasons),
        },
        "level": plan.level.value,
        "capabilities": [value.value for value in plan.capabilities],
        "unavailable_capabilities": [value.value for value in plan.unavailable_capabilities],
        "minimum_depth": plan.minimum_depth.value,
        "context_scope": plan.context_scope.value,
        "context_budget_tokens": plan.context_budget_tokens,
        "query_bounds": {
            "max_items": plan.query_bounds.max_items,
            "max_depth": plan.query_bounds.max_depth,
        },
        "evidence_needs": list(plan.evidence_needs),
        "escalation_conditions": list(plan.escalation_conditions),
        "fallback_rule": plan.fallback_rule,
        "reasons": list(plan.reasons),
        "actual_capabilities": [value.value for value in item.actual_capabilities],
        "actual_evidence_ids": list(item.actual_evidence_ids),
        "expansion_count": item.expansion_count,
        "fallback_reason": item.fallback_reason,
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


def _weak_local_evidence_json(package: WeakLocalEvidencePackage) -> dict[str, Any]:
    stable = stable_evidence_envelope()
    stable_payload = json.dumps(
        stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    stable_with_id = {
        **stable,
        "stable_prefix_id": hashlib.sha256(stable_payload).hexdigest()[:24],
    }
    task_evidence = {
        "revision_id": package.revision_id,
        "source_revision": package.source_revision.value if package.source_revision else None,
        "objective_fingerprint": package.objective_fingerprint,
        "scope": package.scope.value,
        "provenance": [
            {
                "id": identifier,
                "source": item.source,
                "producer": item.producer,
                "producer_version": item.producer_version,
            }
            for identifier, item in package.provenance
        ],
        "items": [
            {
                "id": item.evidence_id,
                "ref": item.canonical_ref.value,
                "kind": item.kind,
                "summary": item.summary,
                "reason": item.reason,
                "confidence": item.confidence,
                "provenance_id": item.provenance_id,
                "status": item.status,
            }
            for item in package.items
        ],
        "selected_evidence_ids": list(package.selected_evidence_ids),
        "prior_evidence_ids": list(package.prior_evidence_ids),
        "unresolved_evidence_gaps": list(package.unresolved_gaps),
        "request_next_scope": package.next_scope.value if package.next_scope else "none",
    }
    task_payload = json.dumps(
        task_evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return {
        "stable_envelope": stable_with_id,
        "task_evidence": task_evidence,
        "metrics": {
            "stable_prefix_canonical_bytes": len(stable_payload),
            "task_evidence_canonical_bytes": len(task_payload),
            "candidate_count": package.candidate_count,
            "selected_count": len(package.items),
            "excluded_count": package.excluded_count,
            "estimated_evidence_tokens": package.used_tokens,
            "token_budget": package.token_budget,
            "truncated": package.truncated,
            "candidate_search_truncated": package.candidate_search_truncated,
            "deterministic_resolution": package.deterministic_resolution,
            "cache_observation": "model_response_metrics",
        },
    }
