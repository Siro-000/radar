import json
import sys


def cmd_parse(args: list[str]) -> None:
    if not args:
        print("Usage: radar parse <repo_path>")
        sys.exit(1)
    from radar.parser import parse_repo
    functions = parse_repo(args[0])
    print(json.dumps([f.model_dump() for f in functions], indent=2))


def cmd_serve(args: list[str]) -> None:
    import argparse
    parser = argparse.ArgumentParser(prog="radar serve")
    parser.add_argument("--repo", required=True, help="Path to the repository to index")
    parser.add_argument("--index-path", default=None, help="Path to persist the vector index")
    parsed = parser.parse_args(args)

    from radar.server import load_server, mcp
    print(f"Indexing {parsed.repo}...")
    load_server(parsed.repo, persist_path=parsed.index_path)
    print("Index ready. Starting MCP server (stdio)...")
    mcp.run(transport="stdio")


COMMANDS = {"parse": cmd_parse, "serve": cmd_serve}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: radar <command> [options]")
        print(f"Commands: {', '.join(COMMANDS)}")
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
