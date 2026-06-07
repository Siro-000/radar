# HYBRID design — single retrieval floor (see CLAUDE.md "The contract").
#
# Radar no longer makes the duplicate decision with a precision-critical threshold.
# It returns the top candidate's SOURCE when the top similarity clears this floor,
# and the AGENT judges duplication by reading the code. The floor is therefore a
# RECALL-oriented gate ("is anything worth showing at all?"), not a precision
# boundary — the agent is the precision stage.
#
# Chosen conservatively and deliberately LOW: true near-duplicates we observed score
# >= ~0.62 (via the engine's query path), clear negatives <= ~0.52. It is NOT finely
# tuned to the held-out set, so it is not sensitive to calibration-set leakage —
# over-surfacing a weak candidate is cheap (the agent rejects it after reading it),
# whereas a missed candidate is not recoverable.
RETRIEVAL_FLOOR = 0.55
DEFAULT_TOP_K = 3
