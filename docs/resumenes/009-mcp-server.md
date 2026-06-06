# RADAR-009: adapters/mcp_server.py — MCP stdio server

Expone `find_similar_function` como una tool MCP sobre stdio para que Claude Code, Cursor u otro agente pueda llamarla. Es un wrapper fino de 30 líneas sobre el engine. La regla crítica: absolutamente nada va a stdout salvo el protocolo MCP — un `print()` accidental rompe la conexión. Acepta `--repo` para indexar al arrancar o `--index-path` para cargar un índice preexistente.
