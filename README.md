# Radar

Semantic recall layer that prevents AI agents from duplicating logic that already exists in your codebase.

## What it does

AI agents generate code without seeing the full codebase they're working on. The measurable result: they rewrite logic that already exists instead of reusing it, inflating repositories with duplication that then needs to be maintained.

Radar understands *what* each function in a repository does — not how it's written — and exposes that knowledge where code decisions are made.

## How it works

Funnel architecture (retrieve-then-rerank):

1. **Vector lookup** — reduces millions of functions to a handful of candidates in milliseconds, deterministically
2. **LLM rerank** (optional) — judges whether candidates are real duplicates

## Surfaces

- **CI gate** — blocks PRs with detected duplication
- **IDE / agent integration** — before generating a function, checks if the logic already exists

## Status

Work in progress.

---

## Using Radar on any local repository

Run the setup script — it installs dependencies and registers the MCP server in one step:

```bash
bash setup.sh
```

The script asks whether you want to register Radar **globally** (all projects) or only for **one specific repo**.

### Option A — Global (any project)

The script registers Radar in Claude Code with `claude mcp add --global`. Then, for each project you want to use it in, add two lines to its `CLAUDE.md`:

```markdown
On startup, call `index_repo` with the absolute path of this project.
Before implementing any new function, call `find_similar_function`.
```

The agent indexes the repo when the session starts and searches for duplicates before writing.

### Option B — Specific repo

The script writes a `.mcp.json` at the project root pointing to that repo. The server indexes automatically on startup — just add this line to the project's `CLAUDE.md`:

```markdown
Before implementing any new function, call `find_similar_function`.
```

### Notes

- After setup, verify the connection with `claude mcp list`.
- The global index is stored at `~/.radar-index`. When switching repos, the agent calls `index_repo` again to rebuild it.
- If the repo changes (new functions added), call `index_repo` again.

---

## Uso en cualquier repositorio (local)

Corré el script de setup — instala dependencias y registra el servidor MCP en un solo paso:

```bash
bash setup.sh
```

El script te pregunta si querés registrarlo **globalmente** (disponible en todos tus proyectos) o solo en **un repo específico**.

### Opción A — Global (cualquier proyecto)

El script registra Radar en Claude Code con `claude mcp add --global`. Una vez hecho, en cada proyecto que quieras usarlo agregá dos líneas al `CLAUDE.md`:

```markdown
Al iniciar, llamá `index_repo` con la ruta absoluta de este proyecto.
Antes de implementar cualquier función nueva, llamá `find_similar_function`.
```

El agente indexa el repo al arrancar la sesión y busca duplicados antes de escribir.

### Opción B — Repo específico

El script escribe un `.mcp.json` en la raíz del proyecto apuntando a ese repo. El servidor indexa automáticamente al arrancar — solo agregá esta línea al `CLAUDE.md` del proyecto:

```markdown
Antes de implementar cualquier función nueva, llamá `find_similar_function`.
```

### Notas

- Al terminar el setup, verificá la conexión con `claude mcp list`.
- El índice global se guarda en `~/.radar-index`. Si cambiás de repo, el agente llama `index_repo` de nuevo para reconstruirlo.
- Si el repo cambia (agregaste funciones), volvé a llamar `index_repo`.
