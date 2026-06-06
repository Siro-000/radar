"""
N0 — Smoke: index the seed repo, call find_similar_function with a known
duplicate, assert it comes back as a match.

Direct Python call — no MCP, no agent.
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


def _make_vec(pattern: str) -> list[float]:
    """Deterministic unit vector from a string — distinct patterns → near-zero cosine."""
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
    """Build a real Chroma index from seed_repo with deterministic mock embeddings."""
    functions = parse_repo(SEED_REPO)
    vectors = [_make_vec(fn.name) for fn in functions]
    with patch("radar.server.parse_repo", return_value=functions), \
         patch("radar.server.embed_batch", return_value=vectors):
        index = build_index(SEED_REPO)
    server_module._index = index
    return index


def test_known_duplicate_appears_in_matches(seed_index):
    """A near-identical 'calculate_discount' variant must appear in matches."""
    query = (
        "def apply_discount(price, pct):\n"
        "    if pct < 0 or pct > 100:\n"
        "        raise ValueError('bad')\n"
        "    return price - price * pct / 100"
    )
    with patch("radar.server.embed", return_value=_make_vec("calculate_discount")):
        result = find_similar_function(code=query)

    names = [m["name"] for m in result["matches"]]
    assert "calculate_discount" in names, f"Expected calculate_discount in matches, got: {names}"


def test_novel_query_yields_novel_verdict(seed_index):
    """A completely unrelated snippet must produce a 'novel' verdict with no matches."""
    unrelated = _make_vec("zzz_totally_unrelated_xyz_9182736455")
    with patch("radar.server.embed", return_value=unrelated):
        result = find_similar_function(code="def foo(): pass")

    assert result["verdict"] == "novel", f"Expected 'novel', got: {result['verdict']}"
    assert result["matches"] == []


def test_smoke_result_has_top_level_contract_keys(seed_index):
    """Smoke check: result must contain the three top-level contract keys."""
    with patch("radar.server.embed", return_value=_make_vec("calculate_discount")):
        result = find_similar_function(code="def apply_discount(p, pct): ...")

    assert set(result.keys()) == {"query_id", "verdict", "matches"}
