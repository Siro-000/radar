"""
MCP stdio server exposing ``find_similar_function`` to coding agents
(Claude Code, Cursor, ...).

Thin adapter over ``radar.engine.engine.find_similar_function`` — it contains
no detection or threshold logic.

STDIO HYGIENE (the #1 "connects but doesn't respond" bug): only the MCP protocol
may be written to **stdout**. Every log, progress bar, and model-load message must
go to **stderr**. We therefore redirect stdout -> stderr for the whole setup phase
(index build/load + model warmup) and only hand stdout back to the protocol once we
call ``mcp.run()``.
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from radar.engine import config
from radar.engine.build import build_index
from radar.engine.engine import find_similar_function as _engine_find
from radar.engine.engine import load_index

mcp = FastMCP("radar")

_index_path: Path | None = None  # set once in run_server, shared with index_repo


def _log(msg: str) -> None:
    print(f"[radar] {msg}", file=sys.stderr, flush=True)


@mcp.tool(
    name="find_similar_function",
    description=(
        "Before writing a new function, retrieve the most similar existing function "
        "in the indexed repository (semantic search over code, not text matching). "
        "Call this BEFORE writing any new function, passing the full source you intend "
        "to write as `code`. Radar does NOT decide duplication — YOU do. "
        "If verdict is 'not_duplicate', nothing similar exists; write your function. "
        "If verdict is 'candidate', read the returned match's `source_code`: if it "
        "implements the same logic as what you were about to write, reuse it via the "
        "match's `import_statement` instead of rewriting; otherwise write your own."
    ),
)
def find_similar_function(
    code: str,
    language: str = "java",
    intent: str = "",
    top_k: int = config.DEFAULT_TOP_K,
) -> dict:
    """Return the frozen QueryResult contract as a plain dict.

    Args:
        code: Full source of the function the agent is about to write.
        language: Source language (default "java").
        intent: Optional natural-language description of what it should do.
        top_k: Max number of candidate matches to return (default 3).
    """
    try:
        result = _engine_find(code=code, language=language, intent=intent, top_k=top_k)
        return result.model_dump()
    except RuntimeError:
        return {"error": "No index loaded. Call index_repo(repo_path=<absolute path>) first."}


@mcp.tool(
    name="index_repo",
    description=(
        "Index a repository so find_similar_function can search it. "
        "Call this once (or whenever the repo changes) before querying. "
        "Pass the absolute path to the repo root as `repo_path`. "
        "The index is written to the path configured at server startup and "
        "reloaded in memory immediately — no restart needed."
    ),
)
def index_repo(repo_path: str) -> dict:
    """Build (or rebuild) the FAISS index from ``repo_path`` and reload it.

    Args:
        repo_path: Absolute path to the repository root to index.
    """
    if _index_path is None:
        raise RuntimeError("Server not fully initialised (index_path unknown).")
    with contextlib.redirect_stdout(sys.stderr):
        build_index(repo_path, _index_path)
        load_index(_index_path)
    _log(f"index rebuilt from {repo_path!r} and reloaded")
    return {"status": "ok", "indexed_repo": repo_path, "index_path": str(_index_path)}


def _warmup() -> None:
    """Force the embedding model to load now, while stdout is still redirected,
    so the first real query is fast and no model-load output corrupts stdout."""
    try:
        _engine_find(code="int warmup() { return 0; }")
        _log("model warmed up")
    except Exception as exc:  # noqa: BLE001
        _log(f"warmup skipped: {exc}")


def run_server(repo: str | None, index_path: str) -> None:
    """Start the MCP server.

    If an index already exists at ``index_path``, load it.
    If not and ``repo`` is given, build the index from ``repo`` first.
    If not and no ``repo`` is given, start empty — the agent must call
    ``index_repo`` before querying.
    """
    global _index_path
    idx = Path(index_path)
    _index_path = idx

    with contextlib.redirect_stdout(sys.stderr):
        if (idx / "index.faiss").exists():
            _log(f"loading existing index at {idx}")
            load_index(idx)
            _warmup()
        elif repo:
            _log(f"no index at {idx}; building from repo '{repo}' ...")
            build_index(repo, idx)
            load_index(idx)
            _warmup()
        else:
            _log(f"no index at {idx} — call index_repo() to build one")

    _log("ready — serving find_similar_function over MCP stdio")
    mcp.run()  # FastMCP defaults to the stdio transport


if __name__ == "__main__":
    # Allow `python -m radar.adapters.mcp_server [repo] [index_path]` as a fallback
    # to the `radar serve` CLI entry point.
    _repo = sys.argv[1] if len(sys.argv) > 1 else "."
    _index = sys.argv[2] if len(sys.argv) > 2 else ".radar-index"
    run_server(_repo, _index)
