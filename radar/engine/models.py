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
    similarity: float


class QueryResult(BaseModel):
    query_id: str
    verdict: Literal["duplicate", "similar", "novel"]
    matches: list[Match]
