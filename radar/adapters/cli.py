"""
Radar CLI — thin wrapper over the engine.

Subcommands:
    radar index  --repo PATH --index-path PATH      build the offline index
    radar query  CODE        --index-path PATH      one-shot similarity query (JSON)
    radar serve  --repo PATH --index-path PATH      run the MCP stdio server

`serve` is what .mcp.json invokes for Claude Code. `query` is the dev/demo fallback.
All adapter logic stays thin: detection and thresholds live in the engine.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_INDEX_PATH = ".radar-index"


def _cmd_index(args: argparse.Namespace) -> int:
    from radar.engine.build import build_index

    index = build_index(args.repo, args.index_path)
    print(f"Indexed {index.count()} functions -> {args.index_path}", file=sys.stderr)
    return 0


def _cmd_query(args: argparse.Namespace) -> int:
    from radar.engine.engine import find_similar_function, load_index

    if args.file:
        code = Path(args.file).read_text()
    elif args.code:
        code = args.code
    else:
        code = sys.stdin.read()

    if not Path(args.index_path, "index.faiss").exists():
        print(
            f"error: no index at '{args.index_path}'. Run `radar index` first.",
            file=sys.stderr,
        )
        return 1

    load_index(args.index_path)
    result = find_similar_function(code=code, language=args.language, top_k=args.top_k)
    # CLI: JSON to stdout is intended here (this is not the MCP transport).
    print(json.dumps(result.model_dump(), indent=2))
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    from radar.adapters.mcp_server import run_server

    run_server(repo=args.repo, index_path=args.index_path)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="radar", description="Radar semantic recall layer.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="build the offline index for a repo")
    p_index.add_argument("--repo", default=".", help="repo root to index (default: .)")
    p_index.add_argument("--index-path", default=DEFAULT_INDEX_PATH, help="where to write the index")
    p_index.set_defaults(func=_cmd_index)

    p_query = sub.add_parser("query", help="one-shot similarity query (prints JSON)")
    p_query.add_argument("code", nargs="?", help="function source; omit to read from --file or stdin")
    p_query.add_argument("--file", help="read the function source from a file")
    p_query.add_argument("--language", default="java")
    p_query.add_argument("--top-k", type=int, default=3)
    p_query.add_argument("--index-path", default=DEFAULT_INDEX_PATH)
    p_query.set_defaults(func=_cmd_query)

    p_serve = sub.add_parser("serve", help="run the MCP stdio server")
    p_serve.add_argument("--repo", default=None, help="repo to index on startup if no index exists (optional)")
    p_serve.add_argument("--index-path", default=DEFAULT_INDEX_PATH)
    p_serve.set_defaults(func=_cmd_serve)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
