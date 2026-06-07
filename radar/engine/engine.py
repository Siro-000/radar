import hashlib
import uuid
from pathlib import Path

from radar.engine.config import DEFAULT_TOP_K, RETRIEVAL_FLOOR
from radar.engine.embed import embed
from radar.engine.index import Index, load
from radar.engine.models import Function, Match, QueryResult

_index: Index | None = None


def load_index(artifacts_path: Path | str) -> None:
    global _index
    _index = load(Path(artifacts_path))


def _get_index() -> Index:
    if _index is None:
        raise RuntimeError("Index not loaded. Call load_index() first.")
    return _index


def find_similar_function(
    code: str,
    language: str = "java",
    intent: str = "",
    top_k: int = DEFAULT_TOP_K,
) -> QueryResult:
    """Hybrid retrieval.

    Radar does NOT decide duplication. It runs a deterministic nearest-neighbour
    search and, if the top similarity clears RETRIEVAL_FLOOR, returns that single
    candidate WITH its full source so the agent can judge for itself. Below the
    floor it returns the safe negative `not_duplicate` (nothing worth showing).
    """
    query_id = str(uuid.uuid4())

    dummy = Function(
        name="query",
        file="",
        start_line=0,
        end_line=0,
        source_code=code,
        signature=code.splitlines()[0].strip() if code.strip() else "",
    )

    query_vector = embed(dummy)
    results = _get_index().search(query_vector, k=top_k)

    if not results or results[0].score < RETRIEVAL_FLOOR:
        return QueryResult(query_id=query_id, verdict="not_duplicate", matches=[])

    top = results[0]
    fn = top.function
    match_id = hashlib.sha256(f"{code}{fn.file}{fn.name}".encode()).hexdigest()[:16]
    match = Match(
        match_id=match_id,
        name=fn.name,
        signature=fn.signature,
        location=f"{fn.file}:{fn.start_line}-{fn.end_line}",
        summary=fn.summary,
        import_statement=fn.import_statement,
        source_code=fn.source_code,
        similarity=round(top.score, 6),
    )
    return QueryResult(query_id=query_id, verdict="candidate", matches=[match])
