"""Exploratory and descriptive numbers quoted in the paper that analyze.py and summarize.py do not print.
All post hoc (Amendment 3). Usage: python scripts/extra_stats.py
"""
import collections, glob, json, random, re, statistics

EXCLUDE = {"psf__requests-1766", "pylint-dev__pylint-7277"}
TRIO = ["flat", "fresh", "ctrl"]
FIVE = ["mask", "summ", "flat", "fresh", "ctrl"]

runs = {}
for f in glob.glob("runs/main_s*_*.jsonl"):
    s = int(re.search(r"main_s(\d+)_", f).group(1))
    for l in open(f):
        r = json.loads(l)
        if r.get("error") or r["iid"] in EXCLUDE:
            continue
        runs[(s, r["arm"], r["iid"])] = r
units = sorted({(s, t) for s, a, t in runs if all((s, b, t) in runs for b in TRIO)})


def boot(a, b, us, n=5000):
    rng = random.Random(1)
    tasks = sorted({t for _, t in us}); byt = collections.defaultdict(list)
    for s, t in us:
        byt[t].append(int(bool(runs[(s, a, t)]["resolved"])) - int(bool(runs[(s, b, t)]["resolved"])))
    m = statistics.mean(v for t in tasks for v in byt[t])
    bs = sorted(statistics.mean(v for t in rng.choices(tasks, k=len(tasks)) for v in byt[t]) for _ in range(n))
    return m * 100, bs[int(0.025 * n)] * 100, bs[int(0.975 * n)] * 100


print("== fresh vs ctrl, pooled (%d units): %+.1f [%+.1f, %+.1f]" % ((len(units),) + boot("fresh", "ctrl", units)))
for name, us in [("django", [u for u in units if u[1].startswith("django")]), ("non-django", [u for u in units if not u[1].startswith("django")])]:
    res = {a: sum(bool(runs[(s, a, t)]["resolved"]) for s, t in us) for a in TRIO}
    print("== %s stratum, %d units, resolved %s, fresh vs flat %+.1f [%+.1f, %+.1f] (exploratory)" % ((name, len(us), res) + boot("fresh", "flat", us)))

print("== seed 0: submitted vs step-limit runs and how many of each resolved")
for a in FIVE:
    c = collections.Counter()
    for (s, aa, t), r in runs.items():
        if s == 0 and aa == a:
            c[r["status"]] += 1; c[r["status"] + "_resolved"] += bool(r["resolved"])
    print(f"  {a:6} submitted {c['submitted']} ({c['submitted_resolved']} resolved), step_limit {c['step_limit']} ({c['step_limit_resolved']} resolved)")

print("== step kinds (read/edit/test)")
for label, seeds, arms in [("seed 0", [0], FIVE), ("both seeds", [0, 1], TRIO)]:
    for a in arms:
        k = collections.Counter(e["kind"] for (s, aa, t), r in runs.items() if aa == a and s in seeds for e in r["log"] if e["ev"] == "step")
        print(f"  {label} {a:6} {k['read']}/{k['edit']}/{k['test']}")

print("== seed 0: runs with at least one test step, django vs other repositories")
for a in FIVE:
    dj = [r for (s, aa, t), r in runs.items() if s == 0 and aa == a and t.startswith("django")]
    ot = [r for (s, aa, t), r in runs.items() if s == 0 and aa == a and not t.startswith("django")]
    f = lambda rs: sum(any(e["kind"] == "test" for e in r["log"] if e["ev"] == "step") for r in rs)
    print(f"  {a:6} django {f(dj)}/{len(dj)}  other {f(ot)}/{len(ot)}")

print("== django test-step share: dev pilots vs held-out flat seed 0")
for f in ["runs/dev_pilot1.jsonl", "runs/dev_pilot2.jsonl"]:
    steps = tests = 0
    for l in open(f):
        r = json.loads(l)
        if r.get("error") or not r["iid"].startswith("django") or r["arm"] not in FIVE:
            continue
        for e in r["log"]:
            if e["ev"] == "step":
                steps += 1; tests += e["kind"] == "test"
    print(f"  {f}: {tests}/{steps}")
steps = tests = 0
for (s, a, t), r in runs.items():
    if s == 0 and a == "flat" and t.startswith("django"):
        for e in r["log"]:
            if e["ev"] == "step":
                steps += 1; tests += e["kind"] == "test"
print(f"  held-out flat seed 0: {tests}/{steps}")

print("== discordant pairs, fresh vs flat")
for s in (0, 1):
    d = sum(bool(runs[(s, "fresh", t)]["resolved"]) != bool(runs[(s, "flat", t)]["resolved"]) for ss, t in units if ss == s)
    print(f"  seed {s}: {d}")

print("== tag lengths beyond the flat tag (characters)")
print("  fresh current", len(" current"), "fresh older", len(" older code state, not validated on current"), "ctrl", len(" seq-a, no validity claim made here"))

print("== held-out gold preflight and the main comparisons without the tasks whose gold patch fails")
gold = [json.loads(l) for l in open("runs/controls_heldout_gold.jsonl")]
gfail = sorted(r["iid"] for r in gold if not r.get("resolved") and not r.get("error"))
print(f"  gold resolved {sum(bool(r['resolved']) for r in gold)}/{len(gold)}, fails: {gfail}")
for a in FIVE:
    hit = [(s, t) for (s, aa, t), r in runs.items() if aa == a and t in gfail and r["resolved"]]
    if hit: print(f"  WARNING {a} resolved a gold-failing task: {hit}")
keep0 = [t for (s, a, t) in runs if s == 0 and a == "flat" and t not in gfail]
print("  seed 0 without them, n=%d:" % len(keep0), {a: sum(bool(runs[(0, a, t)]["resolved"]) for t in keep0) for a in FIVE})
u0 = [(0, t) for t in keep0 if all((0, b, t) in runs for b in FIVE)]
for a in ["mask", "summ", "fresh", "ctrl"]:
    print("    %s vs flat %+.1f [%+.1f, %+.1f]" % ((a,) + boot(a, "flat", u0)))
ug = [u for u in units if u[1] not in gfail]
print("  pooled trio without them, %d units:" % len(ug), {a: sum(bool(runs[(s, a, t)]["resolved"]) for s, t in ug) for a in TRIO})
print("    fresh vs flat %+.1f [%+.1f, %+.1f]" % boot("fresh", "flat", ug))
print("    ctrl vs flat %+.1f [%+.1f, %+.1f]" % boot("ctrl", "flat", ug))

print("== same-seed fresh replicate (r1, window logging) against the original seed-0 fresh run")
import os
if os.path.exists("runs/rep_r1_s0_c8000_fresh.jsonl"):
    rep = {}
    for l in open("runs/rep_r1_s0_c8000_fresh.jsonl"):
        r = json.loads(l)
        if not r.get("error"): rep[r["iid"]] = r
    orig = {t: runs[(0, "fresh", t)] for t in rep if (0, "fresh", t) in runs}
    common = sorted(orig)
    flips = [t for t in common if bool(orig[t]["resolved"]) != bool(rep[t]["resolved"])]
    print(f"  runs {len(rep)}, common {len(common)}, original resolved {sum(bool(orig[t]['resolved']) for t in common)}, replicate resolved {sum(bool(rep[t]['resolved']) for t in common)}")
    print(f"  flips {len(flips)} (gained {sum(bool(rep[t]['resolved']) for t in flips)}, lost {sum(bool(orig[t]['resolved']) for t in flips)}), both {sum(bool(orig[t]['resolved']) and bool(rep[t]['resolved']) for t in common)}, either {sum(bool(orig[t]['resolved']) or bool(rep[t]['resolved']) for t in common)}")
    first3 = lambda r: [e["action"] for e in r["log"] if e["ev"] == "step"][:3]
    print(f"  same first three actions {sum(first3(orig[t]) == first3(rep[t]) for t in common)}, same step count {sum(orig[t].get('steps') == rep[t].get('steps') for t in common)}")
    c = collections.Counter()
    for r in rep.values():
        comps = [e for e in r["log"] if e["ev"] == "compact"]; steps = [e for e in r["log"] if e["ev"] == "step"]
        wc = [e["window"] for e in comps if e.get("window")]; ws = [e["window"] for e in steps if e.get("window")]
        c["compacted"] += bool(comps); c["counter_flags"] += any(e.get("stale_tests_retained", 0) > 0 for e in comps)
        c["window_stale_test_at_compaction"] += any(w["stale_tests"] > 0 for w in wc)
        c["window_stale_result_at_compaction"] += any(w["stale_tests_with_result"] > 0 for w in wc)
        c["window_stale_result_any_step"] += any(w["stale_tests_with_result"] > 0 for w in ws)
        c["window_stale_result_without_current_test"] += any(w["stale_tests_with_result"] > 0 and not w["current_test_in_window"] for w in ws)
        c["steps_after_first_compaction"] += len(ws); c["steps_with_stale_result_in_window"] += sum(w["stale_tests_with_result"] > 0 for w in ws)
        c["resolved_among_exposed"] += bool(r["resolved"]) and any(w["stale_tests_with_result"] > 0 for w in ws)
    print("  window exposure:", dict(c))

print("== pooled fresh vs flat: task-clustered against unit-level bootstrap (Amendment 3 named the clustered one, after the seed-1 table was seen)")
def boot_units(a, b, us, n=5000):
    rng = random.Random(1)
    d = [int(bool(runs[(s, a, t)]["resolved"])) - int(bool(runs[(s, b, t)]["resolved"])) for s, t in us]
    bs = sorted(statistics.mean(rng.choices(d, k=len(d))) for _ in range(n))
    return statistics.mean(d) * 100, bs[int(0.025 * n)] * 100, bs[int(0.975 * n)] * 100
for a, b in [("fresh", "flat"), ("fresh", "ctrl"), ("ctrl", "flat")]:
    print("  %s vs %s clustered %+.1f [%+.2f, %+.2f]; unit-level %+.1f [%+.2f, %+.2f]" % ((a, b) + boot(a, b, units) + boot_units(a, b, units)))
print("== seed 0: runs with a stale read record counted at a compaction")
for a in FIVE:
    n = sum(any(e["ev"] == "compact" and e.get("stale_reads_retained", 0) > 0 for e in r["log"]) for (s, aa, t), r in runs.items() if s == 0 and aa == a)
    print(f"  {a:6} {n}/145")
