# Story RADAR-006: engine/config.py + engine/engine.py — find_similar_function

**Status:** Draft

## Story

As an AI agent, I need to call `find_similar_function` and receive a complete, actionable response that tells me whether the logic I am about to write already exists, so that I can reuse it instead of duplicating it.

## Acceptance Criteria

1. [ ] `find_similar_function(code, language, intent, top_k)` implements the full frozen contract
2. [ ] Returns `query_id` (UUID4), `verdict`, and a list of `Match` objects
3. [ ] `verdict` is decided server-side: `"duplicate"` if top score >= 0.85, `"similar"` if >= 0.70, `"novel"` otherwise
4. [ ] Each `Match` includes all fields: `match_id`, `name`, `signature`, `location`, `summary`, `import_statement`, `similarity`
5. [ ] `import_statement` is constructed from the `file` path of the `Function` record
6. [ ] `location` has the format `"file.py:start_line-end_line"`
7. [ ] `summary` is read from the metadata store (precomputed at index time — no LLM in the query path)
8. [ ] The function is deterministic: same input → same output (same matches, same scores, same verdict)
9. [ ] The threshold is server-side config only — not a parameter the caller can override

## Tasks

- [ ] 1. Create `config.py`:
  ```python
  DUPLICATE_THRESHOLD = 0.85
  SIMILAR_THRESHOLD = 0.70
  DEFAULT_TOP_K = 3
  ```
- [ ] 2. Implement `engine.py` with `find_similar_function()` that orchestrates: normalize → embed → index.search → threshold → build response
- [ ] 3. Implement verdict logic based on the highest match score
- [ ] 4. Build `import_statement` from file path: `"from {module_path} import {name}"`
- [ ] 5. Write tests:
  - [ ] Score >= 0.85 → verdict is `"duplicate"`
  - [ ] Score in [0.70, 0.85) → verdict is `"similar"`
  - [ ] Score < 0.70 → verdict is `"novel"`, matches is empty
  - [ ] Calling twice with same input → identical output (except `query_id`)

## Dev Notes

The query path is: `normalize(code)` → `embed()` → `index.search(k)` → apply thresholds → build `QueryResult`.

The online path never reindexes. It only embeds the incoming snippet and searches the prebuilt index. Indexing artifacts are loaded at engine startup.

`match_id` identifies the pair (query ↔ candidate), not just the candidate. Construct it as a deterministic hash of `query_content + candidate_file + candidate_name`.

## Dependencies

- RADAR-002: extract (for offline indexing step)
- RADAR-003: normalize
- RADAR-004: embed
- RADAR-005: index search
