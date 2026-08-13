"""Deterministic structural and Python AST graph analysis."""

from __future__ import annotations

import ast
import builtins
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from extendcodeagent.core.contracts import (
    CanonicalRef,
    Confidence,
    Diagnostic,
    ProjectRef,
    Provenance,
)
from extendcodeagent.graph.contracts import FactStatus, GraphEdge, GraphNode

from .contracts import GraphAnalysis

if TYPE_CHECKING:
    from extendcodeagent.twin.source_snapshot import SourceSnapshot

PYTHON_ANALYZER_VERSION = "python_ast.v1"
_BUILTINS = frozenset(dir(builtins))


@dataclass(frozen=True, slots=True)
class _Definition:
    ref: str
    kind: str
    name: str
    qualname: str
    module: str
    path: str
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


@dataclass(frozen=True, slots=True)
class _ModuleInfo:
    path: str
    dotted: str
    tree: ast.Module
    imports: dict[str, tuple[str, str | None]]


class PythonGraphAnalyzer:
    """Analyze a source snapshot without store, host, or model dependencies."""

    analyzer_versions: tuple[tuple[str, str], ...] = (("python_ast", PYTHON_ANALYZER_VERSION),)

    def analyze(
        self,
        project: ProjectRef,
        snapshot: SourceSnapshot,
        *,
        paths: tuple[str, ...] | None = None,
    ) -> GraphAnalysis:
        root = Path(project.root_uri.removeprefix("file://")).resolve()
        selected = set(paths) if paths is not None else None
        all_modules = {
            _module_dotted(item.path): item.path
            for item in snapshot.files
            if item.path.endswith(".py")
        }
        modules: list[_ModuleInfo] = []
        diagnostics: list[Diagnostic] = []
        for item in snapshot.files:
            if not item.path.endswith(".py") or (
                selected is not None and item.path not in selected
            ):
                continue
            try:
                tree = ast.parse((root / item.path).read_text(encoding="utf-8"), item.path)
            except (OSError, UnicodeError, SyntaxError) as exc:
                diagnostics.append(
                    Diagnostic("python_parse_error", f"could not parse {item.path}: {exc}")
                )
                continue
            dotted = _module_dotted(item.path)
            modules.append(_ModuleInfo(item.path, dotted, tree, _imports(tree, dotted, item.path)))

        definitions = _collect_definitions(modules)
        nodes: dict[str, GraphNode] = {}
        edges: dict[str, GraphEdge] = {}

        def add_node(
            ref: str,
            kind: str,
            source_ref: str,
            *,
            confidence: float = 1.0,
            status: FactStatus = FactStatus.DECLARED,
            properties: dict[str, object] | None = None,
        ) -> None:
            nodes.setdefault(
                ref,
                GraphNode(
                    _stable_id("node", ref),
                    CanonicalRef(ref),
                    kind,
                    source_ref,
                    _provenance(snapshot),
                    Confidence(confidence, "deterministic Python AST"),
                    status,
                    snapshot.source_revision,
                    properties or {},
                ),
            )

        def add_edge(
            source: str,
            target: str,
            kind: str,
            source_ref: str,
            *,
            confidence: float = 1.0,
            status: FactStatus = FactStatus.DECLARED,
            properties: dict[str, object] | None = None,
        ) -> None:
            key = f"{source}\0{kind}\0{target}"
            edges.setdefault(
                key,
                GraphEdge(
                    _stable_id("edge", key),
                    CanonicalRef(source),
                    CanonicalRef(target),
                    kind,
                    source_ref,
                    _provenance(snapshot),
                    Confidence(confidence, "deterministic Python AST"),
                    status,
                    snapshot.source_revision,
                    properties or {},
                ),
            )

        repo_ref = f"repo://{project.project_id}/{project.workspace_id}"
        if selected is None:
            add_node(repo_ref, "repository", ".")
        file_by_path = {item.path: item for item in snapshot.files}
        analyzed_paths = {
            item.path for item in snapshot.files if selected is None or item.path in selected
        }
        for path in sorted(analyzed_paths):
            item = file_by_path[path]
            file_ref = f"file://{path}"
            add_node(
                file_ref,
                "file",
                path,
                properties={"size": item.size, "content_hash": item.content_hash},
            )
            parent_ref = repo_ref
            parts = Path(path).parts[:-1]
            cumulative: list[str] = []
            for part in parts:
                cumulative.append(part)
                directory = "/".join(cumulative)
                directory_ref = f"dir://{directory}"
                if selected is None:
                    add_node(directory_ref, "directory", directory)
                    add_edge(parent_ref, directory_ref, "contains", directory)
                parent_ref = directory_ref
            add_edge(parent_ref, file_ref, "contains", path)

        for module in modules:
            module_ref = f"module://{module.dotted}"
            file_ref = f"file://{module.path}"
            add_node(module_ref, "module", module.path)
            add_edge(file_ref, module_ref, "contains", module.path)
            for bound, (imported_module, imported_name) in sorted(module.imports.items()):
                target_module = _best_module(imported_module, all_modules)
                if target_module is None:
                    dependency = imported_module.split(".", 1)[0]
                    target = f"dependency://{dependency}"
                    add_node(target, "dependency", module.path)
                elif imported_name is None:
                    target = f"module://{imported_module}"
                else:
                    target = f"py://{imported_module}#{imported_name}"
                add_edge(
                    module_ref,
                    target,
                    "imports",
                    module.path,
                    properties={"bound_name": bound},
                )

        for definition in definitions.values():
            if selected is not None and definition.path not in selected:
                continue
            add_node(
                definition.ref,
                "test" if _is_test(definition) else definition.kind,
                definition.path,
                properties={
                    "name": definition.name,
                    "qualname": definition.qualname,
                    "start_line": definition.node.lineno,
                    "end_line": getattr(definition.node, "end_lineno", definition.node.lineno),
                },
            )
            add_edge(
                f"module://{definition.module}",
                definition.ref,
                "defines",
                definition.path,
            )

        by_module_name = {(item.module, item.name): item for item in definitions.values()}
        classes = {item.ref: item for item in definitions.values() if item.kind == "class"}
        methods = {
            (item.module, item.qualname.rsplit(".", 1)[0], item.name): item
            for item in definitions.values()
            if item.kind == "method"
        }
        for module in modules:
            for definition in definitions.values():
                if definition.module != module.dotted or definition.path != module.path:
                    continue
                _emit_semantic_edges(
                    definition,
                    module,
                    definitions,
                    by_module_name,
                    classes,
                    methods,
                    add_edge,
                )

        return GraphAnalysis(
            tuple(sorted(nodes.values(), key=lambda item: item.canonical_ref.value)),
            tuple(sorted(edges.values(), key=lambda item: item.edge_id)),
            tuple(diagnostics),
            self.analyzer_versions,
        )


def _emit_semantic_edges(
    definition: _Definition,
    module: _ModuleInfo,
    definitions: dict[str, _Definition],
    by_module_name: dict[tuple[str, str], _Definition],
    classes: dict[str, _Definition],
    methods: dict[tuple[str, str, str], _Definition],
    add_edge: object,
) -> None:
    emit = add_edge
    assert callable(emit)
    node = definition.node
    for decorator in getattr(node, "decorator_list", ()):
        expression = decorator.func if isinstance(decorator, ast.Call) else decorator
        name = _expression_name(expression)
        if name:
            target, resolved = _resolve_expression(name, module, by_module_name)
            emit(
                definition.ref,
                target,
                "decorated_by",
                definition.path,
                confidence=1.0 if resolved else 0.5,
                status=FactStatus.DECLARED if resolved else FactStatus.INFERRED,
            )
    if isinstance(node, ast.ClassDef):
        for base_node in node.bases:
            name = _expression_name(base_node)
            if not name:
                continue
            target, resolved = _resolve_expression(name, module, by_module_name)
            emit(
                definition.ref,
                target,
                "inherits",
                definition.path,
                confidence=1.0 if resolved else 0.5,
                status=FactStatus.DECLARED if resolved else FactStatus.INFERRED,
            )
        return
    if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        return
    owner_class = definition.qualname.rsplit(".", 1)[0] if definition.kind == "method" else None
    call_nodes: set[int] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        call_nodes.add(id(child.func))
        name = _expression_name(child.func)
        if not name:
            continue
        call_target, confidence = _resolve_call(
            name, owner_class, module, definitions, by_module_name, classes, methods
        )
        resolved = call_target is not None
        emit(
            definition.ref,
            call_target or f"pyname://{name.rsplit('.', 1)[-1]}",
            "calls" if resolved else "may_call",
            definition.path,
            confidence=confidence,
            status=FactStatus.DECLARED if resolved else FactStatus.INFERRED,
        )
    for child in ast.walk(node):
        if not isinstance(child, ast.Name) or not isinstance(child.ctx, ast.Load):
            continue
        if id(child) in call_nodes or child.id in _BUILTINS:
            continue
        target, resolved = _resolve_expression(child.id, module, by_module_name)
        if resolved:
            emit(definition.ref, target, "references", definition.path, confidence=0.9)


def _resolve_call(
    name: str,
    owner_class: str | None,
    module: _ModuleInfo,
    definitions: dict[str, _Definition],
    by_module_name: dict[tuple[str, str], _Definition],
    classes: dict[str, _Definition],
    methods: dict[tuple[str, str, str], _Definition],
) -> tuple[str | None, float]:
    if name.startswith("self.") and owner_class:
        method_name = name.split(".")[-1]
        direct = methods.get((module.dotted, owner_class, method_name))
        if direct:
            return direct.ref, 0.95
        class_ref = f"py://{module.dotted}#{owner_class}"
        class_definition = classes.get(class_ref)
        if class_definition and isinstance(class_definition.node, ast.ClassDef):
            for base in class_definition.node.bases:
                base_name = _expression_name(base)
                if not base_name:
                    continue
                inherited = methods.get((module.dotted, base_name, method_name))
                if inherited:
                    return inherited.ref, 0.9
        return None, 0.35
    target, resolved = _resolve_expression(name, module, by_module_name)
    if resolved and target in definitions:
        return target, 1.0
    if resolved and target.startswith("py://"):
        return target, 1.0
    return None, 0.35


def _resolve_expression(
    name: str,
    module: _ModuleInfo,
    by_module_name: dict[tuple[str, str], _Definition],
) -> tuple[str, bool]:
    first, _, rest = name.partition(".")
    imported = module.imports.get(first)
    if imported:
        imported_module, imported_name = imported
        symbol = imported_name or rest
        if symbol:
            return f"py://{imported_module}#{symbol}", True
        return f"module://{imported_module}", True
    local = by_module_name.get((module.dotted, first))
    if local:
        return local.ref, True
    return f"pyname://{name.rsplit('.', 1)[-1]}", False


def _collect_definitions(modules: list[_ModuleInfo]) -> dict[str, _Definition]:
    result: dict[str, _Definition] = {}
    for module in modules:
        for node in module.tree.body:
            if isinstance(node, ast.ClassDef):
                ref = f"py://{module.dotted}#{node.name}"
                result[ref] = _Definition(
                    ref, "class", node.name, node.name, module.dotted, module.path, node
                )
                for child in node.body:
                    if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                        qualname = f"{node.name}.{child.name}"
                        method_ref = f"py://{module.dotted}#{qualname}"
                        result[method_ref] = _Definition(
                            method_ref,
                            "method",
                            child.name,
                            qualname,
                            module.dotted,
                            module.path,
                            child,
                        )
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                ref = f"py://{module.dotted}#{node.name}"
                result[ref] = _Definition(
                    ref, "function", node.name, node.name, module.dotted, module.path, node
                )
    return result


def _imports(tree: ast.Module, dotted: str, path: str) -> dict[str, tuple[str, str | None]]:
    result: dict[str, tuple[str, str | None]] = {}
    package = dotted if path.endswith("/__init__.py") else dotted.rpartition(".")[0]
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                result[alias.asname or alias.name.split(".", 1)[0]] = (alias.name, None)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = package.split(".") if package else []
                keep = max(0, len(parts) - (node.level - 1))
                base = ".".join([*parts[:keep], *([base] if base else [])]).strip(".")
            for alias in node.names:
                if alias.name != "*":
                    result[alias.asname or alias.name] = (base, alias.name)
    return result


def _best_module(imported: str, modules: dict[str, str]) -> str | None:
    if imported in modules:
        return imported
    return next((name for name in modules if name.startswith(f"{imported}.")), None)


def _module_dotted(path: str) -> str:
    value = Path(path).with_suffix("")
    parts = list(value.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _expression_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _expression_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return None


def _is_test(definition: _Definition) -> bool:
    filename = Path(definition.path).name
    return definition.name.startswith("test_") and (
        filename.startswith("test_") or filename.endswith("_test.py")
    )


def _stable_id(kind: str, value: str) -> str:
    return hashlib.sha256(f"{kind}\0{value}".encode()).hexdigest()


def _provenance(snapshot: SourceSnapshot) -> Provenance:
    return Provenance(
        "source_ast", "python_graph_analyzer", PYTHON_ANALYZER_VERSION, snapshot.source_revision
    )
