#!/usr/bin/env bash
# Corre la tarea SIN Radar y muestra los tokens gastados al final.
# Requiere haber corrido `bash demo/run_prueba.sh` primero.
set -euo pipefail

RADAR_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR_SIN="$RADAR_ROOT/../prueba/sin"
MODEL="${RADAR_DEMO_MODEL:-sonnet}"

[ -d "$DIR_SIN" ] || { echo "error: corré primero: bash demo/run_prueba.sh" >&2; exit 1; }

cd "$DIR_SIN"
claude -p "$(cat "$RADAR_ROOT/demo/task_prueba.md")" \
  --model "$MODEL" \
  --strict-mcp-config --mcp-config "$RADAR_ROOT/../prueba/empty.mcp.json" \
  --permission-mode acceptEdits \
  --allowedTools "Edit Write" \
  --disallowedTools "Read Glob Grep Bash Task WebFetch WebSearch" \
  --verbose --output-format stream-json \
  | python3 "$RADAR_ROOT/demo/show_tokens.py"
