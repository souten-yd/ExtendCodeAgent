"""Bounded, workspace-safe source snapshots with Git and non-Git identity."""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

from extendcodeagent.core.contracts import (
    Diagnostic,
    DiagnosticSeverity,
    ProjectRef,
    SourceRevision,
)

SOURCE_SNAPSHOT_VERSION = "source_snapshot.v2"
IGNORED_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "dist",
        "build",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".extendcodeagent",
    }
)


class SourceSnapshotError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SourceFileSnapshot:
    path: str
    size: int
    content_hash: str


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    project: ProjectRef
    source_revision: SourceRevision
    worktree_fingerprint: str
    files: tuple[SourceFileSnapshot, ...]
    changed_paths: tuple[str, ...]
    deleted_paths: tuple[str, ...]
    analyzer_versions: tuple[tuple[str, str], ...]
    diagnostics: tuple[Diagnostic, ...] = ()


class SourceSnapshotter:
    def __init__(self, *, max_files: int = 10_000, max_file_bytes: int = 2_000_000) -> None:
        if max_files <= 0 or max_file_bytes <= 0:
            raise ValueError("source snapshot bounds must be positive")
        self.max_files = max_files
        self.max_file_bytes = max_file_bytes

    def snapshot(
        self, project: ProjectRef, *, changed_paths: tuple[str, ...] | None = None
    ) -> SourceSnapshot:
        root = _root(project)
        requested = (
            None
            if changed_paths is None
            else tuple(_safe_rel(root, item) for item in changed_paths)
        )
        files: list[SourceFileSnapshot] = []
        diagnostics: list[Diagnostic] = []
        candidates, scope_source = _candidate_paths(root)
        diagnostics.append(Diagnostic("snapshot_scope", f"source scope resolved by {scope_source}"))
        for path in candidates:
            if not path.is_file():
                continue
            resolved = path.resolve()
            try:
                relative = resolved.relative_to(root)
            except ValueError:
                diagnostics.append(Diagnostic("unsafe_path", f"skipped path outside root: {path}"))
                continue
            if any(
                part.lower() in IGNORED_NAMES or part.lower().endswith(".egg-info")
                for part in relative.parts
            ):
                continue
            if len(files) >= self.max_files:
                # Truncation silently starves whole subtrees of the Twin, so it is an error
                # rather than a note: every downstream PI answer would be scoped to a prefix
                # of the walk order instead of to the project.
                diagnostics.append(
                    Diagnostic(
                        "file_limit",
                        f"source file count limit reached at {self.max_files}; "
                        "the Twin covers only part of the project",
                        DiagnosticSeverity.ERROR,
                    )
                )
                break
            size = resolved.stat().st_size
            if size > self.max_file_bytes:
                diagnostics.append(
                    Diagnostic("oversized_file", f"skipped oversized file: {relative}")
                )
                continue
            data = resolved.read_bytes()
            if b"\0" in data[:2048]:
                diagnostics.append(Diagnostic("binary_file", f"skipped binary file: {relative}"))
                continue
            files.append(
                SourceFileSnapshot(relative.as_posix(), size, hashlib.sha256(data).hexdigest())
            )
        git_head = _git(root, "rev-parse", "HEAD")
        source_revision = SourceRevision(
            git_head or _tree_hash(files), "git" if git_head else "content"
        )
        status = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
        changed, deleted = _changes(root, status, requested)
        fingerprint = _fingerprint(source_revision.value, files)
        resolved_project = ProjectRef(
            project.project_id,
            project.workspace_id,
            root.as_uri(),
            project.repository_id,
            project.branch,
            source_revision.value,
            fingerprint,
        )
        return SourceSnapshot(
            resolved_project,
            source_revision,
            fingerprint,
            tuple(files),
            changed,
            deleted,
            (("source_snapshot", SOURCE_SNAPSHOT_VERSION),),
            tuple(diagnostics),
        )


def _root(project: ProjectRef) -> Path:
    if not project.root_uri.startswith("file://"):
        raise SourceSnapshotError("PR-B source snapshots require a file URI")
    root = Path(project.root_uri.removeprefix("file://")).resolve()
    if not root.is_dir():
        raise SourceSnapshotError(f"project root is not a directory: {root}")
    return root


def _safe_rel(root: Path, value: str) -> str:
    candidate = (root / value).resolve()
    try:
        return candidate.relative_to(root).as_posix()
    except ValueError as exc:
        raise SourceSnapshotError(f"path escapes project root: {value}") from exc


def _candidate_paths(root: Path) -> tuple[tuple[Path, ...], str]:
    """Resolve the project's own source scope.

    A recursive walk cannot tell project source from build output, evaluation corpora or
    vendored checkouts, so in a Git worktree the repository's own ignore rules decide the
    scope. Only a non-Git root falls back to the walk plus `IGNORED_NAMES`.
    """

    listed = _git_lines(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if listed is None:
        return tuple(sorted(root.rglob("*"))), "filesystem_walk"
    return tuple(sorted(root / item for item in listed)), "git_exclude_standard"


def _git_lines(root: Path, *args: str) -> tuple[str, ...] | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    listed = result.stdout.decode("utf-8", "surrogateescape").split("\0")
    return tuple(item for item in listed if item)


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _tree_hash(files: list[SourceFileSnapshot]) -> str:
    return hashlib.sha256(
        "\n".join(f"{f.path}:{f.content_hash}" for f in files).encode()
    ).hexdigest()


def _fingerprint(source_revision: str, files: list[SourceFileSnapshot]) -> str:
    payload = "\n".join([source_revision, *(f"{f.path}:{f.size}:{f.content_hash}" for f in files)])
    return hashlib.sha256(payload.encode()).hexdigest()


def _changes(
    root: Path, status: str | None, requested: tuple[str, ...] | None
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if requested is not None:
        requested_deleted = tuple(sorted(path for path in requested if not (root / path).exists()))
        return tuple(sorted(set(requested))), requested_deleted
    changed: set[str] = set()
    git_deleted: set[str] = set()
    for line in (status or "").splitlines():
        raw = line[3:].split(" -> ")[-1].strip('"')
        rel = _safe_rel(root, raw)
        changed.add(rel)
        if "D" in line[:2]:
            git_deleted.add(rel)
    return tuple(sorted(changed)), tuple(sorted(git_deleted))
