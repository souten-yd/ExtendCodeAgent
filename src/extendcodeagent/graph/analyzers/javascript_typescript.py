"""Deterministic JavaScript/TypeScript semantic facts from official tree-sitter grammars."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import chain
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

import tree_sitter_javascript
import tree_sitter_typescript
from tree_sitter import Language, Node, Parser

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

JAVASCRIPT_TYPESCRIPT_ANALYZER_VERSION = "tree_sitter_js_ts.v1"
_SUFFIXES = frozenset({".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"})
_JS_LANGUAGE = Language(tree_sitter_javascript.language())
_TS_LANGUAGE = Language(tree_sitter_typescript.language_typescript())
_TSX_LANGUAGE = Language(tree_sitter_typescript.language_tsx())


@dataclass(frozen=True, slots=True)
class _Import:
    target_path: str | None
    target_name: str | None
    specifier: str


@dataclass(frozen=True, slots=True)
class _Definition:
    ref: str
    kind: str
    name: str
    qualname: str
    path: str
    node_type: str
    start_byte: int
    end_byte: int
    start_line: int
    end_line: int
    owner_class: str | None = None
    decorators: tuple[str, ...] = ()
    base_name: str | None = None


@dataclass(frozen=True, slots=True)
class _Module:
    path: str
    source: bytes
    imports: dict[str, _Import]
    import_targets: tuple[tuple[str, str | None], ...]


class JavaScriptTypeScriptGraphAnalyzer:
    """Emit declared facts only when tree-sitter structure supports them."""

    analyzer_versions: tuple[tuple[str, str], ...] = (
        ("javascript_typescript", JAVASCRIPT_TYPESCRIPT_ANALYZER_VERSION),
    )

    def analyze(
        self,
        project: ProjectRef,
        snapshot: SourceSnapshot,
        *,
        paths: tuple[str, ...] | None = None,
    ) -> GraphAnalysis:
        root_path = Path(project.root_uri.removeprefix("file://")).resolve()
        selected = set(paths) if paths is not None else None
        relevant_paths = {
            item.path for item in snapshot.files if Path(item.path).suffix.lower() in _SUFFIXES
        }
        parsers = {
            "javascript": Parser(_JS_LANGUAGE),
            "typescript": Parser(_TS_LANGUAGE),
            "tsx": Parser(_TSX_LANGUAGE),
        }
        modules: list[_Module] = []
        definitions: dict[str, _Definition] = {}
        diagnostics: list[Diagnostic] = []
        for path in sorted(relevant_paths):
            try:
                source = (root_path / path).read_bytes()
                tree = _parser_for(path, parsers).parse(source)
            except OSError as exc:
                if selected is None or path in selected:
                    diagnostics.append(
                        Diagnostic(
                            "javascript_typescript_parse_error",
                            f"could not parse {path}: {exc}",
                        )
                    )
                continue
            if tree.root_node.has_error:
                if selected is None or path in selected:
                    diagnostics.append(
                        Diagnostic(
                            "javascript_typescript_parse_error",
                            f"tree-sitter reported a syntax error in {path}",
                        )
                    )
                continue
            imports, targets = _imports(path, tree.root_node, source, relevant_paths)
            module = _Module(path, source, imports, targets)
            modules.append(module)
            _collect_module_definitions(definitions, module, tree.root_node)

        by_path_name = {(item.path, item.name): item for item in definitions.values()}
        modules_by_path = {item.path: item for item in modules}
        classes = {item.ref: item for item in definitions.values() if item.kind == "class"}
        methods = {
            (item.path, item.owner_class or "", item.name): item
            for item in definitions.values()
            if item.kind == "method"
        }
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
                    Confidence(confidence, "deterministic tree-sitter syntax"),
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
                    Confidence(confidence, "deterministic tree-sitter syntax"),
                    status,
                    snapshot.source_revision,
                    properties or {},
                ),
            )

        repo_ref = f"repo://{project.project_id}/{project.workspace_id}"
        if selected is None:
            add_node(repo_ref, "repository", ".")
        file_by_path = {item.path: item for item in snapshot.files}
        emitted_paths = sorted(
            path for path in relevant_paths if selected is None or path in selected
        )
        for path in emitted_paths:
            item = file_by_path[path]
            file_ref = f"file://{path}"
            add_node(
                file_ref,
                "file",
                path,
                properties={"size": item.size, "content_hash": item.content_hash},
            )
            parent_ref = repo_ref
            cumulative: list[str] = []
            for part in PurePosixPath(path).parts[:-1]:
                cumulative.append(part)
                directory = "/".join(cumulative)
                directory_ref = f"dir://{directory}"
                if selected is None:
                    add_node(directory_ref, "directory", directory)
                    add_edge(parent_ref, directory_ref, "contains", directory)
                parent_ref = directory_ref
            add_edge(parent_ref, file_ref, "contains", path)

        for module in modules:
            if selected is not None and module.path not in selected:
                continue
            module_ref = f"module://{module.path}"
            add_node(module_ref, "module", module.path)
            add_edge(f"file://{module.path}", module_ref, "contains", module.path)
            for specifier, target_path in module.import_targets:
                if target_path is None:
                    target = f"dependency://{specifier.split('/', 1)[0].removeprefix('@')}"
                    add_node(target, "dependency", module.path)
                    add_edge(module_ref, target, "depends_on", module.path)
                else:
                    target = f"module://{target_path}"
                add_edge(
                    module_ref,
                    target,
                    "imports",
                    module.path,
                    properties={"specifier": specifier},
                )

        for definition in definitions.values():
            if selected is not None and definition.path not in selected:
                continue
            add_node(
                definition.ref,
                definition.kind,
                definition.path,
                properties={
                    "name": definition.name,
                    "qualname": definition.qualname,
                    "start_line": definition.start_line,
                    "end_line": definition.end_line,
                },
            )
            owner = (
                f"js://{definition.path}#{definition.owner_class}"
                if definition.owner_class
                else f"module://{definition.path}"
            )
            add_edge(owner, definition.ref, "defines", definition.path)

        for module in modules:
            if selected is not None and module.path not in selected:
                continue
            tree = _parser_for(module.path, parsers).parse(module.source)
            wanted_ranges = {
                (definition.start_byte, definition.end_byte, definition.node_type)
                for definition in definitions.values()
                if definition.path == module.path
            }
            nodes_by_range = {
                (node.start_byte, node.end_byte, node.type): node
                for node in chain((tree.root_node,), _walk(tree.root_node))
                if (node.start_byte, node.end_byte, node.type) in wanted_ranges
            }
            for definition in definitions.values():
                if definition.path != module.path:
                    continue
                node = nodes_by_range.get(
                    (definition.start_byte, definition.end_byte, definition.node_type)
                )
                if node is None:
                    continue
                _emit_definition_edges(
                    definition,
                    node,
                    module,
                    by_path_name,
                    classes,
                    methods,
                    modules_by_path,
                    add_edge,
                )

        return GraphAnalysis(
            tuple(sorted(nodes.values(), key=lambda item: item.canonical_ref.value)),
            tuple(sorted(edges.values(), key=lambda item: item.edge_id)),
            tuple(diagnostics),
            self.analyzer_versions,
        )


def _parser_for(path: str, parsers: dict[str, Parser]) -> Parser:
    suffix = Path(path).suffix.lower()
    key = "tsx" if suffix == ".tsx" else "typescript" if suffix == ".ts" else "javascript"
    return parsers[key]


def _imports(
    path: str,
    root: Node,
    source: bytes,
    available_paths: set[str],
) -> tuple[dict[str, _Import], tuple[tuple[str, str | None], ...]]:
    bindings: dict[str, _Import] = {}
    targets: set[tuple[str, str | None]] = set()
    for statement in root.named_children:
        if statement.type != "import_statement":
            continue
        source_node = statement.child_by_field_name("source")
        if source_node is None:
            continue
        specifier = _string_value(source, source_node)
        target_path = _resolve_module_path(path, specifier, available_paths)
        targets.add((specifier, target_path))
        for node in _walk(statement):
            if node.type == "import_specifier":
                name_node = node.child_by_field_name("name")
                alias_node = node.child_by_field_name("alias")
                if name_node is None:
                    continue
                target_name = _text(source, name_node)
                bound = _text(source, alias_node or name_node)
                bindings[bound] = _Import(target_path, target_name, specifier)
            elif node.type == "namespace_import":
                identifier = next(
                    (child for child in node.named_children if child.type == "identifier"), None
                )
                if identifier is not None:
                    bindings[_text(source, identifier)] = _Import(target_path, None, specifier)
        clause = next(
            (child for child in statement.named_children if child.type == "import_clause"), None
        )
        if clause is not None:
            default = next(
                (child for child in clause.named_children if child.type == "identifier"), None
            )
            if default is not None:
                bindings[_text(source, default)] = _Import(target_path, "default", specifier)
    return bindings, tuple(sorted(targets, key=lambda item: (item[0], item[1] or "")))


def _resolve_module_path(current: str, specifier: str, available: set[str]) -> str | None:
    if not specifier.startswith("."):
        return None
    base = PurePosixPath(current).parent.joinpath(specifier)
    normalized = str(PurePosixPath(*[part for part in base.parts if part != "."]))
    while "/../" in f"/{normalized}/":
        parts: list[str] = []
        for part in PurePosixPath(normalized).parts:
            if part == ".." and parts:
                parts.pop()
            elif part != ".":
                parts.append(part)
        normalized = "/".join(parts)
    candidates = [normalized]
    if Path(normalized).suffix.lower() not in _SUFFIXES:
        candidates.extend(f"{normalized}{suffix}" for suffix in sorted(_SUFFIXES))
        candidates.extend(f"{normalized}/index{suffix}" for suffix in sorted(_SUFFIXES))
    return next((item for item in candidates if item in available), None)


def _collect_module_definitions(
    result: dict[str, _Definition], module: _Module, root: Node
) -> None:
    pending_decorators: list[Node] = []
    for top in root.named_children:
        declaration = top
        decorators: tuple[Node, ...] = ()
        if top.type == "export_statement":
            declaration = top.child_by_field_name("declaration") or top
            decorators = tuple(child for child in top.named_children if child.type == "decorator")
        if declaration.type == "decorator":
            pending_decorators.append(declaration)
            continue
        decorators = (*pending_decorators, *decorators)
        pending_decorators.clear()
        _collect_declaration(result, module, declaration, decorators)


def _collect_declaration(
    result: dict[str, _Definition],
    module: _Module,
    node: Node,
    decorators: tuple[Node, ...],
) -> None:
    if node.type in {"function_declaration", "generator_function_declaration"}:
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            _store_definition(
                result, module, node, _text(module.source, name_node), "function", decorators
            )
        return
    if node.type == "class_declaration":
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        class_name = _text(module.source, name_node)
        _store_definition(result, module, node, class_name, "class", decorators)
        body = node.child_by_field_name("body")
        if body is None:
            return
        pending: list[Node] = []
        for child in body.named_children:
            if child.type == "decorator":
                pending.append(child)
                continue
            if child.type != "method_definition":
                pending.clear()
                continue
            method_name = child.child_by_field_name("name")
            if method_name is not None:
                _store_definition(
                    result,
                    module,
                    child,
                    _text(module.source, method_name),
                    "method",
                    tuple(pending),
                    class_name,
                )
            pending.clear()
        return
    if node.type in {"interface_declaration", "type_alias_declaration"}:
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            _store_definition(
                result, module, node, _text(module.source, name_node), "type", decorators
            )
        return
    if node.type in {"lexical_declaration", "variable_declaration"}:
        for declarator in (
            child for child in node.named_children if child.type == "variable_declarator"
        ):
            name_node = declarator.child_by_field_name("name")
            value = declarator.child_by_field_name("value")
            if (
                name_node is not None
                and value is not None
                and value.type
                in {
                    "arrow_function",
                    "function_expression",
                    "generator_function",
                }
            ):
                _store_definition(
                    result,
                    module,
                    value,
                    _text(module.source, name_node),
                    "function",
                    decorators,
                )


def _store_definition(
    result: dict[str, _Definition],
    module: _Module,
    node: Node,
    name: str,
    kind: str,
    decorators: tuple[Node, ...],
    owner_class: str | None = None,
) -> None:
    qualname = f"{owner_class}.{name}" if owner_class else name
    ref = f"js://{module.path}#{qualname}"
    emitted_kind = "test" if kind == "function" and _is_test(module.path, name) else kind
    decorator_names = tuple(
        decorator_name
        for decorator in decorators
        if (decorator_name := _decorator_name(module.source, decorator)) is not None
    )
    base_name: str | None = None
    if kind == "class":
        heritage = next((item for item in _walk(node) if item.type == "extends_clause"), None)
        if heritage is not None:
            base_name = _expression_name(module.source, heritage.child_by_field_name("value"))
    result[ref] = _Definition(
        ref,
        emitted_kind,
        name,
        qualname,
        module.path,
        node.type,
        node.start_byte,
        node.end_byte,
        node.start_point.row + 1,
        node.end_point.row + 1,
        owner_class,
        decorator_names,
        base_name,
    )


def _decorator_name(source: bytes, decorator: Node) -> str | None:
    expression = next(iter(decorator.named_children), None)
    if expression is not None and expression.type == "call_expression":
        expression = expression.child_by_field_name("function")
    return _expression_name(source, expression)


def _emit_definition_edges(
    definition: _Definition,
    definition_node: Node,
    module: _Module,
    definitions: dict[tuple[str, str], _Definition],
    classes: dict[str, _Definition],
    methods: dict[tuple[str, str, str], _Definition],
    modules: dict[str, _Module],
    add_edge: object,
) -> None:
    emit = add_edge
    assert callable(emit)
    for name in definition.decorators:
        target = _resolve_name(name, module, definitions)
        emit(
            definition.ref,
            target[0] if target else f"jsname://{name.rsplit('.', 1)[-1]}",
            "decorated_by",
            definition.path,
            confidence=target[1] if target else 0.5,
            status=FactStatus.DECLARED if target else FactStatus.INFERRED,
        )
    if definition.kind == "class":
        if definition.base_name:
            target = _resolve_name(definition.base_name, module, definitions)
            emit(
                definition.ref,
                target[0] if target else f"jsname://{definition.base_name}",
                "inherits",
                definition.path,
                confidence=target[1] if target else 0.5,
                status=FactStatus.DECLARED if target else FactStatus.INFERRED,
            )
        return
    if definition.kind not in {"function", "method", "test"}:
        return
    variable_classes = _variable_classes(definition_node, module, definitions)
    call_functions: set[tuple[int, int]] = set()
    for node in _scope_walk(definition_node):
        if node.type != "call_expression":
            continue
        function = node.child_by_field_name("function")
        if function is None:
            continue
        call_functions.add((function.start_byte, function.end_byte))
        target = _resolve_call(
            function,
            definition,
            module,
            definitions,
            classes,
            methods,
            variable_classes,
            modules,
        )
        name = _expression_name(module.source, function) or "dynamic"
        emit(
            definition.ref,
            target[0] if target else f"jsname://{name.rsplit('.', 1)[-1]}",
            "calls" if target else "may_call",
            definition.path,
            confidence=target[1] if target else 0.35,
            status=FactStatus.DECLARED if target else FactStatus.INFERRED,
        )
    for node in _scope_walk(definition_node):
        if node.type not in {"identifier", "type_identifier"}:
            continue
        if (node.start_byte, node.end_byte) in call_functions:
            continue
        name = _text(module.source, node)
        target = _resolve_name(name, module, definitions)
        if target:
            emit(
                definition.ref,
                target[0],
                "references",
                definition.path,
                confidence=min(target[1], 0.9),
            )


def _variable_classes(
    definition_node: Node,
    module: _Module,
    definitions: dict[tuple[str, str], _Definition],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for node in _scope_walk(definition_node):
        if node.type != "variable_declarator":
            continue
        name_node = node.child_by_field_name("name")
        value = node.child_by_field_name("value")
        if name_node is None or value is None or value.type != "new_expression":
            continue
        constructor = value.child_by_field_name("constructor")
        class_name = _expression_name(module.source, constructor)
        target = _resolve_name(class_name or "", module, definitions)
        if target:
            result[_text(module.source, name_node)] = target[0]
    return result


def _resolve_call(
    node: Node,
    definition: _Definition,
    module: _Module,
    definitions: dict[tuple[str, str], _Definition],
    classes: dict[str, _Definition],
    methods: dict[tuple[str, str, str], _Definition],
    variable_classes: dict[str, str],
    modules: dict[str, _Module],
) -> tuple[str, float] | None:
    if node.type in {"identifier", "type_identifier"}:
        return _resolve_name(_text(module.source, node), module, definitions)
    if node.type != "member_expression":
        return None
    object_node = node.child_by_field_name("object")
    property_node = node.child_by_field_name("property")
    if object_node is None or property_node is None:
        return None
    object_name = _text(module.source, object_node)
    method_name = _text(module.source, property_node)
    class_ref: str | None = None
    if object_node.type == "this" and definition.owner_class:
        class_ref = f"js://{definition.path}#{definition.owner_class}"
    elif object_node.type == "identifier":
        class_ref = variable_classes.get(object_name)
        imported = module.imports.get(object_name)
        if class_ref is None and imported and imported.target_path and imported.target_name is None:
            target = definitions.get((imported.target_path, method_name))
            return (target.ref, 1.0) if target else None
    elif object_node.type == "new_expression":
        constructor = object_node.child_by_field_name("constructor")
        resolved = _resolve_name(
            _expression_name(module.source, constructor) or "", module, definitions
        )
        class_ref = resolved[0] if resolved else None
    if class_ref is None or class_ref not in classes:
        return None
    owner = classes[class_ref]
    direct = methods.get((owner.path, owner.name, method_name))
    if direct:
        return direct.ref, 0.95
    base_ref = _base_class_ref(owner, modules, definitions)
    if base_ref and base_ref in classes:
        base = classes[base_ref]
        inherited = methods.get((base.path, base.name, method_name))
        if inherited:
            return inherited.ref, 0.9
    return None


def _base_class_ref(
    definition: _Definition,
    modules: dict[str, _Module],
    definitions: dict[tuple[str, str], _Definition],
) -> str | None:
    if definition.base_name is None:
        return None
    module = modules.get(definition.path)
    if module is None:
        return None
    return_value = _resolve_name(definition.base_name, module, definitions)
    return return_value[0] if return_value else None


def _resolve_name(
    name: str,
    module: _Module,
    definitions: dict[tuple[str, str], _Definition],
) -> tuple[str, float] | None:
    direct = definitions.get((module.path, name))
    if direct:
        return direct.ref, 1.0
    imported = module.imports.get(name)
    if imported and imported.target_path and imported.target_name:
        target = definitions.get((imported.target_path, imported.target_name))
        if target:
            return target.ref, 1.0
    return None


def _expression_name(source: bytes, node: Node | None) -> str | None:
    if node is None:
        return None
    if node.type in {"identifier", "type_identifier", "property_identifier", "this"}:
        return _text(source, node)
    if node.type == "member_expression":
        owner = _expression_name(source, node.child_by_field_name("object"))
        prop = _expression_name(source, node.child_by_field_name("property"))
        return f"{owner}.{prop}" if owner and prop else prop
    return None


def _walk(node: Node) -> Iterator[Node]:
    pending = list(reversed(node.named_children))
    while pending:
        current = pending.pop()
        yield current
        pending.extend(reversed(current.named_children))


def _scope_walk(node: Node) -> Iterator[Node]:
    pending = list(reversed(node.named_children))
    nested = {
        "function_declaration",
        "function_expression",
        "arrow_function",
        "generator_function",
        "class_declaration",
    }
    while pending:
        current = pending.pop()
        if current is not node and current.type in nested:
            continue
        yield current
        pending.extend(reversed(current.named_children))


def _text(source: bytes, node: Node) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8")


def _string_value(source: bytes, node: Node) -> str:
    value = _text(source, node)
    return value[1:-1] if len(value) >= 2 and value[0] in "'\"`" else value


def _is_test(path: str, name: str) -> bool:
    filename = PurePosixPath(path).name.lower()
    return (".test." in filename or ".spec." in filename or "__tests__" in path.lower()) and (
        name.lower().startswith("test") or name.lower().startswith("it")
    )


def _stable_id(kind: str, value: str) -> str:
    return hashlib.sha256(f"{kind}\0{value}".encode()).hexdigest()


def _provenance(snapshot: SourceSnapshot) -> Provenance:
    return Provenance(
        "source_ast",
        "javascript_typescript_graph_analyzer",
        JAVASCRIPT_TYPESCRIPT_ANALYZER_VERSION,
        snapshot.source_revision,
    )
