#!/usr/bin/env python3
"""Compare the two arms produced by run_prueba.sh and print a verdict.

Arms:
  sin  — no Radar tool, no repo search (baseline)
  con  — Radar MCP tool (semantic retrieval)

Artifact: FeeCalculator.java
  REUSED        -> references TaxCalculator/calculateTax or LevyEngine/applyLevy
  REIMPLEMENTED -> contains inline arithmetic (/ 100)

Usage:
  python3 compare_prueba.py <run_dir>
  python3 compare_prueba.py <run_dir> --readme /path/to/README.md
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REUSE_MARKERS = ("TaxCalculator", "calculateTax", "VendorFeeEngine", "applyVendorFee")
REIMPL_RE = re.compile(r"commissionRate\s*/\s*100|saleAmount\s*\*\s*commissionRate")

ARMS = [
    ("sin", "SIN RADAR (baseline)"),
    ("con", "CON RADAR (semantic retrieval)"),
]


def find_artifact(arm_dir: Path) -> Path | None:
    hits = sorted(arm_dir.rglob("CommissionCalculator.java"))
    return hits[0] if hits else None


def classify(java: str) -> str:
    reused = any(m in java for m in REUSE_MARKERS)
    reimpl = bool(REIMPL_RE.search(java))
    if reused and not reimpl:
        return "REUSED"
    if reused and reimpl:
        return "REUSED (+ inline math)"
    if reimpl:
        return "REIMPLEMENTED"
    return "UNCLEAR"


def parse_transcript(jsonl: Path) -> dict:
    info = {
        "tool_called": False, "turns": 0, "duration_ms": 0,
        "input_tokens": 0, "cache_read": 0, "cache_creation": 0,
        "output_tokens": 0, "total_tokens": 0, "cost_usd": 0.0,
    }
    if not jsonl.exists():
        return info
    for line in jsonl.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "assistant":
            for block in obj.get("message", {}).get("content", []):
                if block.get("type") == "tool_use" and "find_similar_function" in block.get("name", ""):
                    info["tool_called"] = True
        elif obj.get("type") == "result":
            u = obj.get("usage", {})
            info["turns"] = obj.get("num_turns", 0)
            info["duration_ms"] = obj.get("duration_ms", 0)
            info["input_tokens"] = u.get("input_tokens", 0)
            info["cache_read"] = u.get("cache_read_input_tokens", 0)
            info["cache_creation"] = u.get("cache_creation_input_tokens", 0)
            info["output_tokens"] = u.get("output_tokens", 0)
            info["total_tokens"] = (
                info["input_tokens"] + info["cache_read"]
                + info["cache_creation"] + info["output_tokens"]
            )
            info["cost_usd"] = obj.get("total_cost_usd", 0.0)
    return info


def summarize(run_dir: Path, arm: str) -> dict:
    arm_dir = run_dir / arm
    artifact = find_artifact(arm_dir)
    code = artifact.read_text() if artifact else ""
    t = parse_transcript(run_dir / f"{arm}.jsonl")
    return {
        "arm": arm,
        "file": str(artifact.relative_to(arm_dir)) if artifact else "(not created)",
        "verdict": classify(code) if code else "NO FILE",
        "code": code,
        **t,
    }


def build_plain(arms: dict) -> str:
    bar = "=" * 65
    lines = []
    lines.append(bar)
    lines.append("  RADAR A/B — RESULTADO")
    lines.append(bar)

    for key, label in ARMS:
        s = arms[key]
        lines.append(f"\n[{label}]")
        lines.append(f"  archivo producido : {s['file']}")
        lines.append(f"  resultado         : {s['verdict']}")
        lines.append(f"  llamó Radar       : {'sí' if s['tool_called'] else 'no'}")
        if s["code"]:
            snippet = "\n".join("      " + ln for ln in s["code"].splitlines()[:20])
            lines.append("  código:\n" + snippet)

    lines.append("\n" + bar)
    lines.append("  TOKENS / COSTO / TIEMPO")
    lines.append(bar)
    headers = [h for _, h in ARMS]
    lines.append(f"  {'métrica':<20}" + "".join(f"{h:>22}" for h in headers))
    lines.append("  " + "-" * (20 + 22 * len(ARMS)))

    def row(label, key, fmt=lambda v: f"{v:,}"):
        lines.append(f"  {label:<20}" + "".join(f"{fmt(arms[a][key]):>22}" for a, _ in ARMS))

    row("turns", "turns")
    row("input tokens", "input_tokens")
    row("cache read", "cache_read")
    row("output tokens", "output_tokens")
    row("total tokens", "total_tokens")
    row("costo (USD)", "cost_usd", fmt=lambda v: f"${v:.4f}")
    row("tiempo (ms)", "duration_ms")

    base = arms["sin"]
    s = arms["con"]
    if base["total_tokens"] and s["total_tokens"]:
        td = s["total_tokens"] - base["total_tokens"]
        cd = s["cost_usd"] - base["cost_usd"]
        pct = 100 * td / base["total_tokens"] if base["total_tokens"] else 0
        lines.append("")
        lines.append(f"  CON RADAR vs baseline:")
        lines.append(f"    total tokens : {td:+,} ({pct:+.1f}%)")
        lines.append(f"    costo        : {cd:+.4f} USD")

    lines.append("\n" + bar)
    sin_v = arms["sin"]["verdict"]
    con_v = arms["con"]["verdict"]
    if con_v.startswith("REUSED") and not sin_v.startswith("REUSED"):
        lines.append("  ✓ CONTRASTE CLARO:")
        lines.append("    SIN Radar → reimplementó la lógica inline.")
        lines.append("    CON Radar → encontró el duplicado semántico y lo reutilizó.")
    elif con_v.startswith("REUSED") and sin_v.startswith("REUSED"):
        lines.append("  ~ Ambos reutilizaron. El contraste es el costo: CON Radar lo hizo en una llamada.")
    else:
        lines.append("  ! El brazo CON Radar no reutilizó esta ejecución (no determinista). Volvé a correr.")
    lines.append(bar)

    return "\n".join(lines)


def build_markdown(arms: dict, command: str) -> str:
    sin_v = arms["sin"]["verdict"]
    con_v = arms["con"]["verdict"]
    sin = arms["sin"]
    con = arms["con"]

    base_tok = sin["total_tokens"] or 1
    td = con["total_tokens"] - sin["total_tokens"]
    cd = con["cost_usd"] - sin["cost_usd"]
    pct = 100 * td / base_tok

    if con_v.startswith("REUSED") and not sin_v.startswith("REUSED"):
        verdict_line = "✓ **CONTRASTE CLARO** — SIN Radar reimplementó; CON Radar reutilizó el duplicado semántico."
    elif con_v.startswith("REUSED") and sin_v.startswith("REUSED"):
        verdict_line = "~ Ambos reutilizaron. El contraste real es el costo: CON Radar lo hizo en una llamada."
    else:
        verdict_line = "! El brazo CON Radar no reutilizó esta ejecución (no determinista)."

    return f"""
## Demo de prueba — última ejecución

```bash
{command}
```

**Tarea:** implementar `FeeCalculator.computeHandlingFee(baseAmount, feePercent)` —
misma lógica que `TaxCalculator.calculateTax` y `LevyEngine.applyLevy` (oculto).

| métrica | SIN Radar | CON Radar | delta |
|---|---|---|---|
| resultado | {sin_v} | {con_v} | — |
| llamó Radar | {"sí" if sin["tool_called"] else "no"} | {"sí" if con["tool_called"] else "no"} | — |
| turns | {sin["turns"]:,} | {con["turns"]:,} | {con["turns"] - sin["turns"]:+,} |
| output tokens | {sin["output_tokens"]:,} | {con["output_tokens"]:,} | {con["output_tokens"] - sin["output_tokens"]:+,} |
| total tokens | {sin["total_tokens"]:,} | {con["total_tokens"]:,} | {td:+,} ({pct:+.1f}%) |
| costo (USD) | ${sin["cost_usd"]:.4f} | ${con["cost_usd"]:.4f} | {cd:+.4f} |
| tiempo (ms) | {sin["duration_ms"]:,} | {con["duration_ms"]:,} | {con["duration_ms"] - sin["duration_ms"]:+,} |

{verdict_line}
"""


def update_readme(readme_path: Path, markdown: str) -> None:
    marker_start = "## Demo de prueba"
    text = readme_path.read_text() if readme_path.exists() else ""
    if marker_start in text:
        text = text[:text.index(marker_start)].rstrip()
    readme_path.write_text(text + "\n" + markdown)


def main() -> int:
    args = sys.argv[1:]
    readme_path: Path | None = None
    command = "bash demo/run_prueba.sh"

    if "--readme" in args:
        idx = args.index("--readme")
        readme_path = Path(args[idx + 1])
        args = args[:idx] + args[idx + 2:]
    if "--command" in args:
        idx = args.index("--command")
        command = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    run_dir = Path(args[0] if args else "/tmp/radar-prueba-run")
    arms = {key: summarize(run_dir, key) for key, _ in ARMS}

    plain = build_plain(arms)
    print(plain)

    if readme_path:
        md = build_markdown(arms, command)
        update_readme(readme_path, md)
        print(f"\n>> README actualizado: {readme_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
