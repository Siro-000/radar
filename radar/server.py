from pathlib import Path

from mcp.server.fastmcp import FastMCP

from radar.embeddings import embed, embed_batch
from radar.index import VectorIndex, SearchResult
from radar.models import Function
from radar.parser import parse_repo

mcp = FastMCP(
    "radar",
    instructions=(
        "Radar finds semantically similar functions in your codebase. "
        "Call find_similar_function before implementing any new function "
        "to check if the logic already exists."
    ),
)

_index: VectorIndex | None = None


def _get_index() -> VectorIndex:
    if _index is None:
        raise RuntimeError("Index not loaded. Start the server with `radar serve --repo <path>`.")
    return _index


def build_index(repo_path: str | Path, persist_path: str | Path | None = None) -> VectorIndex:
    functions = parse_repo(repo_path)
    embeddings = embed_batch(functions)
    index = VectorIndex(persist_path=persist_path)
    index.add_batch(functions, embeddings)
    return index


def load_server(repo_path: str | Path, persist_path: str | Path | None = None) -> None:
    global _index
    persist = Path(persist_path) if persist_path else None
    if persist and persist.exists():
        _index = VectorIndex(persist_path=persist)
    else:
        _index = build_index(repo_path, persist_path=persist)


@mcp.tool()
def find_similar_function(query: str, k: int = 5) -> list[dict]:
    """
    Search for functions in the indexed repository that do the same thing as
    the given code snippet or natural-language description.

    Call this before implementing any new function to reuse existing logic
    instead of duplicating it.

    Args:
        query: Source code of the function you are about to write, or a
               natural-language description of its intended behavior.
        k:     Maximum number of candidates to return (default 5).

    Returns:
        List of candidates ordered by similarity (highest first), each with
        name, file, start_line, source_code, and similarity_score.
        Empty list if no candidates exceed the 0.70 similarity threshold.
    """
    dummy = Function(name="query", file="", start_line=0, end_line=0, source_code=query)
    query_embedding = embed(dummy)

    results: list[SearchResult] = _get_index().search(query_embedding, k=k)
    threshold = 0.70
    return [
        {
            "name": r.function.name,
            "file": r.function.file,
            "start_line": r.function.start_line,
            "source_code": r.function.source_code,
            "similarity_score": r.score,
        }
        for r in results
        if r.score >= threshold
    ]
