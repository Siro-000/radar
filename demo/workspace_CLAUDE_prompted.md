# Project conventions

This is a Java utility codebase (`com.acme.*`). **Reuse before you write — never
duplicate existing logic.**

Before implementing ANY new utility or helper function, you MUST first search the
repository EXHAUSTIVELY to confirm an equivalent does not already exist:

1. **Search broadly, not by one keyword.** A function with the same behaviour may
   use completely different names — e.g. a "tax" calculation might be called
   `applyFactor`, `addMargin`, `gross`, `surcharge`, `withRate`, etc. Grep for
   multiple synonyms, list the packages, and read every candidate file in full.
2. **Compare the LOGIC, not the name.** Two functions are duplicates if they
   compute the same result, regardless of how they are named or where they live.
3. **If an equivalent exists, DO NOT reimplement it** — import and call it. Only
   write new code once you are confident, after an exhaustive search, that no
   equivalent exists anywhere in the repository.

Keep new code consistent with the existing package layout under `src/com/acme/`.
