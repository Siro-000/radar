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
- **Embedder** — `jina-embeddings-v2-base-code`. Wrap it behind `engine/embed.py` so the rest of the code never
  imports the model directly — swapping models must be a one-file change.
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

# eval: precision/recall against the held-out set
python -m radar.eval.eval
```

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
   shape, lock the embedder, confirm it embeds a string on CPU.
1. **Engine (biggest):** extract → normalize → embed all → FAISS + metadata → query
   function. Test with a flat script. Leave time to calibrate the threshold.
2. **MCP smoke test (early, in parallel):** stand up a stdio server with a dummy tool,
   connect Claude Code / Cursor, confirm the agent calls it — before the engine is done.
3. **Wire the real engine into the MCP.**
4. **Demo:** polish the before/after, the determinism cherry, compute the number.
5. **Freeze + safety net:** rehearse, record a backup video of the working demo.

**Degraded-but-dignified fallback:** if the MCP↔client chain isn't alive in time, the
demo is the **CLI** showing a match + its import + the deterministic gate run twice.
That still proves recall and reproducibility.

## Don'ts

- Don't put an LLM in the query critical path.
- Don't change the contract after T0 without telling everyone.
- Don't reindex on query.
- Don't build the human loop, the async pipeline, or the 3D graph for the hackathon.
- Don't let detection logic leak into an adapter.

