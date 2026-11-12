"""Build paper/writeup.md (the Kaggle Writeup body) from paper/draft.md: same text, a byline, the five figures
inserted as images served from the public repository at tag v1.0, and a project-links footer.
Usage: python scripts/make_writeup.py"""
import re
RAW = "https://raw.githubusercontent.com/heilcheng/gemma4-compaction-audit/v1.0/figures/"
REPO = "https://github.com/heilcheng/gemma4-compaction-audit"
CAPTIONS = {
    1: ("overview.png", "Study design: the agent loop, compaction at 8000 tokens through one of five memory policies, the two measurements, and one older test record as each evidence arm renders it.", "Figure 1 summarises the design. "),
    2: ("differences.png", "Resolved-rate differences in percentage points with 95% paired bootstrap intervals. Hollow markers: the noise reference, one arm rerun with a new seed (flat) or the same seed (fresh). Filled markers: arms against flat in seed 0 (all four), in seed 1 and both seeds pooled (fresh and ctrl, task-clustered; fresh also with each task-run independent), at the 16K trigger and under the corrected loop (fresh); one row is fresh minus ctrl. Seed-1 and pooled rows share runs, and some coincide exactly. Only the seed-0 fresh row was frozen in advance; the bottom row is the post hoc pooling of the four fresh and flat pairs. Grey band: plus or minus 2 points, the target effect.", "an upper bound on what the rendered window held.\n"),
    3: ("flips.png", "Every task resolved by at least one of five passes: flat and fresh at seed 0 (s0) and seed 1 (s1), and the same-seed rerun of fresh. Filled dots mark the passes that resolved the task; the left bar marks django tasks (orange) against other repositories (grey); the bottom row gives each pass's resolved count.", "6 were solved by all five and 13 by only one.\n"),
    4: ("exposure_funnel.png", "Exposure in the same-seed replicate of fresh (145 runs; not the Table 1 arm, whose counter flagged 32): runs that compacted, runs the counter flagged (blue, an upper bound), runs whose rendered window held a stale test record and then one with a result marker and no current-state test beside it (orange, logged at run time with tag length approximated), and the one of those that resolved; the tick marks the 0.9 expected at the compacted-run rate (7 of 125).", "at the compacted-run rate (7 of 125).\n"),
    5: ("stall.png", "Replies with no command. Left: their share at each reply index among runs still going, for seed-0 flat at the 8000 and 16K triggers and under the corrected loop (145 runs each). Right: runs ending in ten or more of them, by arm (seeds pooled at the 8000 trigger; seed 0 at 16K and for the two corrected-loop passes). Onset is confounded with run length and compaction.", "14 only under mask (sign test p = 0.003).\n"),
}
s = open("paper/draft.md").read()
title, rest = s.split("\n", 1)
rest = "\nHailey H. L. Cheng, Columbia University. November 2026. Submission topic: Tasks and Benchmarks.\n" + rest
for n, (png, cap, anchor) in CAPTIONS.items():
    img = f"\n\n![Figure {n}]({RAW}{png})\n\nFigure {n}. {cap}\n"
    assert anchor in rest, anchor
    if n == 1:  # before the Methods paragraph that starts with the anchor
        rest = rest.replace(anchor, img.lstrip("\n") + "\n" + anchor, 1)
    else:
        rest = rest.replace(anchor, anchor.rstrip("\n") + img, 1)
footer = (f"\n\n## Project links\n\nCode, protocol, results and action logs: {REPO} (tag v1.0). "
          f"PDF: {REPO}/blob/v1.0/paper/latex/main.pdf.\n")
open("paper/writeup.md", "w").write(title + "\n" + rest.rstrip("\n") + footer)
body = re.sub(r"^\|.*$", "", (title + rest).split("## References")[0], flags=re.M)
print("wrote paper/writeup.md;", len(body.split()), "prose words outside the table (figure lines included)")
