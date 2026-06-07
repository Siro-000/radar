#!/usr/bin/env python3
"""Generate demo/big_repo: a larger Java corpus whose only tax-equivalent
function is named WITHOUT any tax/price/rate vocabulary, so a baseline agent
cannot find it by grepping the task's keywords — it must read many files (costly)
or give up and reimplement. Radar matches it by *logic* in one cheap lookup.

This is the corpus that actually demonstrates Radar's token savings.

    python3 demo/gen_big_repo.py
    RADAR_DEMO_FAIR=1 RADAR_DEMO_REPO=demo/big_repo bash demo/run_ab.sh

The hidden target is Surcharges.surcharge(amount, factor): same logic as
`price + price * rate / 100` but with no tax/price/rate vocabulary.
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "big_repo"
SRC = OUT / "src"

N_FILLER = 40  # filler classes -> too many for an agent to read exhaustively


def filler_class(i: int) -> str:
    pkg = f"com.acme.mod{i:02d}"
    return f"""package {pkg};

public class Mod{i:02d} {{

    public static int sumElements(int[] xs) {{
        int acc = 0;
        for (int x : xs) {{
            acc += x;
        }}
        return acc;
    }}

    public static String joinWords(String[] ws) {{
        StringBuilder sb = new StringBuilder();
        for (String w : ws) {{
            sb.append(w);
        }}
        return sb.toString();
    }}

    public static boolean anyNegative(int[] xs) {{
        for (int x : xs) {{
            if (x < 0) {{
                return true;
            }}
        }}
        return false;
    }}
}}
"""


# The hidden tax-equivalent: same logic as `price + price * rate / 100`, but named
# with no tax/price/rate vocabulary — so grep for the task's keywords misses it,
# while Radar still matches it by logic (~0.73 similarity -> "duplicate").
HIDDEN_TARGET = """package com.acme.adjust;

/** Applies a percentage surcharge to an amount. */
public class Surcharges {

    public static double surcharge(double amount, double factor) {
        double extra = amount * factor / 100;
        double total = amount + extra;
        return total;
    }
}
"""


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    for i in range(N_FILLER):
        pkg_dir = SRC / "com" / "acme" / f"mod{i:02d}"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / f"Mod{i:02d}.java").write_text(filler_class(i))
    target_dir = SRC / "com" / "acme" / "adjust"
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "Surcharges.java").write_text(HIDDEN_TARGET)
    print(f"Generated {N_FILLER} filler classes + 1 hidden target (Surcharges.surcharge) at {OUT}")
    print("The tax-equivalent has no tax/price/rate vocabulary — not greppable by the")
    print("task's keywords, but Radar matches it by logic (~0.73 -> duplicate).")


if __name__ == "__main__":
    main()
