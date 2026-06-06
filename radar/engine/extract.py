"""Java function extractor using tree-sitter-java.

Public API:
    parse_file(path, repo_root) -> list[Function]
    parse_repo(repo_path)       -> list[Function]
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
_MIN_LINES = 4  # skip methods where (end_line - start_line + 1) < 4


def _collect_nodes(node, results: list) -> None:
    """Recursively collect method/constructor declaration nodes."""
    if node.type in _EXTRACT_TYPES:
        results.append(node)
    for child in node.children:
        _collect_nodes(child, results)


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

        nodes: list = []
        _collect_nodes(tree.root_node, nodes)

        rel_path = str(path.relative_to(repo_root))
        functions: list[Function] = []

        for node in nodes:
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

            functions.append(
                Function(
                    name=name,
                    file=rel_path,
                    start_line=start_line,
                    end_line=end_line,
                    source_code=source_code,
                    signature=signature,
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
