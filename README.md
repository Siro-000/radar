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

The script registers Radar in Claude Code with `claude mcp add -s user`. Then, for each project you want to use it in, add two lines to its `CLAUDE.md`:

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

## Running the demo

Run both commands from the repo root (`radar/radar`).

### Step 1 — Build the workspace

```bash
bash demo/run_prueba.sh
```

Creates `../prueba/con/` with a realistic Java e-commerce repo (3 semantic duplicates planted), builds the Radar index inside it, and writes the MCP config at `../prueba/radar.mcp.json`. Takes ~30 seconds on first run while the embedder downloads.

### Step 2 — Run the agent

```bash
bash demo/arm_con.sh
```

Launches Claude headlessly in `../prueba/con` with Radar connected via the MCP config. The agent is instructed to call `find_similar_function` before writing any new function. Live output streams to your terminal; a token summary prints at the end:

```
==================================================
  TOKENS GASTADOS
==================================================
  turns            : 3
  input tokens     : 4,821
  cache read       : 12,043
  output tokens    : 287
  total tokens     : 17,151
  costo (USD)      : $0.0312
  tiempo           : 18.4s
==================================================
```

### What to look for

The task asks the agent to implement `calculateCommission(saleAmount, rate)` — percentage-on-top arithmetic. The repo already has two functions with that exact logic:

- `TaxCalculator.calculateTax(price, rate)` — same math, tax vocabulary
- `LevyEngine.applyLevy(amount, factor)` — same math, billing vocabulary, zero shared keywords

A keyword search finds neither. Radar finds both.

When it works: the agent calls `find_similar_function`, gets back the candidate with full source, recognises the match, and writes an import instead of reimplementing the arithmetic.

---
---

# Radar (Español)

Capa de recuperación semántica que previene que los agentes de IA dupliquen lógica que ya existe en el codebase.

## Qué hace

Los agentes de IA generan código sin ver el codebase completo en el que trabajan. El resultado medible: reescriben lógica que ya existe en lugar de reutilizarla, inflando los repositorios con duplicación que luego hay que mantener.

Radar entiende *qué* hace cada función de un repositorio — no cómo está escrita — y expone ese conocimiento donde se toman las decisiones de código.

## Cómo funciona

Arquitectura en embudo (recuperar y reordenar):

1. **Búsqueda vectorial** — reduce millones de funciones a un puñado de candidatos en milisegundos, de forma determinista
2. **Reordenamiento con LLM** (opcional) — juzga si los candidatos son duplicados reales

## Superficies

- **CI gate** — bloquea PRs con duplicación detectada
- **Integración IDE / agente** — antes de generar una función, verifica si la lógica ya existe

## Estado

En desarrollo.

---

## Uso en cualquier repositorio (local)

Corré el script de setup — instala dependencias y registra el servidor MCP en un solo paso:

```bash
bash setup.sh
```

El script te pregunta si querés registrarlo **globalmente** (disponible en todos tus proyectos) o solo en **un repo específico**.

### Opción A — Global (cualquier proyecto)

El script registra Radar en Claude Code con `claude mcp add -s user`. Una vez hecho, en cada proyecto que quieras usarlo agregá dos líneas al `CLAUDE.md`:

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

---

## Cómo correr la demo

Ambos comandos se corren desde la raíz del repo (`radar/radar`).

### Paso 1 — Preparar el workspace

```bash
bash demo/run_prueba.sh
```

Crea `../prueba/con/` con un repo Java de e-commerce realista (3 duplicados semánticos plantados), construye el índice Radar adentro y escribe la config MCP en `../prueba/radar.mcp.json`. Tarda ~30 segundos la primera vez mientras descarga el embedder.

### Paso 2 — Correr el agente

```bash
bash demo/arm_con.sh
```

Lanza Claude de forma automática en `../prueba/con` con Radar conectado vía la config MCP. El agente tiene instrucción de llamar `find_similar_function` antes de escribir cualquier función nueva. El output se muestra en tiempo real; al final se imprime el resumen de tokens.

### Qué mirar

La tarea le pide al agente implementar `calculateCommission(saleAmount, rate)` — aritmética de porcentaje sobre un monto. El repo ya tiene dos funciones con exactamente esa lógica:

- `TaxCalculator.calculateTax(price, rate)` — misma matemática, vocabulario de impuestos
- `LevyEngine.applyLevy(amount, factor)` — misma matemática, vocabulario de facturación, sin ninguna palabra clave en común

Una búsqueda por texto no encuentra ninguna. Radar encuentra ambas.

Cuando funciona: el agente llama `find_similar_function`, recibe el candidato con el código fuente completo, reconoce el duplicado y escribe un import en lugar de reimplementar la aritmética.
