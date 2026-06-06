import hashlib
import uuid
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

DUPLICATE_THRESHOLD = 0.85
SIMILAR_THRESHOLD = 0.70


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


def _import_statement(file: str, name: str) -> str:
    module = file.replace("\\", "/").removesuffix(".py").replace("/", ".")
    return f"from {module} import {name}"


def _verdict(top_similarity: float) -> str:
    if top_similarity >= DUPLICATE_THRESHOLD:
        return "duplicate"
    if top_similarity >= SIMILAR_THRESHOLD:
        return "similar"
    return "novel"


def _match_id(query_code: str, candidate_file: str, candidate_name: str) -> str:
    key = f"{query_code}::{candidate_file}::{candidate_name}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


@mcp.tool()
def find_similar_function(
    code: str,
    language: str = "python",
    intent: str = "",
    top_k: int = 3,
) -> dict:
    """
    Search the indexed repository for functions that do the same thing as the
    given code snippet. Call this before implementing any new function to reuse
    existing logic instead of duplicating it.

    Args:
        code:     Source code of the function you are about to write.
        language: Programming language hint (default "python").
        intent:   Optional natural-language description of intended behavior.
        top_k:    Maximum number of candidates to return (default 3).

    Returns:
        A dict with query_id, verdict ("duplicate"/"similar"/"novel"), and a
        matches list. Each match includes name, signature, location, summary,
        import_statement, and similarity. Empty matches list when verdict is
        "novel".
    """
    dummy = Function(name="query", file="", start_line=0, end_line=0, source_code=code)
    query_embedding = embed(dummy)

    raw: list[SearchResult] = _get_index().search(query_embedding, k=top_k)
    matches_above = [r for r in raw if r.score >= SIMILAR_THRESHOLD]
    top_score = matches_above[0].score if matches_above else 0.0

    matches = [
        {
            "match_id": _match_id(code, r.function.file, r.function.name),
            "name": r.function.name,
            "signature": r.function.source_code.strip().splitlines()[0],
            "location": f"{r.function.file}:{r.function.start_line}-{r.function.end_line}",
            "summary": f"Function to {r.function.name.replace('_', ' ')} (in {r.function.file})",
            "import_statement": _import_statement(r.function.file, r.function.name),
            "similarity": r.score,
        }
        for r in matches_above
    ]

    return {
        "query_id": str(uuid.uuid4()),
        "verdict": _verdict(top_score),
        "matches": matches,
    }
