#!/usr/bin/env bash
#
# Radar — scripted demo (deterministic, no live agent required).
# The "degraded-but-dignified" fallback: it proves recall, the actionable import,
# determinism, and the calibrated precision/recall number — all without a network
# round-trip to an agent. Safe to run live on stage.
set -euo pipefail

RADAR_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UV="$(command -v uv || echo /opt/homebrew/bin/uv)"
IDX="$RADAR_ROOT/.radar-eval-index"

cd "$RADAR_ROOT"
if [ ! -d "$IDX" ]; then
  echo ">> Building index over data/seed_repo ..." >&2
  "$UV" run radar index --repo data/seed_repo --index-path "$IDX" >&2
fi

QUERY='public static double computeTax(double cost, double pct) {
    double tax = cost * pct / 100;
    return cost + tax;
}'

echo "############################################################"
echo "#  Radar — does this function already exist?"
echo "############################################################"
echo
echo ">> An agent is about to write this NEW function:"
echo "------------------------------------------------------------"
echo "$QUERY"
echo "------------------------------------------------------------"
echo
echo ">> Radar's answer:"
"$UV" run radar query --index-path "$IDX" "$QUERY" 2>/dev/null
echo
echo ">> Determinism cherry — running the SAME check twice:"
A="$("$UV" run radar query --index-path "$IDX" "$QUERY" 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["verdict"], round(d["matches"][0]["similarity"],6), d["matches"][0]["name"])')"
B="$("$UV" run radar query --index-path "$IDX" "$QUERY" 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["verdict"], round(d["matches"][0]["similarity"],6), d["matches"][0]["name"])')"
echo "   run 1: $A"
echo "   run 2: $B"
if [ "$A" = "$B" ]; then echo "   => IDENTICAL ✓ (deterministic, no LLM in the query path)"; else echo "   => DIFFERED ✗"; fi
echo
echo ">> Calibrated quality on the held-out set:"
"$UV" run radar-eval 2>/dev/null | grep -E "precision="
