"""Paper figures: overview schematic, differences against flat with intervals, and the exposure funnel.
Reads runs/*.jsonl (private) and writes figures/overview.{pdf,png}, figures/differences.{pdf,png},
figures/exposure_funnel.{pdf,png}. Usage: python scripts/make_paper_figures.py
Palette and mark rules follow a validated categorical set (blue, orange, aqua, yellow, magenta), thin marks,
hairline axes, direct labels in text colour."""
import collections, glob, gzip, json, random, re, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BLUE, ORANGE, AQUA, YELLOW, MAGENTA = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
INK, INK2, MUTED, RULE = "#0b0b0b", "#52514e", "#8a8984", "#d9d8d4"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": RULE, "axes.linewidth": 0.6,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.labelcolor": INK2, "text.color": INK,
                     "savefig.dpi": 300, "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
ARM_COLOR = {"mask": YELLOW, "summ": MAGENTA, "flat": AQUA, "fresh": ORANGE, "ctrl": BLUE}


def load():
    runs = {}
    for f in glob.glob("runs/main_s*_*.jsonl") + glob.glob("runs/cap16000_s0_*.jsonl"):
        m = re.search(r"(main|cap16000)_s(\d+)_(\w+)\.jsonl", f)
        cap = 16000 if m.group(1) == "cap16000" else 8000
        for l in open(f):
            r = json.loads(l)
            if not r.get("error"):
                runs[(cap, int(m.group(2)), r["arm"], r["iid"])] = bool(r["resolved"])
    for l in open("runs/rep_r1_s0_c8000_fresh.jsonl"):          # same-seed rerun of fresh (cap 8000, seed 0), kept under its own arm key
        r = json.loads(l)
        if not r.get("error"):
            runs[(8000, 0, "fresh_r1", r["iid"])] = bool(r["resolved"])
    for arm in ("flat", "fresh"):                               # corrected loop (cap 8000, seed 0), kept under its own cap key
        for l in gzip.open(f"logs/diag/dropfix_s0_{arm}.jsonl.gz", "rt"):
            r = json.loads(l)
            if not r.get("error"):
                runs[("fix", 0, arm, r["iid"])] = bool(r["resolved"])
    return runs


def boot_diff(runs, ka, kb, n=5000):
    """Paired difference (ka minus kb) in resolved rate with a bootstrap interval over tasks; ka, kb are (cap, seed, arm)."""
    tasks = sorted({t for (c, s, arm, t) in runs if (c, s, arm) == ka and (*kb, t) in runs})
    d = [int(runs[(*ka, t)]) - int(runs[(*kb, t)]) for t in tasks]
    rng = random.Random(1)
    bs = sorted(statistics.mean(rng.choices(d, k=len(d))) for _ in range(n))
    return statistics.mean(d) * 100, bs[int(0.025 * n)] * 100, bs[int(0.975 * n)] * 100, len(tasks)


def paired(runs, cap, seed, a, b, n=5000):
    return boot_diff(runs, (cap, seed, a), (cap, seed, b), n)


def pooled(runs, a, b, clustered=True, n=5000):
    units = sorted({(s, t) for (c, s, arm, t) in runs if c == 8000 and arm == a and s in (0, 1)
                    and all((8000, s, x, t) in runs for x in ("flat", "fresh", "ctrl"))})
    byt = collections.defaultdict(list)
    for s, t in units:
        byt[t].append(int(runs[(8000, s, a, t)]) - int(runs[(8000, s, b, t)]))
    rng = random.Random(1)
    if clustered:
        tasks = sorted(byt)
        bs = sorted(statistics.mean(v for t in rng.choices(tasks, k=len(tasks)) for v in byt[t]) for _ in range(n))
    else:
        d = [int(runs[(8000, s, a, t)]) - int(runs[(8000, s, b, t)]) for s, t in units]   # same order as extra_stats.py
        bs = sorted(statistics.mean(rng.choices(d, k=len(d))) for _ in range(n))
    m = statistics.mean(v for t in byt for v in byt[t])
    return m * 100, bs[int(0.025 * n)] * 100, bs[int(0.975 * n)] * 100, len(units)


def pooled_pairs(runs, n=5000):
    """Fresh minus flat over the four pairs of passes (seed 0, seed 1, 16K, corrected loop), bootstrap over tasks."""
    byt = collections.defaultdict(list)
    for c, s in ((8000, 0), (8000, 1), (16000, 0), ("fix", 0)):
        for t in sorted({t for (c2, s2, arm, t) in runs if (c2, s2, arm) == (c, s, "fresh") and (c, s, "flat", t) in runs}):
            byt[t].append(int(runs[(c, s, "fresh", t)]) - int(runs[(c, s, "flat", t)]))
    tasks = sorted(byt)
    rng = random.Random(1)
    bs = []
    for _ in range(n):
        v = [x for t in rng.choices(tasks, k=len(tasks)) for x in byt[t]]
        bs.append(statistics.mean(v))
    bs.sort()
    allv = [x for t in tasks for x in byt[t]]
    return statistics.mean(allv) * 100, bs[int(0.025 * n)] * 100, bs[int(0.975 * n)] * 100, len(allv)


def differences(runs):
    H, R = "hdr", "row"
    rows = [(H, "Same arm, rerun (noise reference)", False),
            (R, "flat, seed 1 minus seed 0", boot_diff(runs, (8000, 1, "flat"), (8000, 0, "flat")), "flat", True),
            (R, "fresh, same-seed rerun minus seed 0", boot_diff(runs, (8000, 0, "fresh_r1"), (8000, 0, "fresh")), "fresh", True),
            (H, "Seed 0, 145 tasks", False)]
    for a in ("mask", "summ", "fresh", "ctrl"):
        rows.append((R, a, paired(runs, 8000, 0, a, "flat"), a, False))
    rows += [(H, "Seed 1, 144 tasks", True)]
    for a in ("fresh", "ctrl"):
        rows.append((R, a, paired(runs, 8000, 1, a, "flat"), a, False))
    rows += [(H, "Pooled, 289 task-runs", True),
             (R, "fresh (task-clustered)", pooled(runs, "fresh", "flat", True), "fresh", False),
             (R, "fresh (each task-run independent)", pooled(runs, "fresh", "flat", False), "fresh", False),
             (R, "ctrl (task-clustered)", pooled(runs, "ctrl", "flat", True), "ctrl", False),
             (R, "fresh minus ctrl (task-clustered)", pooled(runs, "fresh", "ctrl", True), "fresh", False),
             (H, "16K trigger, seed 0", False), (R, "fresh", paired(runs, 16000, 0, "fresh", "flat"), "fresh", False),
             (H, "Corrected loop, seed 0", False), (R, "fresh", paired(runs, "fix", 0, "fresh", "flat"), "fresh", False),
             (H, "Four pairs pooled, post hoc", False), (R, "fresh (task-clustered)", pooled_pairs(runs), "fresh", False)]
    fig, ax = plt.subplots(figsize=(6.4, 4.7))
    ax.axvspan(-12, 0, color=RULE, alpha=0.25, lw=0, zorder=0)
    ax.axvspan(-2, 2, color=MUTED, alpha=0.22, lw=0, zorder=0)
    y = 0
    ys, labels, groups, cur = [], [], [], None
    for item in rows:
        if item[0] == H:
            if cur: groups.append(cur)
            cur = [y, y] if item[2] else None
            ax.text(-0.01, y, item[1], transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=7.5, color=INK, fontweight="bold")
            y -= 1
            continue
        _, label, (m, lo, hi, n), arm, hollow = item
        col = ARM_COLOR[arm]
        ax.plot([lo, hi], [y, y], color=col, lw=1.6, solid_capstyle="round", zorder=2)
        if hollow:
            ax.plot(m, y, "o", ms=5.5, mfc="white", mec=col, mew=1.3, zorder=3)
        else:
            ax.plot(m, y, "o", ms=5.5, color=col, mec="white", mew=1.2, zorder=3)
        ax.text(hi + 0.4, y, f"{m:+.1f} [{lo:+.1f}, {hi:+.1f}]", va="center", fontsize=6.8, color=INK2)
        ys.append(y); labels.append(label)
        if cur: cur[1] = y
        y -= 1
    if cur: groups.append(cur)
    for y0, y1 in groups:                      # muted bracket outside the frame: these rows reuse the same flat runs
        tr = ax.get_yaxis_transform()
        top, bot = y0 + 0.3, y1 - 0.3
        ax.plot([1.008, 1.016, 1.016, 1.008], [top, top, bot, bot], transform=tr, color=MUTED, lw=0.6, clip_on=False)
        ax.text(1.026, (top + bot) / 2, "share runs", transform=tr, ha="left", va="center", fontsize=6.3, color=MUTED)
    ax.axvline(0, color=INK2, lw=0.8, zorder=1)
    ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=7.5)
    ax.set_xlim(-11, 13); ax.set_ylim(y - 0.2, 0.8)
    ax.set_xlabel("Difference in resolved rate, percentage points (95% paired bootstrap)\nrows are against flat unless the label says minus", fontsize=7.2)
    ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
    ax.text(-10.8, y + 0.3, "lower resolved rate", fontsize=6.8, color=MUTED, va="center")
    ax.text(12.8, y + 0.3, "higher resolved rate", fontsize=6.8, color=MUTED, va="center", ha="right")
    ax.text(0, 1.012, "2-point target band", transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=6.5, color=MUTED)
    fig.tight_layout()
    fig.savefig("figures/differences.pdf"); fig.savefig("figures/differences.png")
    return [(it[1], it[2]) for it in rows if it[0] == R]


def exposure_funnel():
    rep = [json.loads(l) for l in open("runs/rep_r1_s0_c8000_fresh.jsonl")]
    rep = [r for r in rep if not r.get("error")]
    N = len(rep)
    def any_w(r, f):
        return any(e.get("window") and f(e["window"]) for e in r["log"] if e["ev"] == "step")
    with_result = sum(any_w(r, lambda w: w["stale_tests_with_result"] > 0) for r in rep)
    no_current = sum(any_w(r, lambda w: w["stale_tests_with_result"] > 0 and not w["current_test_in_window"]) for r in rep)
    assert with_result == no_current, (with_result, no_current)       # the two rows were equal, so they merge into one
    resolved_of = sum(bool(r["resolved"]) and any_w(r, lambda w: w["stale_tests_with_result"] > 0 and not w["current_test_in_window"]) for r in rep)
    comp = [r for r in rep if any(e["ev"] == "compact" for e in r["log"])]
    rate = sum(bool(r["resolved"]) for r in comp) / len(comp)         # resolve rate among compacted runs (exposed runs all compacted)
    stages = [
        ("runs", N, MUTED),
        ("compacted at least once", sum(any(e["ev"] == "compact" for e in r["log"]) for r in rep), MUTED),
        ("counter: stale test step executed\nbefore a compaction", sum(any(e["ev"] == "compact" and e.get("stale_tests_retained", 0) > 0 for e in r["log"]) for r in rep), BLUE),
        ("rendered window held a stale\ntest record", sum(any_w(r, lambda w: w["stale_tests"] > 0) for r in rep), ORANGE),
        ("that record carried a result marker\nand no current-state test sat beside it", no_current, ORANGE),
        ("of those, resolved", resolved_of, ORANGE),
    ]
    fig, ax = plt.subplots(figsize=(6.2, 2.9))
    n = len(stages)
    for i, (label, v, col) in enumerate(stages):
        yy = n - 1 - i
        ax.barh(yy, v, height=0.55, color=col, lw=0)
        ax.text(max(v, 0) + 2, yy, f"{v} ({100 * v / N:.0f}%)", va="center", fontsize=7.5, color=INK)
        ax.text(-2, yy, label, va="center", ha="right", fontsize=7.0, color=INK2, linespacing=1.25)
    exp = stages[-2][1] * rate
    ax.plot([exp, exp], [-0.36, 0.36], color=INK, lw=1.0)
    ax.text(exp, -0.42, f"{exp:.1f} expected at the compacted-run rate ({sum(bool(r['resolved']) for r in comp)} of {len(comp)})", va="top", ha="left", fontsize=6.4, color=MUTED)
    ax.set_xlim(0, 160); ax.set_ylim(-0.95, n - 0.4)
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_xlabel("Runs in the same-seed replicate of fresh (seed 0; not the Table 1 arm)")
    ax.tick_params(axis="x", labelsize=7)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="counter at compaction (upper bound)"), Patch(color=ORANGE, label="rendered window (measured)")],
              loc="center right", bbox_to_anchor=(1.0, 0.56), frameon=False, fontsize=6.8, handlelength=1.0, labelcolor=INK2, borderaxespad=0.3)
    fig.tight_layout()
    fig.savefig("figures/exposure_funnel.pdf"); fig.savefig("figures/exposure_funnel.png")
    return [(l.replace("\n", " "), v) for l, v, _ in stages], rate


def box(ax, x, y, w, h, title, body, color, title_size=7.4, body_size=5.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012", fc="white", ec=color, lw=1.1))
    ax.text(x + 0.012, y + h - 0.028, title, fontsize=title_size, fontweight="bold", color=INK, va="top")
    ax.text(x + 0.012, y + h - 0.075, body, fontsize=body_size, color=INK2, va="top", linespacing=1.4)


def arrow(ax, x0, y0, x1, y1, color=INK2):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=8, lw=0.9, color=color))


def overview():
    """Sparse pipeline: loop, compaction with the five policies, measurement; one callout shows the tag manipulation.
    Vertical positions are given in inches from the bottom and converted to axes fractions."""
    H = 4.5
    Y = lambda inch: inch / H
    fig, ax = plt.subplots(figsize=(7.4, H))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    def node(x, w, title, sub, title_size=7.0, y=3.15, h=1.12):
        ax.add_patch(FancyBboxPatch((x, Y(y)), w, h / H, boxstyle="round,pad=0.004,rounding_size=0.015", fc="white", ec=INK2, lw=1.0))
        ax.text(x + w / 2, Y(y + h - 0.17), title, ha="center", va="top", fontsize=title_size, fontweight="bold", color=INK)
        ax.text(x + w / 2, Y(y + 0.16), sub, ha="center", va="bottom", fontsize=5.8, color=INK2, linespacing=1.35)

    mid = Y(3.15 + 0.56)
    node(0.015, 0.155, "Agent loop", "one bash command\nper step\n80 steps, 145 tasks")
    arrow(ax, 0.17, mid, 0.2, mid)
    node(0.2, 0.265, "Compaction at 8K tokens", "keep the last 3 steps verbatim\nolder steps: one policy", title_size=6.5)
    arrow(ax, 0.465, mid, 0.495, mid)
    # policies as pills right of compaction, with two tiny group labels
    pills = [("mask", YELLOW, "actions only"), ("summ", MAGENTA, "model summary"), ("flat", AQUA, "records, tag #4"),
             ("fresh", ORANGE, "+ current / older"), ("ctrl", BLUE, "+ coded tag")]
    py = [3.15 + 0.56 + (2 - i) * 0.225 for i in range(5)]
    for (name, col, sub), yy in zip(pills, py):
        ax.add_patch(FancyBboxPatch((0.5, Y(yy - 0.08)), 0.07, 0.16 / H, boxstyle="round,pad=0.002,rounding_size=0.02", fc=col, ec="none"))
        ax.text(0.535, Y(yy), name, ha="center", va="center", fontsize=6.2, color="white", fontweight="bold")
        ax.text(0.58, Y(yy), sub, ha="left", va="center", fontsize=5.8, color=INK2)
    def bracket(y_top, y_bot, label):
        x = 0.708
        ax.plot([x - 0.006, x, x, x - 0.006], [Y(y_top + 0.07), Y(y_top + 0.07), Y(y_bot - 0.07), Y(y_bot - 0.07)], color=MUTED, lw=0.6)
        ax.text(x + 0.008, Y((y_top + y_bot) / 2), label, ha="left", va="center", fontsize=5.4, color=MUTED, linespacing=1.3)
    bracket(py[0], py[1], "own policy")
    bracket(py[2], py[4], "one evidence store,\ntag differs")
    arrow(ax, 0.846, mid, 0.866, mid)
    node(0.868, 0.117, "Measure", "resolved\n(swebench)\nstale test\nin window")

    # Callout: what the model sees for one test record, aged and current
    top, bottom = 2.85, 0.08
    ax.add_patch(FancyBboxPatch((0.015, Y(bottom)), 0.97, (top - bottom) / H, boxstyle="round,pad=0.004,rounding_size=0.015", fc="#f6f6f4", ec="none"))
    ax.text(0.03, Y(top - 0.2), "One test record, as rendered in each evidence arm", fontsize=6.6, fontweight="bold", color=INK, va="center")
    blocks = [("an older test record from an earlier code state",
               [("flat", AQUA, "[#4] test: pytest tests/test_forms.py   ...   1 failed"),
                ("fresh", ORANGE, "[#4 older code state, not validated on current] test: pytest tests/test_forms.py   ...   1 failed"),
                ("ctrl", BLUE, "[#4 seq-b, no validity claim made here] test: pytest tests/test_forms.py   ...   1 failed")]),
              ("the same record when it is current",
               [("flat", AQUA, "[#4] test: pytest tests/test_forms.py   ...   1 failed"),
                ("fresh", ORANGE, "[#4 current] test: pytest tests/test_forms.py   ...   1 failed"),
                ("ctrl", BLUE, "[#4 seq-a, no validity claim made here] test: pytest tests/test_forms.py   ...   1 failed")])]
    y = top - 0.48
    for head, rows in blocks:
        ax.text(0.03, Y(y), head, fontsize=6.2, fontweight="bold", color=INK2, va="center")
        y -= 0.27
        for name, col, txt in rows:
            ax.add_patch(FancyBboxPatch((0.03, Y(y - 0.085)), 0.055, 0.17 / H, boxstyle="round,pad=0.002,rounding_size=0.02", fc=col, ec="none"))
            ax.text(0.0575, Y(y), name, ha="center", va="center", fontsize=6.0, color="white", fontweight="bold")
            ax.text(0.1, Y(y), txt, ha="left", va="center", fontsize=6.0, color=INK, family="DejaVu Sans Mono")
            y -= 0.24
        y -= 0.10
    ax.text(0.03, Y(bottom + 0.19), "Compared by paired bootstrap over tasks (two seeds for flat, fresh, ctrl); a same-arm rerun gives the noise reference.",
            fontsize=5.8, color=MUTED, va="center")
    fig.savefig("figures/overview.pdf", bbox_inches="tight", pad_inches=0.04); fig.savefig("figures/overview.png", bbox_inches="tight", pad_inches=0.04)


if __name__ == "__main__":
    runs = load()
    rows = differences(runs)
    for label, est in rows:
        if est: print(f"  {label:26} {est[0]:+.1f} [{est[1]:+.1f}, {est[2]:+.1f}] n={est[3]}")
    print(exposure_funnel())
    overview()
    print("wrote figures/overview, differences, exposure_funnel (.pdf, .png)")
