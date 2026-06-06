# Story RADAR-007: data/seed_repo + data/heldout.json — demo data

**Status:** Draft

## Story

As the demo team, we need a Python repository with hand-planted duplicates and a held-out set of known pairs, so that we can demonstrate real detection and report a concrete precision/recall number in the pitch.

## Acceptance Criteria

1. [ ] `data/seed_repo/` contains at least 30 Python functions distributed across multiple files
2. [ ] At least 8 semantic duplicate pairs are planted (same logic, different names/variable names)
3. [ ] Duplicates cover varied cases: variable renaming, operand reordering, different function names
4. [ ] `data/heldout.json` contains at least 10 pairs: 6 true duplicates + 4 negatives (non-duplicates)
5. [ ] The held-out set is NOT indexed — it is used only for eval
6. [ ] Each function in the seed_repo has a one-line `summary` stored in `data/summaries.json` (precomputed at index time, no LLM)
7. [ ] Running `radar index data/seed_repo` produces a valid index without errors

## Tasks

- [ ] 1. Write `data/seed_repo/` by hand across these files:
  - `utils/dates.py` — date/time helpers
  - `utils/strings.py` — string manipulation
  - `utils/math_ops.py` — math operations
  - `billing/tax.py` — tax calculation (duplicates something from math_ops)
  - `billing/discounts.py` — discount logic (duplicates something from math_ops)
  - `parsing/csv_reader.py` — CSV parsing helpers
  - `parsing/json_loader.py` — JSON loading helpers
- [ ] 2. Plant at least 8 duplicate pairs with different names and variable names
- [ ] 3. Write `data/heldout.json` with 10 cases (format below)
- [ ] 4. Write `data/summaries.json` with one-line summaries per function name

## Dev Notes

**Do not copy from OSS repos.** Write the functions by hand so you control exactly what is and isn't a duplicate. This doubles as ground truth for the eval.

The agent A/B demo also needs a `CLAUDE.md` inside `seed_repo/` that instructs the agent: "Before writing any new function, call `find_similar_function` with the code you intend to write."

### heldout.json format

```json
[
  {
    "query_code": "def apply_tax(price, rate):\n    return price * (1 + rate / 100)",
    "expected_match": "calculate_tax",
    "is_duplicate": true
  },
  {
    "query_code": "def send_notification(msg):\n    print(msg)",
    "expected_match": null,
    "is_duplicate": false
  }
]
```

## Dependencies

- RADAR-002: verify the extractor can parse seed_repo correctly
