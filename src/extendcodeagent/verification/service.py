"""Deterministic V0a semantic-change and required-verification projections."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import replace

from extendcodeagent.analysis import ImpactReport
from extendcodeagent.core.contracts import CanonicalRef, FreshnessPolicy, TwinRevisionRef
from extendcodeagent.graph import FactStatus, GraphEdge, GraphNode, GraphSnapshot

from .contracts import (
    ChangeOperation,
    Criticality,
    ObligationStatus,
    ObligationType,
    RequiredSetQuality,
    RequiredVerificationProvider,
    RequiredVerificationSet,
    SemanticChangeSet,
    SemanticEntityChange,
    SemanticRelationChange,
    VerificationObligation,
)

_PUBLIC_TYPES = frozenset({"api_route", "api_schema", "config", "feature_flag"})
_TEST_TYPES = frozenset({"test", "test_intent"})


def derive_semantic_change_set(base: GraphSnapshot, candidate: GraphSnapshot) -> SemanticChangeSet:
    """Project an actual Graph/Twin delta without creating another source of truth."""

    if candidate.revision is None:
        raise ValueError("candidate snapshot must have a revision")
    base_identity = (base.project.project_id, base.project.workspace_id, base.project.root_uri)
    candidate_identity = (
        candidate.project.project_id,
        candidate.project.workspace_id,
        candidate.project.root_uri,
    )
    if base_identity != candidate_identity:
        raise ValueError("base and candidate snapshots must belong to the same project/workspace")

    base_nodes = {item.canonical_ref.value: item for item in base.nodes}
    candidate_nodes = {item.canonical_ref.value: item for item in candidate.nodes}
    entity_changes = _entity_changes(base_nodes, candidate_nodes)
    entity_changes = _expand_changed_file_uncertainty(entity_changes, candidate.nodes)

    base_edges = {_edge_key(item): item for item in base.edges}
    candidate_edges = {_edge_key(item): item for item in candidate.edges}
    relation_changes = _relation_changes(base_edges, candidate_edges)
    changed_files = tuple(
        sorted(
            {
                *(item.source_ref for item in entity_changes),
                *(item.source_ref for item in relation_changes),
            }
        )
    )
    unresolved = {
        ref
        for item in relation_changes
        if item.status is FactStatus.INFERRED
        for ref in (item.source, item.target)
    }
    unresolved.update(
        item.canonical_ref for item in entity_changes if item.status is FactStatus.INFERRED
    )
    base_revision = (
        TwinRevisionRef(base.revision.revision_id, base.revision.source_revision)
        if base.revision is not None
        else None
    )
    candidate_revision = TwinRevisionRef(
        candidate.revision.revision_id, candidate.revision.source_revision
    )
    payload = {
        "project": (candidate.project.project_id, candidate.project.workspace_id),
        "base": base_revision.revision_id if base_revision else None,
        "candidate": candidate_revision.revision_id,
        "entities": [
            (item.canonical_ref.value, item.entity_type, item.operation.value)
            for item in entity_changes
        ],
        "relations": [
            (item.source.value, item.target.value, item.relation_type, item.operation.value)
            for item in relation_changes
        ],
    }
    change_set_id = (
        "changeset:"
        + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:24]
    )
    return SemanticChangeSet(
        change_set_id,
        candidate.project,
        base_revision,
        candidate_revision,
        entity_changes,
        relation_changes,
        changed_files,
        tuple(sorted(unresolved, key=lambda ref: ref.value)),
    )


def derive_required_verification_set(
    change_set: SemanticChangeSet,
    impact: ImpactReport,
) -> RequiredVerificationSet:
    """Derive obligations and candidate providers without applying them to agent behavior."""

    if (
        impact.revision is None
        or impact.revision.revision_id != change_set.candidate_revision.revision_id
    ):
        raise ValueError("impact report must match the candidate Twin revision")

    obligation_specs: list[tuple[ObligationType, tuple[str, ...], float, bool]] = []
    for entity in change_set.entities:
        obligation_type = (
            ObligationType.TEST_INTENT
            if entity.entity_type in _TEST_TYPES
            else ObligationType.PUBLIC_CONTRACT
            if entity.entity_type in _PUBLIC_TYPES
            else ObligationType.LOCAL_BEHAVIOR
        )
        obligation_specs.append(
            (
                obligation_type,
                (entity.canonical_ref.value,),
                entity.confidence,
                entity.status is FactStatus.INFERRED,
            )
        )
    for impacted in (*impact.direct_impacts, *impact.transitive_impacts):
        if impacted.item_type not in _TEST_TYPES:
            obligation_specs.append(
                (
                    ObligationType.CONSUMER_BEHAVIOR,
                    (impacted.canonical_ref,),
                    min(impacted.confidence, impacted.path_confidence),
                    impacted.status is FactStatus.INFERRED,
                )
            )
    for requirement in impact.affected_requirements:
        obligation_specs.append(
            (
                ObligationType.REQUIREMENT,
                (requirement.canonical_ref,),
                requirement.path_confidence,
                False,
            )
        )
    for side_effect in impact.side_effects:
        obligation_specs.append(
            (
                ObligationType.SIDE_EFFECT,
                (side_effect.canonical_ref,),
                side_effect.path_confidence,
                False,
            )
        )
    for ref in change_set.unresolved_refs:
        obligation_specs.append((ObligationType.UNCERTAINTY_BOUNDARY, (ref.value,), 0.0, True))

    obligations = _obligations(change_set, obligation_specs)
    graph_coverable = {
        item.obligation_id
        for item in obligations
        if item.obligation_type
        in {
            ObligationType.LOCAL_BEHAVIOR,
            ObligationType.CONSUMER_BEHAVIOR,
            ObligationType.TEST_INTENT,
        }
    }
    providers = [
        RequiredVerificationProvider(
            f"test:{item.canonical_ref}",
            "test",
            CanonicalRef(item.canonical_ref),
            tuple(sorted(graph_coverable)),
            min(item.confidence, item.path_confidence),
            item.reason,
        )
        for item in impact.recommended_tests
    ]
    accepted_by_obligation = {
        obligation.obligation_id: tuple(
            sorted(
                provider.provider_id
                for provider in providers
                if obligation.obligation_id in provider.obligation_ids
            )
        )
        for obligation in obligations
    }
    obligations = tuple(
        replace(item, accepted_provider_ids=accepted_by_obligation[item.obligation_id])
        for item in obligations
    )
    selectable = {
        obligation_id for provider in providers for obligation_id in provider.obligation_ids
    }
    uncovered = tuple(
        item.obligation_id for item in obligations if item.obligation_id not in selectable
    )
    diagnostics: list[str] = []
    if not providers:
        diagnostics.append("no accepted verification provider covers the required obligations")
    if uncovered:
        diagnostics.append("required obligations remain uncovered")
    return RequiredVerificationSet(
        change_set.change_set_id,
        change_set.candidate_revision,
        obligations,
        tuple(sorted(providers, key=lambda item: item.provider_id)),
        uncovered,
        tuple(diagnostics),
    )


def evaluate_required_set_quality(
    required: RequiredVerificationSet, expected_provider_ids: Iterable[str]
) -> RequiredSetQuality:
    """Make V0a selection precision/recall measurable without tuning the selector here."""

    predicted = tuple(sorted({item.provider_id for item in required.providers}))
    expected = tuple(sorted(set(expected_provider_ids)))
    predicted_set = set(predicted)
    expected_set = set(expected)
    true_positive = len(predicted_set & expected_set)
    false_positive = len(predicted_set - expected_set)
    false_negative = len(expected_set - predicted_set)
    precision = (
        true_positive / len(predicted_set) if predicted_set else (1.0 if not expected_set else 0.0)
    )
    recall = true_positive / len(expected_set) if expected_set else 1.0
    return RequiredSetQuality(
        predicted,
        expected,
        true_positive,
        false_positive,
        false_negative,
        precision,
        recall,
    )


def _entity_changes(
    base: dict[str, GraphNode], candidate: dict[str, GraphNode]
) -> tuple[SemanticEntityChange, ...]:
    changes: list[SemanticEntityChange] = []
    for ref in sorted(set(base) | set(candidate)):
        before = base.get(ref)
        after = candidate.get(ref)
        if before is None:
            assert after is not None
            changes.append(_entity_change(after, ChangeOperation.ADDED))
        elif after is None:
            changes.append(_entity_change(before, ChangeOperation.REMOVED))
        elif _node_value(before) != _node_value(after):
            changes.append(_entity_change(after, ChangeOperation.CHANGED))
    return tuple(changes)


def _relation_changes(
    base: dict[tuple[str, str, str], GraphEdge],
    candidate: dict[tuple[str, str, str], GraphEdge],
) -> tuple[SemanticRelationChange, ...]:
    changes: list[SemanticRelationChange] = []
    for key in sorted(set(base) | set(candidate)):
        before = base.get(key)
        after = candidate.get(key)
        if before is None:
            assert after is not None
            changes.append(_relation_change(after, ChangeOperation.ADDED))
        elif after is None:
            changes.append(_relation_change(before, ChangeOperation.REMOVED))
        elif _edge_value(before) != _edge_value(after):
            changes.append(_relation_change(after, ChangeOperation.CHANGED))
    return tuple(changes)


def _expand_changed_file_uncertainty(
    changes: tuple[SemanticEntityChange, ...], candidate_nodes: tuple[GraphNode, ...]
) -> tuple[SemanticEntityChange, ...]:
    """Surface unmodeled body changes instead of treating unchanged symbol shells as unchanged."""

    changed_files = {
        item.source_ref
        for item in changes
        if item.entity_type == "file" and item.operation is ChangeOperation.CHANGED
    }
    if not changed_files:
        return changes
    by_ref = {item.canonical_ref.value: item for item in changes}
    for node in candidate_nodes:
        if (
            node.source_ref in changed_files
            and node.node_type not in {"repository", "directory", "file", "module", "package"}
            and node.canonical_ref.value not in by_ref
        ):
            by_ref[node.canonical_ref.value] = SemanticEntityChange(
                node.canonical_ref,
                node.node_type,
                node.source_ref,
                ChangeOperation.CHANGED,
                min(node.confidence.value, 0.5),
                FactStatus.INFERRED,
                node.provenance,
            )
    return tuple(sorted(by_ref.values(), key=lambda item: item.canonical_ref.value))


def _entity_change(item: GraphNode, operation: ChangeOperation) -> SemanticEntityChange:
    return SemanticEntityChange(
        item.canonical_ref,
        item.node_type,
        item.source_ref,
        operation,
        item.confidence.value,
        item.status,
        item.provenance,
    )


def _relation_change(item: GraphEdge, operation: ChangeOperation) -> SemanticRelationChange:
    return SemanticRelationChange(
        item.source,
        item.target,
        item.edge_type,
        item.source_ref,
        operation,
        item.confidence.value,
        item.status,
        item.provenance,
    )


def _node_value(item: GraphNode) -> tuple[object, ...]:
    return (
        item.node_type,
        item.source_ref,
        item.confidence,
        item.status,
        dict(item.properties),
        item.evidence,
    )


def _edge_key(item: GraphEdge) -> tuple[str, str, str]:
    return item.source.value, item.target.value, item.edge_type


def _edge_value(item: GraphEdge) -> tuple[object, ...]:
    return (
        item.source_ref,
        item.confidence,
        item.status,
        dict(item.properties),
        item.evidence,
    )


def _obligations(
    change_set: SemanticChangeSet,
    specs: list[tuple[ObligationType, tuple[str, ...], float, bool]],
) -> tuple[VerificationObligation, ...]:
    unique = sorted(set(specs), key=lambda item: (item[0].value, item[1]))
    obligations: list[VerificationObligation] = []
    for obligation_type, refs, confidence, uncertain in unique:
        payload = f"{change_set.change_set_id}\0{obligation_type.value}\0{'|'.join(refs)}"
        obligation_id = "obligation:" + hashlib.sha256(payload.encode()).hexdigest()[:24]
        required_kinds = _required_evidence_kinds(obligation_type)
        criticality = (
            Criticality.HIGH
            if obligation_type
            in {
                ObligationType.PUBLIC_CONTRACT,
                ObligationType.SIDE_EFFECT,
                ObligationType.UNCERTAINTY_BOUNDARY,
            }
            else Criticality.NORMAL
        )
        obligations.append(
            VerificationObligation(
                obligation_id,
                obligation_type,
                tuple(CanonicalRef(ref) for ref in refs),
                required_kinds,
                FreshnessPolicy.REQUIRED,
                confidence,
                uncertain,
                criticality,
                (),
                ObligationStatus.UNCOVERED,
            )
        )
    return tuple(obligations)


def _required_evidence_kinds(obligation_type: ObligationType) -> tuple[str, ...]:
    if obligation_type is ObligationType.SIDE_EFFECT:
        return ("test", "runtime")
    if obligation_type is ObligationType.PUBLIC_CONTRACT:
        return ("test", "integration")
    if obligation_type is ObligationType.UNCERTAINTY_BOUNDARY:
        return ("integration", "runtime")
    return ("test",)
