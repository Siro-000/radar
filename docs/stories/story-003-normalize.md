# Story RADAR-003: engine/normalize.py — canonicalization

**Status:** Draft

## Story

As the detection engine, I need to normalize source code before embedding it, so that two semantically identical functions with different variable names produce similar vectors.

## Acceptance Criteria

1. [ ] `normalize(source: str) -> str` returns canonicalized code
2. [ ] Strips inline comments and docstrings
3. [ ] Renames local variables to `var_0`, `var_1`, `var_2` ... in order of first appearance
4. [ ] Normalizes whitespace: consistent indentation, no multiple blank lines
5. [ ] Preserves function names, parameter names, and attribute names (they carry semantic meaning)
6. [ ] Is deterministic: same input → same output, always
7. [ ] Does not crash on invalid syntax — returns the input unchanged

## Tasks

- [ ] 1. Use the `ast` stdlib module to strip comments and docstrings via `ast.NodeTransformer`
- [ ] 2. Implement local variable renaming with a second `ast.NodeTransformer` pass
- [ ] 3. Normalize whitespace with `textwrap` / string ops after unparsing
- [ ] 4. Wrap in try/except so invalid syntax falls back to returning input as-is
- [ ] 5. Write tests:
  - [ ] Function with comments → comments stripped
  - [ ] Two functions with different var names, same logic → same normalized output
  - [ ] Invalid syntax → returns input unchanged

## Dev Notes

Example transformation:
```python
# Input
def calc_tax(price, rate):
    # apply tax
    total = price * rate
    return total

# Output
def calc_tax(price, rate):
    var_0 = price * rate
    return var_0
```

Parameter names (`price`, `rate`) are preserved — they are part of the semantic signature. Only local variables are renamed.

## Dependencies

- RADAR-001: `Function` model
