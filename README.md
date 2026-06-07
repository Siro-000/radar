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

### Step 1 — Prepare the workspace

```bash
bash demo/run_prueba.sh
```

Generates a realistic Java e-commerce repo with 3 hidden semantic duplicates and builds the Radar index. Takes ~30 seconds on first run (embedder download).

### Step 2 — Run the agent

Open Claude Code in `../prueba/con` and paste the prompt below, or run headlessly:

```bash
bash demo/arm_con.sh
```

**Prompt:**

```
Add sales commission tracking to the platform.

Create src/com/acme/commerce/sales/CommissionCalculator.java with a public class
CommissionCalculator that exposes:

    public static double calculateCommission(double saleAmount, double commissionRate)

A sales agent earns a percentage on top of every sale. The method returns the total
amount — sale price plus the agent's commission. Follow the existing package conventions
and reuse utilities where appropriate.
```

Token summary is printed at the end of the headless run:

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

The repo already has `TaxCalculator.calculateTax(price, rate)` — same math as the function the agent needs to write. It also has `LevyEngine.applyLevy(amount, factor)` in the billing package: identical logic but with no tax/sale/commission vocabulary, so a keyword search misses it entirely.

One call to `find_similar_function` surfaces the match. The agent reads the source, recognises the duplicate, and imports it instead of reimplementing.

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

### Paso 1 — Preparar el workspace

```bash
bash demo/run_prueba.sh
```

Genera un repo Java de e-commerce realista con 3 duplicados semánticos ocultos y construye el índice Radar. Tarda ~30 segundos la primera vez (descarga del embedder).

### Paso 2 — Correr el agente

Abrí Claude Code en `../prueba/con` y pegá el prompt de abajo, o correlo de forma automática:

```bash
bash demo/arm_con.sh
```

**Prompt:**

```
Agregar seguimiento de comisiones de ventas a la plataforma.

Crear src/com/acme/commerce/sales/CommissionCalculator.java con una clase pública
CommissionCalculator que exponga:

    public static double calculateCommission(double saleAmount, double commissionRate)

Un agente de ventas gana un porcentaje sobre cada venta. El método retorna el monto
total — precio de venta más la comisión del agente. Seguir las convenciones del
paquete existente y reutilizar utilidades donde corresponda.
```

El resumen de tokens se imprime al final de la ejecución automática.

### Qué mirar

El repo ya tiene `TaxCalculator.calculateTax(price, rate)` — la misma matemática que la función que el agente necesita escribir. También tiene `LevyEngine.applyLevy(amount, factor)` en el paquete de facturación: lógica idéntica pero sin ninguna palabra clave de comisión, venta ni impuesto, así que una búsqueda por texto no lo encuentra.

Una llamada a `find_similar_function` devuelve el candidato. El agente lee el código fuente, reconoce el duplicado y lo importa en lugar de reimplementarlo.
