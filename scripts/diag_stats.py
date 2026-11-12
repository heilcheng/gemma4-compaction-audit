"""Statistics for the empty-reply diagnostic (PROTOCOL.md Amendment 4) and for the fresh pass under the
changed loop (Amendment 5), from the public logs only.

Reads logs/diag/{diag,dropfix}_s0_flat.jsonl.gz, logs/diag/dropfix_s0_fresh.jsonl.gz when it exists, and
logs/actions/main_s0_{flat,fresh}.jsonl.gz.
Usage: python scripts/diag_stats.py > results/diag_stats.txt
"""
import collections, gzip, itertools, json, os, random, statistics
from math import comb


def load(p):
    return {r["iid"]: r for r in map(json.loads, gzip.open(p, "rt")) if not r.get("error")}


D = load("logs/diag/diag_s0_flat.jsonl.gz")
F = load("logs/diag/dropfix_s0_flat.jsonl.gz")
O = load("logs/actions/main_s0_flat.jsonl.gz")
T40 = open("manifests/diag40.txt").read().split()
ALL = open("manifests/heldout.txt").read().split()


def ncmd(r):
    return sum(e["ev"] == "step" for e in r["log"])


def nemp(r):
    return r["steps"] - ncmd(r) - (r["status"] == "submitted")


def tail(r):
    if r["status"] != "step_limit":
        return 0
    ii = [e["i"] for e in r["log"] if e["ev"] == "step"]
    return r["steps"] - 1 - (max(ii) if ii else -1)


def seq(r):
    ii = set(e["i"] for e in r["log"] if e["ev"] == "step")
    return [i in ii for i in range(r["steps"] - (r["status"] == "submitted"))]


def res(r):
    return bool(r.get("resolved"))


def sign(x, y):
    n, k = x + y, min(x, y)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0


def loop(e):
    return e["lines"] > 0 and e["thought_lines"] >= 0.9 * e["lines"]


def describe(name, R, ids):
    rs = [R[i] for i in ids]
    rep = sum(r["steps"] for r in rs)
    emp = sum(map(nemp, rs))
    t = collections.Counter()
    for r in rs:
        q = seq(r)
        for u, v in zip(q, q[1:]):
            t[("c" if u else "e") + ("c" if v else "e")] += 1
    st = [len(list(g)) for r in rs for k, g in itertools.groupby(seq(r)) if not k]
    kinds = collections.Counter(e["kind"] for r in rs for e in r["log"] if e["ev"] == "step")
    print(f"{name}: {len(rs)} runs")
    print(f"  replies {rep}, with no command {emp} ({100 * emp / rep:.1f} pct)")
    print(f"  no command after none {100 * t['ee'] / max(1, t['ee'] + t['ec']):.0f} pct, after a command {100 * t['ce'] / max(1, t['ce'] + t['cc']):.0f} pct")
    print(f"  unbroken runs of no-command replies: {len(st)}, longest {max(st) if st else 0}, of five or more {sum(x >= 5 for x in st)}")
    print(f"  runs ending in ten or more no-command replies: {sum(tail(r) >= 10 for r in rs)}")
    print(f"  step limit {sum(r['status'] == 'step_limit' for r in rs)}, submitted {sum(r['status'] == 'submitted' for r in rs)}, resolved {sum(map(res, rs))}"
          f" (at the step limit {sum(res(r) and r['status'] == 'step_limit' for r in rs)})")
    print(f"  executed commands per run: median {statistics.median(map(ncmd, rs)):.0f}, total {sum(map(ncmd, rs))}"
          f" (read {kinds['read']}, edit {kinds['edit']}, test {kinds['test']})")
    print(f"  compacted {sum(any(e['ev'] == 'compact' for e in r['log']) for r in rs)}, stale test retained (counter) "
          f"{sum(any(e['ev'] == 'compact' and e.get('stale_tests_retained', 0) > 0 for e in r['log']) for r in rs)}")
    print(f"  completion tokens per run {sum(r['totals']['completion'] for r in rs) / len(rs):.0f}, wall minutes per run {sum(r['wall_s'] for r in rs) / len(rs) / 60:.0f}")
    ev = [e for r in rs for e in r["log"] if e["ev"] == "empty"]
    if ev:
        lp = sum(map(loop, ev))
        cut = sum((not loop(e)) and e["fences"] % 2 == 1 for e in ev)
        print(f"  logged no-command replies {len(ev)}: the word thought on at least 90 pct of lines {lp} ({100 * lp / len(ev):.0f} pct), "
              f"cut off inside an open code block {cut}, other {len(ev) - lp - cut}; finish reason {dict(collections.Counter(e['finish'] for e in ev))}; "
              f"mean completion tokens {sum(e['completion_tokens'] for e in ev) / len(ev):.0f}")
        cm = [e for r in rs for e in r["log"] if e["ev"] == "step"]
        print(f"  replies with a command: median completion tokens {statistics.median(e['completion_tokens'] for e in cm):.0f}, "
              f"hit the limit {sum(e['finish'] == 'length' for e in cm)} of {len(cm)}")


def paired(n1, X, n2, Y, ids):
    w = sum(res(Y[i]) and not res(X[i]) for i in ids)
    l = sum(res(X[i]) and not res(Y[i]) for i in ids)
    a = sum(tail(X[i]) >= 10 and tail(Y[i]) < 10 for i in ids)
    b = sum(tail(X[i]) < 10 and tail(Y[i]) >= 10 for i in ids)
    d = [res(Y[i]) - res(X[i]) for i in ids]
    rng = random.Random(1)
    bs = sorted(100 * sum(rng.choice(d) for _ in d) / len(d) for _ in range(5000))
    print(f"{n2} against {n1}, {len(ids)} tasks: resolved {sum(res(Y[i]) for i in ids)} against {sum(res(X[i]) for i in ids)}, "
          f"difference {100 * sum(d) / len(d):+.1f} points [{bs[124]:+.1f}, {bs[4874]:+.1f}], gained {w}, lost {l}, sign test p = {sign(w, l):.2f}")
    print(f"  ending in ten or more no-command replies: only in {n1} {a}, only in {n2} {b}, sign test p = {sign(a, b):.1g}")


print("== The 40 diagnostic tasks (manifests/diag40.txt), flat arm, seed 0, 8000-token trigger")
assert set(T40) <= set(D) and set(T40) <= set(F) and set(T40) <= set(O)
describe("main matrix, seed-0 flat (loop unchanged, replies not logged)", O, T40)
describe("phase 1, label diag (loop unchanged, replies logged)", D, T40)
describe("phase 2, label dropfix (text of a no-command reply replaced by a placeholder)", F, T40)
paired("diag", D, "dropfix", F, T40)
paired("main", O, "dropfix", F, T40)
paired("main", O, "diag", D, T40)
full = [i for i in ALL if i in F and i in O]
if len(full) > 40:
    print(f"\n== All held-out tasks with a dropfix run ({len(full)} of {len(ALL)})")
    describe("main matrix, seed-0 flat", O, full)
    describe("dropfix", F, full)
    paired("main", O, "dropfix", F, full)
    rest = [i for i in full if i not in set(T40)]
    print(f"\n== The {len(rest)} tasks outside the diagnostic 40")
    paired("main", O, "dropfix", F, rest)


def compacts(r):
    return [e for e in r["log"] if e["ev"] == "compact"]


def exposure(name, R, ids):
    rs = [R[i] for i in ids]
    comp = [r for r in rs if compacts(r)]
    never = [r for r in rs if not compacts(r)]
    cnt = [r for r in rs if any(e.get("stale_tests_retained", 0) > 0 for e in compacts(r))]
    w = lambda r, k: any((e.get("window") or {}).get(k, 0) > 0 for e in compacts(r))
    win, wres = [r for r in rs if w(r, "stale_tests")], [r for r in rs if w(r, "stale_tests_with_result")]
    alone = [r for r in rs if any((e.get("window") or {}).get("stale_tests_with_result", 0) > 0 and not e["window"]["current_test_in_window"] for e in compacts(r))]
    logged = any(e.get("window") for r in rs for e in compacts(r))
    print(f"{name}: compacted {len(comp)} (resolved {sum(map(res, comp))}), never compacted {len(never)} (resolved {sum(map(res, never))}), "
          f"stale test retained by the counter {len(cnt)} (resolved {sum(map(res, cnt))}), ran a test {sum(any(e['ev'] == 'step' and e['kind'] == 'test' for e in r['log']) for r in rs)}")
    if logged:
        print(f"  window held a stale test record {len(win)}, one with a result marker {len(wres)} (resolved {sum(map(res, wres))}), "
              f"one with a result marker and no current-state test beside it {len(alone)}")


print("\n== Where the changed loop gains, and what it leaves the tag to act on (flat, seed 0, all held-out tasks)")
exposure("main matrix, seed-0 flat (window not logged)", O, full)
exposure("dropfix flat", F, full)

if os.path.exists("logs/diag/dropfix_s0_fresh.jsonl.gz"):
    G = load("logs/diag/dropfix_s0_fresh.jsonl.gz")
    P = load("logs/actions/main_s0_fresh.jsonl.gz")
    both = [i for i in ALL if i in F and i in G]
    print(f"\n== Amendment 5: fresh against flat under the changed loop, seed 0 ({len(both)} of {len(ALL)} tasks)")
    describe("dropfix flat", F, both)
    describe("dropfix fresh", G, both)
    paired("dropfix flat", F, "dropfix fresh", G, both)
    exposure("dropfix fresh", G, both)
    paired("main fresh", P, "dropfix fresh", G, [i for i in both if i in P])
    ex = [i for i in both if any(e.get("stale_tests_retained", 0) > 0 for e in compacts(G[i]))]
    print(f"  tasks where the fresh run retained a stale test record ({len(ex)}): fresh resolved {sum(res(G[i]) for i in ex)}, flat resolved {sum(res(F[i]) for i in ex)}")
    fl = [i for i in both if res(F[i]) != res(G[i])]
    print(f"  tasks whose outcome differs between the two arms {len(fl)}, of which the fresh run retained a stale test record in {sum(i in set(ex) for i in fl)}")
    two = [res(F[i]) + res(G[i]) for i in both]
    print(f"  resolved by both {sum(x == 2 for x in two)}, by one {sum(x == 1 for x in two)}; both passes together {sum(two)} of {2 * len(both)}")
