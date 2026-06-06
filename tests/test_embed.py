import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from radar.engine.models import Function
from radar.engine.embed import embed, embed_batch, _cache, _cache_key

FAKE_DIM = 768  # jina-embeddings-v2-base-code output dimension


def make_function(name: str, source: str) -> Function:
    return Function(
        name=name,
        file="test.py",
        start_line=1,
        end_line=5,
        source_code=source,
        signature=f"def {name}()",
    )


def fake_embedding(seed: int) -> list[float]:
    return [float(seed)] * FAKE_DIM


def mock_model(vectors: list[list[float]]) -> MagicMock:
    """Returns 1D array for str input, 2D for list input — mirrors SentenceTransformer."""
    model = MagicMock()

    def _encode(inputs, **kwargs):
        if isinstance(inputs, str):
            return np.array(vectors[0])  # 1D
        return np.array(vectors)  # 2D

    model.encode.side_effect = _encode
    return model


@pytest.fixture(autouse=True)
def clear_cache():
    _cache.clear()
    yield
    _cache.clear()


def test_embed_returns_list_of_floats():
    fn = make_function("foo", "def foo():\n    return 42\n")
    with patch("radar.engine.embed._get_model", return_value=mock_model([fake_embedding(1)])):
        result = embed(fn)
    assert isinstance(result, list)
    assert len(result) == FAKE_DIM
    assert all(isinstance(v, float) for v in result)


def test_embed_uses_cache():
    fn = make_function("foo", "def foo():\n    return 42\n")
    model = mock_model([fake_embedding(1)])
    with patch("radar.engine.embed._get_model", return_value=model):
        embed(fn)
        embed(fn)
        # Model encode should only be called once despite two embed() calls
        assert model.encode.call_count == 1


def test_embed_batch_returns_one_vector_per_function():
    fns = [
        make_function("foo", "def foo():\n    return 1\n"),
        make_function("bar", "def bar():\n    return 2\n"),
    ]
    with patch(
        "radar.engine.embed._get_model",
        return_value=mock_model([fake_embedding(1), fake_embedding(2)]),
    ):
        results = embed_batch(fns)
    assert len(results) == 2
    assert all(len(v) == FAKE_DIM for v in results)


def test_embed_batch_skips_cached():
    fn1 = make_function("foo", "def foo():\n    return 1\n")
    fn2 = make_function("bar", "def bar():\n    return 2\n")

    # Pre-populate fn1 in the cache via embed()
    with patch("radar.engine.embed._get_model", return_value=mock_model([fake_embedding(1)])):
        embed(fn1)

    # embed_batch should only call the model for fn2 (fn1 is cached)
    model2 = mock_model([fake_embedding(2)])
    with patch("radar.engine.embed._get_model", return_value=model2):
        results = embed_batch([fn1, fn2])
        assert model2.encode.call_count == 1
        last_inputs = model2.encode.call_args[0][0]
        assert len(last_inputs) == 1

    # Both results should have the correct dimension
    assert len(results) == 2
    assert all(len(v) == FAKE_DIM for v in results)
