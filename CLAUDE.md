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

## The contract — FROZEN

This is the interface everything depends on. **Do not change the signature or the
field names without telling the whole team.** Adapters, the engine, and the eval all
agree on exactly this.

```
find_similar_function({
  code: string,        // required: the function the agent is about to write
  language?: string,   // optional, default inferred ("python")
  intent?: string,     // optional: NL description of what it's trying to do
  top_k?: int          // optional, default 3
}) -> {
  query_id: string,                            // event id (telemetry)
  verdict: "duplicate" | "similar" | "novel",  // decided server-side vs threshold
  matches: [
    {
      match_id: string,         // stable id of the PAIR (query <-> candidate)
      name: string,             // "parse_dates"
      signature: string,        // "def parse_dates(s: str, tz: str = 'UTC') -> datetime"
      location: string,         // "utils/dates.py:42-58"
      summary: string,          // 1 line, precomputed at index time (no LLM)
      import_statement: string, // "from utils.dates import parse_dates"  <- the actionable part
      similarity: float         // 0.0–1.0
    }
  ]
}
```

- `verdict` is decided server-side: high score → `duplicate`, mid band → `similar`,
  below → `novel`.
- The **threshold is server-side config**, never a tool parameter the agent can set
  or loosen.
- The response must be **actionable**: `import_statement` is what makes the agent
  reuse instead of regenerate. Returning "duplicate: 0.9" alone is not enough.

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

> Fill these in as the code lands; keep this section current.

```bash
# install
pip install -e .

# build the index for a repo (offline)
python -m radar.engine.index build ./radar/data/seed_repo

# query via CLI (dev + demo fallback)
python -m radar.adapters.cli "def my_func(...): ..."

# run the MCP server (stdio)
python -m radar.adapters.mcp_server

# run tests (N0/N2 + contract shape)
pytest

# eval: precision/recall against the held-out set (N1 — calibrate the threshold here)
python -m radar.eval.eval

# register the MCP server with Claude Code for the agent demo (use an ABSOLUTE path)
claude mcp add --transport stdio radar -- python /abs/path/to/radar/adapters/mcp_server.py
claude mcp list          # verify it registered; inside a session, /mcp shows status
# --scope project writes .mcp.json (committable, shared with the team)
```

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

- **Determinism.** The query path must be reproducible: same input → same output.
  No randomness, no network calls, **no LLM in the query critical path**. This is the
  product's whole differentiator (it's what enables a CI gate).
- **No LLM in the hot path.** `summary` and `import_statement` are precomputed at index
  time. An optional LLM rerank over the top candidates is out of MVP scope.
- **Offline vs online split.** Indexing is offline; the online query never reindexes.
- **Threshold is server-side**, calibrated offline for **precision over recall** —
  a false positive (agent reuses something it shouldn't) introduces a subtle bug, and
  false positives are the #1 product risk. Better to miss a duplicate than flag a fake one.
- **`match_id` identifies the pair** (query ↔ candidate), not just the candidate.
- **MCP stdio hygiene.** The server must write **only MCP protocol to stdout**. All
  logging goes to **stderr**. A stray `print()` to stdout corrupts the stdio transport —
  this is the #1 "connects but doesn't respond" bug.
- **Adapters stay thin.** All logic lives in `engine/`.

## MVP scope (8-hour hackathon)

**In:** Python only · single seeded repo · offline index · `find_similar_function` ·
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
