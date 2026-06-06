import json
import sys

from radar.parser import parse_repo


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "parse":
        print("Usage: radar parse <repo_path>")
        sys.exit(1)

    repo_path = sys.argv[2]
    functions = parse_repo(repo_path)
    print(json.dumps([f.model_dump() for f in functions], indent=2))


if __name__ == "__main__":
    main()
