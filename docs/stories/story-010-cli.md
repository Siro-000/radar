# Story RADAR-010: adapters/cli.py — CLI

**Status:** Draft

## Story

As a developer, I need a CLI to index a repo and run manual queries, so that I can develop and demo the engine without needing a connected AI agent.

## Acceptance Criteria

1. [ ] `radar index <repo_path>` builds the index and persists it to `artifacts/`
2. [ ] `radar query "<code>"` finds similar functions and prints formatted matches
3. [ ] `radar serve --repo <path>` starts the MCP server (delegates to `mcp_server.py`)
4. [ ] `radar query` output shows: verdict, and for each match: name, location, score, import_statement
5. [ ] Demo fallback works end-to-end: `radar index ./data/seed_repo && radar query "def apply_tax(p, r): ..."`

## Tasks

- [ ] 1. Parse subcommands with `argparse`
- [ ] 2. `cmd_index`: call `parse_repo` → `embed_batch` → `index.build` → `index.save(artifacts/)`
- [ ] 3. `cmd_query`: load index from `artifacts/` → call `engine.find_similar_function` → print formatted output
- [ ] 4. `cmd_serve`: delegate to `mcp_server.main()`

## Dev Notes

### Expected output of `radar query`

```
verdict: duplicate

  1. calculate_tax  (billing/tax.py:12-18)  score=0.93
     from billing.tax import calculate_tax

  2. apply_rate  (utils/math_ops.py:5-11)  score=0.71
     from utils.math_ops import apply_rate
```

This is the degraded-but-dignified demo fallback: if the MCP↔client chain is not live in time, the CLI showing a match + its import + the determinism run twice still proves recall and reproducibility.

## Dependencies

- RADAR-006: engine
- RADAR-009: mcp_server (for `cmd_serve`)
