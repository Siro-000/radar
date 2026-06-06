from pathlib import Path

import pytest

from radar.parser import parse_repo
from radar.models import Function

FIXTURE = Path(__file__).parent / "fixtures" / "sample_repo"


def test_returns_list_of_functions():
    functions = parse_repo(FIXTURE)
    assert isinstance(functions, list)
    assert all(isinstance(f, Function) for f in functions)


def test_extracts_expected_function_names():
    functions = parse_repo(FIXTURE)
    names = {f.name for f in functions}
    assert "greet" in names
    assert "calculate_discount" in names
    assert "method_one" in names
    assert "method_two" in names


def test_ignores_functions_under_min_lines():
    functions = parse_repo(FIXTURE)
    names = {f.name for f in functions}
    # `add` is 2 lines, `short` is 1 line — both should be excluded
    assert "add" not in names
    assert "short" not in names


def test_function_has_correct_fields():
    functions = parse_repo(FIXTURE)
    greet = next(f for f in functions if f.name == "greet")
    assert greet.file == "utils.py"
    assert greet.start_line > 0
    assert greet.end_line >= greet.start_line
    assert "Hello" in greet.source_code


def test_function_is_serializable():
    functions = parse_repo(FIXTURE)
    for f in functions:
        data = f.model_dump()
        assert set(data.keys()) == {"name", "file", "start_line", "end_line", "source_code"}


def test_empty_repo(tmp_path):
    functions = parse_repo(tmp_path)
    assert functions == []


def test_repo_with_no_py_files(tmp_path):
    (tmp_path / "notes.txt").write_text("nothing here")
    functions = parse_repo(tmp_path)
    assert functions == []
