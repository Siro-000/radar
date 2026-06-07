"""
RAN ONCE PER REPOSITORY (offline indexing).

Thin composition of engine primitives: extract -> embed -> build FAISS store.
No detection/threshold logic lives here (that belongs to engine.py); this only
wires together pure engine calls so adapters never reimplement the pipeline.
"""

from __future__ import annotations

import sys
from pathlib import Path

from radar.engine.embed import embed_batch
from radar.engine.extract import parse_repo
from radar.engine.index import Index, build


def build_index(repo_path: Path | str, index_path: Path | str) -> Index:
    """Index every Java function under ``repo_path`` into ``index_path``.

    Embeds the raw function source (identical to the query path in engine.py)
    so the offline index and the online query live in the same vector space.
    Returns the in-memory :class:`Index`; also persists it to disk.
    """
    repo_path = Path(repo_path)
    functions = parse_repo(repo_path)
    print(
        f"[radar] extracted {len(functions)} functions from {repo_path}",
        file=sys.stderr,
        flush=True,
    )

    embeddings = embed_batch(functions)
    print(f"[radar] embedded {len(embeddings)} functions", file=sys.stderr, flush=True)

    index = build(functions, embeddings, index_path)
    print(f"[radar] wrote index to {index_path}", file=sys.stderr, flush=True)
    return index
