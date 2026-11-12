"""Figure 5: replies with no command by reply index, and the runs that end in ten or more of them.
Reads the public logs only (logs/actions and logs/diag) and writes figures/stall.{pdf,png}.
Usage: python scripts/make_stall_figure.py"""
import gzip, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE, ORANGE, AQUA, YELLOW, MAGENTA = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
INK, INK2, MUTED, RULE = "#0b0b0b", "#52514e", "#8a8984", "#d9d8d4"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": RULE, "axes.linewidth": 0.6,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.labelcolor": INK2, "text.color": INK,
                     "savefig.dpi": 300, "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
ARM_COLOR = {"mask": YELLOW, "summ": MAGENTA, "flat": AQUA, "fresh": ORANGE, "ctrl": BLUE}


def load(p):
    return [r for r in map(json.loads, gzip.open(p, "rt")) if not r.get("error")]


def seq(r):
    ii = set(e["i"] for e in r["log"] if e["ev"] == "step")
    return [i in ii for i in range(r["steps"] - (r["status"] == "submitted"))]


def tail(r):
    if r["status"] != "step_limit":
        return 0
    ii = [e["i"] for e in r["log"] if e["ev"] == "step"]
    return r["steps"] - 1 - (max(ii) if ii else -1)


def share_by_index(rs):
    out = []
    for i in range(80):
        q = [seq(r)[i] for r in rs if len(seq(r)) > i]
        out.append(100 * (1 - sum(q) / len(q)) if q else None)
    return out


def stall(rs):
    return 100 * sum(tail(r) >= 10 for r in rs) / len(rs)


main = {(s, a): load(f"logs/actions/main_s{s}_{a}.jsonl.gz") for s in (0, 1) for a in ARM_COLOR if not (s == 1 and a in ("mask", "summ"))}
c16 = {a: load(f"logs/actions/cap16000_s0_{a}.jsonl.gz") for a in ("flat", "fresh")}
fix = load("logs/diag/dropfix_s0_flat.jsonl.gz")
fixg = load("logs/diag/dropfix_s0_fresh.jsonl.gz")

fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.6, 2.8), gridspec_kw={"width_ratios": [1.25, 1]})
x = range(1, 81)
for rs, col, ls, lab, at in ((main[(0, "flat")], AQUA, "-", "flat, 8000 trigger", (56, 74)), (c16["flat"], AQUA, "--", "flat, 16K trigger", (56, 44)),
                             (fix, INK, "-", "flat, corrected loop", (56, 22))):
    ax.plot(x, share_by_index(rs), color=col, ls=ls, lw=1.3)
    ax.text(at[0], at[1], lab, fontsize=6.6, color=INK2, va="center", linespacing=1.2)
ax.set_xlim(1, 80); ax.set_ylim(0, 100)
ax.set_xlabel("Reply index within the run"); ax.set_ylabel("Replies with no command (%)\namong runs still going")
ax.tick_params(labelsize=7)

rows = [(a, [r for s in (0, 1) if (s, a) in main for r in main[(s, a)]], ARM_COLOR[a]) for a in ("mask", "summ", "flat", "fresh", "ctrl")]
rows += [("flat, 16K", c16["flat"], AQUA), ("fresh, 16K", c16["fresh"], ORANGE), ("flat, corrected", fix, INK), ("fresh, corrected", fixg, INK)]
n = len(rows)
for i, (lab, rs, col) in enumerate(rows):
    y = n - 1 - i
    v = stall(rs)
    bx.barh(y, v, height=0.6, color=col, lw=0, alpha=0.55 if "16K" in lab else 1.0)
    bx.text(v + 1.5, y, f"{v:.0f}% ({sum(tail(r) >= 10 for r in rs)} of {len(rs)})", va="center", fontsize=6.6, color=INK)
bx.set_yticks(range(n)); bx.set_yticklabels([r[0] for r in rows][::-1], fontsize=7)
bx.set_xlim(0, 100); bx.set_ylim(-0.6, n - 0.4)
bx.spines["left"].set_visible(False); bx.tick_params(axis="y", length=0); bx.tick_params(axis="x", labelsize=7)
bx.set_xlabel("Runs ending in ten or more\nreplies with no command (%)")
fig.tight_layout()
fig.savefig("figures/stall.pdf"); fig.savefig("figures/stall.png")
print("wrote figures/stall (.pdf, .png);", {lab: round(stall(rs)) for lab, rs, _ in rows})
