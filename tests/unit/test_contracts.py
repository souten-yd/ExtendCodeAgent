from __future__ import annotations

import dataclasses

import pytest

from extendcodeagent.core.contracts import (
    Confidence,
    ContractError,
    EvidenceRef,
    EvidenceStatus,
    ProjectRef,
    Provenance,
)


def test_project_ref_is_host_neutral_and_immutable() -> None:
    project = ProjectRef("project", "workspace", "file:///repo")
    with pytest.raises(dataclasses.FrozenInstanceError):
        project.project_id = "other"  # type: ignore[misc]


def test_confidence_rejects_out_of_range_values() -> None:
    with pytest.raises(ContractError):
        Confidence(1.01)


def test_provenance_copies_and_freezes_attributes() -> None:
    mutable = {"parser": "ast"}
    provenance = Provenance("static", "python", "1", attributes=mutable)
    mutable["parser"] = "changed"
    assert provenance.attributes["parser"] == "ast"
    with pytest.raises(TypeError):
        provenance.attributes["other"] = "value"  # type: ignore[index]


def test_unavailable_evidence_remains_explicit() -> None:
    evidence = EvidenceRef("evidence-1", EvidenceStatus.UNAVAILABLE)
    assert evidence.status is EvidenceStatus.UNAVAILABLE
