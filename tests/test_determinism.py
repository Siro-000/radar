"""
N2 — Determinism: same input twice → identical output (excluding query_id).

This is the product's core claim: the engine is a deterministic gate, not a
probabilistic classifier. Same code in, same verdict and same ranked matches out.
"""
import hashlib
import math
from pathlib import Path
from unittest.mock import patch

import pytest

import radar.server as server_module
from radar.parser import parse_repo
from radar.server import build_index, find_similar_function

SEED_REPO = Path(__file__).parent.parent / "data" / "seed_repo"
DIM = 1536

_QUERY = (
    "def apply_discount(price, pct):\n"
    "    if pct < 0 or pct > 100:\n"
    "        raise ValueError('bad')\n"
    "    return price - price * pct / 100"
)


def _make_vec(pattern: str) -> list[float]:
    seed = int.from_bytes(hashlib.sha256(pattern.encode()).digest(), "big")
    vec: list[float] = []
    for _ in range(DIM):
        seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
        vec.append(seed / 0xFFFFFFFF * 2 - 1)
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec]


@pytest.fixture(autouse=True)
def reset_index():
    server_module._index = None
    yield
    server_module._index = None


@pytest.fixture
def seed_index():
    functions = parse_repo(SEED_REPO)
    vectors = [_make_vec(fn.name) for fn in functions]
    with patch("radar.server.parse_repo", return_value=functions), \
         patch("radar.server.embed_batch", return_value=vectors):
        index = build_index(SEED_REPO)
    server_module._index = index
    return index


def _without_query_id(result: dict) -> dict:
    """Strip query_id before comparing — it is intentionally unique per call."""
    return {k: v for k, v in result.items() if k != "query_id"}


def test_verdict_is_identical_on_repeat(seed_index):
    vec = _make_vec("calculate_discount")
    with patch("radar.server.embed", return_value=vec):
        r1 = find_similar_function(code=_QUERY)
        r2 = find_similar_function(code=_QUERY)

    assert r1["verdict"] == r2["verdict"]


def test_matches_are_identical_on_repeat(seed_index):
    vec = _make_vec("calculate_discount")
    with patch("radar.server.embed", return_value=vec):
        r1 = find_similar_function(code=_QUERY)
        r2 = find_similar_function(code=_QUERY)

    assert r1["matches"] == r2["matches"]


def test_match_ids_are_stable_across_calls(seed_index):
    """match_id is a hash of the query+candidate pair — must be identical on repeat."""
    vec = _make_vec("calculate_discount")
    with patch("radar.server.embed", return_value=vec):
        r1 = find_similar_function(code=_QUERY)
        r2 = find_similar_function(code=_QUERY)

    ids1 = [m["match_id"] for m in r1["matches"]]
    ids2 = [m["match_id"] for m in r2["matches"]]
    assert ids1 == ids2


def test_query_id_differs_across_calls(seed_index):
    """query_id is the one field allowed to differ — it is a per-call telemetry event id."""
    vec = _make_vec("calculate_discount")
    with patch("radar.server.embed", return_value=vec):
        r1 = find_similar_function(code=_QUERY)
        r2 = find_similar_function(code=_QUERY)

    assert r1["query_id"] != r2["query_id"]


def test_full_result_minus_query_id_is_identical(seed_index):
    vec = _make_vec("calculate_discount")
    with patch("radar.server.embed", return_value=vec):
        r1 = find_similar_function(code=_QUERY)
        r2 = find_similar_function(code=_QUERY)

    assert _without_query_id(r1) == _without_query_id(r2)
