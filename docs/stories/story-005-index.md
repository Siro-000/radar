# Story RADAR-005: engine/index.py — FAISS index + metadata store

**Status:** Draft

## Story

As the detection engine, I need to build, persist, and query a vector index of functions, so that I can find the most similar ones to a query in milliseconds.

## Acceptance Criteria

1. [ ] `build(functions, embeddings, path)` builds a FAISS index and persists it to disk alongside the metadata store
2. [ ] `load(path) -> Index` loads the index and metadata from disk
3. [ ] `search(index, query_vector, k) -> list[SearchResult]` returns the k nearest neighbors with similarity score
4. [ ] `SearchResult` contains the full `Function` record and a similarity score between 0.0 and 1.0
5. [ ] Score is cosine similarity (not distance): 1.0 = identical
6. [ ] `search` latency < 100ms on a loaded in-memory index
7. [ ] The metadata store is a JSON file (`metadata.json`) that persists all `Function` fields including `summary` and `import_statement`

## Tasks

- [ ] 1. Use `faiss-cpu` with `IndexFlatIP` (inner product on normalized vectors = cosine similarity)
- [ ] 2. Normalize all vectors to unit length before adding to the index
- [ ] 3. Implement metadata store as `metadata.json` — a list of `Function` dicts indexed by FAISS position
- [ ] 4. Implement `build(functions, embeddings, path)` — saves `index.faiss` + `metadata.json` to `path`
- [ ] 5. Implement `load(path) -> Index` — loads both files from `path`
- [ ] 6. Implement `search(query_vector, k) -> list[SearchResult]`
- [ ] 7. Write tests:
  - [ ] Add functions + search returns them
  - [ ] Persist to disk and reload — results are identical
  - [ ] Score is between 0.0 and 1.0
  - [ ] Most similar function is ranked first

## Dev Notes

`IndexFlatIP` with L2-normalized vectors computes exact cosine similarity. No approximation needed for the MVP — the index will have at most a few thousand functions.

The `artifacts/` directory holds two files per index:
- `index.faiss` — the FAISS binary index
- `metadata.json` — list of Function dicts, position matches FAISS id

JSON was chosen over SQLite for simplicity: no schema migrations, no driver, human-readable for debugging.

## Dependencies

- RADAR-001: `Function`, `SearchResult` models
- RADAR-004: embeddings as input to `build`
