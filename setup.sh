#!/usr/bin/env bash
set -e

RADAR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "=== Radar setup ==="
echo ""

# Step 1: install dependencies
echo "[ 1/2 ] Installing dependencies..."
cd "$RADAR_DIR"
uv sync
echo "       Done."
echo ""

# Step 2: register the MCP server
# Accept choice as argument: --global (or 1) / --project PATH (or 2)
case "${1:-}" in
  --global|1) choice=1 ;;
  --project|2) choice=2; project_path="${2:-}" ;;
  *)
    echo "[ 2/2 ] How do you want to register the MCP server?"
    echo ""
    echo "  1) Global  — available in every project you open in Claude Code"
    echo "  2) Project — only available in one specific repo (writes .mcp.json there)"
    echo ""
    read -rp "Choose [1/2]: " choice
    ;;
esac

case "$choice" in
  1)
    echo ""
    echo "Registering Radar globally..."
    claude mcp add -s user radar -- \
      uv --directory "$RADAR_DIR" run radar serve \
      --index-path "$HOME/.radar-index"
    echo ""
    echo "Done. Radar is now available in every Claude Code session."
    echo ""
    echo "Add these two lines to the CLAUDE.md of any project you want to use it in:"
    echo ""
    echo "  On startup, call \`index_repo\` with the absolute path of this project."
    echo "  Before implementing any new function, call \`find_similar_function\`."
    ;;
  2)
    echo ""
    if [[ -z "${project_path:-}" ]]; then
      read -rp "Absolute path to the project repo: " project_path
    fi
    if [[ ! -d "$project_path" ]]; then
      echo "Error: '$project_path' is not a directory." >&2
      exit 1
    fi
    mcp_file="$project_path/.mcp.json"
    cat > "$mcp_file" <<EOF
{
  "mcpServers": {
    "radar": {
      "command": "uv",
      "args": [
        "--directory", "$RADAR_DIR",
        "run", "radar", "serve",
        "--repo", ".",
        "--index-path", "$project_path/.radar-index"
      ]
    }
  }
}
EOF
    echo ""
    echo "Done. Written to $mcp_file"
    echo ""
    echo "The server will index '$project_path' automatically on first start."
    echo "Add this line to $project_path/CLAUDE.md:"
    echo ""
    echo "  Before implementing any new function, call \`find_similar_function\`."
    ;;
  *)
    echo "Invalid choice. Run the script again." >&2
    exit 1
    ;;
esac

echo ""
echo "Verify the connection with: claude mcp list"
echo ""
