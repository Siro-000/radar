# Project conventions

This is a Java utility codebase (`com.acme.*`). **Reuse before you write.**

Before implementing any new utility or helper function, FIRST call the
`find_similar_function` tool (the Radar MCP) with the source of the function you
intend to write:

- If the verdict is **`not_duplicate`**, no equivalent exists — write your function.
- If the verdict is **`candidate`**, READ the returned match's `source_code`. If it
  implements the same logic as what you were about to write, DO NOT reimplement it:
  import and call it using the match's `import_statement`. If it is genuinely
  different, write your own.

Keep new code consistent with the existing package layout under `src/com/acme/`.
