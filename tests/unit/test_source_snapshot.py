from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from extendcodeagent.core.contracts import ProjectRef
from extendcodeagent.twin import SourceSnapshotter
from extendcodeagent.twin.source_snapshot import SourceSnapshotError


def _project(root: Path) -> ProjectRef:
    return ProjectRef("p", "w", root.resolve().as_uri())


def test_non_git_snapshot_is_deterministic_and_detects_same_size_edit(tmp_path: Path) -> None:
    path = tmp_path / "app.py"
    path.write_text("value = 1\n", encoding="utf-8")
    first = SourceSnapshotter().snapshot(_project(tmp_path))
    again = SourceSnapshotter().snapshot(_project(tmp_path))
    path.write_text("value = 2\n", encoding="utf-8")
    changed = SourceSnapshotter().snapshot(_project(tmp_path))
    assert first.source_revision.kind == "content"
    assert first.worktree_fingerprint == again.worktree_fingerprint
    assert changed.worktree_fingerprint != first.worktree_fingerprint


def test_snapshot_is_bounded_and_skips_binary(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "blob.bin").write_bytes(b"\0\1")
    snapshot = SourceSnapshotter().snapshot(_project(tmp_path))
    assert [item.path for item in snapshot.files] == ["a.py"]
    assert any(item.code == "binary_file" for item in snapshot.diagnostics)


def test_requested_path_escape_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(SourceSnapshotError):
        SourceSnapshotter().snapshot(_project(tmp_path), changed_paths=("../outside.py",))


def test_git_head_and_untracked_state_are_distinct(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.com"], check=True
    )
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test"], check=True)
    (tmp_path / "tracked.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "tracked.py"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-qm", "initial"], check=True)
    clean = SourceSnapshotter().snapshot(_project(tmp_path))
    (tmp_path / "new.py").write_text("new = True\n", encoding="utf-8")
    dirty = SourceSnapshotter().snapshot(_project(tmp_path))
    assert clean.source_revision == dirty.source_revision
    assert clean.worktree_fingerprint != dirty.worktree_fingerprint
    assert dirty.changed_paths == ("new.py",)
