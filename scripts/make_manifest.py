"""Reproducible dev (20) and held-out (150) manifests from SWE-bench Verified, stratified by repo. Seed fixed, no outcomes used."""
import random, collections
from datasets import load_dataset
ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
by = collections.defaultdict(list)
for r in ds: by[r["repo"]].append(r["instance_id"])
rng = random.Random(20261104)
for v in by.values(): v.sort(); rng.shuffle(v)
tot = sum(map(len, by.values()))
def take(n, offset):
    out = []
    for repo, ids in sorted(by.items()):
        k = max(1, round(n * len(ids) / tot))
        out += ids[offset:offset + k]
    return out
dev = take(20, 0)
held = [i for i in take(150, 5) if i not in dev]
open("manifests/dev.txt", "w").write("\n".join(dev) + "\n"); open("manifests/heldout.txt", "w").write("\n".join(held) + "\n")
print(len(dev), len(held), collections.Counter(i.split("__")[0] for i in held))
