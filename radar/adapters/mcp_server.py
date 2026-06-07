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


def _log(msg: str) -> None:
    print(f"[radar] {msg}", file=sys.stderr, flush=True)


@mcp.tool(
    name="find_similar_function",
    description=(
        "Check whether a function with this logic ALREADY EXISTS in the indexed "
        "repository before you write it. Detects semantic duplication (same logic, "
        "different syntax), not textual copy/paste. Call this BEFORE writing any new "
        "function. If the verdict is 'duplicate', reuse the existing function via the "
        "returned `import_statement` instead of rewriting it. If 'similar', review the "
        "matches before deciding. If 'novel', no equivalent exists — write it. "
        "Pass the full source of the function you intend to write as `code`."
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
    result = _engine_find(code=code, language=language, intent=intent, top_k=top_k)
    return result.model_dump()


def _warmup() -> None:
    """Force the embedding model to load now, while stdout is still redirected,
    so the first real query is fast and no model-load output corrupts stdout."""
    try:
        _engine_find(code="int warmup() { return 0; }")
        _log("model warmed up")
    except Exception as exc:  # noqa: BLE001
        _log(f"warmup skipped: {exc}")


def run_server(repo: str, index_path: str) -> None:
    """Ensure an index exists at ``index_path`` (building from ``repo`` if absent),
    load it, warm up the model, then serve ``find_similar_function`` over stdio."""
    idx = Path(index_path)

    # Setup phase: anything below may print to stdout (model loaders, faiss, etc.).
    # Redirect it to stderr so the stdio MCP transport stays clean.
    with contextlib.redirect_stdout(sys.stderr):
        if (idx / "index.faiss").exists():
            _log(f"loading existing index at {idx}")
        else:
            _log(f"no index at {idx}; building from repo '{repo}' ...")
            build_index(repo, idx)
        load_index(idx)
        _warmup()

    _log("ready — serving find_similar_function over MCP stdio")
    mcp.run()  # FastMCP defaults to the stdio transport


if __name__ == "__main__":
    # Allow `python -m radar.adapters.mcp_server [repo] [index_path]` as a fallback
    # to the `radar serve` CLI entry point.
    _repo = sys.argv[1] if len(sys.argv) > 1 else "."
    _index = sys.argv[2] if len(sys.argv) > 2 else ".radar-index"
    run_server(_repo, _index)
