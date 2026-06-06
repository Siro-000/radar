import hashlib
from openai import OpenAI

from radar.models import Function

MODEL = "text-embedding-3-small"
_client: OpenAI | None = None
_cache: dict[str, list[float]] = {}


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _cache_key(source_code: str) -> str:
    return hashlib.sha256(source_code.encode()).hexdigest()


def _to_input(function: Function) -> str:
    return f"Function {function.name}:\n{function.source_code}"


def embed(function: Function) -> list[float]:
    key = _cache_key(function.source_code)
    if key in _cache:
        return _cache[key]
    response = _get_client().embeddings.create(model=MODEL, input=_to_input(function))
    vector = response.data[0].embedding
    _cache[key] = vector
    return vector


def embed_batch(functions: list[Function]) -> list[list[float]]:
    results: list[list[float] | None] = [None] * len(functions)
    uncached_indices = []
    uncached_inputs = []

    for i, fn in enumerate(functions):
        key = _cache_key(fn.source_code)
        if key in _cache:
            results[i] = _cache[key]
        else:
            uncached_indices.append(i)
            uncached_inputs.append(_to_input(fn))

    if uncached_inputs:
        response = _get_client().embeddings.create(model=MODEL, input=uncached_inputs)
        for idx, item in zip(uncached_indices, response.data):
            vector = item.embedding
            key = _cache_key(functions[idx].source_code)
            _cache[key] = vector
            results[idx] = vector

    return results  # type: ignore[return-value]
