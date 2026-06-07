from typing import Literal
from pydantic import BaseModel


class Function(BaseModel):
    name: str
    file: str
    start_line: int
    end_line: int
    source_code: str
    signature: str
    summary: str = ""
    import_statement: str = ""


class Match(BaseModel):
    match_id: str
    name: str
    signature: str
    location: str
    summary: str
    import_statement: str
    source_code: str  # full source so the AGENT can judge duplication itself
    similarity: float


class QueryResult(BaseModel):
    # HYBRID verdict: Radar only asserts the safe negative.
    #   "not_duplicate" -> top similarity below the retrieval floor; nothing to show.
    #   "candidate"     -> a match cleared the floor; `matches` holds the top-1 with
    #                      its source_code + similarity. The agent decides if it's a
    #                      real duplicate and whether to reuse it.
    query_id: str
    verdict: Literal["not_duplicate", "candidate"]
    matches: list[Match]
