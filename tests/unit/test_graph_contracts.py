from __future__ import annotations

import dataclasses

import pytest

from extendcodeagent.core.contracts import (
    CanonicalRef,
    Confidence,
    ProjectRef,
    Provenance,
    SourceRevision,
)
from extendcodeagent.graph import FactStatus, GraphNode, GraphRevision


def test_graph_fact_carries_required_truth_metadata_and_is_immutable() -> None:
    source = SourceRevision("abc")
    node = GraphNode(
        "n1",
        CanonicalRef("file://app.py"),
        "file",
        "app.py",
        Provenance("static", "source_snapshot", "v1", source),
        Confidence(1.0),
        FactStatus.DECLARED,
        source,
        {"size": 10},
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        node.status = FactStatus.INVALIDATED  # type: ignore[misc]
    with pytest.raises(TypeError):
        node.properties["size"] = 11  # type: ignore[index]


def test_graph_revision_analyzer_versions_are_copied_and_frozen() -> None:
    versions = {"source_snapshot": "v1"}
    revision = GraphRevision(
        "r1", ProjectRef("p", "w", "file:///repo"), SourceRevision("abc"), "dirty", versions
    )
    versions["source_snapshot"] = "changed"
    assert revision.analyzer_versions["source_snapshot"] == "v1"
