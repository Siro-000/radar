# Radar demo

Two ways to show Radar, plus a token-cost experiment.

- **Scripted demo** — deterministic, no live agent. Always works; stage-safe.
- **Live agent A/B** — runs `claude -p` twice (with / without the tool) and compares.
- **Token-cost experiment** — does the tool save tokens? Measured, with real numbers below.

---

## Prerequisites

```bash
# from the radar repo root
uv sync                 # installs deps (incl. the embedder, downloaded on first run)
claude --version        # the live A/B drives the `claude` CLI in headless mode
```

The first index build downloads the `jina-embeddings-v2-base-code` model (~150 MB),
then runs on CPU.

---

## 1. Scripted demo (deterministic, always works)

```bash
bash demo/scripted_demo.sh
```

Shows, with no model-in-the-loop nondeterminism:
1. a function an agent is about to write,
2. Radar's answer: `verdict: candidate` + the matched `source_code` and
   `import_statement` (Radar surfaces it; the agent decides if it's a duplicate),
3. the **determinism cherry** — Radar's output is byte-identical across two runs,
4. the held-out retrieval numbers (recall-oriented floor; the agent is precision).

---

## 2. Live agent A/B (step by step)

```bash
bash demo/run_ab.sh                       # controlled mode, sonnet (default)
RADAR_DEMO_MODEL=opus bash demo/run_ab.sh # pin a different model
```

What it does, in order:
1. Copies `data/seed_repo` into two throwaway workspaces under `/tmp/radar-demo-run`
   (`without/` and `with/`) and drops in `workspace_CLAUDE.md` as each one's `CLAUDE.md`.
2. Builds the Radar index over the `with/` workspace.
3. Runs the **same task** (`task.md`) twice with `claude -p --output-format stream-json`:
   - **WITHOUT** — `--strict-mcp-config` with an empty MCP config (Radar not available).
   - **WITH** — `--strict-mcp-config` pointing at a generated Radar MCP config.
4. `compare.py` reads each arm's produced `Invoice.java` + transcript and prints the verdict.

Expected (controlled mode):

| Arm | Outcome |
|-----|---------|
| **WITHOUT** | `REIMPLEMENTED` — writes `price * rate / 100` inline (duplicates `TaxCalculator.calculateTax`) |
| **WITH** | `REUSED` — calls `find_similar_function`, reuses `import static …TaxCalculator.calculateTax;` |

### Controlled vs fair mode

The A/B isolates **one variable: access to Radar's semantic recall.**

- **Default (controlled):** neither arm browses the repo — both get only `Edit Write`
  (`Read/Glob/Grep/...` are denied). This models a codebase too large to read
  exhaustively. The WITH arm additionally gets `mcp__radar__find_similar_function`, so
  Radar is the *only* difference → clean outcome contrast.
- **`RADAR_DEMO_FAIR=1`:** both arms also get `Read Glob Grep`. On the small seed repo a
  strong agent finds the duplicate by reading, so both reuse — the difference shows up in
  the token/cost numbers instead.

Permissions default to `--permission-mode acceptEdits` + an explicit allowlist (no
blanket bypass). `RADAR_DEMO_YOLO=1` switches to `--dangerously-skip-permissions`
(throwaway env only). Runs happen under `/tmp/radar-demo-run`; `data/seed_repo` is
never mutated.

> This spawns autonomous `claude -p` sub-agents and consumes tokens.

---

## 3. Does Radar save tokens?

`compare.py` reports per-arm **turns, input/cache/output tokens, total tokens, cost (USD),
and wall-clock**, with the deltas. The honest answer depends on the corpus:

### On the small seed repo (`RADAR_DEMO_FAIR=1`, grep-findable duplicate)

The baseline finds `TaxCalculator` cheaply (a couple of greps over small files), so:

- **output tokens DOWN ~40%** (the agent reasons/explores less),
- **total tokens UP** (the MCP tool schema + tool result add context),
- **cost ≈ flat.**

Net: no token win — Radar's context overhead roughly cancels the saved exploration.

### On a large repo with a non-greppable duplicate (the real win)

```bash
python3 demo/gen_big_repo.py     # 40 filler classes + 1 hidden tax-equivalent
RADAR_DEMO_FAIR=1 RADAR_DEMO_REPO=demo/big_repo bash demo/run_ab.sh
```

`gen_big_repo.py` plants `Surcharges.surcharge(amount, factor)` — the same logic as
`price + price * rate / 100` but with **no tax/price/rate vocabulary**, so `grep` on the
task's keywords misses it, and the repo is too big to read exhaustively. Measured run
(sonnet):

| metric | WITHOUT | WITH | delta |
|---|---|---|---|
| outcome | **REIMPLEMENTED** | **REUSED** `Surcharges.surcharge` | correctness win |
| output tokens | 3,022 | 1,206 | **−60%** |
| total tokens | 222,942 | 217,309 | −2.5% |
| **cost (USD)** | 0.2091 | 0.1169 | **−44%** |
| wall-clock | 85 s | 33 s | −62% |

Here Radar wins on **both** axes: it finds a duplicate the baseline can't (grep misses
it, the repo is too large to read), and it costs less because the baseline burns output
tokens exploring before giving up and reimplementing. *(Agents are nondeterministic;
your numbers will vary, but the direction is stable.)*

### Caveat — the MVP embedder

`jina-embeddings-v2-base-code` is small and somewhat sensitive to identifier names: a
**fully** renamed duplicate can score just under the threshold and be missed. Radar
reliably catches near-duplicates (same logic, partially overlapping vocabulary,
different structure). Rename-robust detection is a post-MVP embedder upgrade.

---

## Files

- `task.md` — the coding task given to both arms
- `workspace_CLAUDE.md` — the "reuse before you write" instruction
- `run_ab.sh` — the A/B harness (env: `RADAR_DEMO_MODEL`, `RADAR_DEMO_FAIR`, `RADAR_DEMO_REPO`, `RADAR_DEMO_YOLO`, `RADAR_DEMO_RUNDIR`)
- `compare.py` — analyzes the two arms (outcome + tokens/cost) and prints the verdict
- `scripted_demo.sh` — the deterministic fallback demo
- `gen_big_repo.py` — generates the large corpus with a non-greppable duplicate
