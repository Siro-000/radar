#!/usr/bin/env python3
"""Compare the three A/B/C arms produced by run_ab.sh and print a verdict.

Arms:
  - without   baseline, no Radar tool (controlled: no repo search either)
  - prompted  no Radar tool, but ordered to search EXHAUSTIVELY + given Read/Glob/Grep
  - with      the Radar MCP tool (semantic retrieval)

Source of truth = the artifact the agent produced (Invoice.java):
  - REUSED        -> references TaxCalculator / calculateTax (the existing function)
  - REIMPLEMENTED -> contains the inline tax arithmetic (price * rate / 100)

Plus, from each run's stream-json transcript:
  - whether the agent made a *structured* call to find_similar_function
  - efficiency: turns, input/cache/output tokens, total tokens, cost, wall-clock
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


# (arm key, column header, full label)
ARMS = [
    ("without",  "WITHOUT",  "WITHOUT Radar (baseline)"),
    ("prompted", "PROMPTED", "WITHOUT Radar + exhaustive-search prompt"),
    ("with",     "WITH",     "WITH Radar (semantic retrieval)"),
]


def main() -> int:
    run_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/radar-demo-run")
    arms = {key: summarize(run_dir, key) for key, _, _ in ARMS}

    bar = "=" * 70
    print(bar)
    print("  RADAR A/B/C DEMO — RESULT")
    print(bar)
    for key, _, label in ARMS:
        s = arms[key]
        print(f"\n[{label}]")
        print(f"  produced file    : {s['file']}")
        print(f"  outcome          : {s['verdict']}")
        print(f"  called Radar     : {'yes' if s['tool_called'] else 'no'}")
        if s["code"]:
            snippet = "\n".join("      " + ln for ln in s["code"].splitlines()[:18])
            print("  code:\n" + snippet)

    # Token / cost comparison — three columns, one per arm.
    print("\n" + bar)
    print("  EFFICIENCY (tokens / cost / time per arm)")
    print(bar)
    print(f"  {'metric':<18}" + "".join(f"{h:>16}" for _, h, _ in ARMS))
    print("  " + "-" * (18 + 16 * len(ARMS)))

    def row(label: str, key: str, fmt=lambda v: f"{v:,}"):
        print(f"  {label:<18}" + "".join(f"{fmt(arms[a][key]):>16}" for a, _, _ in ARMS))

    row("turns", "turns")
    row("input tokens", "input_tokens")
    row("cache read", "cache_read")
    row("output tokens", "output_tokens")
    row("total tokens", "total_tokens")
    row("cost (USD)", "cost_usd", fmt=lambda v: f"{v:.4f}")
    row("wall-clock (ms)", "duration_ms")

    # Deltas vs the baseline (`without`).
    base = arms["without"]

    def pct(d, b):
        return 100 * d / b if b else 0.0

    if base["total_tokens"]:
        print()
        for key, _, label in ARMS:
            if key == "without":
                continue
            s = arms[key]
            if not s["total_tokens"]:
                continue
            td = s["total_tokens"] - base["total_tokens"]
            cd = s["cost_usd"] - base["cost_usd"]
            print(f"  {label}")
            print(f"    total tokens vs baseline : {td:+,} ({pct(td, base['total_tokens']):+.1f}%)")
            print(f"    cost vs baseline         : {cd:+.4f} USD")

    # Verdict — the three-way contrast.
    print("\n" + bar)
    wo, pr, wi = (arms["without"]["verdict"], arms["prompted"]["verdict"],
                  arms["with"]["verdict"])
    wi_reused, pr_reused = wi.startswith("REUSED"), pr.startswith("REUSED")
    if wi_reused and not pr_reused:
        print("  ✓ STRONGEST CONTRAST: even when explicitly ordered to search the")
        print("    repo EXHAUSTIVELY (prompted arm, with Read/Glob/Grep), the no-Radar")
        print("    agent still REIMPLEMENTED — the duplicate was not lexically findable.")
        print("    Radar found it SEMANTICALLY in one deterministic call and reused it.")
        print("    => A strong prompt + grep is NOT a substitute for semantic retrieval.")
    elif wi_reused and pr_reused:
        print("  ~ Both the exhaustive-search PROMPT and Radar reused the existing")
        print("    function (the duplicate was greppable here). Compare the cost: the")
        print("    prompted arm paid for many grep/read turns; Radar paid for ONE tool")
        print("    call. For an OUTCOME-level contrast, use a non-greppable duplicate:")
        print("      python3 demo/gen_big_repo.py && \\")
        print("      RADAR_DEMO_REPO=demo/big_repo bash demo/run_ab.sh")
    elif not wi_reused:
        print("  ! Radar arm did not reuse this run (agents are nondeterministic).")
        print("    Re-run, or inspect the files under", run_dir)
    print(bar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
