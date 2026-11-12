"""Export the empty-reply diagnostic (PROTOCOL.md Amendment 4) in publishable form.

Reads the run records pulled from the results volume (runs/vol/s0_c8000_<label>/<arm>/*.json) and writes
logs/diag/<label>_s0_<arm>.jsonl.gz (the Amendment 5 fresh pass under the changed loop included). Kept per executed step: what logs/actions keeps, plus the reply's
completion tokens and finish reason. Kept per reply with no command: tokens, finish reason, the first 200
characters of the reply, its length, and counts that let the classification be redone without the full
text (non-blank lines, lines that are exactly the word "thought", code fences). Tool outputs are left out
as in logs/actions.

Usage: python scripts/export_diag.py
"""
import glob, gzip, json, os

os.makedirs("logs/diag", exist_ok=True)
KEEP_STEP = ("ev", "i", "kind", "prompt_tokens", "completion_tokens", "finish", "action", "state", "window")
KEEP_COMPACT = ("ev", "step", "n_old", "stale_tests_retained", "stale_reads_retained", "n_seen", "records", "prompt_tokens", "window")
KEEP_TOP = ("iid", "arm", "seed", "cap", "rep", "max_tokens", "empty_fix", "status", "steps", "resolved", "patch_chars", "test_s", "wall_s", "totals", "error")

for label, arm in (("diag", "flat"), ("dropfix", "flat"), ("dropfix", "fresh")):
    files = sorted(glob.glob(f"runs/vol/s0_c8000_{label}/{arm}/*.json"))
    if not files:
        continue
    with gzip.open(f"logs/diag/{label}_s0_{arm}.jsonl.gz", "wt") as g:
        for f in files:
            r = json.load(open(f))
            slim = {k: r[k] for k in KEEP_TOP if k in r}
            log = []
            for e in r.get("log", []):
                if e["ev"] == "empty":
                    raw = e["raw"]
                    lines = [x.strip() for x in raw.split("\n") if x.strip()]
                    log.append(dict(ev="empty", i=e["i"], prompt_tokens=e["prompt_tokens"], completion_tokens=e["completion_tokens"],
                                    finish=e["finish"], head=raw[:200], chars=len(raw), lines=len(lines),
                                    thought_lines=sum(x == "thought" for x in lines), fences=raw.count("```")))
                else:
                    keep = KEEP_STEP if e["ev"] == "step" else KEEP_COMPACT if e["ev"] == "compact" else ("ev", "attempt", "status")
                    log.append({k: e[k] for k in keep if k in e})
            slim["log"] = log
            g.write(json.dumps(slim) + "\n")
    print(f"{label} {arm}: wrote {len(files)} runs")
