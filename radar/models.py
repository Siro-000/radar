from pydantic import BaseModel


class Function(BaseModel):
    name: str
    file: str
    start_line: int
    end_line: int
    source_code: str
