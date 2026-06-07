#!/usr/bin/env bash
#
# Prepara el workspace con Radar para la demo:
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
DIR_CON="$PRUEBA_DIR/con"

# 1. Genera el repo
echo ">> [1/3] Generando repo en $DIR_CON ..." >&2
rm -rf "$PRUEBA_DIR"
"$UV" run --project "$RADAR_ROOT" python3 "$DEMO_DIR/gen_test_repo.py" "$DIR_CON" >&2

# 2. Inyecta el CLAUDE.md
echo ">> [2/3] Configurando CLAUDE.md ..." >&2
cp "$DEMO_DIR/workspace_CLAUDE_con.md" "$DIR_CON/CLAUDE.md"

# 3. Construye el índice Radar
echo ">> [3/3] Indexando el repo ..." >&2
"$UV" run --project "$RADAR_ROOT" radar index \
  --repo "$DIR_CON" --index-path "$DIR_CON/.radar-index" >&2

# Genera la config MCP para el script wrapper
mkdir -p "$PRUEBA_DIR"
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
echo ">> Listo. Workspace preparado:" >&2
echo "     $DIR_CON  (con Radar)" >&2
echo "" >&2
echo ">> Corré la demo con:" >&2
echo "     bash demo/arm_con.sh" >&2
