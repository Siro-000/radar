# Story RADAR-011: Tests N0 / N2 / N3 — smoke, determinism, contract

**Status:** Draft

## Story

As the team, we need three deterministic tests that validate the engine without going through the agent, so that we can confidently claim the system works and that results are reproducible.

## Acceptance Criteria

### N0 — Smoke (`tests/test_smoke.py`)
1. [ ] Indexes the full `seed_repo` (Java files)
2. [ ] Calls `find_similar_function` with a known duplicate Java method from the held-out set
3. [ ] Asserts the expected match appears in the results with score >= 0.70
4. [ ] Runs in < 60 seconds (includes indexing)

### N2 — Determinism (`tests/test_determinism.py`)
5. [ ] Calls `find_similar_function` with the same Java method input exactly twice
6. [ ] Asserts `query_id` differs between calls (it is a UUID per call)
7. [ ] Asserts `verdict` is identical between calls
8. [ ] Asserts all match scores are identical to the last decimal place
9. [ ] Asserts match order is identical

### N3 — Contract shape (`tests/test_contract.py`)
10. [ ] The response has exactly the fields defined in the frozen contract — no more, no less
11. [ ] `verdict` is one of: `"duplicate"`, `"similar"`, `"novel"`
12. [ ] Each `Match` has: `match_id`, `name`, `signature`, `location`, `summary`, `import_statement`, `similarity`
13. [ ] `similarity` is a float between 0.0 and 1.0
14. [ ] `location` matches the format `"File.java:start-end"`

## Tasks

- [ ] 1. `test_smoke.py`: fixture that builds a real index from seed_repo (Java), queries with known duplicate Java method, asserts match
- [ ] 2. `test_determinism.py`: two consecutive calls with the same Java method input, field-by-field comparison
- [ ] 3. `test_contract.py`: call with a mocked index, validate full response shape with explicit assertions

## Dev Notes

Test the engine deterministically. Never validate recall quality through the agent: if the agent doesn't reuse, you can't tell whether the recall missed the duplicate or the agent ignored the match it received.

The N0 smoke test is the critical one for the demo — if it passes, the engine works end-to-end on real Java data.

Test fixture Java snippet example:
```java
public double applyTax(double price, double rate) {
    return price * (1 + rate / 100);
}
```

## Dependencies

- RADAR-006: engine
- RADAR-007: seed_repo (for N0)
