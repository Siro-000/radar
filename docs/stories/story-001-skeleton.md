# Story RADAR-001: Skeleton + tipos del contrato

**Status:** Draft

## Story

As a developer, I need the project skeleton with all dependencies installed and the frozen contract types defined, so that all subsequent modules have a common foundation to build on.

## Acceptance Criteria

1. [ ] `pyproject.toml` lists all dependencies: `sentence-transformers`, `faiss-cpu`, `mcp`, `tree-sitter`, `tree-sitter-python`, `pydantic`
2. [ ] `Function` model defined with fields: `name`, `file`, `start_line`, `end_line`, `source_code`, `signature`
3. [ ] `Match` model defined with fields: `match_id`, `name`, `signature`, `location`, `summary`, `import_statement`, `similarity`
4. [ ] `QueryResult` model defined with fields: `query_id`, `verdict` (literal "duplicate"|"similar"|"novel"), `matches`
5. [ ] The embedder loads and embeds a string on CPU without errors
6. [ ] Folder layout created: `engine/`, `adapters/`, `eval/`, `data/`, `tests/`, `artifacts/`
7. [ ] `artifacts/` is in `.gitignore`

## Tasks

- [ ] 1. Create `pyproject.toml` with all deps and entry point `radar = "radar.adapters.cli:main"`
- [ ] 2. Create `engine/models.py` with `Function`, `Match`, `QueryResult` using pydantic
- [ ] 3. Write a smoke script that loads `SentenceTransformer("jinaai/jina-embeddings-v2-base-code", trust_remote_code=True)` and embeds a string — confirm it runs on CPU
- [ ] 4. Create folder structure with `__init__.py` files
- [ ] 5. Add `artifacts/` to `.gitignore`

## Dev Notes

The `Function` record is the seam between `extract.py` and `embed.py`/`index.py`. Its shape must be agreed on here — it's where two people meet.

The frozen contract types (`Match`, `QueryResult`) must not change after this story. All adapters and the engine agree on exactly these field names.

## Dependencies

None — this is the foundation.
