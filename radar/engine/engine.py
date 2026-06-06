import hashlib
import uuid
from pathlib import Path

from radar.engine.config import DEFAULT_TOP_K, DUPLICATE_THRESHOLD, SIMILAR_THRESHOLD
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

    matches = []
    for result in results:
        if result.score < SIMILAR_THRESHOLD:
            continue
        fn = result.function
        match_id = hashlib.sha256(f"{code}{fn.file}{fn.name}".encode()).hexdigest()[:16]
        matches.append(Match(
            match_id=match_id,
            name=fn.name,
            signature=fn.signature,
            location=f"{fn.file}:{fn.start_line}-{fn.end_line}",
            summary=fn.summary,
            import_statement=fn.import_statement,
            similarity=round(result.score, 6),
        ))

    if matches and matches[0].similarity >= DUPLICATE_THRESHOLD:
        verdict = "duplicate"
    elif matches:
        verdict = "similar"
    else:
        verdict = "novel"

    return QueryResult(query_id=query_id, verdict=verdict, matches=matches)
