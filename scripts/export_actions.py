"""Export publishable per-run logs: every action string, step kind, token counts and compaction events,
without tool outputs (which contain repository source). One gzip-compressed JSONL per run file.

Usage: python scripts/export_actions.py          # writes logs/actions/<run file>.jsonl.gz
"""
import glob, gzip, json, os

os.makedirs("logs/actions", exist_ok=True)
KEEP_STEP = ("ev", "i", "kind", "prompt_tokens", "action", "state", "window")
KEEP_COMPACT = ("ev", "step", "n_old", "stale_tests_retained", "stale_reads_retained", "n_seen", "records", "prompt_tokens", "window")
KEEP_TOP = ("iid", "arm", "seed", "cap", "rep", "status", "steps", "resolved", "patch_chars", "test_s", "wall_s", "totals", "error")

n = 0
for f in sorted(glob.glob("runs/main_s*_*.jsonl") + glob.glob("runs/cap*_s*_*.jsonl") + glob.glob("runs/rep_*.jsonl") + glob.glob("runs/controls_heldout_*.jsonl")):
    out = "logs/actions/" + os.path.basename(f) + ".gz"
    with gzip.open(out, "wt") as g:
        for l in open(f):
            r = json.loads(l)
            slim = {k: r[k] for k in KEEP_TOP if k in r}
            log = []
            for e in r.get("log", []):
                keep = KEEP_STEP if e["ev"] == "step" else KEEP_COMPACT if e["ev"] == "compact" else ("ev", "attempt", "status")
                log.append({k: e[k] for k in keep if k in e})
            slim["log"] = log
            g.write(json.dumps(slim) + "\n"); n += 1
print(f"wrote {n} runs to logs/actions/")
