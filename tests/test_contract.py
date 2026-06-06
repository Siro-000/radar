"""
Contract shape + MCP transport tests.

Verifies that find_similar_function returns the exact frozen contract shape
(field names, types, verdict enum values, threshold logic), then tests the
MCP stdio transport (N3) by starting the server in a subprocess and calling
it via the MCP client — no AI agent involved.
"""
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import radar.server as server_module
from radar.index import VectorIndex, SearchResult
from radar.models import Function
from radar.server import find_similar_function

CONTRACT_TOP_LEVEL = {"query_id", "verdict", "matches"}
CONTRACT_MATCH_KEYS = {
    "match_id", "name", "signature", "location", "summary", "import_statement", "similarity"
}
VALID_VERDICTS = {"duplicate", "similar", "novel"}

PROJECT_ROOT = Path(__file__).parent.parent


# ── Helpers ──────────────────────────────────────────────────────────────────

def _fn(name: str, source: str | None = None) -> Function:
    return Function(
        name=name,
        file="utils.py",
        start_line=1,
        end_line=5,
        source_code=source or f"def {name}():\n    pass\n    pass\n    pass",
    )


def _hit(name: str, score: float) -> SearchResult:
    return SearchResult(function=_fn(name), score=score)


@pytest.fixture(autouse=True)
def reset_index():
    server_module._index = None
    yield
    server_module._index = None


@pytest.fixture
def mock_index_with(request):
    """Parametrised fixture: mock_index_with(results) patches _index."""
    def factory(results: list[SearchResult]):
        idx = MagicMock(spec=VectorIndex)
        idx.search.return_value = results
        server_module._index = idx
        return idx
    return factory


# ── Contract shape ────────────────────────────────────────────────────────────

def test_result_has_top_level_keys(mock_index_with):
    mock_index_with([_hit("foo", 0.88)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        result = find_similar_function(code="def foo(): pass")
    assert set(result.keys()) == CONTRACT_TOP_LEVEL


def test_verdict_is_a_valid_enum_value(mock_index_with):
    mock_index_with([_hit("foo", 0.88)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        result = find_similar_function(code="def foo(): pass")
    assert result["verdict"] in VALID_VERDICTS


def test_match_has_all_contract_keys(mock_index_with):
    mock_index_with([_hit("foo", 0.88)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        result = find_similar_function(code="def foo(): pass")
    assert result["matches"], "Expected at least one match"
    assert set(result["matches"][0].keys()) == CONTRACT_MATCH_KEYS


def test_similarity_is_float_between_0_and_1(mock_index_with):
    mock_index_with([_hit("foo", 0.88)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        result = find_similar_function(code="def foo(): pass")
    for m in result["matches"]:
        assert 0.0 <= m["similarity"] <= 1.0


def test_import_statement_is_importable_syntax(mock_index_with):
    """import_statement must be 'from <module> import <name>' syntax."""
    mock_index_with([_hit("foo", 0.88)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        result = find_similar_function(code="def foo(): pass")
    stmt = result["matches"][0]["import_statement"]
    assert stmt.startswith("from ") and " import " in stmt


def test_location_is_file_and_line_range(mock_index_with):
    """location must be 'file:start-end'."""
    mock_index_with([_hit("foo", 0.88)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        result = find_similar_function(code="def foo(): pass")
    loc = result["matches"][0]["location"]
    assert ":" in loc and "-" in loc


def test_query_id_differs_between_calls(mock_index_with):
    """query_id is a per-call telemetry event id and must never repeat."""
    mock_index_with([_hit("foo", 0.88)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        r1 = find_similar_function(code="def foo(): pass")
        r2 = find_similar_function(code="def foo(): pass")
    assert r1["query_id"] != r2["query_id"]


def test_match_id_is_stable_for_same_query_and_candidate(mock_index_with):
    """match_id is a hash of (query, candidate) — must be identical across calls."""
    mock_index_with([_hit("foo", 0.88)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        r1 = find_similar_function(code="def foo(): pass")
    mock_index_with([_hit("foo", 0.88)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        r2 = find_similar_function(code="def foo(): pass")
    assert r1["matches"][0]["match_id"] == r2["matches"][0]["match_id"]


# ── Threshold / verdict logic ─────────────────────────────────────────────────

def test_high_score_yields_duplicate(mock_index_with):
    """Scores >= DUPLICATE_THRESHOLD (0.85) → 'duplicate'."""
    mock_index_with([_hit("foo", 0.90)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        result = find_similar_function(code="def foo(): pass")
    assert result["verdict"] == "duplicate"


def test_mid_score_yields_similar(mock_index_with):
    """Scores in [SIMILAR_THRESHOLD, DUPLICATE_THRESHOLD) → 'similar'."""
    mock_index_with([_hit("foo", 0.75)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        result = find_similar_function(code="def foo(): pass")
    assert result["verdict"] == "similar"


def test_low_score_yields_novel_with_empty_matches(mock_index_with):
    """Scores below SIMILAR_THRESHOLD (0.70) → 'novel' with empty matches."""
    mock_index_with([_hit("foo", 0.50)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        result = find_similar_function(code="def foo(): pass")
    assert result["verdict"] == "novel"
    assert result["matches"] == []


def test_only_above_threshold_matches_returned(mock_index_with):
    """Matches below SIMILAR_THRESHOLD must be filtered out."""
    mock_index_with([_hit("high", 0.92), _hit("low", 0.55)])
    with patch("radar.server.embed", return_value=[0.1] * 8):
        result = find_similar_function(code="def foo(): pass")
    names = [m["name"] for m in result["matches"]]
    assert "high" in names
    assert "low" not in names


def test_no_index_raises_runtime_error():
    with patch("radar.server.embed", return_value=[0.1] * 8):
        with pytest.raises(RuntimeError, match="Index not loaded"):
            find_similar_function(code="def foo(): pass")


# ── MCP transport (N3) ────────────────────────────────────────────────────────


def _run_mcp_list_tools() -> list:
    """Start the server in a subprocess and return the listed MCP tools."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def _async():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-c", "from radar.server import mcp; mcp.run(transport='stdio')"],
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return result.tools

    return asyncio.run(_async())


def test_mcp_tool_is_listed_over_stdio():
    """N3: Server exposes find_similar_function in tools/list via stdio MCP protocol."""
    pytest.importorskip("mcp.client.stdio", reason="MCP client SDK not available")
    tools = _run_mcp_list_tools()
    names = [t.name for t in tools]
    assert "find_similar_function" in names


def test_mcp_tool_schema_requires_code():
    """N3: The MCP tool schema declares 'code' as a required parameter."""
    pytest.importorskip("mcp.client.stdio", reason="MCP client SDK not available")
    tools = _run_mcp_list_tools()
    tool = next((t for t in tools if t.name == "find_similar_function"), None)
    assert tool is not None, "find_similar_function not in tool list"
    schema = tool.inputSchema
    assert "code" in schema.get("properties", {}), "missing 'code' in schema properties"
    assert "code" in (schema.get("required") or []), "code must be required"


def test_mcp_tool_schema_has_optional_params():
    """N3: The MCP tool schema lists language, intent, top_k as optional parameters."""
    pytest.importorskip("mcp.client.stdio", reason="MCP client SDK not available")
    tools = _run_mcp_list_tools()
    tool = next(t for t in tools if t.name == "find_similar_function")
    props = tool.inputSchema.get("properties", {})
    for param in ("language", "intent", "top_k"):
        assert param in props, f"missing optional param '{param}' in schema"
