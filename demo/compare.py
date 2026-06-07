#!/usr/bin/env python3
"""Compare the two A/B arms produced by run_ab.sh and print a verdict.

Source of truth = the artifact the agent produced (Invoice.java):
  - REUSED        -> references TaxCalculator / calculateTax (the existing function)
  - REIMPLEMENTED -> contains the inline tax arithmetic (price * rate / 100)

Plus, from each run's stream-json transcript:
  - whether the agent made a *structured* call to find_similar_function
  - efficiency: turns, output tokens, wall-clock
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Reuse targets across both demo corpora: seed_repo -> TaxCalculator.calculateTax,
# big_repo -> Surcharges.surcharge (the hidden, non-greppable tax-equivalent).
REUSE_MARKERS = ("TaxCalculator", "calculateTax", "Surcharges", "surcharge")
REIMPL_RE = re.compile(r"/\s*100")  # the inline tax arithmetic: ... / 100


def find_invoice(arm_dir: Path) -> Path | None:
    hits = sorted(arm_dir.rglob("Invoice.java"))
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
    """Return tool-use + efficiency + token/cost metrics from a stream-json run."""
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
            info["total_tokens"] = (info["input_tokens"] + info["cache_read"]
                                    + info["cache_creation"] + info["output_tokens"])
            info["cost_usd"] = obj.get("total_cost_usd", 0.0)
    return info


def summarize(run_dir: Path, arm: str) -> dict:
    arm_dir = run_dir / arm
    inv = find_invoice(arm_dir)
    code = inv.read_text() if inv else ""
    t = parse_transcript(run_dir / f"{arm}.jsonl")
    return {
        "arm": arm,
        "file": str(inv.relative_to(arm_dir)) if inv else "(not created)",
        "verdict": classify(code) if code else "NO FILE",
        "code": code,
        **t,
    }


def main() -> int:
    run_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/radar-demo-run")
    without = summarize(run_dir, "without")
    with_ = summarize(run_dir, "with")

    bar = "=" * 64
    print(bar)
    print("  RADAR A/B DEMO — RESULT")
    print(bar)
    for s in (without, with_):
        label = "WITHOUT Radar" if s["arm"] == "without" else "WITH Radar"
        print(f"\n[{label}]")
        print(f"  produced file    : {s['file']}")
        print(f"  outcome          : {s['verdict']}")
        print(f"  called Radar     : {'yes' if s['tool_called'] else 'no'}")
        if s["code"]:
            snippet = "\n".join("      " + ln for ln in s["code"].splitlines()[:22])
            print("  code:\n" + snippet)

    # Token / cost comparison — does the tool save tokens in the session?
    print("\n" + bar)
    print("  EFFICIENCY (does Radar save tokens?)")
    print(bar)
    print(f"  {'metric':<20} {'WITHOUT':>14} {'WITH':>14} {'delta':>14}")
    print("  " + "-" * 62)

    def row(label: str, key: str, fmt=lambda v: f"{v:,}"):
        wo, wi = without[key], with_[key]
        delta = wi - wo
        sign = "" if delta == 0 else ("+" if delta > 0 else "")
        print(f"  {label:<20} {fmt(wo):>14} {fmt(wi):>14} {sign + fmt(delta):>14}")

    row("turns", "turns")
    row("input tokens", "input_tokens")
    row("cache read", "cache_read")
    row("output tokens", "output_tokens")
    row("total tokens", "total_tokens")
    row("cost (USD)", "cost_usd", fmt=lambda v: f"{v:.4f}")
    row("wall-clock (ms)", "duration_ms")

    if without["total_tokens"] and with_["total_tokens"]:
        def pct(d, base):
            return 100 * d / base if base else 0.0
        out_d = with_["output_tokens"] - without["output_tokens"]
        tot_d = with_["total_tokens"] - without["total_tokens"]
        print()
        print(f"  output tokens : {out_d:+,} ({pct(out_d, without['output_tokens']):+.1f}%)  "
              "<- the agent's own generation")
        print(f"  total tokens  : {tot_d:+,} ({pct(tot_d, without['total_tokens']):+.1f}%)  "
              "<- incl. context + MCP tool overhead")
        print()
        if tot_d < 0:
            print(f"  => Net token WIN for Radar: {-tot_d:,} fewer total tokens.")
        else:
            print("  => No net token win here. Radar cuts the agent's OUTPUT tokens,")
            print("     but its MCP tool schema + result add context tokens. Net")
            print("     savings need a codebase where the baseline would otherwise")
            print("     read many files to find the duplicate — i.e. a large repo")
            print("     where the match isn't greppable. Try:")
            print("       python3 demo/gen_big_repo.py && \\")
            print("       RADAR_DEMO_FAIR=1 RADAR_DEMO_REPO=demo/big_repo bash demo/run_ab.sh")

    print("\n" + bar)
    if with_["verdict"].startswith("REUSED") and without["verdict"] == "REIMPLEMENTED":
        print("  ✓ CONTRAST SHOWN: without Radar the agent duplicated existing")
        print("    logic; with Radar it called find_similar_function and reused")
        print("    the existing function via the returned import.")
    elif with_["verdict"].startswith("REUSED") and without["verdict"].startswith("REUSED"):
        print("  ~ Both reused. Look at 'called Radar' and the efficiency numbers:")
        print("    Radar reused via a single deterministic lookup; the baseline")
        print("    had to discover it. Try the default (controlled) mode, or a")
        print("    larger corpus, for an outcome-level contrast.")
    else:
        print("  ! Inconclusive this run (agents are nondeterministic). Re-run,")
        print("    or inspect the files under", run_dir)
    print(bar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
