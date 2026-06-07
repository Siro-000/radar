#!/usr/bin/env bash
#
# Radar A/B/C demo: run the SAME coding task across THREE arms and compare what
# the agent produced + how many tokens it spent.
#
#   without   -> baseline. Same CLAUDE.md as `with` (told to reuse) but no Radar
#                tool and (controlled mode) no repo search -> reimplements.
#   prompted  -> NO Radar tool, but a CLAUDE.md that explicitly orders an
#                EXHAUSTIVE, synonym-aware repository search to avoid duplicates,
#                AND always gets Read/Glob/Grep. Tests whether a strong prompt +
#                lexical search can substitute for semantic retrieval.
#   with      -> the Radar MCP tool + a CLAUDE.md telling it to call
#                find_similar_function -> finds the duplicate semantically, reuses.
#
# Throwaway copies of the source repo live under $RUN_DIR; data/seed_repo is never
# mutated. --strict-mcp-config keeps the non-Radar arms from seeing any globally
# registered server.
#
# Env overrides:
#   RADAR_DEMO_MODEL    model alias (default: sonnet)
#   RADAR_DEMO_REPO     source repo to copy (default: data/seed_repo)
#   RADAR_DEMO_RUNDIR   run directory (default: /tmp/radar-demo-run)
#   RADAR_DEMO_FAIR=1   also give `without`/`with` full repo search (Read/Glob/Grep)
#   RADAR_DEMO_YOLO=1   use --dangerously-skip-permissions instead of the default
#                       acceptEdits + explicit tool allowlist
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

# Each arm gets the right CLAUDE.md. `without` and `with` share the Radar-style
# "reuse, call find_similar_function" file so the ONLY difference between them is
# tool access. `prompted` gets the exhaustive-search file (no tool mention).
cp -R "$SRC_REPO/." "$RUN_DIR/without/";  cp "$DEMO_DIR/workspace_CLAUDE.md"          "$RUN_DIR/without/CLAUDE.md"
cp -R "$SRC_REPO/." "$RUN_DIR/prompted/"; cp "$DEMO_DIR/workspace_CLAUDE_prompted.md" "$RUN_DIR/prompted/CLAUDE.md"
cp -R "$SRC_REPO/." "$RUN_DIR/with/";     cp "$DEMO_DIR/workspace_CLAUDE.md"          "$RUN_DIR/with/CLAUDE.md"

echo ">> Building the Radar index over the WITH workspace" >&2
"$UV" run --project "$RADAR_ROOT" radar index \
  --repo "$RUN_DIR/with" --index-path "$RUN_DIR/with/.radar-index" >&2

# MCP configs: an empty one for the non-Radar arms, the radar one for WITH.
EMPTY_MCP="$RUN_DIR/empty.mcp.json"
printf '{"mcpServers":{}}\n' > "$EMPTY_MCP"
RADAR_MCP="$RUN_DIR/radar.mcp.json"
cat > "$RADAR_MCP" <<EOF
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

# Tool policy. SEARCH = repo-discovery tools; EXEC_DENY = things we never want the
# autonomous demo agent to do. The variable under test is the DISCOVERY mechanism
# each arm is handed:
#   without  : (controlled) no search, no tool   |  (fair) search
#   prompted : ALWAYS search (its whole point), never Radar
#   with     : Radar tool                        |  (fair) + search
# Arrays are built with += of explicit values only (no expansion of a possibly
# empty array) so this stays safe under `set -u` on bash 3.2 (macOS default).
SEARCH="Read Glob Grep"
EXEC_DENY="Bash Task WebFetch WebSearch"

run_arm() {
  # run_arm <arm> <allowed-tools> <disallowed-tools> <mcp-config-path>
  local arm="$1" allowed="$2" disallowed="$3" mcp_cfg="$4"
  local perm=()
  if [ "${RADAR_DEMO_YOLO:-0}" = "1" ]; then
    perm=(--dangerously-skip-permissions)
  else
    perm=(--permission-mode acceptEdits --allowedTools "$allowed")
    [ -n "$disallowed" ] && perm+=(--disallowedTools "$disallowed")
  fi
  echo "============================================================" >&2
  echo "  ARM — $arm" >&2
  echo "============================================================" >&2
  # stream-json (one JSON object per line) lets compare.py detect *structured*
  # tool calls — a tool_use block, not a text mention of the tool's name.
  ( cd "$RUN_DIR/$arm" && claude -p "$TASK" \
      --model "$MODEL" \
      --strict-mcp-config --mcp-config "$mcp_cfg" \
      "${perm[@]}" \
      --verbose --output-format stream-json \
      > "$RUN_DIR/$arm.jsonl" 2> "$RUN_DIR/$arm.log" ) \
    || echo ">> ($arm arm exited non-zero; see $RUN_DIR/$arm.log)" >&2
}

if [ "${RADAR_DEMO_FAIR:-0}" = "1" ]; then
  run_arm without  "$SEARCH Edit Write"                                   "$EXEC_DENY"         "$EMPTY_MCP"
  run_arm prompted "$SEARCH Edit Write"                                   "$EXEC_DENY"         "$EMPTY_MCP"
  run_arm with     "$SEARCH Edit Write mcp__radar__find_similar_function" "$EXEC_DENY"         "$RADAR_MCP"
else
  run_arm without  "Edit Write"                                           "$SEARCH $EXEC_DENY" "$EMPTY_MCP"
  run_arm prompted "$SEARCH Edit Write"                                   "$EXEC_DENY"         "$EMPTY_MCP"
  run_arm with     "Edit Write mcp__radar__find_similar_function"         "$SEARCH $EXEC_DENY" "$RADAR_MCP"
fi

echo >&2
python3 "$DEMO_DIR/compare.py" "$RUN_DIR"
