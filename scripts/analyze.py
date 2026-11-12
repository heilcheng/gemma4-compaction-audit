"""Paired analysis over runs/main_*.jsonl. Bootstrap by task. Prints the main table and exposure counts.

Usage: python scripts/analyze.py [seed] [cap]   (cap other than 8000 reads runs/cap<cap>_s<seed>_<arm>.jsonl)
"""
import collections, glob, json, random, statistics, sys

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 0
CAP = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
PREFIX = f"runs/main_s{SEED}_" if CAP == 8000 else f"runs/cap{CAP}_s{SEED}_"
EXCLUDE = {"psf__requests-1766", "pylint-dev__pylint-7277"}   # gold patch fails preflight
ARMS = [a for a in ["mask", "summ", "flat", "fresh", "ctrl"] if glob.glob(f"{PREFIX}{a}.jsonl")]

runs = {}
for f in glob.glob(f"{PREFIX}*.jsonl"):
    for l in open(f):
        r = json.loads(l)
        if r.get("error") or r["iid"] in EXCLUDE:
            continue
        runs[(r["arm"], r["iid"])] = r

tasks = {iid for a, iid in runs}
common = sorted(t for t in tasks if all((a, t) in runs for a in ARMS))
print(f"seed {SEED}, cap {CAP}: {len(tasks)} tasks seen, {len(common)} complete across all arms\n")


def boot_diff(a, b, n=5000):
    rng = random.Random(1)
    d = [int(bool(runs[(a, t)]["resolved"])) - int(bool(runs[(b, t)]["resolved"])) for t in common]
    if not d:
        return 0, (0, 0)
    bs = sorted(statistics.mean(rng.choices(d, k=len(d))) for _ in range(n))
    return statistics.mean(d), (bs[int(0.025 * n)], bs[int(0.975 * n)])


print(f"{'arm':6}{'n':>5}{'resolved':>10}{'rate':>7}{'vs flat (95% CI)':>26}{'wins/losses':>13}{'gen tok/run':>13}{'model s/run':>13}{'step-cap':>10}")
for a in ARMS:
    rs = [runs[(a, t)] for t in common]
    if not rs:
        continue
    res = sum(bool(r["resolved"]) for r in rs)
    gen = statistics.mean(r["totals"]["completion"] + r["totals"]["summ_completion"] for r in rs)
    ms = statistics.mean(r["totals"]["model_s"] + r["totals"]["summ_s"] for r in rs)
    cap = sum(r["status"] == "step_limit" for r in rs)
    if a == "flat":
        ci, wl = "reference", ""
    else:
        m, (lo, hi) = boot_diff(a, "flat")
        w = sum(bool(runs[(a, t)]["resolved"]) and not runs[("flat", t)]["resolved"] for t in common)
        l = sum(not runs[(a, t)]["resolved"] and bool(runs[("flat", t)]["resolved"]) for t in common)
        ci, wl = f"{m*100:+.1f} [{lo*100:+.1f}, {hi*100:+.1f}]", f"{w}/{l}"
    print(f"{a:6}{len(rs):>5}{res:>10}{res/len(rs):>7.1%}{ci:>26}{wl:>13}{gen:>13.0f}{ms:>13.0f}{cap:>10}")

print("\nExposure at compaction (all arms, all tasks seen):")
k = collections.Counter(); per_arm = collections.defaultdict(lambda: collections.Counter())
for (a, t), r in runs.items():
    steps = [e for e in r["log"] if e["ev"] == "step"]
    comps = [e for e in r["log"] if e["ev"] == "compact"]
    c = per_arm[a]
    c["runs"] += 1
    c["compacted"] += bool(comps)
    c["any_test"] += any(e["kind"] == "test" for e in steps)
    c["stale_test_at_compact"] += any(e.get("stale_tests_retained", 0) > 0 for e in comps)
    c["stale_read_at_compact"] += any(e.get("stale_reads_retained", 0) > 0 for e in comps)
    for e in steps:
        k[e["kind"]] += 1
for a in ARMS:
    print(a, dict(per_arm[a]))
print("step kinds overall", dict(k))

print("\nPer-repo resolved (common tasks):")
by = collections.defaultdict(lambda: collections.Counter())
for a in ARMS:
    for t in common:
        by[t.split("__")[0]][a] += bool(runs[(a, t)]["resolved"])
        by[t.split("__")[0]]["n"] += 1 if a == "flat" else 0
for repo, c in sorted(by.items()):
    print(f"  {repo:14} n={c['n']:3} " + " ".join(f"{a}={c[a]}" for a in ARMS))
