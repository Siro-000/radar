import json
from pathlib import Path

import faiss
import numpy as np
from pydantic import BaseModel

from radar.engine.models import Function


class SearchResult(BaseModel):
    function: Function
    score: float


class Index:
    def __init__(self, faiss_index, metadata: list[dict]) -> None:
        self._index = faiss_index
        self._metadata = metadata  # position matches faiss id

    def search(self, query_vector: list[float], k: int = 5) -> list[SearchResult]:
        if self._index.ntotal == 0:
            return []
        q = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(q)
        k = min(k, self._index.ntotal)
        scores, ids = self._index.search(q, k)
        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue
            results.append(SearchResult(function=Function(**self._metadata[idx]), score=float(score)))
        return results

    def count(self) -> int:
        return self._index.ntotal


_DEFAULT_DIM = 768


def build(functions: list[Function], embeddings: list[list[float]], path: Path | str) -> Index:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

    metadata = [fn.model_dump() for fn in functions]
    (path / "metadata.json").write_text(json.dumps(metadata, indent=2))

    if not embeddings:
        index = faiss.IndexFlatIP(_DEFAULT_DIM)
        faiss.write_index(index, str(path / "index.faiss"))
        return Index(index, metadata)

    vectors = np.array(embeddings, dtype=np.float32)
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    faiss.write_index(index, str(path / "index.faiss"))
    return Index(index, metadata)


def load(path: Path | str) -> Index:
    path = Path(path)
    index = faiss.read_index(str(path / "index.faiss"))
    metadata = json.loads((path / "metadata.json").read_text())
    return Index(index, metadata)
