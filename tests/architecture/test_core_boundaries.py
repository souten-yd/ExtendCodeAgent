from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[2] / "src" / "extendcodeagent"
HOST_NEUTRAL_DIRS = (
    "analysis",
    "context",
    "core",
    "graph",
    "runtime",
    "service",
    "storage",
    "testing",
    "twin",
)
FORBIDDEN_IMPORT_PREFIXES = (
    "opencode",
    "atlas",
    "nexus",
    "openai",
    "anthropic",
    "google.generativeai",
    "extendcodeagent.adapters",
)


def test_core_has_no_host_application_or_provider_sdk_imports() -> None:
    violations: list[str] = []
    for directory in HOST_NEUTRAL_DIRS:
        for path in sorted((PACKAGE_ROOT / directory).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                modules: list[str] = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules = [node.module]
                for module in modules:
                    if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
                        location = f"{path.relative_to(PACKAGE_ROOT)}:{getattr(node, 'lineno', 0)}"
                        violations.append(f"{location}: {module}")
    assert violations == []


def test_core_source_contains_no_atlas_or_opencode_contract_names() -> None:
    forbidden = ("ProjectIdentity", "PlanPool", "@opencode-ai/")
    violations = []
    for directory in HOST_NEUTRAL_DIRS:
        for path in sorted((PACKAGE_ROOT / directory).rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            for token in forbidden:
                if token in source:
                    violations.append(f"{path.relative_to(PACKAGE_ROOT)}: {token}")
    assert violations == []
