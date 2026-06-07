"""
RAN ONCE PER REPOSITORY

Java function extractor using tree-sitter-java.

Public API:
    parse_file(path, repo_root) -> list[Function]
    parse_repo(repo_path)       -> list[Function]

Besides the raw function record, this precomputes the two *actionable* fields the
agent needs at query time (no LLM in the hot path):
    - import_statement: how to reuse the function (Java import / static import)
    - summary: a one-line, deterministic description
"""

from __future__ import annotations

import sys
from pathlib import Path

import tree_sitter_java
from tree_sitter import Language, Parser

from radar.engine.models import Function

JAVA_LANGUAGE = Language(tree_sitter_java.language())
_parser = Parser(JAVA_LANGUAGE)

_EXTRACT_TYPES = {"method_declaration", "constructor_declaration"}
_CLASS_TYPES = {"class_declaration", "interface_declaration", "enum_declaration", "record_declaration"}
_MIN_LINES = 4  # skip methods where (end_line - start_line + 1) < 4


def _package_name(root) -> str:
    """Return the package name (e.g. 'com.acme.util') or '' if none."""
    for child in root.children:
        if child.type == "package_declaration":
            text = child.text.decode()
            return text.replace("package", "", 1).replace(";", "").strip()
    return ""


def _is_static(node) -> bool:
    for child in node.children:
        if child.type == "modifiers" and "static" in child.text.decode():
            return True
    return False


def _build_import(package: str, class_name: str, method_name: str, is_static: bool, is_ctor: bool) -> str:
    """How to reuse this function from another file."""
    fqcn = f"{package}.{class_name}" if package else class_name
    if is_ctor:
        return f"import {fqcn};"
    if is_static:
        # static import lets the caller invoke `method_name(...)` directly
        return f"import static {fqcn}.{method_name};" if package else f"// reuse {class_name}.{method_name}"
    return f"import {fqcn};"


def _build_summary(class_name: str, signature: str) -> str:
    sig = signature.rstrip().rstrip("{").strip()
    return f"{class_name}: {sig}" if class_name else sig


def _collect(node, class_name: str, found: list) -> None:
    """Walk the tree, tracking the nearest enclosing class for each declaration."""
    current_class = class_name
    if node.type in _CLASS_TYPES:
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            current_class = name_node.text.decode()

    if node.type in _EXTRACT_TYPES:
        found.append((node, current_class))

    for child in node.children:
        _collect(child, current_class, found)


def parse_file(path: Path, repo_root: Path) -> list[Function]:
    """Parse a single Java file and return a list of Function records.

    On any error (syntax error, I/O, etc.) prints to stderr and returns [].
    """
    try:
        source_bytes = path.read_bytes()
        tree = _parser.parse(source_bytes)

        if tree.root_node.has_error:
            print(f"[extract] syntax error in {path}, skipping", file=sys.stderr)
            return []

        package = _package_name(tree.root_node)

        collected: list = []
        _collect(tree.root_node, "", collected)

        rel_path = str(path.relative_to(repo_root))
        functions: list[Function] = []

        for node, class_name in collected:
            name_node = node.child_by_field_name("name")
            if name_node is None:
                continue

            name = name_node.text.decode()
            # start_point / end_point are 0-based rows; convert to 1-based lines
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            if (end_line - start_line + 1) < _MIN_LINES:
                continue

            source_code = source_bytes[node.start_byte : node.end_byte].decode()
            signature = source_code.splitlines()[0].strip()

            is_ctor = node.type == "constructor_declaration"
            is_static = _is_static(node)

            functions.append(
                Function(
                    name=name,
                    file=rel_path,
                    start_line=start_line,
                    end_line=end_line,
                    source_code=source_code,
                    signature=signature,
                    summary=_build_summary(class_name, signature),
                    import_statement=_build_import(package, class_name, name, is_static, is_ctor),
                )
            )

        return functions

    except Exception as exc:  # noqa: BLE001
        print(f"[extract] error parsing {path}: {exc}", file=sys.stderr)
        return []


def parse_repo(repo_path: Path | str) -> list[Function]:
    """Walk all *.java files under repo_path and return all Function records."""
    repo_path = Path(repo_path)
    functions: list[Function] = []

    for java_file in sorted(repo_path.glob("**/*.java")):
        functions.extend(parse_file(java_file, repo_path))

    return functions
