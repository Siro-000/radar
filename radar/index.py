import uuid
from pathlib import Path

import chromadb
from pydantic import BaseModel

from radar.models import Function


class SearchResult(BaseModel):
    function: Function
    score: float


class VectorIndex:
    def __init__(self, persist_path: str | Path | None = None, collection_name: str = "functions"):
        if persist_path:
            self._client = chromadb.PersistentClient(path=str(persist_path))
        else:
            self._client = chromadb.EphemeralClient()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, function: Function, embedding: list[float]) -> None:
        self._collection.add(
            ids=[self._id(function)],
            embeddings=[embedding],
            metadatas=[function.model_dump()],
        )

    def add_batch(self, functions: list[Function], embeddings: list[list[float]]) -> None:
        self._collection.add(
            ids=[self._id(f) for f in functions],
            embeddings=embeddings,
            metadatas=[f.model_dump() for f in functions],
        )

    def search(self, query_embedding: list[float], k: int = 5) -> list[SearchResult]:
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self._collection.count()),
        )
        output = []
        for metadata, distance in zip(
            results["metadatas"][0], results["distances"][0]
        ):
            output.append(
                SearchResult(
                    function=Function(**metadata),
                    score=round(1 - distance, 4),
                )
            )
        return output

    def count(self) -> int:
        return self._collection.count()

    @staticmethod
    def _id(function: Function) -> str:
        return f"{function.file}::{function.name}::{function.start_line}"
