# Story RADAR-008: eval/eval.py — precision/recall + threshold calibration

**Status:** Draft

## Story

As the team, we need a script that measures precision/recall of the engine against the held-out set, so that we can calibrate the server-side threshold and have a concrete number to show in the pitch.

## Acceptance Criteria

1. [ ] `python -m radar.eval.eval` runs the engine over `data/heldout.json` and prints precision, recall, and F1
2. [ ] Prints a per-case breakdown: query, expected match, found match, score, pass/fail
3. [ ] Accepts `--threshold` flag to test different values without touching `config.py`
4. [ ] Accepts `--sweep` flag to test thresholds from 0.60 to 0.95 in steps of 0.05 and print the optimal
5. [ ] Runs in < 30 seconds over the full held-out set (index already built)
6. [ ] Exit code 0 if precision >= 0.85, exit code 1 otherwise (usable in CI)

## Tasks

- [ ] 1. Load the prebuilt index from `artifacts/`
- [ ] 2. For each case in `heldout.json`: call `find_similar_function`, compare result against `expected_match`
- [ ] 3. Compute precision, recall, F1 at the given threshold
- [ ] 4. Implement `--sweep` mode
- [ ] 5. Print a formatted summary table

## Dev Notes

### Expected output

```
Running eval on 10 cases...

query                  expected        found           score   ok
apply_tax              calculate_tax   calculate_tax   0.91    ✓
send_notification      null            null            —       ✓
...

Results at threshold=0.70:
  Precision: 0.92
  Recall:    0.87
  F1:        0.89

Recommended threshold: 0.72  (F1=0.91)
```

This is where the threshold gets calibrated — not through the agent. Run `--sweep`, pick the threshold with the best F1, update `config.py`.

## Dependencies

- RADAR-006: `engine.find_similar_function`
- RADAR-007: `heldout.json` + built index from seed_repo
