"""
Integration tests for find_similar_function against the frozen contract.

Builds a real Chroma index from the sample_repo fixture using deterministic
mock embeddings, then verifies:
  - a known duplicate appears in matches
  - latency stays under 150 ms on a loaded index
  - the 0.70 threshold is always respected (no below-threshold matches)
  - the frozen contract field names are present on every match
  - a missing index produces a clear error
"""
import hashlib
import math
import time
from pathlib import Path
from unittest.mock import patch

import pytest

import radar.server as server_module
from radar.parser import parse_repo
from radar.server import build_index, find_similar_function

FIXTURES = Path(__file__).parent / "fixtures" / "sample_repo"
DIM = 1536


def _make_vec(pattern: str) -> list[float]:
    """Deterministic unit vector — two distinct patterns have near-zero cosine similarity."""
    seed = int.from_bytes(hashlib.sha256(pattern.encode()).digest(), "big")
    vec: list[float] = []
    for _ in range(DIM):
        seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
        vec.append(seed / 0xFFFFFFFF * 2 - 1)
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec]


_DISCOUNT_VEC = _make_vec("calculate_discount")
_QUERY_VEC = _make_vec("calculate_discount")    # identical → cosine similarity = 1.0
_UNRELATED_VEC = _make_vec("send_email_smtp_totally_unrelated_xyz_9182736")


@pytest.fixture(autouse=True)
def reset_index():
    server_module._index = None
    yield
    server_module._index = None


@pytest.fixture
def loaded_index():
    """Build a real Chroma index from sample_repo with mock embeddings.

    calculate_discount gets _DISCOUNT_VEC; every other function gets a unique
    direction so it won't accidentally surface in discount-related queries.
    """
    functions = parse_repo(FIXTURES)
    embeddings = [
        _DISCOUNT_VEC if fn.name == "calculate_discount" else _make_vec(fn.name)
        for fn in functions
    ]
    with patch("radar.server.parse_repo", return_value=functions), \
         patch("radar.server.embed_batch", return_value=embeddings):
        index = build_index(FIXTURES)

    server_module._index = index
    yield index


def test_known_query_returns_correct_function_in_top3(loaded_index):
    with patch("radar.server.embed", return_value=_QUERY_VEC):
        result = find_similar_function(
            code="def apply_discount(price, percent):\n    return price * (1 - percent / 100)"
        )

    names = [m["name"] for m in result["matches"]]
    assert "calculate_discount" in names, f"Expected calculate_discount in matches, got: {names}"
    assert names.index("calculate_discount") < 3, "calculate_discount should be in top-3"


def test_latency_under_150ms(loaded_index):
    with patch("radar.server.embed", return_value=_QUERY_VEC):
        t0 = time.perf_counter()
        find_similar_function(code="def compute_discount(price, rate): ...")
        elapsed_ms = (time.perf_counter() - t0) * 1000

    assert elapsed_ms < 150, f"Query took {elapsed_ms:.1f} ms, expected < 150 ms"


def test_threshold_always_respected(loaded_index):
    """Every returned match must have similarity >= 0.70 — threshold is server-side."""
    with patch("radar.server.embed", return_value=_UNRELATED_VEC):
        result = find_similar_function(code="def send_email(to, subject, body): ...")

    for m in result["matches"]:
        assert m["similarity"] >= 0.70, (
            f"{m['name']} slipped through with similarity {m['similarity']}"
        )


def test_result_fields_match_frozen_contract(loaded_index):
    with patch("radar.server.embed", return_value=_QUERY_VEC):
        result = find_similar_function(code="def apply_discount(price, pct): ...")

    assert result["matches"], "Expected at least one match for a near-identical query"
    assert set(result.keys()) == {"query_id", "verdict", "matches"}
    assert set(result["matches"][0].keys()) == {
        "match_id", "name", "signature", "location", "summary", "import_statement", "similarity"
    }


def test_index_not_loaded_raises_clear_error():
    assert server_module._index is None
    with patch("radar.server.embed", return_value=_QUERY_VEC):
        with pytest.raises(RuntimeError, match="Index not loaded"):
            find_similar_function(code="def foo(): pass")
