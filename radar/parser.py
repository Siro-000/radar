from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from radar.models import Function

PY_LANGUAGE = Language(tspython.language())
_parser = Parser(PY_LANGUAGE)

MIN_LINES = 3


def _extract_functions(source: str, filepath: str) -> list[Function]:
    tree = _parser.parse(source.encode())
    functions = []

    def walk(node):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            name = name_node.text.decode() if name_node else "<anonymous>"
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            if (end_line - start_line + 1) >= MIN_LINES:
                source_code = source.splitlines()
                func_lines = source_code[start_line - 1 : end_line]
                functions.append(
                    Function(
                        name=name,
                        file=filepath,
                        start_line=start_line,
                        end_line=end_line,
                        source_code="\n".join(func_lines),
                    )
                )
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return functions


def parse_repo(repo_path: str | Path) -> list[Function]:
    repo = Path(repo_path)
    functions = []
    for py_file in repo.rglob("*.py"):
        try:
            source = py_file.read_text(encoding="utf-8")
            rel_path = str(py_file.relative_to(repo))
            functions.extend(_extract_functions(source, rel_path))
        except Exception:
            continue
    return functions
