# Story RADAR-002: engine/extract.py — function extractor

**Status:** Draft

## Story

As the detection engine, I need to extract all functions from a Python repository with their full metadata, so that they can be indexed and searched for semantic duplicates.

## Acceptance Criteria

1. [ ] `parse_file(path) -> list[Function]` extracts all functions from a single `.py` file
2. [ ] `parse_repo(path) -> list[Function]` recursively walks all `.py` files in a directory
3. [ ] Each `Function` includes `signature` — the full `def ...` line with type hints if present
4. [ ] Functions shorter than 4 lines are skipped (too trivial to index)
5. [ ] Class methods are extracted in addition to top-level functions
6. [ ] `location` can be derived as `"file.py:start_line-end_line"` from the record fields
7. [ ] Files with syntax errors are skipped and logged to stderr — no crash

## Tasks

- [ ] 1. Set up `tree-sitter` + `tree-sitter-python` parser
- [ ] 2. Implement `parse_file(path: Path) -> list[Function]` — traverse `function_definition` AST nodes, capture name, lines, full source, and first line as signature
- [ ] 3. Implement `parse_repo(repo_path: Path) -> list[Function]` — glob `**/*.py`, call `parse_file`, flatten
- [ ] 4. Write tests:
  - [ ] File with top-level functions and class methods
  - [ ] File with a syntax error (must skip gracefully)
  - [ ] Empty repo returns empty list

## Dev Notes

Use tree-sitter, not the `ast` stdlib module — tree-sitter handles partial/broken files. The `signature` field is the raw first line of the function source (the `def` line), not reconstructed — simpler and reliable.

## Dependencies

- RADAR-001: `Function` model
