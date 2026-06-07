#!/usr/bin/env bash
#
# Radar A/B demo: run the SAME coding task twice — once WITHOUT the Radar MCP
# tool and once WITH it — and compare what the agent produced.
#
#   WITHOUT  ->  agent reimplements logic that already exists (duplication)
#   WITH     ->  agent calls find_similar_function, sees "duplicate", reuses the import
#
# The runs happen in throwaway copies of the seed repo under $RUN_DIR, so the
# canonical data/seed_repo is never mutated. We use --strict-mcp-config so the
# WITHOUT arm cannot accidentally see a globally-registered radar server.
#
# Env overrides:
#   RADAR_DEMO_MODEL    model alias (default: sonnet)
#   RADAR_DEMO_RUNDIR   run directory (default: /tmp/radar-demo-run)
#   RADAR_DEMO_YOLO=1   use --dangerously-skip-permissions instead of the
#                       default acceptEdits + explicit tool allowlist
set -euo pipefail

RADAR_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEMO_DIR="$RADAR_ROOT/demo"
UV="$(command -v uv || echo /opt/homebrew/bin/uv)"
MODEL="${RADAR_DEMO_MODEL:-sonnet}"
RUN_DIR="${RADAR_DEMO_RUNDIR:-/tmp/radar-demo-run}"

TASK="$(cat "$DEMO_DIR/task.md")"
SRC_REPO="${RADAR_DEMO_REPO:-$RADAR_ROOT/data/seed_repo}"
[ -d "$SRC_REPO" ] || { echo "error: source repo not found: $SRC_REPO" >&2; exit 1; }

echo ">> Source repo: $SRC_REPO" >&2
echo ">> Preparing throwaway workspaces under $RUN_DIR" >&2
rm -rf "$RUN_DIR"
mkdir -p "$RUN_DIR"
for arm in without with; do
  cp -R "$SRC_REPO/." "$RUN_DIR/$arm/"
  cp "$DEMO_DIR/workspace_CLAUDE.md" "$RUN_DIR/$arm/CLAUDE.md"
done

echo ">> Building the Radar index over the WITH workspace" >&2
"$UV" run --project "$RADAR_ROOT" radar index \
  --repo "$RUN_DIR/with" --index-path "$RUN_DIR/with/.radar-index" >&2

# Radar MCP config for the WITH arm (absolute paths; serve loads the prebuilt index)
MCP_CONFIG="$RUN_DIR/radar.mcp.json"
cat > "$MCP_CONFIG" <<EOF
{
  "mcpServers": {
    "radar": {
      "command": "$UV",
      "args": ["run", "--project", "$RADAR_ROOT", "radar", "serve",
               "--repo", "$RUN_DIR/with", "--index-path", "$RUN_DIR/with/.radar-index"]
    }
  }
}
EOF

# Tool strategy. We isolate ONE variable: access to Radar's semantic recall.
#
#   default (controlled): neither arm browses the repo — only Write/Edit. This
#       models a large codebase the agent can't read exhaustively (or a
#       generate-first workflow). The WITH arm additionally gets the radar tool,
#       so it is the ONLY discovery path that differs between the two.
#   RADAR_DEMO_FAIR=1   : give both arms full repo search (Read/Glob/Grep) too.
#       On a small repo a strong agent often finds the duplicate by reading, so
#       expect the contrast to show up as efficiency (tokens/turns), not outcome.
# In controlled mode we must DENY the repo-discovery tools — acceptEdits otherwise
# auto-allows read-only tools (Read/Grep/Glob), and a strong agent will just read
# the repo and find the duplicate on its own. Denying them leaves Radar as the WITH
# arm's only discovery path. FAIR mode denies nothing.
# Arrays are built with += of explicit values only (no expansion of a possibly
# empty array) so this stays safe under `set -u` on bash 3.2 (macOS default).
if [ "${RADAR_DEMO_FAIR:-0}" = "1" ]; then
  BASE_TOOLS="Read Glob Grep Edit Write"
else
  BASE_TOOLS="Edit Write"
fi

# Base permission flags shared by both arms.
if [ "${RADAR_DEMO_YOLO:-0}" = "1" ]; then
  PERM_WITHOUT=(--dangerously-skip-permissions)
  PERM_WITH=(--dangerously-skip-permissions)
else
  PERM_WITHOUT=(--permission-mode acceptEdits --allowedTools "$BASE_TOOLS")
  PERM_WITH=(--permission-mode acceptEdits --allowedTools "$BASE_TOOLS mcp__radar__find_similar_function")
fi

# Controlled mode: DENY the repo-discovery tools. Otherwise acceptEdits auto-allows
# read-only tools and a strong agent just reads the repo and finds the duplicate on
# its own. Denying them leaves Radar as the WITH arm's only discovery path. FAIR
# mode denies nothing (both arms may explore freely).
if [ "${RADAR_DEMO_FAIR:-0}" != "1" ]; then
  PERM_WITHOUT+=(--disallowedTools "Read Glob Grep Bash Task WebFetch WebSearch")
  PERM_WITH+=(--disallowedTools "Read Glob Grep Bash Task WebFetch WebSearch")
fi

# stream-json (one JSON object per line) lets compare.py detect *structured* tool
# calls — a tool_use block, not a text mention of the tool's name.
echo "============================================================" >&2
echo "  ARM A — WITHOUT Radar" >&2
echo "============================================================" >&2
( cd "$RUN_DIR/without" && claude -p "$TASK" \
    --model "$MODEL" \
    --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
    "${PERM_WITHOUT[@]}" \
    --verbose --output-format stream-json > "$RUN_DIR/without.jsonl" 2> "$RUN_DIR/without.log" ) \
  || echo ">> (without arm exited non-zero; see $RUN_DIR/without.log)" >&2

echo "============================================================" >&2
echo "  ARM B — WITH Radar" >&2
echo "============================================================" >&2
( cd "$RUN_DIR/with" && claude -p "$TASK" \
    --model "$MODEL" \
    --strict-mcp-config --mcp-config "$MCP_CONFIG" \
    "${PERM_WITH[@]}" \
    --verbose --output-format stream-json > "$RUN_DIR/with.jsonl" 2> "$RUN_DIR/with.log" ) \
  || echo ">> (with arm exited non-zero; see $RUN_DIR/with.log)" >&2

echo >&2
python3 "$DEMO_DIR/compare.py" "$RUN_DIR"
