#!/usr/bin/env bash
#
# Prepara dos workspaces con el mismo código para probar Radar:
#   ../prueba/sin  -> sin MCP Radar
#   ../prueba/con  -> con Radar indexado
#
# Env:
#   RADAR_DEMO_MODEL   modelo (default: sonnet)
#
set -euo pipefail

RADAR_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEMO_DIR="$RADAR_ROOT/demo"
UV="$(command -v uv || echo /opt/homebrew/bin/uv)"
PRUEBA_DIR="$RADAR_ROOT/../prueba"
DIR_SIN="$PRUEBA_DIR/sin"
DIR_CON="$PRUEBA_DIR/con"

# 1. Genera el mismo repo en los dos directorios
echo ">> [1/3] Generando repos en $PRUEBA_DIR ..." >&2
rm -rf "$PRUEBA_DIR"
"$UV" run --project "$RADAR_ROOT" python3 "$DEMO_DIR/gen_test_repo.py" "$DIR_SIN" "$DIR_CON" >&2

# 2. Inyecta el CLAUDE.md de cada brazo y bloquea herramientas en sin/
echo ">> [2/3] Configurando CLAUDE.md y permisos de cada brazo ..." >&2
cp "$DEMO_DIR/workspace_CLAUDE_sin.md" "$DIR_SIN/CLAUDE.md"
cp "$DEMO_DIR/workspace_CLAUDE_con.md" "$DIR_CON/CLAUDE.md"

mkdir -p "$DIR_SIN/.claude"
cat > "$DIR_SIN/.claude/settings.json" <<'EOF'
{
  "permissions": {
    "deny": ["Read", "Glob", "Grep", "Bash", "Task", "WebFetch", "WebSearch"]
  }
}
EOF

# 3. Construye el índice Radar sobre el brazo CON
echo ">> [3/3] Indexando el repo para el brazo CON ..." >&2
"$UV" run --project "$RADAR_ROOT" radar index \
  --repo "$DIR_CON" --index-path "$DIR_CON/.radar-index" >&2

# Genera las configs MCP para los scripts wrapper
mkdir -p "$PRUEBA_DIR"
printf '{"mcpServers":{}}\n' > "$PRUEBA_DIR/empty.mcp.json"
cat > "$PRUEBA_DIR/radar.mcp.json" <<EOF
{
  "mcpServers": {
    "radar": {
      "command": "$UV",
      "args": ["run", "--project", "$RADAR_ROOT", "radar", "serve",
               "--repo", "$DIR_CON",
               "--index-path", "$DIR_CON/.radar-index"]
    }
  }
}
EOF

echo "" >&2
echo ">> Listo. Workspaces preparados:" >&2
echo "     $DIR_SIN  (sin Radar)" >&2
echo "     $DIR_CON  (con Radar)" >&2
echo "" >&2
echo ">> Corré cada brazo con:" >&2
echo "     bash demo/arm_sin.sh   # sin Radar" >&2
echo "     bash demo/arm_con.sh   # con Radar" >&2
