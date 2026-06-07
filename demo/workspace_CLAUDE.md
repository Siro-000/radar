# Project conventions

This is a Java utility codebase (`com.acme.*`). **Reuse before you write.**

Before implementing any new utility or helper function, FIRST call the
`find_similar_function` tool (the Radar MCP) with the source of the function you
intend to write:

- If the verdict is **`duplicate`** or **`similar`**, treat it as an existing
  implementation of the same logic: DO NOT reimplement it. Import and call the
  matched function using the exact `import_statement` the tool returns.
- Only write new logic when the verdict is **`novel`** (no match returned).

Keep new code consistent with the existing package layout under `src/com/acme/`.
