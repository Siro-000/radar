# Radar demo

Two ways to show Radar, plus a token-cost experiment.

- **Scripted demo** — deterministic, no live agent. Always works; stage-safe.
- **Live agent A/B/C** — runs `claude -p` three times (no tool / no tool + exhaustive-search prompt / with the tool) and compares.
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

## 2. Live agent A/B/C (step by step)

```bash
bash demo/run_ab.sh                       # controlled mode, sonnet (default)
RADAR_DEMO_MODEL=opus bash demo/run_ab.sh # pin a different model
```

What it does, in order:
1. Copies the source repo into **three** throwaway workspaces under
   `/tmp/radar-demo-run` (`without/`, `prompted/`, `with/`) and drops in the right
   `CLAUDE.md` for each.
2. Builds the Radar index over the `with/` workspace.
3. Runs the **same task** (`task.md`) three times with `claude -p --output-format
   stream-json`:
   - **without** — empty MCP config; baseline.
   - **prompted** — empty MCP config, but a `CLAUDE.md` that explicitly orders an
     *exhaustive, synonym-aware* repository search, and `Read/Glob/Grep` always on.
   - **with** — `--strict-mcp-config` pointing at a generated Radar MCP config.
4. `compare.py` reads each arm's produced `Invoice.java` + transcript and prints the verdict.

Expected (controlled mode, on a repo with a non-greppable duplicate):

| Arm | Outcome |
|-----|---------|
| **without** | `REIMPLEMENTED` — writes `price * rate / 100` inline (no discovery path) |
| **prompted** | `REIMPLEMENTED` — greps for tax/price/rate, the duplicate uses none of those words, gives up and reimplements (often after burning many search turns) |
| **with** | `REUSED` — calls `find_similar_function`, reuses the existing function via its `import_statement` |

The headline: **telling the agent to "search exhaustively" is not a substitute for
semantic retrieval.** On a small/greppable repo the `prompted` arm *can* find the
duplicate by reading — but it pays for many grep/read turns to do what Radar does in
one deterministic call (see the efficiency table).

### The three arms — what each one isolates

The demo separates two questions that are easy to conflate:

1. *Does the agent need a discovery mechanism at all?* → `without` vs `with`.
2. *Is a strong prompt + plain lexical search enough, or do you need semantic
   retrieval?* → `prompted` vs `with`.

- **`without`** uses the **same `CLAUDE.md` as `with`** (told to reuse) but has no Radar
  tool, so tool availability is the only difference between them.
- **`prompted`** always gets `Read/Glob/Grep` (searching is its whole point) and a
  `CLAUDE.md` that pushes an exhaustive, synonym-aware search — no Radar tool.
- **`with`** additionally gets `mcp__radar__find_similar_function`.

### Controlled vs fair mode

- **Default (controlled):** `without` and `with` do **not** browse the repo
  (`Read/Glob/Grep` denied) — this models a codebase too large to read exhaustively.
  `prompted` still searches (that is the variable it tests). So the WITH arm's only
  discovery path is Radar → clean outcome contrast.
- **`RADAR_DEMO_FAIR=1`:** `without` and `with` also get `Read Glob Grep`. Now `without`
  and `prompted` differ only by the **prompt**, isolating whether the exhaustive-search
  instruction alone changes behaviour. On a small seed repo a strong agent finds the
  duplicate by reading, so the contrast moves to the token/cost numbers.

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

- `task.md` — the coding task given to all three arms
- `workspace_CLAUDE.md` — the Radar "reuse, call `find_similar_function`" instruction (`without` + `with` arms)
- `workspace_CLAUDE_prompted.md` — the exhaustive-search-no-duplicates instruction (`prompted` arm, no tool mention)
- `run_ab.sh` — the A/B/C harness (env: `RADAR_DEMO_MODEL`, `RADAR_DEMO_FAIR`, `RADAR_DEMO_REPO`, `RADAR_DEMO_YOLO`, `RADAR_DEMO_RUNDIR`)
- `compare.py` — analyzes the three arms (outcome + tokens/cost) and prints the verdict
- `scripted_demo.sh` — the deterministic fallback demo
- `gen_big_repo.py` — generates the large corpus with a non-greppable duplicate
