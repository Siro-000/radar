"""
RADAR-008: precision/recall + threshold calibration.

Runs the engine over a held-out set of known duplicate / non-duplicate pairs and
reports precision, recall and F1 at a given detection threshold. This is where the
threshold is calibrated — against ground truth, NOT through the agent.

Usage:
    radar-eval                      # eval at the configured DUPLICATE_THRESHOLD
    radar-eval --threshold 0.80     # eval at a specific threshold
    radar-eval --sweep              # sweep the full range, recommend the best one

The query is embedded exactly as engine.find_similar_function embeds it (raw source),
but eval reads the *raw* top-neighbour score from the index — bypassing the verdict
filter — so the sweep is meaningful across the whole range.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from radar.engine import config
from radar.engine.build import build_index
from radar.engine.embed import embed
from radar.engine.index import Index, load
from radar.engine.models import Function

DEFAULT_REPO = "data/seed_repo"
DEFAULT_INDEX = ".radar-eval-index"
DEFAULT_HELDOUT = "data/heldout.json"


def _ensure_index(repo: str, index_path: str) -> Index:
    if (Path(index_path) / "index.faiss").exists():
        return load(index_path)
    return build_index(repo, index_path)


def _top_match(index: Index, code: str):
    """Return (name, score) of the nearest indexed function, or (None, 0.0)."""
    dummy = Function(
        name="query",
        file="",
        start_line=0,
        end_line=0,
        source_code=code,
        signature=code.splitlines()[0].strip() if code.strip() else "",
    )
    results = index.search(embed(dummy), k=1)
    if not results:
        return None, 0.0
    return results[0].function.name, results[0].score


def _score_at(cases: list[dict], threshold: float) -> dict:
    tp = fp = fn = tn = 0
    for case in cases:
        is_dup = case["is_duplicate"]
        predicted = case["top_score"] >= threshold
        matched_right = is_dup and case["top_name"] == case["expected_match"]
        if is_dup and predicted and matched_right:
            tp += 1
        elif predicted:  # fired on a negative, or on a positive but wrong target
            fp += 1
        elif is_dup:  # missed a real duplicate
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"threshold": threshold, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": precision, "recall": recall, "f1": f1}


def _print_breakdown(cases: list[dict], threshold: float) -> None:
    print(f"\nPer-case @ threshold {threshold:.2f}")
    print(f"  {'case':<32} {'truth':<6} {'top match':<22} {'score':>6} {'verdict':<10} ok")
    print("  " + "-" * 86)
    for c in cases:
        predicted = c["top_score"] >= threshold
        truth = "DUP" if c["is_duplicate"] else "novel"
        verdict = "duplicate" if predicted else "novel"
        if c["is_duplicate"]:
            ok = predicted and c["top_name"] == c["expected_match"]
        else:
            ok = not predicted
        print(f"  {c['name']:<32} {truth:<6} {str(c['top_name']):<22} "
              f"{c['top_score']:>6.3f} {verdict:<10} {'✓' if ok else '✗'}")


def _print_metrics(m: dict) -> None:
    print(f"\n  precision={m['precision']:.3f}  recall={m['recall']:.3f}  f1={m['f1']:.3f}  "
          f"(TP={m['tp']} FP={m['fp']} FN={m['fn']} TN={m['tn']})")


def run(repo: str, index_path: str, heldout: str, threshold: float | None, sweep: bool) -> int:
    index = _ensure_index(repo, index_path)
    cases = json.loads(Path(heldout).read_text())

    # Precompute top match + score once per case (independent of threshold).
    for c in cases:
        c["top_name"], c["top_score"] = _top_match(index, c["query_code"])

    if sweep:
        candidates = [round(0.50 + 0.01 * i, 2) for i in range(46)]  # 0.50 .. 0.95
        rows = [_score_at(cases, t) for t in candidates]
        # best F1, tie-break on higher precision (product favours precision over recall)
        best = max(rows, key=lambda r: (r["f1"], r["precision"]))
        print("Threshold sweep (precision / recall / f1):")
        for r in rows:
            mark = "  <-- best" if r["threshold"] == best["threshold"] else ""
            if r["threshold"] in (0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90) or mark:
                print(f"  t={r['threshold']:.2f}  P={r['precision']:.3f}  "
                      f"R={r['recall']:.3f}  F1={r['f1']:.3f}{mark}")
        _print_breakdown(cases, best["threshold"])
        _print_metrics(best)
        print(f"\nRecommended DUPLICATE_THRESHOLD = {best['threshold']:.2f} "
              f"(currently {config.DUPLICATE_THRESHOLD:.2f})")
        return 0

    t = threshold if threshold is not None else config.DUPLICATE_THRESHOLD
    m = _score_at(cases, t)
    _print_breakdown(cases, t)
    _print_metrics(m)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="radar-eval", description="Precision/recall + threshold calibration.")
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument("--index-path", default=DEFAULT_INDEX)
    p.add_argument("--heldout", default=DEFAULT_HELDOUT)
    p.add_argument("--threshold", type=float, default=None, help="evaluate at this threshold")
    p.add_argument("--sweep", action="store_true", help="sweep 0.50–0.95 and recommend the best")
    args = p.parse_args(argv)
    return run(args.repo, args.index_path, args.heldout, args.threshold, args.sweep)


if __name__ == "__main__":
    raise SystemExit(main())
