"""V0a must project existing truth, not introduce a competing verification store."""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).parents[2] / "src" / "extendcodeagent" / "verification"


def test_verification_slice_has_no_storage_or_runtime_adapter_dependency() -> None:
    imported: set[str] = set()
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(item.name for item in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)

    forbidden = ("extendcodeagent.storage", "sqlite", "opencode", "pathlib")
    assert not any(name.startswith(forbidden) for name in imported)


def test_verification_service_exposes_only_pure_projection_operations() -> None:
    path = PACKAGE / "service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }

    assert public_functions == {
        "derive_semantic_change_set",
        "derive_required_verification_set",
        "evaluate_required_set_quality",
    }
    assert not any(isinstance(node, ast.ClassDef) for node in tree.body)


def test_verification_contract_dataclasses_are_frozen_and_slotted() -> None:
    path = PACKAGE / "contracts.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    dataclasses = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and getattr(decorator.func, "id", None) == "dataclass"
            ):
                dataclasses.append(decorator)

    assert dataclasses
    for decorator in dataclasses:
        keywords = {item.arg: item.value for item in decorator.keywords}
        frozen = keywords.get("frozen")
        slots = keywords.get("slots")
        assert isinstance(frozen, ast.Constant)
        assert frozen.value is True
        assert isinstance(slots, ast.Constant)
        assert slots.value is True
