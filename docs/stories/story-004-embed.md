# Story RADAR-004: engine/embed.py — embedder wrapper

**Status:** Draft

## Story

As the detection engine, I need a single access point to the embedding model, so that swapping models in the future is a one-file change with no impact on any other module.

## Acceptance Criteria

1. [ ] `embed(function: Function) -> list[float]` returns the embedding vector for one function
2. [ ] `embed_batch(functions: list[Function]) -> list[list[float]]` processes in batch (more efficient)
3. [ ] Input to the model is: `"Function {name}:\n{normalized_source}"`
4. [ ] In-memory cache keyed by SHA-256 of the normalized source — never re-embeds the same content twice
5. [ ] Model is loaded lazily on first call, not at import time
6. [ ] No other module imports `sentence_transformers` directly
7. [ ] `embed_batch` only calls the model for uncached functions — cached ones are returned directly

## Tasks

- [ ] 1. Load `jinaai/jina-embeddings-v2-base-code` with `trust_remote_code=True` in a lazy `_get_model()` function
- [ ] 2. Implement `embed()` with cache lookup and store
- [ ] 3. Implement `embed_batch()` — split into cached/uncached, call model only for uncached, merge results
- [ ] 4. Write tests (mock the model):
  - [ ] `embed` returns a list of floats
  - [ ] Second call to `embed` with same input hits cache (model called once)
  - [ ] `embed_batch` skips already-cached functions

## Dev Notes

The model produces 768-dimensional vectors. It is deprecated by Jina but chosen deliberately for being CPU-friendly (137M params). Do NOT upgrade to `jina-embeddings-v4` — that's 3.8B params and won't run comfortably on a laptop without a GPU.

`normalize()` from RADAR-003 is applied inside `embed()` before building the model input string.

## Dependencies

- RADAR-001: `Function` model
- RADAR-003: `normalize()` applied before embedding
