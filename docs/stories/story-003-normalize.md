# Story RADAR-003: engine/normalize.py — canonicalization

**Status:** Draft

## Story

As the detection engine, I need to normalize Java source code before embedding it, so that two semantically identical methods with different variable names produce similar vectors.

## Acceptance Criteria

1. [ ] `normalize(source: str) -> str` returns canonicalized Java code
2. [ ] Strips single-line comments (`//`) and block comments (`/* */`)
3. [ ] Strips Javadoc comments (`/** */`)
4. [ ] Renames local variables to `var0`, `var1`, `var2` ... in order of first appearance
5. [ ] Normalizes whitespace: consistent indentation, no multiple blank lines
6. [ ] Preserves method names, parameter names, and field names (they carry semantic meaning)
7. [ ] Is deterministic: same input → same output, always
8. [ ] Does not crash on invalid syntax — returns the input unchanged

## Tasks

- [ ] 1. Use tree-sitter-java to parse the method and traverse local variable declarations
- [ ] 2. Strip comment nodes from the tree and reconstruct the source without them
- [ ] 3. Implement local variable renaming by replacing identifier nodes in order of appearance
- [ ] 4. Normalize whitespace with string ops after reconstruction
- [ ] 5. Wrap in try/except so invalid syntax falls back to returning input as-is
- [ ] 6. Write tests:
  - [ ] Method with comments → comments stripped
  - [ ] Two methods with different var names, same logic → same normalized output
  - [ ] Invalid syntax → returns input unchanged

## Dev Notes

Example transformation:
```java
// Input
public double calcTax(double price, double rate) {
    // apply tax
    double total = price * rate; // result
    return total;
}

// Output
public double calcTax(double price, double rate) {
    double var0 = price * rate;
    return var0;
}
```

Parameter names (`price`, `rate`) are preserved — they are part of the semantic signature. Only local variables declared inside the method body are renamed.

Use tree-sitter-java (already a dependency from RADAR-002) — do not use regex for Java parsing.

## Dependencies

- RADAR-001: `Function` model
- RADAR-002: tree-sitter-java already set up
