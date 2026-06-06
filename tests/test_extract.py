"""Tests for radar.engine.extract — Java function extractor."""

from pathlib import Path

import pytest

from radar.engine.extract import parse_file, parse_repo
from radar.engine.models import Function

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_JAVA = FIXTURES_DIR / "SampleService.java"


# ---------------------------------------------------------------------------
# test 1 — parse_file extracts the expected methods
# ---------------------------------------------------------------------------

def test_parse_file_extracts_methods():
    functions = parse_file(SAMPLE_JAVA, FIXTURES_DIR)
    names = {f.name for f in functions}
    assert "calculateTax" in names
    assert "greet" in names
    assert "add" in names


# ---------------------------------------------------------------------------
# test 2 — methods shorter than 4 lines are skipped
# ---------------------------------------------------------------------------

def test_parse_file_skips_short_methods():
    functions = parse_file(SAMPLE_JAVA, FIXTURES_DIR)
    names = {f.name for f in functions}
    # noop has only 2 lines (body is empty) — must be excluded
    assert "noop" not in names


# ---------------------------------------------------------------------------
# test 3 — constructors are extracted
# ---------------------------------------------------------------------------

def test_parse_file_extracts_constructor():
    functions = parse_file(SAMPLE_JAVA, FIXTURES_DIR)
    names = {f.name for f in functions}
    assert "SampleService" in names


# ---------------------------------------------------------------------------
# test 4 — Function fields are populated correctly
# ---------------------------------------------------------------------------

def test_function_has_correct_fields():
    functions = parse_file(SAMPLE_JAVA, FIXTURES_DIR)
    calc = next(f for f in functions if f.name == "calculateTax")

    # name
    assert calc.name == "calculateTax"

    # file is relative to repo_root (FIXTURES_DIR in this call)
    assert calc.file == "SampleService.java"

    # line numbers are 1-based and sensible
    assert calc.start_line >= 1
    assert calc.end_line >= calc.start_line

    # signature is the first line of the source, stripped
    assert calc.signature == "public double calculateTax(double price, double rate) {"

    # source_code contains the full body
    assert "calculateTax" in calc.source_code
    assert "return result;" in calc.source_code


# ---------------------------------------------------------------------------
# test 5 — parse_repo walks a directory and finds .java files
# ---------------------------------------------------------------------------

def test_parse_repo_walks_directory(tmp_path):
    java_src = """\
public class Temp {
    public int multiply(int a, int b) {
        int product = a * b;
        return product;
    }
}
"""
    (tmp_path / "Temp.java").write_text(java_src)
    functions = parse_repo(tmp_path)
    assert len(functions) >= 1
    names = {f.name for f in functions}
    assert "multiply" in names


# ---------------------------------------------------------------------------
# test 6 — parse_repo on an empty directory returns []
# ---------------------------------------------------------------------------

def test_parse_repo_empty_returns_empty(tmp_path):
    functions = parse_repo(tmp_path)
    assert functions == []
