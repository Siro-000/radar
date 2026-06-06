# Story RADAR-009: adapters/mcp_server.py — MCP stdio server

**Status:** Draft

## Story

As an AI agent (Claude Code, Cursor), I need to access `find_similar_function` as an MCP tool over stdio, so that I can query it automatically before writing any new function.

## Acceptance Criteria

1. [ ] The server exposes exactly one tool: `find_similar_function` with the frozen contract schema
2. [ ] Accepts `--repo <path>` to build the index on startup, or `--index-path <path>` to load a prebuilt index
3. [ ] All logging goes to **stderr** — stdout contains only MCP protocol
4. [ ] The tool response matches the full frozen contract (query_id, verdict, matches with all fields)
5. [ ] Server starts in < 5 seconds when loading a prebuilt index
6. [ ] `claude mcp add --transport stdio radar -- radar serve --repo <path>` connects without errors
7. [ ] A stray `print()` to stdout does not exist anywhere in this file

## Tasks

- [ ] 1. Use `mcp.server.fastmcp.FastMCP` to define and register the tool
- [ ] 2. Parse `--repo` / `--index-path` args before starting the server
- [ ] 3. Replace all potential `print()` calls with `logging` directed to stderr
- [ ] 4. Write the tool description: `"Call before writing any new function. Returns existing functions that do the same thing, with import statements for reuse."`
- [ ] 5. Verify N3: use a minimal MCP client or the MCP inspector to call the tool and confirm well-formed JSON response

## Dev Notes

The #1 "connects but doesn't respond" bug is a stray `print()` to stdout corrupting the stdio transport. Audit carefully.

### Registration command

```bash
claude mcp add --transport stdio radar -- /abs/path/.venv/bin/radar serve --repo /abs/path/to/repo
claude mcp list        # verify registration
# inside a session: /mcp shows live status
```

Use `--scope project` to write `.mcp.json` (committable, shared with the team).

## Dependencies

- RADAR-006: `engine.find_similar_function`
