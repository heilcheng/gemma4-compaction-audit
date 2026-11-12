"""Recompute the paper's numbers from the released files only.

usage: python3 -I scripts/recompute_from_release.py <repo-root> [--full]
Reads only <root>/results/{per_run.csv,per_run_extra.csv,summary.json}, <root>/logs/actions/*.jsonl.gz and
<root>/logs/diag/*.jsonl.gz.
Never imports or runs anything from the clone.  Standard library only (Python 3.9+).
--full also runs the 1-point-effect power search (adds about a minute).
"""
import csv, gzip, json, random, statistics, sys, time, collections, os

ROOT = sys.argv[1]
FULL = "--full" in sys.argv
T0 = time.time()
RESULTS = []  # (item, paper, recomputed, source, status)


def rec(item, paper, got, src, tol=None):
    if tol is None:
        ok = (str(paper) == str(got))
    else:
        ok = abs(float(paper) - float(got)) <= tol
    RESULTS.append((item, paper, got, src, "MATCH" if ok else "DIFF"))
    return ok


def load_log(name):
    out = []
    with gzip.open(os.path.join(ROOT, "logs", "actions", name + ".jsonl.gz"), "rt") as f:
        for line in f:
            out.append(json.loads(line))
    return out


ARMS = ["mask", "summ", "flat", "fresh", "ctrl"]
main = {}
for s in (0, 1):
    for a in ARMS:
        try:
            main[(s, a)] = load_log("main_s%d_%s" % (s, a))
        except FileNotFoundError:
            pass
rep = load_log("rep_r1_s0_c8000_fresh")
P = lambda *a: print(*a)


def res(r):
    return 1 if r["resolved"] else 0


def by_iid(rows):
    return {r["iid"]: res(r) for r in rows}


def compacts(r):
    return [e for e in r["log"] if e["ev"] == "compact"]


def pct(x):
    return "%+.1f" % (100 * x)


# ---------------------------------------------------------------- bootstrap helpers
def boot_ci_rr(units, B=5000, seed=1, variant="int"):
    """units: list of paired differences (arm - flat) in {-1,0,1}. Resample units with replacement.
    returns (mean, lo, hi) in points. variant picks the percentile index convention."""
    rng = random.Random(seed)
    n = len(units)
    means = []
    for _ in range(B):
        means.append(sum(units[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    if variant == "int":
        lo, hi = means[int(0.025 * B)], means[int(0.975 * B)]
    else:  # symmetric: 125th smallest and 125th largest
        lo, hi = means[int(0.025 * B)], means[B - 1 - int(0.025 * B)]
    return 100 * sum(units) / n, 100 * lo, 100 * hi


def boot_ci(units, B=5000, seed=1):
    rng = random.Random(seed)
    n = len(units)
    idx = list(range(n))
    means = sorted(sum(units[i] for i in rng.choices(idx, k=n)) / n for _ in range(B))
    return 100 * sum(units) / n, 100 * means[int(0.025 * B)], 100 * means[int(0.975 * B)]


def fmt_ci(t):
    return "%+.1f [%+.1f, %+.1f]" % t


def norm_zero(s):  # paper writes 0.0 without sign
    return s.replace("+0.0 [", "0.0 [", 1) if s.startswith("+0.0 [") else s


# ================================================================ (a) Table 1
P("=" * 78)
P("(a) TABLE 1, seed 0 (per_run.csv; cross-checked against logs/actions)")
rows = list(csv.DictReader(open(os.path.join(ROOT, "results", "per_run.csv"))))
paper_t1 = {  # n, resolved, step_limit, compacted, stale_test_retained, ci vs flat, W/L
    "mask": (145, 14, 112, 131, 24, "+0.7 [-2.8, +4.1]", "4/3"),
    "summ": (145, 15, 114, 126, 26, "+1.4 [-2.8, +5.5]", "6/4"),
    "flat": (145, 13, 113, 126, 25, "reference", ""),
    "fresh": (145, 13, 114, 135, 32, "0.0 [-4.1, +4.1]", "5/5"),
    "ctrl": (145, 15, 112, 124, 23, "+1.4 [-2.8, +5.5]", "6/4"),
}
flat0 = {r["iid"]: int(r["resolved"]) for r in rows if r["seed"] == "0" and r["arm"] == "flat"}
for a in ARMS:
    rs = [r for r in rows if r["seed"] == "0" and r["arm"] == a]
    n = len(rs)
    k = sum(int(r["resolved"]) for r in rs)
    sl = sum(r["status"] == "step_limit" for r in rs)
    cp = sum(int(r["n_compactions"]) > 0 for r in rs)
    st = sum(int(r["stale_test_at_compact"]) > 0 for r in rs)
    lg = main[(0, a)]
    cp_l = sum(len(compacts(r)) > 0 for r in lg)
    st_l = sum(any(e["stale_tests_retained"] > 0 for e in compacts(r)) for r in lg)
    k_l = sum(res(r) for r in lg)
    sl_l = sum(r["status"] == "step_limit" for r in lg)
    pn = paper_t1[a]
    rec("T1 %s n" % a, pn[0], n, "per_run.csv")
    rec("T1 %s resolved" % a, pn[1], k, "per_run.csv")
    rec("T1 %s step-limit" % a, pn[2], sl, "per_run.csv")
    rec("T1 %s compacted" % a, pn[3], cp, "per_run.csv")
    rec("T1 %s stale test retained" % a, pn[4], st, "per_run.csv")
    rec("T1 %s (log check) resolved/steplimit/compacted/stale" % a,
        "%d/%d/%d/%d" % pn[1:5], "%d/%d/%d/%d" % (k_l, sl_l, cp_l, st_l), "logs/actions")
    if a != "flat":
        d = {r["iid"]: int(r["resolved"]) - flat0[r["iid"]] for r in rs}
        units = [d[t] for t in sorted(d)]
        w, l = sum(u > 0 for u in units), sum(u < 0 for u in units)
        ci = norm_zero(fmt_ci(boot_ci(units)))
        rec("T1 %s vs flat CI" % a, pn[5], ci, "per_run.csv")
        rec("T1 %s wins/losses" % a, pn[6], "%d/%d" % (w, l), "per_run.csv")

# ================================================================ (b) bootstraps
P("=" * 78)
P("(b) PAIRED BOOTSTRAP vs flat (5000 resamples, random.Random(1), percentile 2.5/97.5)")
R = {}
for (s, a), lg in main.items():
    R[(s, a)] = by_iid(lg)
t1 = sorted(set(R[(1, "flat")]) & set(R[(1, "fresh")]) & set(R[(1, "ctrl")]))
d1 = [R[(1, "fresh")][t] - R[(1, "flat")][t] for t in t1]
d0 = [R[(0, "fresh")][t] - R[(0, "flat")][t] for t in sorted(R[(0, "flat")])]
variants = {}
for nm, u in (("seed0 fresh-flat", d0), ("seed1 fresh-flat", d1)):
    variants[nm] = {
        "randrange/int": fmt_ci(boot_ci_rr(u)),
        "randrange/sym": fmt_ci(boot_ci_rr(u, variant="sym")),
        "choices/int": fmt_ci(boot_ci(u)),
    }
    P("  %-18s n=%d  %s" % (nm, len(u), variants[nm]))
# pooled units
units = []  # (seed, task)
for s in (0, 1):
    com = set(R[(s, "flat")]) & set(R[(s, "fresh")]) & set(R[(s, "ctrl")])
    for t in sorted(com):
        units.append((s, t))
rec("pooled complete units (seed,task)", 289, len(units), "logs/actions")
pd = [R[(s, "fresh")][t] - R[(s, "flat")][t] for s, t in units]
tasks_all = sorted(set(t for _, t in units))
by_task = collections.defaultdict(list)
for (s, t), d in zip(units, pd):
    by_task[t].append(d)


def cluster_boot(by_task, tasks, B=5000, seed=1, mode="ratio", obs_units=None):
    rng = random.Random(seed)
    n = len(tasks)
    out = []
    for _ in range(B):
        pick = rng.choices(tasks, k=n)  # rng.choices order reproduces the paper; a randrange loop moves some endpoints by one step
        if mode == "ratio":
            tot = sum(sum(by_task[t]) for t in pick)
            cnt = sum(len(by_task[t]) for t in pick)
            out.append(tot / cnt)
        else:  # mean of per-task means
            out.append(sum(sum(by_task[t]) / len(by_task[t]) for t in pick) / n)
    out.sort()
    ou = pd if obs_units is None else obs_units
    obs = 100 * sum(ou) / len(ou)
    return obs, 100 * out[int(0.025 * B)], 100 * out[int(0.975 * B)]


cl_ratio = cluster_boot(by_task, tasks_all)
cl_mean = cluster_boot(by_task, tasks_all, mode="meanofmeans")
un = boot_ci_rr(pd)
un_c = boot_ci(pd)
P("  pooled clustered (ratio estimator): %s ; (mean of task means): %s" % (fmt_ci(cl_ratio), fmt_ci(cl_mean)))
P("  pooled unit-level (randrange): %s ; (choices): %s" % (fmt_ci(un), fmt_ci(un_c)))
rec("seed 0 fresh vs flat", "0.0 [-4.1, +4.1]", norm_zero(fmt_ci(boot_ci(d0))), "logs (resolved flags)")
rec("seed 1 fresh vs flat (144 tasks)", "-2.8 [-6.9, +1.4]", fmt_ci(boot_ci(d1)), "logs (resolved flags)")
rec("pooled clustered fresh vs flat", "-1.4 [-3.8, +1.0]", fmt_ci(cl_ratio), "logs (resolved flags)")
rec("pooled unit-level fresh vs flat (rng.choices order)", "[-4.5, +1.7]", "[%+.1f, %+.1f]" % (un_c[1], un_c[2]), "logs (resolved flags)")
P("  INFO: with a rng.randrange resampling loop instead of rng.choices the unit-level upper end is %+.1f (one 1/289 step lower); the interval is otherwise unchanged" % un[2])
rec("seed1 resolved flat/fresh/ctrl (144)", "16/12/12",
    "%d/%d/%d" % tuple(sum(R[(1, a)][t] for t in t1) for a in ("flat", "fresh", "ctrl")), "logs")
rec("pooled resolved flat/fresh/ctrl", "29/25/27",
    "%d/%d/%d" % tuple(sum(R[(s, a)][t] for s, t in units) for a in ("flat", "fresh", "ctrl")), "logs")
pc = [R[(s, "ctrl")][t] - R[(s, "flat")][t] for s, t in units]
pf = [R[(s, "fresh")][t] - R[(s, "ctrl")][t] for s, t in units]
def cl_for(vals):
    bt_ = collections.defaultdict(list)
    for (s, t), d in zip(units, vals):
        bt_[t].append(d)
    return cluster_boot(bt_, tasks_all, obs_units=vals)
rec("pooled fresh vs ctrl (clustered)", "-0.7 [-3.8, +2.4]", fmt_ci(cl_for(pf)), "logs")
rec("pooled ctrl vs flat (clustered)", "-0.7 [-3.8, +2.4]", fmt_ci(cl_for(pc)), "logs")

# ================================================================ (c) flips
P("=" * 78)
P("(c) FLIP COUNTS")
def disc(a, b):
    com = sorted(set(a) & set(b))
    return sum(a[t] != b[t] for t in com), len(com)
Rrep = by_iid(rep)
d_ff, n_ff = disc(R[(0, "flat")], R[(1, "flat")])
rec("flat s0 vs s1 discordant", "11 of 144", "%d of %d" % (d_ff, n_ff), "logs")
d_a, n_a = disc(R[(0, "fresh")], R[(0, "flat")])
d_b, n_b = disc(R[(1, "fresh")], R[(1, "flat")])
rec("fresh vs flat seed 0", "10 of 145", "%d of %d" % (d_a, n_a), "logs")
rec("fresh vs flat seed 1", "10 of 144", "%d of %d" % (d_b, n_b), "logs")
d_c, n_c = disc(R[(0, "fresh")], R[(1, "fresh")])
rec("fresh s0 vs fresh s1 (not in paper text; eval_noise.txt says 13)", "13 of 145", "%d of %d" % (d_c, n_c), "logs")
d_d, n_d = disc(R[(0, "fresh")], Rrep)
rec("fresh s0 vs same-seed replicate", "13 of 145", "%d of %d" % (d_d, n_d), "logs (rep)")
extra = list(csv.DictReader(open(os.path.join(ROOT, "results", "per_run_extra.csv"))))
rep_csv = {r["iid"]: int(r["resolved"]) for r in extra if r["rep"] == "r1"}
rec("replicate flips from per_run_extra.csv", "13 of 145", "%d of %d" % disc(R[(0, "fresh")], rep_csv), "per_run_extra.csv")
rec("replicate resolved / original", "16 / 13", "%d / %d" % (sum(Rrep.values()), sum(R[(0, "fresh")].values())), "logs/per_run_extra")
g = sum(Rrep[t] > R[(0, "fresh")][t] for t in Rrep); l = sum(Rrep[t] < R[(0, "fresh")][t] for t in Rrep)
rec("replicate gained/lost", "8/5", "%d/%d" % (g, l), "logs")
pr = list(csv.DictReader(open(os.path.join(ROOT, "results", "per_run.csv"))))
prd = {(int(r["seed"]), r["arm"], r["iid"]): r for r in pr}
fl_tot = fl_exp = fl_nocomp = 0
for (s_, a_, i_), r_ in prd.items():
    f_ = prd.get((s_, "flat", i_))
    if a_ != "fresh" or f_ is None or r_["resolved"] == f_["resolved"]:
        continue
    fl_tot += 1
    fl_exp += int(r_["stale_test_at_compact"]) > 0
    fl_nocomp += int(r_["n_compactions"]) == 0
rec("tag flips (both seeds) with fresh counter positive", "9 of 20", "%d of %d" % (fl_exp, fl_tot), "per_run.csv")
rec("tag flips where the fresh run never compacted", "2", "%d" % fl_nocomp, "per_run.csv")
passes = {"flat0": R[(0, "flat")], "flat1": R[(1, "flat")], "fresh0": R[(0, "fresh")], "fresh1": R[(1, "fresh")], "fresh0rep": Rrep}
solved = set(t for p in passes.values() for t, v in p.items() if v)
hist = collections.Counter(sum(p.get(t, 0) for p in passes.values()) for t in solved)
rec("tasks solved by all five", 6, hist[5], "logs")
rec("tasks solved by exactly one", 13, hist[1], "logs")
rec("tasks solved at least once", 29, len(solved), "logs")
P("  distribution of k solved: %s" % dict(sorted(hist.items())))
rec("fresh resolved across three passes", "13, 12, 16", "%d, %d, %d" % (sum(R[(0, "fresh")].values()), sum(R[(1, "fresh")].values()), sum(Rrep.values())), "logs")
pairs3 = [(R[(0, "flat")], R[(1, "flat")]), (R[(0, "fresh")], R[(1, "fresh")]), (R[(0, "fresh")], Rrep)]
nd = sum(disc(a, b)[0] for a, b in pairs3)
nn = sum(disc(a, b)[1] for a, b in pairs3)
DISC = nd / nn
rec("discordance over three rerun pairs", 0.085, "%.3f" % DISC, "logs", tol=0.0005)
rec("only 67 of 145 replicate runs repeat first three actions", 67,
    sum(1 for a, b in zip(sorted(main[(0, "fresh")], key=lambda r: r["iid"]), sorted(rep, key=lambda r: r["iid"]))
        if [e["action"] for e in a["log"] if e["ev"] == "step"][:3] == [e["action"] for e in b["log"] if e["ev"] == "step"][:3]),
    "logs (action strings)")

# ================================================================ (d) funnel
P("=" * 78)
P("(d) EXPOSURE FUNNEL (replicate log)")
c_comp = c_flag = c_wst = c_wres = c_any = c_nocur = 0
post = stale_steps = exposed_steps = 0
resolved_exp = 0
n_exp_runs = 0
post_ord = 0  # alternative definition: steps logged after first compact event
for r in rep:
    cs = compacts(r)
    if cs:
        c_comp += 1
    if any(e["stale_tests_retained"] > 0 for e in cs):
        c_flag += 1
    if any((e.get("window") or {}).get("stale_tests", 0) > 0 for e in cs):
        c_wst += 1
    if any((e.get("window") or {}).get("stale_tests_with_result", 0) > 0 for e in cs):
        c_wres += 1
    seen = False
    any_res = nocur = False
    for e in r["log"]:
        if e["ev"] == "compact":
            seen = True
        elif e["ev"] == "step":
            if seen:
                post_ord += 1
            w = e.get("window")
            if w:
                post += 1
                if w["stale_tests_with_result"] > 0:
                    any_res = True
                    stale_steps += 1
                    if not w["current_test_in_window"]:
                        nocur = True
                        exposed_steps += 1
    c_any += any_res
    c_nocur += nocur
    if nocur:
        n_exp_runs += 1
        resolved_exp += res(r)
rec("compacted runs", 125, c_comp, "rep log")
rec("counter-flagged (stale_tests_retained>0)", 22, c_flag, "rep log")
rec("stale test record in window at a compaction", 20, c_wst, "rep log")
rec("stale test with result in window at a compaction", 16, c_wres, "rep log")
rec("stale result in window at some step", 16, c_any, "rep log")
rec("... with no current test beside it at some step", 16, c_nocur, "rep log")
rec("resolved among those", 1, resolved_exp, "rep log")
rec("post-compaction steps (steps with a window)", 2587, post, "rep log")
rec("post-compaction steps (steps after first compact event, log order)", 2587, post_ord, "rep log")
rec("steps with stale result in window", 251, stale_steps, "rep log")
rec("exposed steps (stale result, no current test)", 168, exposed_steps, "rep log")
P("  expected resolved among 16 exposed runs: %.1f at the original fresh rate 13/145, %.1f at the replicate's own rate 16/145" % (16 * 13 / 145, 16 * 16 / 145))
c_res_comp = sum(res(r) for r in rep if any(e["ev"] == "compact" for e in r["log"]))
rec("resolved among compacted replicate runs", 7, c_res_comp, "rep log")
rec("expected resolved among 16 exposed at the compacted-run rate", 0.9, "%.1f" % (16 * c_res_comp / c_comp), "arithmetic")
# next-step test probe
ex_t = ex_n = nx_t = nx_n = 0
for r in rep:
    for e in r["log"]:
        if e["ev"] == "step" and e.get("window"):
            w = e["window"]
            if w["stale_tests_with_result"] > 0 and not w["current_test_in_window"]:
                ex_n += 1; ex_t += e["kind"] == "test"
            else:
                nx_n += 1; nx_t += e["kind"] == "test"
rec("test rate at exposed steps (20 pct) / others (6 pct)", "20 / 6", "%.0f / %.0f" % (100 * ex_t / ex_n, 100 * nx_t / nx_n), "rep log")

# ================================================================ (e) compaction split
P("=" * 78)
P("(e) COMPACTION SPLIT over matrix runs")
allr = [r for lg in main.values() for r in lg]
rec("matrix runs", 1159, len(allr), "logs")
nc = [r for r in allr if not compacts(r)]
cp = [r for r in allr if compacts(r)]
rec("never compacted / resolved", "124 / 55", "%d / %d" % (len(nc), sum(res(r) for r in nc)), "logs")
rec("compacted / resolved", "1035 / 55", "%d / %d" % (len(cp), sum(res(r) for r in cp)), "logs")
rec("compacted resolved rate pct", 5.3, "%.1f" % (100 * sum(res(r) for r in cp) / len(cp)), "logs", tol=0.05)
rec("never-compacted resolved rate pct", 44, "%.0f" % (100 * sum(res(r) for r in nc) / len(nc)), "logs", tol=0.5)
def first_comp_step(r):
    n = 0
    for e in r["log"]:
        if e["ev"] == "compact":
            return n
        if e["ev"] == "step":
            n += 1
fc = sorted(first_comp_step(r) for r in cp)
rec("median first-compaction step (steps logged before it)", 14, statistics.median(fc), "logs")
fc2 = sorted(e["step"] for r in cp for e in compacts(r)[:1])
rec("median first-compaction step (compact event 'step' field)", 14, statistics.median(fc2), "logs")
sub = sorted(r["steps"] for r in allr if r["status"] == "submitted" and res(r))
rec("resolving submissions", 85, len(sub), "logs")
rec("resolving submissions median step", 14, statistics.median(sub), "logs")
rec("resolving submissions by step 40", 78, sum(s <= 40 for s in sub), "logs")
rec("resolving submissions max step", 61, max(sub), "logs")
late = [r for r in allr if r["steps"] > 40]
rec("runs past step 40", 972, len(late), "logs")
rec("... later resolving submissions", 7, sum(r["status"] == "submitted" and res(r) for r in late), "logs")
rec("... resolved at the step limit", 25, sum(r["status"] == "step_limit" and res(r) for r in late), "logs")
arm_late = {}
for (s_, a_), lg in main.items():
    arm_late.setdefault(a_, []).extend(r for r in lg if r["steps"] > 40)
late_rates = sorted(round(100 * sum(res(r) for r in v) / len(v)) for v in arm_late.values())
rec("resolved rate past step 40 per arm, seeds pooled (paper: 2 to 4 percent)", "2-4", "%d-%d" % (late_rates[0], late_rates[-1]), "logs")
sl = sum(r["status"] == "step_limit" for r in allr) / len(allr)
P("  step-limit share overall %.1f pct; per (seed,arm): %s" % (100 * sl, {
    "%d%s" % k: "%.0f" % (100 * sum(r["status"] == "step_limit" for r in v) / len(v)) for k, v in main.items()}))
rec("step-limit share range pct (paper: 77 to 84)", "77-84",
    "%d-%d" % (min(round(100 * sum(r["status"] == "step_limit" for r in v) / len(v)) for v in main.values()),
               max(round(100 * sum(r["status"] == "step_limit" for r in v) / len(v)) for v in main.values())), "logs")
# replies with no complete bash block: they run nothing, are not logged, and count toward the step limit
def n_cmd(r):
    return sum(e["ev"] == "step" for e in r["log"])
def n_empty(r):
    return r["steps"] - n_cmd(r) - (1 if r["status"] == "submitted" else 0)
tot_replies = sum(r["steps"] for r in allr)
tot_empty = sum(n_empty(r) for r in allr)
rec("replies in the matrix", 80083, tot_replies, "logs")
rec("replies with no complete command, pct", 46, "%.0f" % (100 * tot_empty / tot_replies), "logs", tol=0.5)
rec("... in never-compacted runs, pct", 3, "%.0f" % (100 * sum(n_empty(r) for r in nc) / sum(r["steps"] for r in nc)), "logs", tol=0.5)
rec("... in compacted runs, pct", 48, "%.0f" % (100 * sum(n_empty(r) for r in cp) / sum(r["steps"] for r in cp)), "logs", tol=0.5)
arm_all = {}
for (s_, a_), lg in main.items():
    arm_all.setdefault(a_, []).extend(lg)
er = sorted(round(100 * sum(n_empty(r) for r in v) / sum(r["steps"] for r in v)) for v in arm_all.values())
rec("... per arm, seeds pooled (paper: 39 to 49)", "39-49", "%d-%d" % (er[0], er[-1]), "logs")
slr = [r for r in allr if r["status"] == "step_limit"]
def last_cmd(r):
    ii = [e["i"] for e in r["log"] if e["ev"] == "step"]
    return max(ii) if ii else -1
rec("step-limit runs / last command within 40 replies", "921 / 428",
    "%d / %d" % (len(slr), sum(last_cmd(r) < 40 for r in slr)), "logs")
# replies with no command cluster: transition rates between consecutive replies, and the unbroken run of
# them that ends a step-limit run (its length is the step limit minus one minus the last command's index)
def seq(r):
    ii = set(e["i"] for e in r["log"] if e["ev"] == "step")
    n = r["steps"] - (1 if r["status"] == "submitted" else 0)
    return [i in ii for i in range(n)]
ee = ec = ce = cc = 0
for r in allr:
    q = seq(r)
    for u, v in zip(q, q[1:]):
        if u and v: cc += 1
        elif u: ce += 1
        elif v: ec += 1
        else: ee += 1
rec("no command after a reply with none, pct", 90, "%.0f" % (100 * ee / (ee + ec)), "logs", tol=0.5)
rec("no command after a reply with one, pct", 10, "%.0f" % (100 * ce / (ce + cc)), "logs", tol=0.5)
def tail(r):
    return r["steps"] - 1 - last_cmd(r) if r["status"] == "step_limit" else 0
tl = sorted(tail(r) for r in allr if tail(r) > 0)
rec("runs that end in replies with no command / median length", "630 / 56", "%d / %d" % (len(tl), tl[len(tl) // 2]), "logs")
rec("share of no-command replies in those final runs, pct", 84, "%.0f" % (100 * sum(tl) / tot_empty), "logs", tol=0.5)
st = [r for r in allr if tail(r) >= 10]
ot = [r for r in allr if tail(r) < 10]
rec("runs ending in ten or more no-command replies / resolved", "570 / 13", "%d / %d" % (len(st), sum(res(r) for r in st)), "logs")
rec("other runs / resolved", "589 / 97", "%d / %d" % (len(ot), sum(res(r) for r in ot)), "logs")
P("  ending in ten or more, per (seed,arm): %s" % {"%d%s" % k: "%d/%d" % (sum(tail(r) >= 10 for r in v), len(v)) for k, v in main.items()})
sa = {a_: round(100 * sum(tail(r) >= 10 for r in v) / len(v)) for a_, v in arm_all.items()}
rec("... share per arm, seeds pooled: mask, summ, flat, fresh, ctrl", "35 40 54 52 53", " ".join(str(sa[a_]) for a_ in ARMS), "logs")
# completion tokens per reply, least squares through the origin on (empty replies, other replies)
sxx = sxy = syy = sxz = syz = 0.0
for r in allr:
    x, y, z = n_empty(r), r["steps"] - n_empty(r), r["totals"]["completion"]
    sxx += x * x; sxy += x * y; syy += y * y; sxz += x * z; syz += y * z
det = sxx * syy - sxy * sxy
rec("completion tokens per reply with no command (paper: ran to 1200)", 1200, "%.0f" % ((sxz * syy - syz * sxy) / det), "logs", tol=10)
P("  completion tokens per other reply: %.0f" % ((syz * sxx - sxz * sxy) / det))
# test steps 1967 of 27411 seed 0
s0 = [r for a in ARMS for r in main[(0, a)]]
nt = sum(e["kind"] == "test" for r in s0 for e in r["log"] if e["ev"] == "step")
ns = sum(1 for r in s0 for e in r["log"] if e["ev"] == "step")
rec("seed-0 test steps / all steps", "1967 / 27411", "%d / %d" % (nt, ns), "logs")

# ================================================================ (f) noise
P("=" * 78)
P("(f) EVAL NOISE (reimplemented from the description in eval_noise.txt)")
rng = random.Random(1)
sds = []
for nm, (a, b) in (("flat s0 vs s1", (R[(0, "flat")], R[(1, "flat")])),
                   ("fresh s0 vs s1", (R[(0, "fresh")], R[(1, "fresh")])),
                   ("fresh s0 vs rerun", (R[(0, "fresh")], Rrep))):
    tk = sorted(set(a) & set(b))
    dd = {t: a[t] - b[t] for t in tk}
    ds = [statistics.mean(dd[t] for t in rng.choices(tk, k=120)) * 100 for _ in range(5000)]
    sd = statistics.pstdev(ds)
    sds.append(sd)
    P("  %-18s n=%d discordant=%d bootstrap SD of 120-task two-pass difference = %.2f points" % (nm, len(tk), sum(v != 0 for v in dd.values()), sd))
rec("bootstrap SD range (paper: 2.5 to 2.7)", "2.5-2.7", "%.1f-%.1f" % (min(sds), max(sds)), "logs")
rec("analytic SD sqrt(0.085/120) pct", 2.7, "%.2f" % (100 * (0.085 / 120) ** 0.5), "arithmetic", tol=0.05)
rec("analytic SD with recomputed discordance", 2.7, "%.2f" % (100 * (DISC / 120) ** 0.5), "logs", tol=0.05)


def power(n_units, effect_pts, disc_, sims, rng):
    p = (effect_pts / 100 / disc_ + 1) / 2
    hits = 0
    rnd = rng.random
    for _ in range(sims):
        k = sum(1 for _ in range(n_units) if rnd() < disc_)
        if k == 0:
            continue
        w = sum(1 for _ in range(k) if rnd() < p)
        z = (w - k / 2) / (k ** 0.5 / 2)
        hits += abs(z) >= 1.96
    return hits / sims


prng = random.Random(1)
pw = power(289, 2.0, DISC, 6000, prng)
P("  power at 289 units, 2-point effect, normal-approx sign test, 6000 sims: %.3f" % pw)
rec("power at 289 units for 2-point effect (pct)", 22, "%.0f" % (100 * pw), "logs + sim", tol=1.0)
pw290 = power(290, 2.0, DISC, 6000, prng)
P("  (290 units: %.3f)" % pw290)
# exact binomial variant
def power_exact(n_units, effect_pts, disc_, sims, rng):
    from math import comb
    p = (effect_pts / 100 / disc_ + 1) / 2
    hits = 0
    for _ in range(sims):
        k = sum(1 for _ in range(n_units) if rng.random() < disc_)
        if k == 0:
            continue
        w = sum(1 for _ in range(k) if rng.random() < p)
        m = min(w, k - w)
        pv = min(1.0, 2 * sum(comb(k, i) for i in range(0, m + 1)) / 2 ** k)
        hits += pv < 0.05
    return hits / sims
pwx = power_exact(289, 2.0, DISC, 3000, prng)
P("  power at 289 units with exact binomial test: %.3f" % pwx)
# units needed for 80 percent power, 2-point
lo, hi = 200, 4000
while hi - lo > 100:
    mid = (lo + hi) // 2
    if power(mid, 2.0, DISC, 2000, prng) >= 0.8:
        hi = mid
    else:
        lo = mid
P("  units for 80 pct power at a 2-point effect (bisection to 100): about %d (paper: about 1700; eval_noise.txt: 1675)" % hi)
rec("units for 80 pct power, 2-point (within 150 of 1700)", 1700, hi, "logs + sim", tol=150)
if FULL:
    lo, hi = 2000, 12000
    while hi - lo > 200:
        mid = (lo + hi) // 2
        if power(mid, 1.0, DISC, 1500, prng) >= 0.8:
            hi = mid
        else:
            lo = mid
    rec("units for 80 pct power, 1-point (within 500 of 6700)", 6700, hi, "logs + sim", tol=500)

# ================================================================ (g) test share
P("=" * 78)
P("(g) TEST SHARE of post-compaction steps")
paper_g = {(0, "flat"): 9.1, (0, "fresh"): 6.4, (0, "ctrl"): 10.9, (1, "flat"): 3.8, (1, "fresh"): 10.2, (1, "ctrl"): 7.1}
for key, pv in paper_g.items():
    post = tests = 0
    for r in main[key]:
        seen = False
        for e in r["log"]:
            if e["ev"] == "compact":
                seen = True
            elif e["ev"] == "step" and seen:
                post += 1
                tests += e["kind"] == "test"
    rec("test share post-compaction seed %d %s (pct)" % key, pv, "%.1f" % (100 * tests / post), "logs", tol=0.05)

# ================================================================ other claims
P("=" * 78)
P("OTHER CHECKS (Results paragraph, Abstract)")
# stale test retained 18 pct of task-runs
pu = [(s, a, t) for s, t in units for a in ("flat", "fresh", "ctrl")]
lgmap = {(s, a): {r["iid"]: r for r in main[(s, a)]} for s in (0, 1) for a in ARMS if (s, a) in main}
ret = [any(e["stale_tests_retained"] > 0 for e in compacts(lgmap[(s, a)][t])) for s, a, t in pu]
rec("stale test retained share of trio task-runs (pct, paper 18)", 18, "%.0f" % (100 * sum(ret) / len(ret)), "logs", tol=0.5)
fr = [(s, t) for s, t in units if any(e["stale_tests_retained"] > 0 for e in compacts(lgmap[(s, "fresh")][t]))]
fl = [(s, t) for s, t in units if any(e["stale_tests_retained"] > 0 for e in compacts(lgmap[(s, "flat")][t]))]
rec("among stale-retained: fresh resolved x of n", "6 of 57", "%d of %d" % (sum(R[(s, "fresh")][t] for s, t in fr), len(fr)), "logs")
rec("among stale-retained: flat resolved x of n", "5 of 49", "%d of %d" % (sum(R[(s, "flat")][t] for s, t in fl), len(fl)), "logs")
# django strata
dj = [(s, t) for s, t in units if t.startswith("django__")]
nd_ = [(s, t) for s, t in units if not t.startswith("django__")]
rec("django strata units",130,len(dj),"logs")
rec("other strata units",159,len(nd_),"logs")
rec("django strata flat/fresh/ctrl", "15/8/9", "/".join(str(sum(R[(s, a)][t] for s, t in dj)) for a in ("flat", "fresh", "ctrl")), "logs")
rec("other strata flat/fresh/ctrl", "14/17/18", "/".join(str(sum(R[(s, a)][t] for s, t in nd_)) for a in ("flat", "fresh", "ctrl")), "logs")
dd_ = [R[(s, "fresh")][t] - R[(s, "flat")][t] for s, t in dj]
bt_ = collections.defaultdict(list)
for (s, t), d in zip(dj, dd_): bt_[t].append(d)
rec("django stratum fresh vs flat (clustered)", "-5.4 [-10.0, -0.8]", fmt_ci(cluster_boot(bt_, sorted(bt_), obs_units=dd_)), "logs")
dd2 = [R[(s, "fresh")][t] - R[(s, "flat")][t] for s, t in nd_]
bt2 = collections.defaultdict(list)
for (s, t), d in zip(nd_, dd2): bt2[t].append(d)
rec("non-django stratum fresh vs flat (clustered)", "+1.9 [+0.0, +4.4]", fmt_ci(cluster_boot(bt2, sorted(bt2), obs_units=dd2)), "logs")
sr = [any(e["stale_reads_retained"] > 0 for e in compacts(lgmap[(s, a)][t])) for s, a, t in pu]
rec("stale read retained share of trio task-runs (pct; paper: three fifths to two thirds; target 60-67, midpoint 63.5 tol 3.5)", 63.5, "%.1f" % (100 * sum(sr) / len(sr)), "logs", tol=3.5)
per = [100 * sum(any(e["stale_reads_retained"] > 0 for e in compacts(r)) for r in main[(s, a)]) / len(main[(s, a)]) for s in (0,) for a in ARMS]
P("  stale-read share by seed-0 arm (pct): %s" % ["%.0f" % x for x in per])
tpr = [sum(e["kind"] == "test" for e in r["log"] if e["ev"] == "step") for a in ARMS for r in main[(0, a)]]
P("  tests per run seed 0 overall: mean %.1f, median %s (paper: 2.2 to 3.6 per run by arm, median zero)" % (statistics.mean(tpr), statistics.median(tpr)))
rng_ = sorted(statistics.mean(sum(e["kind"] == "test" for e in r["log"] if e["ev"] == "step") for r in main[(0, a)]) for a in ARMS)
rec("tests per run by arm, seed 0 (min-max)", "2.2-3.6", "%.1f-%.1f" % (rng_[0], rng_[-1]), "logs")
rec("gold-preflight failing tasks", "psf__requests-1921,pylint-dev__pylint-6528,pylint-dev__pylint-7080", ",".join(sorted(r["iid"] for r in load_log("controls_heldout_gold") if not r["resolved"])), "logs")
# 16K arm
c16 = {a: load_log("cap16000_s0_" + a) for a in ("flat", "fresh")}
rec("16K resolved flat/fresh", "16/11", "%d/%d" % (sum(map(res, c16["flat"])), sum(map(res, c16["fresh"]))), "logs")
rec("16K compacted flat/fresh", "93/99", "%d/%d" % tuple(sum(bool(compacts(r)) for r in c16[a]) for a in ("flat", "fresh")), "logs")
rec("16K stale test retained flat/fresh", "17/22", "%d/%d" % tuple(sum(any(e["stale_tests_retained"] > 0 for e in compacts(r)) for r in c16[a]) for a in ("flat", "fresh")), "logs")
d16 = [res(a) - res(b) for a, b in zip(sorted(c16["fresh"], key=lambda r: r["iid"]), sorted(c16["flat"], key=lambda r: r["iid"]))]
rec("16K fresh vs flat", "-3.4 [-8.3, +1.4]", fmt_ci(boot_ci(d16)), "logs")
# summary.json spot checks
sj = json.load(open(os.path.join(ROOT, "results", "summary.json")))
rec("summary.json pooled_trio fresh vs flat mean/CI (pct)", "-1.4 [-3.8, +1.0]",
    "%+.1f [%+.1f, %+.1f]" % (100 * sj["pooled_trio"]["vs_flat"]["fresh"]["mean_diff"], 100 * sj["pooled_trio"]["vs_flat"]["fresh"]["ci95"][0], 100 * sj["pooled_trio"]["vs_flat"]["fresh"]["ci95"][1]), "summary.json")
# gold preflight
gold = load_log("controls_heldout_gold")
rec("gold preflight resolved", "142 of 145", "%d of %d" % (sum(map(res, gold)), len(gold)), "logs (controls_heldout_gold)")

# ================================================================ report
P("=" * 78)
P("%-62s %-22s %-22s %-6s" % ("ITEM", "PAPER", "RECOMPUTED", ""))
# ================================================================ (h) round-7 additions
P("=" * 78)
P("(h) RUN AVERAGES, SUBMISSIONS, STRATA SIGN COUNTS")
from math import comb as _comb
pr7 = [r for r in csv.DictReader(open(os.path.join(ROOT, "results", "per_run.csv"))) if r["arm"] in ("mask", "summ", "flat", "fresh", "ctrl")]
st7 = [int(r["steps"]) for r in pr7]
rec("matrix runs: mean steps", 69, round(sum(st7) / len(st7)), "per_run.csv")
rec("matrix runs: mean wall minutes", 50, round(sum(float(r["wall_s"]) for r in pr7) / len(pr7) / 60), "per_run.csv")
rec("matrix runs: completion tokens per step", 680, int(round(sum(int(r["completion_tokens"]) for r in pr7) / sum(st7), -1)), "per_run.csv")
rs7 = [r for r in pr7 if r["resolved"] == "1"]
rec("resolved runs: mean steps", 32, round(sum(int(r["steps"]) for r in rs7) / len(rs7)), "per_run.csv")
rec("resolved runs: mean wall minutes", 20, round(sum(float(r["wall_s"]) for r in rs7) / len(rs7) / 60), "per_run.csv")
rec("resolutions that submitted / all", "85 of 110", "%d of %d" % (sum(r["status"] == "submitted" for r in rs7), len(rs7)), "per_run.csv")
repo7 = {r["iid"]: r["repo"] for r in pr7}
def wl(pred):
    w = l = 0
    for sd in (0, 1):
        for t in R[(sd, "fresh")]:
            if t in R[(sd, "flat")] and pred(repo7[t]):
                d = R[(sd, "fresh")][t] - R[(sd, "flat")][t]
                w += d > 0; l += d < 0
    return w, l
def sign_p(w, l):
    n = w + l; k = min(w, l)
    return min(1.0, 2 * sum(_comb(n, j) for j in range(k + 1)) / 2 ** n)
w7, l7 = wl(lambda x: x == "django"); rec("django wins/losses fresh vs flat (pooled)", "3/10", "%d/%d" % (w7, l7), "logs")
rec("django sign test p", 0.09, "%.2f" % sign_p(w7, l7), "arithmetic")
w8, l8 = wl(lambda x: x != "django"); rec("non-django gains/losses fresh vs flat (pooled)", "5/2", "%d/%d" % (w8, l8), "logs")
rec("non-django sign test p", 0.45, "%.2f" % sign_p(w8, l8), "arithmetic")
def p_ge(k, n=120, d=0.085):
    tot = 0.0
    for m in range(n + 1):
        pm = _comb(n, m) * d ** m * (1 - d) ** (n - m)
        tot += pm * sum(_comb(m, j) / 2 ** m for j in range(m + 1) if abs(2 * j - m) >= k)
    return tot
rec("P(gap >= 5 points on 120 tasks), one in twelve", 0.084, "%.3f" % p_ge(6), "arithmetic")
rec("P(gap >= 6 points on 120 tasks), one in twenty", 0.042, "%.3f" % p_ge(7), "arithmetic")

# the terminal stall by trigger and by arm (a run "stalls" when it ends in ten or more replies with no command)
def stalled(r):
    return tail(r) >= 10
rec("16K stalled runs flat/fresh", "33/31", "%d/%d" % tuple(sum(map(stalled, c16[a])) for a in ("flat", "fresh")), "logs")
rec("flat plus fresh resolved: 16K / 8000 trigger, seed 0", "27 / 26", "%d / %d" % (sum(res(r) for a_ in ("flat", "fresh") for r in c16[a_]), sum(res(r) for a_ in ("flat", "fresh") for r in main[(0, a_)])), "logs")
rec("16K stalled runs that resolved", 0, sum(res(r) for a in ("flat", "fresh") for r in c16[a] if stalled(r)), "logs")
def stall_pair(X, Y):
    x = {r["iid"]: stalled(r) for r in X}; y = {r["iid"]: stalled(r) for r in Y}
    k = [t for t in x if t in y]
    return sum(x[t] and not y[t] for t in k), sum(y[t] and not x[t] for t in k)
for a_ in ("flat", "fresh"):
    rec("%s: stalled only at 8000 / only at 16K" % a_, {"flat": "44 / 4", "fresh": "52 / 6"}[a_], "%d / %d" % stall_pair(main[(0, a_)], c16[a_]), "logs")
sp = stall_pair(main[(0, "flat")], main[(0, "mask")])
rec("seed 0: stalled only in flat / only in mask", "36 / 14", "%d / %d" % sp, "logs")
rec("... sign test p", 0.003, "%.3f" % sign_p(*sp), "arithmetic")
sp = stall_pair(main[(0, "flat")], main[(0, "summ")])
rec("seed 0: stalled only in flat / only in summ", "30 / 15", "%d / %d" % sp, "logs")
rec("... sign test p", 0.036, "%.3f" % sign_p(*sp), "arithmetic")
ncp = {a_: "%.1f" % statistics.mean(len(compacts(r)) for r in main[(0, a_)]) for a_ in ARMS}
rec("compactions per run, seed 0: mask, summ, flat, fresh, ctrl", "11.8 5.6 7.6 8.1 8.2", " ".join(ncp[a_] for a_ in ARMS), "logs")

# the no-command diagnostic (PROTOCOL.md Amendment 4): flat, seed 0, replies logged; diag = loop unchanged on 40
# tasks, dropfix = the text of a no-command reply replaced by a placeholder, on all 145
def load_diag(name):
    with gzip.open(os.path.join(ROOT, "logs", "diag", name + ".jsonl.gz"), "rt") as f:
        return {r["iid"]: r for r in map(json.loads, f) if not r.get("error")}
dg, fx = load_diag("diag_s0_flat"), load_diag("dropfix_s0_flat")
m0 = {r["iid"]: r for r in main[(0, "flat")]}
def empties(rs):
    return [e for r in rs for e in r["log"] if e["ev"] == "empty"]
def looped(e):
    return e["lines"] > 0 and e["thought_lines"] >= 0.9 * e["lines"]
ev = empties(dg.values())
rec("diagnostic, 40 tasks: replies / with no command", "2939 / 1303", "%d / %d" % (sum(r["steps"] for r in dg.values()), len(ev)), "logs/diag")
rec("... that ended at the reply limit", 1303, sum(e["finish"] == "length" for e in ev), "logs/diag")
rec("... one word repeated / cut off inside a code block", "1235 / 68",
    "%d / %d" % (sum(map(looped, ev)), sum((not looped(e)) and e["fences"] % 2 == 1 for e in ev)), "logs/diag")
rec("diagnostic: stalled runs / resolved", "23 / 6", "%d / %d" % (sum(map(stalled, dg.values())), sum(map(res, dg.values()))), "logs/diag")
f40 = [fx[t] for t in dg]
rec("placeholder, same 40 tasks: stalled runs / resolved", "0 / 5", "%d / %d" % (sum(map(stalled, f40)), sum(map(res, f40))), "logs/diag")
rec("no-command replies pct, 40 tasks: diagnostic / placeholder", "44 / 11",
    "%.0f / %.0f" % (100 * len(ev) / sum(r["steps"] for r in dg.values()), 100 * len(empties(f40)) / sum(r["steps"] for r in f40)), "logs/diag")
fa = [fx[t] for t in m0]; ma = list(m0.values())
rec("placeholder, all tasks: runs / no-command replies pct", "145 / 11", "%d / %.0f" % (len(fa), 100 * len(empties(fa)) / sum(r["steps"] for r in fa)), "logs/diag")
rec("stalled runs: seed-0 flat / placeholder", "73 / 0", "%d / %d" % (sum(map(stalled, ma)), sum(map(stalled, fa))), "logs")
rec("median commands per run: seed-0 flat / placeholder", "31 / 70", "%.0f / %.0f" % (statistics.median(map(n_cmd, ma)), statistics.median(map(n_cmd, fa))), "logs")
rec("completion tokens, placeholder as pct of seed-0 flat", 44, "%.0f" % (100 * sum(r["totals"]["completion"] for r in fa) / sum(r["totals"]["completion"] for r in ma)), "logs", tol=0.5)
rec("wall minutes per run: seed-0 flat / placeholder", "49 / 18", "%.0f / %.0f" % (sum(r["wall_s"] for r in ma) / len(ma) / 60, sum(r["wall_s"] for r in fa) / len(fa) / 60), "logs")
rec("step-limit runs: seed-0 flat / placeholder", "113 / 99", "%d / %d" % (sum(r["status"] == "step_limit" for r in ma), sum(r["status"] == "step_limit" for r in fa)), "logs")
rec("resolved: placeholder / seed-0 flat", "19 / 13", "%d / %d" % (sum(map(res, fa)), sum(map(res, ma))), "logs")
dfx = [res(fx[t]) - res(m0[t]) for t in sorted(m0)]
rec("placeholder against seed-0 flat", "+4.1 [-0.7, +9.0]", fmt_ci(boot_ci(dfx)), "logs")
gw, gl = sum(d > 0 for d in dfx), sum(d < 0 for d in dfx)
rec("... gained / lost", "10 / 4", "%d / %d" % (gw, gl), "logs")
rec("... sign test p", 0.18, "%.2f" % sign_p(gw, gl), "arithmetic")
allp = [sum(map(res, v)) for v in main.values()] + [sum(map(res, c16[a_])) for a_ in ("flat", "fresh")] + [sum(map(res, rep))]
rec("resolved count over the 11 earlier passes (min-max)", "11-16", "%d-%d" % (min(allp), max(allp)), "logs")

# Amendment 5: fresh under the changed loop, and what the changed loop leaves the tag to act on
gx = load_diag("dropfix_s0_fresh")
p0 = {r["iid"]: r for r in main[(0, "fresh")]}
ga = [gx[t] for t in m0]; pa = [p0[t] for t in m0]
def ret(r):
    return any(e["stale_tests_retained"] > 0 for e in compacts(r))
def win_res(r):
    return any((e.get("window") or {}).get("stale_tests_with_result", 0) > 0 for e in compacts(r))
rec("placeholder fresh: runs / stalled (seed-0 fresh stalled)", "145 / 0 (77)", "%d / %d (%d)" % (len(ga), sum(map(stalled, ga)), sum(map(stalled, pa))), "logs/diag")
rec("placeholder fresh: resolved (seed-0 fresh) / step limit", "13 (13) / 113", "%d (%d) / %d" % (sum(map(res, ga)), sum(map(res, pa)), sum(r["status"] == "step_limit" for r in ga)), "logs/diag")
dgf = [res(gx[t]) - res(fx[t]) for t in sorted(m0)]
rec("placeholder: fresh against flat", "-4.1 [-9.7, +1.4]", fmt_ci(boot_ci(dgf)), "logs/diag")
gw5, gl5 = sum(d > 0 for d in dgf), sum(d < 0 for d in dgf)
rec("... gained / lost / sign test p", "5 / 11 / 0.21", "%d / %d / %.2f" % (gw5, gl5, sign_p(gw5, gl5)), "logs/diag")
rec("both placeholder passes resolved / both seed-0 passes", "32 / 26", "%d / %d" % (sum(map(res, fa + ga)), sum(map(res, ma + pa))), "logs")
cmp_ = lambda rs: [r for r in rs if compacts(r)]
rec("flat, compacted runs resolved: placeholder / seed 0", "12 of 123 / 6 of 126", "%d of %d / %d of %d" % (sum(map(res, cmp_(fa))), len(cmp_(fa)), sum(map(res, cmp_(ma))), len(cmp_(ma))), "logs")
rec("flat, never-compacted runs resolved: placeholder / seed 0", "7 of 22 / 7 of 19", "%d of %d / %d of %d" % (sum(res(r) for r in fa if not compacts(r)), len(fa) - len(cmp_(fa)), sum(res(r) for r in ma if not compacts(r)), len(ma) - len(cmp_(ma))), "logs")
rec("counter retained a stale test: placeholder flat, fresh (seed-0 flat, fresh)", "27, 34 (25, 32)", "%d, %d (%d, %d)" % (sum(map(ret, fa)), sum(map(ret, ga)), sum(map(ret, ma)), sum(map(ret, pa))), "logs")
rec("window held one with a result marker: placeholder flat, fresh", "21, 27", "%d, %d" % (sum(map(win_res, fa)), sum(map(win_res, ga))), "logs/diag")
rec("... of those resolved: flat, fresh", "3, 0", "%d, %d" % (sum(res(r) for r in fa if win_res(r)), sum(res(r) for r in ga if win_res(r))), "logs/diag")
gc_ = cmp_(ga)
rec("placeholder fresh compacted runs resolved; expected among the 27", "7 of 128; 1.5", "%d of %d; %.1f" % (sum(map(res, gc_)), len(gc_), sum(map(win_res, ga)) * sum(map(res, gc_)) / len(gc_)), "logs/diag")
rec("P(none of the 27 resolve) at that compacted-run rate, about 0.2", 0.22, "%.2f" % ((1 - sum(map(res, gc_)) / len(gc_)) ** 27), "arithmetic")
dif5 = [t for t in sorted(m0) if res(gx[t]) != res(fx[t])]
rec("placeholder: tasks that differ / fresh run retained no stale test", "16 / 12", "%d / %d" % (len(dif5), sum(not ret(gx[t]) for t in dif5)), "logs/diag")
# all four pairs of flat and fresh passes: seed 0, seed 1, the 16K trigger, the changed loop
c16m = {a_: {r["iid"]: res(r) for r in c16[a_]} for a_ in ("flat", "fresh")}
four = [(R[(0, "flat")], R[(0, "fresh")]), (R[(1, "flat")], R[(1, "fresh")]), (c16m["flat"], c16m["fresh"]),
        ({t: res(r) for t, r in fx.items()}, {t: res(r) for t, r in gx.items()})]
bt4 = collections.defaultdict(list)
for fl_, fr_ in four:
    for t in sorted(set(fl_) & set(fr_)):
        bt4[t].append(int(fr_[t]) - int(fl_[t]))
all4 = [d for t in sorted(bt4) for d in bt4[t]]
rec("four pairs: task-runs / flat resolved / fresh resolved", "579 / 64 / 49",
    "%d / %d / %d" % (len(all4), sum(sum(fl_[t] for t in set(fl_) & set(fr_)) for fl_, fr_ in four), sum(sum(fr_[t] for t in set(fl_) & set(fr_)) for fl_, fr_ in four)), "logs")
rec("four pairs: fresh minus flat in tasks, per pair", "0, -4, -5, -6", ", ".join("%d" % sum(int(fr_[t]) - int(fl_[t]) for t in set(fl_) & set(fr_)) for fl_, fr_ in four), "logs")
rec("four pairs pooled fresh vs flat (clustered)", "-2.6 [-5.0, -0.3]", fmt_ci(cluster_boot(bt4, sorted(bt4), obs_units=all4)), "logs")
tw4, tl4 = sum(sum(v) > 0 for v in bt4.values()), sum(sum(v) < 0 for v in bt4.values())
rec("four pairs: tasks net for fresh / net for flat / sign test p", "9 / 18 / 0.12", "%d / %d / %.2f" % (tw4, tl4, sign_p(tw4, tl4)), "logs")
rec("four pairs: task-runs gained / lost", "17 / 32", "%d / %d" % (sum(d > 0 for d in all4), sum(d < 0 for d in all4)), "logs")
for nm, pv, pc, keep in (("django", "-6.2 [-10.4, -2.7]", "260 / 28 / 12", lambda t: t.startswith("django__")), ("other repositories", "+0.3 [-2.2, +2.8]", "319 / 36 / 37", lambda t: not t.startswith("django__"))):
    b4s = {t: v for t, v in bt4.items() if keep(t)}             # the four-pair pooling split by repository, post hoc
    u4s = [d for t in sorted(b4s) for d in b4s[t]]
    rec("four pairs, " + nm + ": task-runs / flat resolved / fresh resolved", pc, "%d / %d / %d" % (len(u4s),
        sum(sum(fl_[t] for t in set(fl_) & set(fr_) if keep(t)) for fl_, fr_ in four), sum(sum(fr_[t] for t in set(fl_) & set(fr_) if keep(t)) for fl_, fr_ in four)), "logs")
    rec("four pairs, " + nm + ": fresh vs flat (clustered)", pv, fmt_ci(cluster_boot(b4s, sorted(b4s), obs_units=u4s)), "logs")
loo = []
for k in range(4):                              # the same pooling with one pair left out
    b3 = collections.defaultdict(list)
    for q, (fl_, fr_) in enumerate(four):
        if q != k:
            for t in sorted(set(fl_) & set(fr_)):
                b3[t].append(int(fr_[t]) - int(fl_[t]))
    loo.append(fmt_ci(cluster_boot(b3, sorted(b3), obs_units=[d for t in sorted(b3) for d in b3[t]])))
for nm, pv, gv in zip(("seed 0", "seed 1", "16K", "placeholder"), ("-3.5 [-6.2, -0.9]", "-2.5 [-5.5, +0.2]", "-2.3 [-4.8, +0.2]", "-2.1 [-4.6, +0.5]"), loo):
    rec("three pairs pooled, leaving out " + nm, pv, gv, "logs")

bad = 0
for item, paper, got, src, st in RESULTS:
    P("%-62s %-22s %-22s %-6s [%s]" % (item[:62], str(paper)[:22], str(got)[:22], st, src))
    bad += st != "MATCH"
P("\n%d items, %d match, %d differ. runtime %.1f s%s" % (len(RESULTS), len(RESULTS) - bad, bad, time.time() - T0, "" if FULL else " (run with --full for the 1-point power search)"))
