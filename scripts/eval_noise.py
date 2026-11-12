"""What our repeated runs say about single-run evaluations of a small agent.
1. Noise band of a 120-task single-run score: for each pair of runs of the same arm (flat seeds 0 and 1,
   fresh seeds 0 and 1, fresh seed 0 and its same-seed rerun), draw 120-task subsets and record the
   difference in resolved rate between the two runs. Reported: SD and the central 95 percent range.
2. Minimum detectable effect: with the observed per-task discordance between two runs, how many
   (task, run) units a paired comparison needs to detect a 2-point and a 1-point true difference at
   80 percent power (two-sided 5 percent), by simulation.
3. Mechanism probe in the window-logged fresh replicate: is the next action a test more often when the
   rendered window holds a stale test result with no current-state test beside it?
Usage: python scripts/eval_noise.py   (writes nothing; paste the numbers into results/extra_stats.txt by rerunning extra_stats)
"""
import json, random, statistics, collections

def load(path):
    return {json.loads(l)["iid"]: json.loads(l) for l in open(path) if not json.loads(l).get("error")}

pairs = {
    "flat seed 0 vs seed 1": (load("runs/main_s0_flat.jsonl"), load("runs/main_s1_flat.jsonl")),
    "fresh seed 0 vs seed 1": (load("runs/main_s0_fresh.jsonl"), load("runs/main_s1_fresh.jsonl")),
    "fresh seed 0 vs same-seed rerun": (load("runs/main_s0_fresh.jsonl"), load("runs/rep_r1_s0_c8000_fresh.jsonl")),
}
rng = random.Random(1)
print("== 1. Noise band of a 120-task single-run resolved rate (same arm, two runs)")
all_d = []
for name, (a, b) in pairs.items():
    tasks = sorted(set(a) & set(b))
    d = {t: int(bool(a[t]["resolved"])) - int(bool(b[t]["resolved"])) for t in tasks}
    all_d += list(d.values())
    # Independent 120-task draws: resample tasks WITH replacement (an earlier version subsampled without
    # replacement from the same 144 or 145 tasks, which shrinks the spread by about sqrt(1 - 120/144)).
    diffs = sorted(statistics.mean(d[t] for t in rng.choices(tasks, k=120)) * 100 for _ in range(5000))
    sd = statistics.pstdev(diffs)
    obs = statistics.mean(d.values()) * 100
    print(f"  {name:32} n={len(tasks)} discordant={sum(v != 0 for v in d.values())} observed full-set difference {obs:+.1f}; 120-task draw: SD {sd:.1f} points, 95% range [{diffs[125]:+.1f}, {diffs[4875]:+.1f}]")
disc = sum(v != 0 for v in all_d) / len(all_d)
print(f"  pooled per-task discordance between two runs of the same arm: {disc:.3f}; analytic SD of a 120-task two-run difference sqrt(disc/120) = {(disc/120)**0.5*100:.1f} points")

print("== 2. Units needed for 80 percent power (two-sided 5 percent), paired sign test on discordant tasks")
def power(n_units, effect_pts, disc, sims=4000):
    # Under H1 the discordant tasks split p:(1-p) so that the net rate difference is effect_pts.
    # discordant fraction stays as observed; effect = disc * (2p - 1) * 100 => p = (effect/100/disc + 1) / 2
    p = (effect_pts / 100 / disc + 1) / 2
    hits = 0
    for _ in range(sims):
        k = sum(rng.random() < disc for _ in range(n_units))          # discordant pairs
        w = sum(rng.random() < p for _ in range(k))                    # wins among them
        # exact two-sided binomial test at k, p0 = 0.5, normal approximation is fine for k >= 15
        if k == 0: continue
        z = (w - k / 2) / (k ** 0.5 / 2)
        hits += abs(z) >= 1.96
    return hits / sims
for effect in (2.0, 1.0):
    for n in (145, 290, 580, 1160, 2320, 4640):
        pw = power(n, effect, disc)
        print(f"  effect {effect:.0f} points, {n:5d} units: power {pw:.2f}")
        if pw >= 0.8: break

print("== 3. Mechanism probe in the window-logged fresh replicate")
rep = [r for r in (json.loads(l) for l in open("runs/rep_r1_s0_c8000_fresh.jsonl")) if not r.get("error")]
c = collections.Counter()
for r in rep:
    steps = [e for e in r["log"] if e["ev"] == "step"]
    for e in steps:
        w = e.get("window")
        if not w: continue   # before the first compaction
        exposed = w["stale_tests_with_result"] > 0 and not w["current_test_in_window"]
        key = "exposed" if exposed else "not_exposed"
        c[key + "_steps"] += 1
        c[key + "_tests"] += e["kind"] == "test"
        c[key + "_edits"] += e["kind"] == "edit"
for key in ("exposed", "not_exposed"):
    s = c[key + "_steps"]
    print(f"  {key:12} post-compaction steps {s:5d}: next action is a test {c[key + '_tests']/s:.3f}, an edit {c[key + '_edits']/s:.3f}")

print("== 3b. Within-run control: runs with both exposed and non-exposed post-compaction steps")
ex_rates, nx_rates = [], []
for r in rep:
    steps = [e for e in r["log"] if e["ev"] == "step" and e.get("window")]
    ex = [e for e in steps if e["window"]["stale_tests_with_result"] > 0 and not e["window"]["current_test_in_window"]]
    nx = [e for e in steps if not (e["window"]["stale_tests_with_result"] > 0 and not e["window"]["current_test_in_window"])]
    if ex and nx:
        ex_rates.append(sum(e["kind"] == "test" for e in ex) / len(ex)); nx_rates.append(sum(e["kind"] == "test" for e in nx) / len(nx))
d = [a - b for a, b in zip(ex_rates, nx_rates)]
print(f"  runs with both kinds of step: {len(d)}; mean test rate exposed {statistics.mean(ex_rates):.3f} vs not exposed {statistics.mean(nx_rates):.3f}; "
      f"within-run difference mean {statistics.mean(d):+.3f}, higher in {sum(x > 0 for x in d)} runs, lower in {sum(x < 0 for x in d)}")
print("== 3c. Same comparison for the first post-compaction step only (what the model sees right after compaction)")
first_ex = first_nx = n_ex = n_nx = 0
for r in rep:
    log = r["log"]
    for i, e in enumerate(log):
        if e["ev"] == "compact" and e.get("window"):
            nxt = next((x for x in log[i + 1:] if x["ev"] == "step"), None)
            if not nxt: continue
            w = e["window"]
            if w["stale_tests_with_result"] > 0 and not w["current_test_in_window"]:
                n_ex += 1; first_ex += nxt["kind"] == "test"
            else:
                n_nx += 1; first_nx += nxt["kind"] == "test"
print(f"  compactions with exposure {n_ex}: next step is a test {first_ex}/{n_ex}; without {n_nx}: {first_nx}/{n_nx}")

print("== 2b. Finer power grid (same simulation), units needed for 80 percent power")
for effect in (2.0, 1.0):
    lo, hi = 200, 12000
    while hi - lo > 100:
        mid = (lo + hi) // 2
        if power(mid, effect, disc, sims=3000) >= 0.8: hi = mid
        else: lo = mid
    print(f"  effect {effect:.0f} points: about {hi} units (power {power(hi, effect, disc, sims=4000):.2f})")

print("== 3d. Between-arm manipulation check: test share of post-compaction steps, and of the three steps right after each compaction")
import glob, re
for f in sorted(glob.glob("runs/main_s*_*.jsonl")):
    arm = re.search(r"main_s(\d)_(\w+)\.jsonl", f); seed, a = arm.group(1), arm.group(2)
    post = tests = soon = soon_tests = 0
    for l in open(f):
        r = json.loads(l)
        if r.get("error"): continue
        log = r["log"]; seen_compact = False; after = 0
        for e in log:
            if e["ev"] == "compact": seen_compact = True; after = 3; continue
            if e["ev"] != "step": continue
            if seen_compact:
                post += 1; tests += e["kind"] == "test"
                if after > 0: soon += 1; soon_tests += e["kind"] == "test"; after -= 1
    print(f"  seed {seed} {a:6} post-compaction steps {post:5d}: tests {tests/post:.3f}; first three steps after a compaction {soon:4d}: tests {soon_tests/max(soon,1):.3f}")

print("== 4. Figure 3 facts: tasks solved by k of the five flat/fresh runs; per-run resolved counts")
files = {"flat s0": "runs/main_s0_flat.jsonl", "flat s1": "runs/main_s1_flat.jsonl", "fresh s0": "runs/main_s0_fresh.jsonl",
         "fresh s1": "runs/main_s1_fresh.jsonl", "fresh s0 rerun": "runs/rep_r1_s0_c8000_fresh.jsonl"}
res = {k: {json.loads(l)["iid"]: bool(json.loads(l)["resolved"]) for l in open(v) if not json.loads(l).get("error")} for k, v in files.items()}
tasks = set().union(*[set(t for t, v in d.items() if v) for d in res.values()])
hist = collections.Counter(sum(res[k].get(t, False) for k in res) for t in tasks)
print("  solved by k runs:", dict(sorted(hist.items())), "total tasks solved at least once:", len(tasks))
print("  per-run resolved:", {k: sum(d.values()) for k, d in res.items()})

print("== 5. Where resolutions happen: compaction and submission step (seed 0 and 1 matrix runs, 8K cap)")
import glob as _g
runs5 = []
for f in _g.glob("runs/main_s*_*.jsonl"):
    for l in open(f):
        r = json.loads(l)
        if not r.get("error"): runs5.append(r)
nc = [r for r in runs5 if not any(e["ev"] == "compact" for e in r["log"])]
cp = [r for r in runs5 if any(e["ev"] == "compact" for e in r["log"])]
print(f"  runs {len(runs5)}: never compacted {len(nc)} ({sum(bool(r['resolved']) for r in nc)} resolved), compacted {len(cp)} ({sum(bool(r['resolved']) for r in cp)} resolved)")
first_c = sorted(sum(1 for x in r["log"][:next(i for i, e in enumerate(r["log"]) if e["ev"] == "compact")] if x["ev"] == "step") for r in cp)
print(f"  median step of first compaction {first_c[len(first_c)//2]}")
sub = sorted(r["steps"] for r in runs5 if r["status"] == "submitted" and r["resolved"])
print(f"  resolving submissions {len(sub)}: median step {sub[len(sub)//2]}, 90th pct {sub[int(0.9*len(sub))]}, max {sub[-1]}; by step 40: {sum(s <= 40 for s in sub)}, by step 60: {sum(s <= 60 for s in sub)}")
late = [r for r in runs5 if r["steps"] > 40]
print(f"  runs still going after step 40: {len(late)}, of which later submitted a resolving patch: {sum(r['status']=='submitted' and r['resolved'] for r in late)}, resolved at the cap: {sum(r['status']=='step_limit' and r['resolved'] for r in late)}")
print(f"  resolved among step-limit runs overall: {sum(r['status']=='step_limit' and bool(r['resolved']) for r in runs5)} of {sum(r['status']=='step_limit' for r in runs5)}")
