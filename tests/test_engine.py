import pytest
from unittest.mock import patch, MagicMock

import radar.engine.engine as engine_module
from radar.engine.engine import find_similar_function
from radar.engine.index import SearchResult
from radar.engine.models import Function, QueryResult
from radar.engine.config import RETRIEVAL_FLOOR


def make_fn(name: str, score: float) -> SearchResult:
    fn = Function(
        name=name, file=f"src/billing/{name}.java",
        start_line=10, end_line=20,
        source_code=f"public void {name}() {{}}",
        signature=f"public void {name}()",
        summary=f"Does {name}",
        import_statement=f"import billing.{name};",
    )
    return SearchResult(function=fn, score=score)


@pytest.fixture(autouse=True)
def reset_index():
    engine_module._index = None
    yield
    engine_module._index = None


def _set_mock_index(results: list[SearchResult]) -> None:
    mock = MagicMock()
    mock.search.return_value = results
    engine_module._index = mock


def test_verdict_candidate_above_floor():
    _set_mock_index([make_fn("calculateTax", RETRIEVAL_FLOOR + 0.01)])
    with patch("radar.engine.engine.embed", return_value=[0.1] * 768):
        result = find_similar_function("public double applyTax(...) {}")
    assert result.verdict == "candidate"
    assert len(result.matches) == 1


def test_verdict_not_duplicate_below_floor():
    _set_mock_index([make_fn("calculateTax", RETRIEVAL_FLOOR - 0.01)])
    with patch("radar.engine.engine.embed", return_value=[0.1] * 768):
        result = find_similar_function("public void unrelated() {}")
    assert result.verdict == "not_duplicate"
    assert result.matches == []


def test_not_duplicate_when_index_empty():
    _set_mock_index([])
    with patch("radar.engine.engine.embed", return_value=[0.1] * 768):
        result = find_similar_function("public void foo() {}")
    assert result.verdict == "not_duplicate"
    assert result.matches == []


def test_returns_only_top_one():
    _set_mock_index([make_fn("calculateTax", 0.92), make_fn("applyDiscount", 0.80)])
    with patch("radar.engine.engine.embed", return_value=[0.1] * 768):
        result = find_similar_function("public double applyTax(...) {}")
    assert len(result.matches) == 1
    assert result.matches[0].name == "calculateTax"


def test_result_has_all_contract_fields():
    _set_mock_index([make_fn("calculateTax", 0.92)])
    with patch("radar.engine.engine.embed", return_value=[0.1] * 768):
        result = find_similar_function("public double applyTax(...) {}")
    assert isinstance(result, QueryResult)
    assert result.query_id
    m = result.matches[0]
    assert m.match_id
    assert m.name
    assert m.signature
    assert m.location
    assert ":" in m.location
    assert m.summary
    assert m.import_statement
    assert m.source_code  # the agent needs the source to judge duplication
    assert 0.0 <= m.similarity <= 1.0


def test_deterministic_scores():
    _set_mock_index([make_fn("calculateTax", 0.91)])
    code = "public double applyTax(double p, double r) { return p * r; }"
    with patch("radar.engine.engine.embed", return_value=[0.1] * 768):
        r1 = find_similar_function(code)
        r2 = find_similar_function(code)
    assert r1.verdict == r2.verdict
    assert r1.matches[0].similarity == r2.matches[0].similarity
    assert r1.query_id != r2.query_id  # UUID differs


def test_raises_without_index():
    with patch("radar.engine.engine.embed", return_value=[0.1] * 768):
        with pytest.raises(RuntimeError, match="Index not loaded"):
            find_similar_function("public void foo() {}")
