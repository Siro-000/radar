import hashlib
from radar.engine.models import Function

MODEL_NAME = "jinaai/jina-embeddings-v2-base-code"
_model = None
_cache: dict[str, list[float]] = {}


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
    return _model


def _cache_key(source_code: str) -> str:
    return hashlib.sha256(source_code.encode()).hexdigest()


def _to_input(function: Function) -> str:
    return f"Function {function.name}:\n{function.source_code}"


def embed(function: Function) -> list[float]:
    """Embed a single Function, using the cache when available."""
    key = _cache_key(function.source_code)
    if key in _cache:
        return _cache[key]

    model = _get_model()
    vector: list[float] = model.encode(_to_input(function)).tolist()
    _cache[key] = vector
    return vector


def embed_batch(functions: list[Function]) -> list[list[float]]:
    """Embed a batch of Functions, skipping any that are already cached."""
    if not functions:
        return []

    results: list[list[float] | None] = [None] * len(functions)
    uncached_indices: list[int] = []
    uncached_inputs: list[str] = []

    for i, fn in enumerate(functions):
        key = _cache_key(fn.source_code)
        if key in _cache:
            results[i] = _cache[key]
        else:
            uncached_indices.append(i)
            uncached_inputs.append(_to_input(fn))

    if uncached_inputs:
        model = _get_model()
        vectors: list[list[float]] = model.encode(uncached_inputs).tolist()
        for idx, vector in zip(uncached_indices, vectors):
            key = _cache_key(functions[idx].source_code)
            _cache[key] = vector
            results[idx] = vector

    return results  # type: ignore[return-value]
