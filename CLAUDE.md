# CLAUDE.md — Radar

Project context for Claude Code. Read this before writing or changing code.

## What we're building

**Radar** is an MCP server backed by a semantic-duplication engine. When a coding
agent is about to write a function, it calls Radar first to find out whether that
logic **already exists in the repo** — and, if so, gets back how to reuse it instead
of duplicating it.

It detects **semantic** duplication (same logic, different syntax), not textual
copy/paste. The detection is a cheap, deterministic vector lookup — **not** a
generative LLM.

There is **no human in the loop**. The agent asks, Radar answers with a deterministic
verdict against a calibrated threshold, the agent decides on its own.

## The one principle that governs the codebase

**One engine, thin adapters.** The recall engine is a pure, importable library.
The CLI, the MCP server, and the eval script are *thin wrappers over the same
engine* — they must never reimplement detection logic. If you find yourself writing
matching/threshold logic inside an adapter, stop: it belongs in the engine.

## How it works

Two phases, kept strictly separate:

1. **Offline indexing** (run once over a repo): tree-sitter extracts functions →
   normalize → embed → build a FAISS index + a metadata store on disk.
2. **Online query** (per call): `find_similar_function(code)` → normalize → embed the
   incoming function → FAISS kNN → apply threshold → assemble matches → verdict.

The online path **never reindexes**. It only embeds the incoming snippet and searches
the prebuilt index. Indexing artifacts (FAISS index + metadata store) are produced
offline and loaded at engine startup.

## The contract — HYBRID (retrieve, agent judges)

This is the interface everything depends on. **Do not change the signature or the
field names without telling the whole team.** Adapters, the engine, and the eval all
agree on exactly this.

Radar does **not** make the duplicate decision. It is a deterministic retriever: it
surfaces the single best existing candidate (with its source) when similarity clears
a low recall floor, and the **agent** judges whether it's truly a duplicate. This
removes the brittle, precision-critical duplicate threshold (and its calibration /
data-leakage problems) and pushes the precision decision to the agent, which can read
the actual code instead of trusting a noisy cosine score.

```
find_similar_function({
  code: string,        // required: the function the agent is about to write
  language?: string,   // optional, default inferred ("java")
  intent?: string,     // optional: NL description of what it's trying to do
  top_k?: int          // optional, search breadth; the response returns the top-1
}) -> {
  query_id: string,                       // event id (telemetry)
  verdict: "not_duplicate" | "candidate", // server only asserts the safe negative
  matches: [                              // empty if not_duplicate; top-1 if candidate
    {
      match_id: string,         // stable id of the PAIR (query <-> candidate)
      name: string,             // "calculateTax"
      signature: string,        // "public double calculateTax(double price, double rate)"
      location: string,         // "src/com/acme/finance/TaxCalculator.java:6-10"
      summary: string,          // 1 line, precomputed at index time (no LLM)
      import_statement: string, // "import static ...TaxCalculator.calculateTax;"
      source_code: string,      // FULL source — what the agent reads to judge duplication
      similarity: float         // 0.0–1.0, a hint (NOT a verdict)
    }
  ]
}
```

- `verdict` is **only** the safe negative: `not_duplicate` when the top similarity is
  below `RETRIEVAL_FLOOR`; otherwise `candidate` (the agent decides from the source).
- The **floor is server-side config** and recall-oriented — the agent is the precision
  stage. `similarity` is returned as a hint, never as the decision.
- The response must be **actionable**: `source_code` lets the agent verify, and
  `import_statement` is what makes it reuse instead of regenerate.
- **Determinism is preserved in Radar's output** (same input → same candidate + score);
  only the final duplicate judgment moves to the (non-deterministic) agent. A
  deterministic CI gate would re-add a high-precision threshold on top of this.

## Tech stack

- **Python 3.11+**
- **tree-sitter** + `tree-sitter-python` — function extraction (MVP: Python only)
- **Embedder** — `jina-embeddings-v2-base-code` (137M params, code-specialized, runs on
  CPU in seconds). It is **deprecated** by Jina but **chosen deliberately** for the MVP
  precisely because it is tiny and CPU-friendly. Do NOT "upgrade" it to
  `jina-embeddings-v4` — that's a 3.8B model and won't run comfortably on a laptop without
  a GPU; swapping to a current encoder is a post-MVP task. Wrap the model behind
  `engine/embed.py` so the rest of the code never imports it directly — changing models
  must be a one-file change.
- **faiss-cpu** — kNN index
- **MCP Python SDK** — stdio server (local; this is the demo-ready form, no hosting)
- **sqlite** (or a JSON file for the MVP) — metadata store mapping vector id → metadata

## Proposed layout

```
radar/
  engine/            # the core — pure, importable, no I/O surprises
    extract.py       # tree-sitter -> function records {name, file, lines, source}
    normalize.py     # canonicalize var names, strip comments/whitespace
    embed.py         # the ONLY place the embedding model is imported
    index.py         # build / load / query the FAISS index
    engine.py        # find_similar_function() — the contract implementation
    config.py        # threshold and other server-side settings
  adapters/
    cli.py           # thin wrapper over engine.find_similar_function
    mcp_server.py    # thin MCP stdio server exposing find_similar_function
  eval/
    eval.py          # precision/recall vs the held-out set (calls engine directly)
  tests/
    test_smoke.py        # N0: index seed repo, a known duplicate comes back as a match
    test_determinism.py  # N2: same input twice -> byte-identical output
    test_contract.py     # output shape matches the frozen contract
  data/
    seed_repo/       # demo asset: a Python repo with planted duplicates
    heldout.json     # known duplicate pairs for the precision/recall number
  artifacts/         # generated, gitignored: index.faiss, metadata.db
  pyproject.toml
```

The **function record** (`{name, file, lines, source}`) is the seam between
`extract.py` and `embed.py`/`index.py` — agree on its shape early; it's where two
people meet.

## Commands

Tooling is `uv` (see `pyproject.toml`; Python 3.12). The `radar` and `radar-eval`
console scripts are the entry points.

```bash
# install (creates .venv, fetches Python 3.12 + deps, incl. the embedder on first run)
uv sync

# build the index for a repo (offline) -> writes index.faiss + metadata.json
uv run radar index --repo data/seed_repo --index-path .radar-index

# query via CLI (dev + demo fallback) — prints the QueryResult as JSON
uv run radar query --index-path .radar-index 'public static double f(...) { ... }'

# run the MCP stdio server (builds the index from --repo if --index-path is empty)
uv run radar serve --repo data/seed_repo --index-path .radar-index

# run tests
uv run pytest

# eval: precision/recall on the held-out set; --sweep recommends a threshold (N1)
uv run radar-eval
uv run radar-eval --sweep

# the project .mcp.json already registers `radar` for Claude Code in this repo.
claude mcp list          # shows `radar` as ✓ Connected; inside a session, /mcp too

# demos (see demo/README.md)
bash demo/scripted_demo.sh                 # deterministic, no agent
bash demo/run_ab.sh                        # live agent A/B (with vs without the tool)
```

> macOS note: native OpenMP workarounds (`KMP_DUPLICATE_LIB_OK`, `OMP_NUM_THREADS`)
> are set in `radar/__init__.py`; without them faiss+torch can SIGSEGV (exit 139).

## Testing

**Test the engine deterministically; the agent A/B is the demo, not a test.** Never
validate recall quality *through* the agent: if the agent doesn't reuse, you can't tell
whether the recall missed the duplicate or the agent ignored the match it received. Five
levels, cheap to expensive:

- **N0 — Smoke (`tests/test_smoke.py`).** Index the seed repo, call
  `find_similar_function` with a known duplicate, assert it returns as a match. Direct
  Python call, no MCP, no agent.
- **N1 — Recall quality (`eval/eval.py`).** Run the engine over the held-out set, compute
  precision/recall at the threshold. **This is where you calibrate.** Deterministic and
  fast — iterate the threshold here, not through the agent.
- **N2 — Determinism (`tests/test_determinism.py`).** Same input twice → identical
  output. Trivial, but it's the product's whole claim, so assert it.
- **N3 — MCP transport.** Confirm the server exposes the tool and returns well-formed
  JSON over stdio, using a minimal client or the MCP inspector — **not** the agent.
  Separates protocol bugs from logic bugs.
- **N4 — Agent A/B (the demo).** Two Claude Code sessions, with and without the tool,
  same prompt. Run last, on a curated case.

Held-out format (`data/heldout.json`):

```json
[
  {"query_code": "def parse(s):\n  return datetime.fromisoformat(s)",
   "expected_match": "parse_iso_date", "is_duplicate": true},
  {"query_code": "def add(a, b): return a + b",
   "expected_match": null, "is_duplicate": false}
]
```

Agent A/B demo — three gotchas that decide whether it works:

1. **Plant the duplicates yourself** in `data/seed_repo` (don't grab a random OSS repo).
   You control exactly what's duplicated → reliable demo + it doubles as ground truth.
2. **The agent does NOT call tools on its own — instruct it.** In the seed repo's own
   CLAUDE.md (or the prompt), tell it: "before writing a new function, call
   `find_similar_function` with the code you intend to write; if it returns a duplicate,
   reuse the import instead of rewriting." The real contrast is *instructed agent with the
   tool available* vs *agent without the tool*.
3. **With** = `claude mcp add ... radar`. **Without** = run in a directory where that MCP
   isn't configured (or `claude mcp remove radar`). Same prompt, same instruction.

Order: make N0–N3 pass first, then run N4 on the curated case and record the backup video.

## Conventions and invariants — do not break

- **Determinism (of Radar's output).** The retrieval path is reproducible: same input
  → same candidate + score. No randomness, no network calls, **no LLM inside Radar**.
  The duplicate *judgment* now lives in the agent (non-deterministic by design); a
  deterministic CI gate would re-add a high-precision threshold on top of the retriever.
- **No LLM in Radar's hot path.** `summary`, `import_statement` and `source_code` are
  precomputed/stored at index time; Radar only embeds + searches + applies the floor.
- **Offline vs online split.** Indexing is offline; the online query never reindexes.
- **Recall floor, not a precision threshold.** `RETRIEVAL_FLOOR` is server-side and
  deliberately low: it decides only *what to surface*, not what counts as a duplicate.
  Over-surfacing is cheap (the agent reads the source and rejects it); a missed
  candidate is not recoverable. The agent is the precision stage.
- **`match_id` identifies the pair** (query ↔ candidate), not just the candidate.
- **MCP stdio hygiene.** The server must write **only MCP protocol to stdout**. All
  logging goes to **stderr**. A stray `print()` to stdout corrupts the stdio transport —
  this is the #1 "connects but doesn't respond" bug.
- **Adapters stay thin.** All logic lives in `engine/`.

## MVP scope (8-hour hackathon)

**In:** Java only · single seeded repo · offline index · `find_similar_function` ·
CLI · MCP stdio server · before/after agent demo · the "determinism cherry" (run the
same check twice → identical result) · a real precision/recall number from the held-out set.

**Out — describe in the pitch, do NOT build:** human-in-the-loop / accept-reject ·
async pipelines · a real CI GitHub Action · the 3D graph visualizer · fine-tuning ·
multi-language · the optional LLM rerank.

## Build order (de-risk the demo)

The two things most likely to blow up late are the **MCP↔client connection** and the
**recall quality (false positives)**. Attack both early.

0. **Setup (~45m, together):** skeleton, deps, freeze the contract + function-record
   shape, confirm the embedder embeds a string on CPU.
1. **Engine (biggest):** extract → normalize → embed all → FAISS + metadata → query
   function. Test with N0 + the eval. Leave time to calibrate the threshold (N1).
2. **MCP smoke test (early, in parallel):** stand up a stdio server with a dummy tool,
   connect Claude Code / Cursor, confirm the agent calls it — before the engine is done.
3. **Wire the real engine into the MCP.**
4. **Demo:** polish the before/after (N4), the determinism cherry, compute the number.
5. **Freeze + safety net:** rehearse, record a backup video of the working demo.

**Degraded-but-dignified fallback:** if the MCP↔client chain isn't alive in time, the
demo is the **CLI** showing a match + its import + the deterministic gate run twice.
That still proves recall and reproducibility.

## Don'ts

- Don't put an LLM in the query critical path.
- Don't change the contract after T0 without telling everyone.
- Don't reindex on query.
- Don't print to stdout in the MCP server — logs go to stderr.
- Don't "upgrade" the embedder to jina-embeddings-v4 (3.8B; won't run on CPU).
- Don't validate recall quality through the agent — use the held-out set.
- Don't build the human loop, the async pipeline, or the 3D graph for the hackathon.
- Don't let detection logic leak into an adapter.
