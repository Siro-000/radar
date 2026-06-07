# Detection thresholds — calibrated offline against data/heldout.json (RADAR-008).
#
# `radar-eval --sweep` over the held-out set: precision=recall=F1=1.0 across the
# whole [0.64, 0.70] plateau. The lowest true duplicate scores 0.722 and the
# highest hard-negative (a fibonacci loop vs. an iterative factorial) scores 0.631.
# We pick 0.70 inside that plateau: it favours PRECISION (the #1 product risk is a
# false positive) by keeping a ~0.07 margin above the highest negative, while still
# catching every planted duplicate. SIMILAR sits below it so borderline matches
# (0.60–0.70) come back as "similar" for the agent to review rather than auto-reuse.
DUPLICATE_THRESHOLD = 0.70
SIMILAR_THRESHOLD = 0.60
DEFAULT_TOP_K = 3
