"""Pooled two-seed view of the primary trio (flat, fresh, ctrl).

The resolve rates, differences and intervals are read from results/summary.json (block pooled_trio,
written by scripts/summarize.py, bootstrap clustered by task), so there is one source for them.
The seed-agreement and stale-test counts below are computed from the run logs.

Usage: python scripts/summarize.py && python scripts/pooled_trio.py
"""
import glob, json, re

EXCLUDE = {"psf__requests-1766", "pylint-dev__pylint-7277"}
ARMS = ["flat", "fresh", "ctrl"]

S = json.load(open("results/summary.json"))["pooled_trio"]
print(f"{S['n_units']} (seed, task) units over {S['n_tasks']} tasks, arms {ARMS}")
for a in ARMS:
    d = S["arms"][a]
    line = f"{a:6} resolved {d['resolved']:3}/{d['n']} = {d['rate']:.1%}"
    if a != "flat":
        v = S["vs_flat"][a]
        line += f"   vs flat {v['mean_diff']*100:+.1f} pp [{v['ci95'][0]*100:+.1f}, {v['ci95'][1]*100:+.1f}]  wins/losses {v['wins']}/{v['losses']}"
    print(line)

runs = {}
for f in glob.glob("runs/main_s*_*.jsonl"):
    seed = int(re.search(r"main_s(\d+)_", f).group(1))
    for l in open(f):
        r = json.loads(l)
        if r.get("error") or r["iid"] in EXCLUDE or int(r["cap"]) != 8000 or r["arm"] not in ARMS:
            continue
        runs[(seed, r["arm"], r["iid"])] = r
units = sorted({(s, t) for s, a, t in runs if all((s, b, t) in runs for b in ARMS)})

for a in ARMS:
    tasks = sorted({t for s, t in units if (0, a, t) in runs and (1, a, t) in runs})
    both = sum(bool(runs[(0, a, t)]["resolved"]) and bool(runs[(1, a, t)]["resolved"]) for t in tasks)
    either = sum(bool(runs[(0, a, t)]["resolved"]) or bool(runs[(1, a, t)]["resolved"]) for t in tasks)
    print(f"{a:6} resolved in both seeds {both}, in at least one {either}, of {len(tasks)} tasks")

for a in ARMS:
    sub = [(s, t) for s, t in units if any(e.get("stale_tests_retained", 0) > 0 for e in runs[(s, a, t)]["log"] if e["ev"] == "compact")]
    res = sum(bool(runs[(s, a, t)]["resolved"]) for s, t in sub)
    print(f"{a:6} units with a stale test retained at a compaction: {len(sub)}, resolved among them {res}")
