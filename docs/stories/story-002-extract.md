# Story RADAR-002: engine/extract.py — function extractor

**Status:** Draft

## Story

As the detection engine, I need to extract all methods and functions from a Java repository with their full metadata, so that they can be indexed and searched for semantic duplicates.

## Acceptance Criteria

1. [ ] `parse_file(path) -> list[Function]` extracts all methods from a single `.java` file
2. [ ] `parse_repo(path) -> list[Function]` recursively walks all `.java` files in a directory
3. [ ] Each `Function` includes `signature` — the full method signature line (visibility + return type + name + params)
4. [ ] Methods shorter than 4 lines are skipped (too trivial to index)
5. [ ] Instance methods, static methods and constructors are all extracted
6. [ ] `location` can be derived as `"File.java:start_line-end_line"` from the record fields
7. [ ] Files with syntax errors are skipped and logged to stderr — no crash

## Tasks

- [ ] 1. Add `tree-sitter-java` dependency to `pyproject.toml`
- [ ] 2. Implement `parse_file(path: Path) -> list[Function]` — traverse `method_declaration` and `constructor_declaration` AST nodes, capture name, lines, full source, and first line as signature
- [ ] 3. Implement `parse_repo(repo_path: Path) -> list[Function]` — glob `**/*.java`, call `parse_file`, flatten
- [ ] 4. Write tests:
  - [ ] File with instance methods, static methods and a constructor
  - [ ] File with a syntax error (must skip gracefully)
  - [ ] Empty repo returns empty list

## Dev Notes

Use tree-sitter + `tree-sitter-java`, not a regex approach — tree-sitter handles partial/broken files gracefully. The `signature` field is the raw first line of the method source, not reconstructed.

Java AST node types to target:
- `method_declaration` — regular instance and static methods
- `constructor_declaration` — constructors

The `name` field maps to the method identifier node. The `file` field stores the relative path from the repo root.

## Dependencies

- RADAR-001: `Function` model
