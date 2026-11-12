"""Figures from results/summary.json and results/per_run.csv.

Writes figures/quality_cost.{pdf,png}, figures/step_kinds.pdf, figures/exposure.pdf.
Run from the repo root after scripts/summarize.py. Exits 0 on partial or empty data.
"""
import csv, json, os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ARMS = ["mask", "summ", "flat", "fresh", "ctrl"]
# Okabe-Ito colorblind-safe palette
COL = {"mask": "#E69F00", "summ": "#56B4E9", "flat": "#009E73", "fresh": "#D55E00", "ctrl": "#CC79A7"}
KIND_COL = {"read": "#0072B2", "edit": "#E69F00", "test": "#009E73"}
W = 3.3

plt.rcParams.update({
    "font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9,
    "savefig.dpi": 300, "figure.dpi": 300, "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False,
})


def empty(ax, msg="no data yet"):
    ax.text(0.5, 0.5, msg, ha="center", va="center", transform=ax.transAxes)


def quality_cost(pooled):
    fig, ax = plt.subplots(figsize=(W, 2.6))
    drawn = False
    for a in ARMS:
        d = pooled["arms"].get(a, {})
        if not d.get("n") or d.get("rate_ci95") is None:
            continue
        x, y = d["mean_gen_tokens"] / 1000, d["rate"]
        lo, hi = d["rate_ci95"]
        ax.errorbar(x, y, yerr=[[max(y - lo, 0)], [max(hi - y, 0)]], fmt="o", color=COL[a], capsize=3, ms=5, lw=1)
        off = {"mask": (5, 5), "summ": (-28, 8), "flat": (5, -12), "fresh": (5, 5), "ctrl": (5, -12)}.get(a, (5, 5))
        ax.annotate(a, (x, y), textcoords="offset points", xytext=off, color=COL[a])
        drawn = True
    if not drawn:
        empty(ax)
    ax.set_xlabel("Mean generated tokens per run (thousands)")
    ax.set_ylabel("Resolved rate")
    ax.margins(x=0.15)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(f"figures/extra/quality_cost.{ext}")
    plt.close(fig)


def step_kinds(pooled):
    fig, ax = plt.subplots(figsize=(W, 2.4))
    arms = [a for a in ARMS if pooled["arms"].get(a, {}).get("n")]
    if not arms:
        empty(ax)
    else:
        bottom = [0] * len(arms)
        for k in ("read", "edit", "test"):
            vals = [pooled["arms"][a]["step_kinds"].get(k, 0) for a in arms]
            ax.bar(arms, vals, bottom=bottom, color=KIND_COL[k], label=k, width=0.7)
            bottom = [b + v for b, v in zip(bottom, vals)]
        ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.22), ncol=3, columnspacing=0.8, handlelength=1)
    ax.set_ylabel("Steps (count)")
    fig.tight_layout()
    fig.savefig("figures/extra/step_kinds.pdf"); fig.savefig("figures/extra/step_kinds.png")
    plt.close(fig)


def exposure():
    rows = []
    if os.path.exists("results/per_run.csv"):
        with open("results/per_run.csv") as fh:
            rows = [r for r in csv.DictReader(fh) if r.get("in_common") == "1"]
    fig, ax = plt.subplots(figsize=(W, 2.6))
    arms = [a for a in ARMS if any(r["arm"] == a for r in rows)]
    if not arms:
        empty(ax)
    else:
        series = [("Compacted", lambda r: int(r["n_compactions"]) > 0, "#0072B2"),
                  ("Ran a test", lambda r: r["any_test"] == "1", "#E69F00"),
                  ("Stale test retained", lambda r: r["stale_test_at_compact"] == "1", "#D55E00")]
        bw = 0.27
        for j, (name, f, c) in enumerate(series):
            vals = []
            for a in arms:
                rs = [r for r in rows if r["arm"] == a]
                vals.append(sum(f(r) for r in rs) / len(rs))
            ax.bar([i + (j - 1) * bw for i in range(len(arms))], vals, width=bw, color=c, label=name)
        ax.set_xticks(range(len(arms)))
        ax.set_xticklabels(arms)
        ax.set_ylim(0, 1.0)
        ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.25), ncol=2, columnspacing=0.8, handlelength=1)
    ax.set_ylabel("Share of runs")
    fig.tight_layout()
    fig.savefig("figures/extra/exposure.pdf"); fig.savefig("figures/extra/exposure.png")
    plt.close(fig)


def main():
    os.makedirs("figures", exist_ok=True)
    try:
        with open("results/summary.json") as fh:
            pooled = json.load(fh)["pooled"]
    except (OSError, ValueError, KeyError):
        pooled = {"arms": {}}
    quality_cost(pooled)
    step_kinds(pooled)
    exposure()
    print("flips figure:", flips())
    print("wrote figures/extra/quality_cost, step_kinds, exposure (.pdf, .png)")



def flips():
    """Figure 4: which of the five flat and fresh runs resolved each task that any of them resolved."""
    import json, glob
    runs = {}
    for f, key in [("runs/main_s0_flat.jsonl", "flat s0"), ("runs/main_s1_flat.jsonl", "flat s1"),
                   ("runs/main_s0_fresh.jsonl", "fresh s0"), ("runs/main_s1_fresh.jsonl", "fresh s1"),
                   ("runs/rep_r1_s0_c8000_fresh.jsonl", "fresh s0 rerun")]:
        for l in open(f):
            r = json.loads(l)
            if not r.get("error"):
                runs[(key, r["iid"])] = bool(r["resolved"])
    cols = ["flat s0", "flat s1", "fresh s0", "fresh s1", "fresh s0 rerun"]
    tasks = sorted({t for (k, t), v in runs.items() if v}, key=lambda t: (-sum(runs.get((c, t), False) for c in cols), t))
    nfill = {t: sum(bool(runs.get((c, t), False)) for c in cols) for t in tasks}
    n_all = sum(v == len(cols) for v in nfill.values())          # solved in all five runs
    n_one = sum(v == 1 for v in nfill.values())                  # solved in exactly one run
    totals = {c: sum(bool(runs.get((c, t), False)) for t in tasks) for c in cols}
    DJ, OTHER = "#E69F00", "#999999"                            # repository group: django versus other
    fig, ax = plt.subplots(figsize=(4.4, 0.17 * len(tasks) + 1.3))
    for j, c in enumerate(cols):
        for i, t in enumerate(tasks):
            v = runs.get((c, t))
            ax.plot(j, i, "o", ms=5, color="#1f77b4" if v else ("#dddddd" if v is not None else "white"),
                    mec="#1f77b4" if v else "#bbbbbb", mew=0.6)
    for i, t in enumerate(tasks):
        ax.add_patch(plt.Rectangle((-0.78, i - 0.4), 0.1, 0.8, color=DJ if t.startswith("django__") else OTHER, lw=0, clip_on=False))
    n = len(tasks)
    for j, c in enumerate(cols):
        ax.text(j, n + 0.35, str(totals[c]), ha="center", va="center", fontsize=7, fontweight="bold")
    ax.text(-0.5, n + 0.35, "resolved", ha="right", va="center", fontsize=6.5, color="#555555")
    ax.plot([-0.5, len(cols) - 0.5], [n - 0.35, n - 0.35], color="#cccccc", lw=0.5)
    ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=30, ha="right", fontsize=7)
    ax.set_yticks(range(len(tasks))); ax.set_yticklabels([t.replace("__", " ") for t in tasks], fontsize=5.5)
    ax.set_ylim(n + 0.9, -0.7); ax.set_xlim(-0.8, len(cols) - 0.5)
    ax.tick_params(length=0); ax.spines["left"].set_visible(False); ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", pad=6)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=DJ, label="django"), Patch(color=OTHER, label="other repositories")], loc="lower left",
               ncol=2, frameon=False, fontsize=6.5, handlelength=1.0, columnspacing=1.2, bbox_to_anchor=(0.0, 0.0))
    ax.set_title(f"{n_all} of {n} tasks solved in all five passes, {n_one} in only one", fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig("figures/flips.pdf"); fig.savefig("figures/flips.png")
    return n, totals, n_all, n_one

if __name__ == "__main__":
    main()
