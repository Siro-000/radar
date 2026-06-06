import re
import sys

import tree_sitter_java
from tree_sitter import Language, Parser

_JAVA_LANGUAGE = Language(tree_sitter_java.language())
_parser = Parser(_JAVA_LANGUAGE)


def normalize(source: str) -> str:
    try:
        source = _strip_comments(source)
        source = _rename_locals(source)
        return _normalize_whitespace(source)
    except Exception:
        return source


def _strip_comments(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r"//[^\n]*", "", source)
    return source


def _rename_locals(source: str) -> str:
    tree = _parser.parse(source.encode())
    local_names = _collect_locals(tree.root_node)
    for i, name in enumerate(local_names):
        source = re.sub(r"\b" + re.escape(name) + r"\b", f"var{i}", source)
    return source


def _collect_locals(node) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    _walk_locals(node, names, seen)
    return names


def _walk_locals(node, names: list[str], seen: set[str]) -> None:
    if node.type == "local_variable_declaration":
        for child in node.children:
            if child.type == "variable_declarator":
                name_node = child.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode()
                    if name not in seen:
                        seen.add(name)
                        names.append(name)
    for child in node.children:
        _walk_locals(child, names, seen)


def _normalize_whitespace(source: str) -> str:
    lines = [line.rstrip() for line in source.splitlines()]
    result: list[str] = []
    prev_blank = False
    for line in lines:
        is_blank = not line.strip()
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank
    return "\n".join(result).strip()
