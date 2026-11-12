"""Pull results from the kaggle-g4paper-results volume into runs/main_s<seed>_<arm>.jsonl (cap 8000) or runs/cap<cap>_s<seed>_<arm>.jsonl.

Usage: python scripts/collect.py <seed> <cap> [rep]
Local records are kept; a volume record replaces a local record for the same (iid, arm) only
when the local one is an error. Prints per-arm counts afterwards.
"""
import glob, json, os, subprocess, sys

seed, cap = int(sys.argv[1]), int(sys.argv[2])
rep = sys.argv[3] if len(sys.argv) > 3 else ""
prefix = f"s{seed}_c{cap}" + (f"_{rep}" if rep else "")
dest = f"runs/vol/{prefix}"
os.makedirs(dest, exist_ok=True)
ok = False
for arm in ("mask", "summ", "flat", "fresh", "ctrl", "gold", "empty"):   # one arm per call: a whole-prefix get times out past ~200 files
    p = subprocess.run(["modal", "--profile", "coglix-labs", "volume", "get", "--force",
                        "kaggle-g4paper-results", f"/{prefix}/{arm}", dest], capture_output=True, text=True)
    ok = ok or p.returncode == 0
if not ok:
    sys.exit(f"nothing on the volume for {prefix} yet")

arms = sorted(d for d in os.listdir(dest) if os.path.isdir(os.path.join(dest, d)))
for arm in arms:
    if arm in ("gold", "empty"):
        out = f"runs/controls_heldout_{arm}.jsonl"
    elif rep:
        out = f"runs/rep_{rep}_s{seed}_c{cap}_{arm}.jsonl"
    else:
        out = f"runs/main_s{seed}_{arm}.jsonl" if cap == 8000 else f"runs/cap{cap}_s{seed}_{arm}.jsonl"
    recs = {}
    if os.path.exists(out):
        for l in open(out):
            r = json.loads(l)
            if int(r["cap"]) == cap:
                recs[r["iid"]] = r
    added = replaced = 0
    for f in glob.glob(f"{dest}/{arm}/*.json"):
        r = json.load(open(f))
        cur = recs.get(r["iid"])
        if cur is None:
            recs[r["iid"]] = r; added += 1
        elif cur.get("error") and not r.get("error"):
            recs[r["iid"]] = r; replaced += 1
    with open(out, "w") as fh:
        for r in recs.values():
            fh.write(json.dumps(r) + "\n")
    n = len(recs); err = sum(bool(r.get("error")) for r in recs.values())
    print(f"{arm:6} total={n:4} err={err:2} (+{added} new, {replaced} errors replaced)")
