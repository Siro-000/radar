from unittest.mock import MagicMock, patch

import pytest

from radar.models import Function
from radar.embeddings import embed, embed_batch, _cache, _cache_key

FAKE_DIM = 1536


def make_function(name: str, source: str) -> Function:
    return Function(name=name, file="test.py", start_line=1, end_line=5, source_code=source)


def fake_embedding(seed: int) -> list[float]:
    return [float(seed)] * FAKE_DIM


def mock_response(vectors: list[list[float]]):
    response = MagicMock()
    response.data = [MagicMock(embedding=v) for v in vectors]
    return response


@pytest.fixture(autouse=True)
def clear_cache():
    _cache.clear()
    yield
    _cache.clear()


def test_embed_returns_vector():
    fn = make_function("foo", "def foo():\n    return 42\n    pass")
    with patch("radar.embeddings._client") as mock_client:
        mock_client.embeddings.create.return_value = mock_response([fake_embedding(1)])
        result = embed(fn)
    assert isinstance(result, list)
    assert len(result) == FAKE_DIM


def test_embed_uses_cache():
    fn = make_function("foo", "def foo():\n    return 42\n    pass")
    with patch("radar.embeddings._client") as mock_client:
        mock_client.embeddings.create.return_value = mock_response([fake_embedding(1)])
        embed(fn)
        embed(fn)
        assert mock_client.embeddings.create.call_count == 1


def test_embed_batch_returns_one_vector_per_function():
    fns = [
        make_function("foo", "def foo():\n    return 1\n    pass"),
        make_function("bar", "def bar():\n    return 2\n    pass"),
    ]
    with patch("radar.embeddings._client") as mock_client:
        mock_client.embeddings.create.return_value = mock_response(
            [fake_embedding(1), fake_embedding(2)]
        )
        results = embed_batch(fns)
    assert len(results) == 2
    assert all(len(v) == FAKE_DIM for v in results)


def test_embed_batch_skips_cached():
    fn1 = make_function("foo", "def foo():\n    return 1\n    pass")
    fn2 = make_function("bar", "def bar():\n    return 2\n    pass")

    with patch("radar.embeddings._client") as mock_client:
        mock_client.embeddings.create.return_value = mock_response([fake_embedding(1)])
        embed(fn1)

        mock_client.embeddings.create.return_value = mock_response([fake_embedding(2)])
        results = embed_batch([fn1, fn2])

        # fn1 was cached, only fn2 should be fetched
        assert mock_client.embeddings.create.call_count == 2
        last_call_inputs = mock_client.embeddings.create.call_args[1]["input"]
        assert len(last_call_inputs) == 1
