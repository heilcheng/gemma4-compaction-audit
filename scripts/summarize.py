"""Summarise runs/main_s{seed}_{arm}.jsonl into results/summary.json and results/per_run.csv.

Same record format, exclusions and 'complete across all arms' rule as scripts/analyze.py.
Usage: python scripts/summarize.py [--concurrency 24]
Run from the repo root. Exits 0 on partial or missing data.
"""
import argparse, collections, csv, glob, json, os, random, re, statistics

ARMS = ["mask", "summ", "flat", "fresh", "ctrl"]
EXCLUDE = {"psf__requests-1766", "pylint-dev__pylint-7277"}  # gold patch fails preflight
RATE_USD_PER_GPU_HOUR = 2.4984
N_BOOT = 5000
BOOT_SEED = 1
KINDS = ["read", "edit", "test"]


def load():
    """runs[(seed, arm, iid)] = record; later lines override earlier ones (as in analyze.py)."""
    runs = {}
    for f in sorted(glob.glob("runs/main_s*_*.jsonl")):
        m = re.fullmatch(r"main_s(\d+)_(\w+)\.jsonl", os.path.basename(f))
        if not m:
            continue
        seed = int(m.group(1))
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue  # partially written trailing line while runs are in progress
                if r.get("error") or r["iid"] in EXCLUDE:
                    continue
                runs[(seed, r["arm"], r["iid"])] = r
    return runs


def feats(r, conc):
    steps = [e for e in r["log"] if e["ev"] == "step"]
    comps = [e for e in r["log"] if e["ev"] == "compact"]
    t = r["totals"]
    model_s = t["model_s"] + t["summ_s"]
    return {
        "resolved": int(bool(r["resolved"])),
        "status": r["status"],
        "steps": r["steps"],
        "completion": t["completion"],
        "summ_completion": t["summ_completion"],
        "gen_tokens": t["completion"] + t["summ_completion"],
        "model_s": model_s,
        "tool_s": t["tool_s"],
        "wall_s": r.get("wall_s"),
        "n_compactions": len(comps),
        "any_test": int(any(e["kind"] == "test" for e in steps)),
        "stale_test_at_compact": int(any(e.get("stale_tests_retained", 0) > 0 for e in comps)),
        "stale_read_at_compact": int(any(e.get("stale_reads_retained", 0) > 0 for e in comps)),
        "kinds": collections.Counter(e["kind"] for e in steps),
        "est_cost_usd": model_s / 3600.0 * RATE_USD_PER_GPU_HOUR / conc,
    }


def mean(xs):
    return statistics.mean(xs) if xs else None


def median(xs):
    return statistics.median(xs) if xs else None


def boot_ci(groups, stat):
    """groups: list (one per task) of lists of values. Resample tasks; stat maps flat list -> number."""
    if not groups:
        return None
    rng = random.Random(BOOT_SEED)
    k = len(groups)
    out = []
    for _ in range(N_BOOT):
        flat = [v for g in rng.choices(groups, k=k) for v in g]
        out.append(stat(flat))
    out.sort()
    return [out[int(0.025 * N_BOOT)], out[int(0.975 * N_BOOT)]]


def summarize(units, F, arms=None):
    arms = arms or ARMS
    """units: list of (seed, iid) complete across all arms. F[(seed,arm,iid)] = features."""
    res = {"n_units": len(units), "n_tasks": len({i for _, i in units}), "arms": {}, "vs_flat": {}, "per_repo": {}}
    by_task = collections.defaultdict(list)
    for s, i in units:
        by_task[i].append(s)
    tasks = sorted(by_task)
    for a in arms:
        fs = [F[(s, a, i)] for s, i in units]
        n = len(fs)
        d = {"n": n}
        if n:
            nres = sum(f["resolved"] for f in fs)
            groups = [[F[(s, a, i)]["resolved"] for s in by_task[i]] for i in tasks]
            gen = [f["gen_tokens"] for f in fs]
            d.update({
                "resolved": nres, "rate": nres / n, "rate_ci95": boot_ci(groups, statistics.mean),
                "mean_gen_tokens": mean(gen), "median_gen_tokens": median(gen),
                "mean_model_s": mean([f["model_s"] for f in fs]),
                "mean_tool_s": mean([f["tool_s"] for f in fs]),
                "step_limit": sum(f["status"] == "step_limit" for f in fs),
                "compactions": sum(f["n_compactions"] for f in fs),
                "runs_compacted": sum(f["n_compactions"] > 0 for f in fs),
                "tasks_any_test": sum(f["any_test"] for f in fs),
                "tasks_stale_test_at_compact": sum(f["stale_test_at_compact"] for f in fs),
                "tasks_stale_read_at_compact": sum(f["stale_read_at_compact"] for f in fs),
                "step_kinds": dict(sum((f["kinds"] for f in fs), collections.Counter())),
                "estimated_mean_cost_usd_per_run": mean([f["est_cost_usd"] for f in fs]),
            })
        res["arms"][a] = d
        if a == "flat" or not n:
            continue
        diffs = [[F[(s, a, i)]["resolved"] - F[(s, "flat", i)]["resolved"] for s in by_task[i]] for i in tasks]
        allv = [v for g in diffs for v in g]
        res["vs_flat"][a] = {
            "mean_diff": mean(allv), "ci95": boot_ci(diffs, statistics.mean),
            "wins": sum(v > 0 for v in allv), "losses": sum(v < 0 for v in allv),
        }
    repos = collections.defaultdict(collections.Counter)
    for s, i in units:
        repo = i.split("__")[0]
        repos[repo]["n"] += 1
        for a in arms:
            repos[repo][a] += F[(s, a, i)]["resolved"]
    res["per_repo"] = {r: dict(c) for r, c in sorted(repos.items())}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=float, default=24, help="assumed concurrent runs per GPU, for the cost estimate")
    args = ap.parse_args()
    conc = args.concurrency

    runs = load()
    F = {k: feats(r, conc) for k, r in runs.items()}
    seeds = sorted({s for s, _, _ in runs})
    common_by_seed, seen_by_seed, arms_by_seed = {}, {}, {}
    for s in seeds:
        tasks = {i for (ss, a, i) in runs if ss == s}
        seen_by_seed[s] = len(tasks)
        arms_by_seed[s] = [a for a in ARMS if any(ss == s and aa == a for ss, aa, _ in runs)]
        common_by_seed[s] = sorted(t for t in tasks if all((s, a, t) in runs for a in arms_by_seed[s]))

    out = {
        "meta": {
            "arms": ARMS, "seeds": seeds, "excluded_tasks": sorted(EXCLUDE),
            "bootstrap": {"unit": "task", "resamples": N_BOOT, "rng_seed": BOOT_SEED, "ci": 0.95},
            "gen_tokens_definition": "completion + summ_completion",
            "model_s_definition": "model_s + summ_s",
            "estimated_cost": {
                "label": "estimated",
                "formula": "(model_s + summ_s) / 3600 * RATE_USD_PER_GPU_HOUR / assumed_concurrency",
                "RATE_USD_PER_GPU_HOUR": RATE_USD_PER_GPU_HOUR, "assumed_concurrency": conc,
            },
            "note": "all statistics use only tasks complete across all arms for that seed; per_run.csv lists every non-excluded run with in_common flag",
        },
        "per_seed": {}, "pooled": None,
    }
    all_units = []
    for s in seeds:
        units = [(s, i) for i in common_by_seed[s]]
        all_units += units
        d = summarize(units, F, arms_by_seed[s])
        d["arms_present"] = arms_by_seed[s]
        d["n_tasks_seen"] = seen_by_seed[s]
        out["per_seed"][str(s)] = d
    # pooled over all five arms: only seeds that ran all five
    five = [(s, i) for s in seeds if arms_by_seed[s] == ARMS for i in common_by_seed[s]]
    out["pooled"] = summarize(five, F)
    out["pooled"]["note"] = "units from seeds with all five arms"
    # pooled primary trio over every seed that has flat, fresh and ctrl
    trio = ["flat", "fresh", "ctrl"]
    trio_units = [(s, i) for s in seeds if set(trio) <= set(arms_by_seed[s])
                  for i in sorted({i for (ss, a, i) in runs if ss == s}) if all((s, a, i) in runs for a in trio)]
    out["pooled_trio"] = summarize(trio_units, F, trio)
    out["pooled_trio"]["note"] = "flat, fresh, ctrl over every seed that ran them"
    kinds_all = collections.Counter()
    for a in ARMS:
        kinds_all.update(out["pooled"]["arms"][a].get("step_kinds", {}))
    out["step_kinds_overall"] = dict(kinds_all)

    os.makedirs("results", exist_ok=True)
    with open("results/summary.json", "w") as fh:
        json.dump(out, fh, indent=2)

    common_set = set(all_units)
    cols = ["seed", "arm", "iid", "repo", "resolved", "status", "steps", "completion_tokens", "summ_tokens",
            "model_s", "tool_s", "wall_s", "n_compactions", "any_test", "stale_test_at_compact",
            "in_common", "est_cost_usd"]
    with open("results/per_run.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for (s, a, i) in sorted(runs, key=lambda k: (k[0], ARMS.index(k[1]) if k[1] in ARMS else 99, k[2])):
            f = F[(s, a, i)]
            w.writerow([s, a, i, i.split("__")[0], f["resolved"], f["status"], f["steps"], f["completion"],
                        f["summ_completion"], round(f["model_s"], 3), round(f["tool_s"], 3),
                        "" if f["wall_s"] is None else round(f["wall_s"], 3), f["n_compactions"], f["any_test"],
                        f["stale_test_at_compact"], int((s, i) in common_set), round(f["est_cost_usd"], 5)])
    print(f"wrote results/summary.json and results/per_run.csv ({len(runs)} runs, seeds {seeds})")

    # Added runs outside the main matrix (Amendment 3): the 16K-cap arm and the same-seed fresh replicate.
    extra = []
    for f in sorted(glob.glob("runs/cap*_s*_*.jsonl") + glob.glob("runs/rep_*.jsonl")):
        for line in open(f):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("error") or r["iid"] in EXCLUDE:
                continue
            fe = feats(r, conc)
            extra.append([r["seed"], r["arm"], r["cap"], r.get("rep", ""), r["iid"], r["iid"].split("__")[0], fe["resolved"],
                          fe["status"], fe["steps"], fe["completion"], fe["n_compactions"], fe["any_test"], fe["stale_test_at_compact"]])
    with open("results/per_run_extra.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["seed", "arm", "cap", "rep", "iid", "repo", "resolved", "status", "steps", "completion_tokens",
                    "n_compactions", "any_test", "stale_test_at_compact"])
        w.writerows(extra)
    print(f"wrote results/per_run_extra.csv ({len(extra)} runs: 16K-cap arm and replicate)")


if __name__ == "__main__":
    main()
