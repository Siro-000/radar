#!/usr/bin/env bash
# Corre la tarea CON Radar y muestra los tokens gastados al final.
# Requiere haber corrido `bash demo/run_prueba.sh` primero.
set -euo pipefail

RADAR_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR_CON="$RADAR_ROOT/../prueba/con"
MODEL="${RADAR_DEMO_MODEL:-sonnet}"

[ -d "$DIR_CON" ] || { echo "error: corré primero: bash demo/run_prueba.sh" >&2; exit 1; }

cd "$DIR_CON"

TASK="$(cat "$RADAR_ROOT/demo/task_prueba.md")"
PROMPT="MANDATORY: Before writing any new function, call find_similar_function with the exact code you intend to write. If the result is 'candidate', reuse the existing function via import instead of reimplementing it.

$TASK"

claude -p "$PROMPT" \
  --model "$MODEL" \
  --strict-mcp-config --mcp-config "$RADAR_ROOT/../prueba/radar.mcp.json" \
  --permission-mode acceptEdits \
  --allowedTools "Edit Write mcp__radar__find_similar_function mcp__radar__index_repo" \
  --disallowedTools "Read Glob Grep Bash Task WebFetch WebSearch" \
  --verbose --output-format stream-json \
  | python3 "$RADAR_ROOT/demo/show_tokens.py"
