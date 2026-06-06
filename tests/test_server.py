from unittest.mock import patch, MagicMock
import pytest

import radar.server as server_module
from radar.index import VectorIndex, SearchResult
from radar.models import Function


def make_function(name: str, source: str = None) -> Function:
    return Function(
        name=name,
        file="utils.py",
        start_line=1,
        end_line=5,
        source_code=source or f"def {name}():\n    pass\n    pass\n    pass",
    )


def make_search_result(name: str, score: float) -> SearchResult:
    return SearchResult(function=make_function(name), score=score)


@pytest.fixture(autouse=True)
def reset_index():
    server_module._index = None
    yield
    server_module._index = None


def test_find_similar_function_returns_above_threshold():
    mock_index = MagicMock(spec=VectorIndex)
    mock_index.search.return_value = [
        make_search_result("calculate_tax", 0.92),
        make_search_result("apply_discount", 0.65),  # below threshold — must be filtered
    ]
    server_module._index = mock_index

    with patch("radar.server.embed", return_value=[0.1] * 10):
        result = server_module.find_similar_function(code="compute tax on price")

    assert len(result["matches"]) == 1
    assert result["matches"][0]["name"] == "calculate_tax"
    assert result["matches"][0]["similarity"] == 0.92


def test_find_similar_function_novel_when_no_match():
    mock_index = MagicMock(spec=VectorIndex)
    mock_index.search.return_value = [
        make_search_result("unrelated", 0.30),
    ]
    server_module._index = mock_index

    with patch("radar.server.embed", return_value=[0.1] * 10):
        result = server_module.find_similar_function(code="something completely different")

    assert result["matches"] == []
    assert result["verdict"] == "novel"


def test_find_similar_function_result_fields():
    mock_index = MagicMock(spec=VectorIndex)
    mock_index.search.return_value = [make_search_result("foo", 0.88)]
    server_module._index = mock_index

    with patch("radar.server.embed", return_value=[0.1] * 10):
        result = server_module.find_similar_function(code="foo logic")

    assert set(result.keys()) == {"query_id", "verdict", "matches"}
    assert set(result["matches"][0].keys()) == {
        "match_id", "name", "signature", "location", "summary", "import_statement", "similarity"
    }


def test_find_similar_function_raises_without_index():
    with patch("radar.server.embed", return_value=[0.1] * 10):
        with pytest.raises(RuntimeError, match="Index not loaded"):
            server_module.find_similar_function(code="anything")


def test_build_index_calls_parse_embed_and_add(tmp_path):
    fns = [make_function("foo"), make_function("bar")]
    fake_embeddings = [[0.1] * 8, [0.2] * 8]

    with patch("radar.server.parse_repo", return_value=fns) as mock_parse, \
         patch("radar.server.embed_batch", return_value=fake_embeddings) as mock_embed, \
         patch("radar.server.VectorIndex") as mock_index_cls:

        mock_index = MagicMock()
        mock_index_cls.return_value = mock_index
        server_module.build_index(tmp_path)

    mock_parse.assert_called_once_with(tmp_path)
    mock_embed.assert_called_once_with(fns)
    mock_index.add_batch.assert_called_once_with(fns, fake_embeddings)
