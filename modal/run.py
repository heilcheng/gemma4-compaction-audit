"""Runs one SWE-bench Verified task on Modal: sandbox from the prebuilt swebench image, agent or control patch, grade.

Deployed usage (survives local disconnects; results land on the kaggle-g4paper-results volume):
    PYTHONPATH=src modal deploy modal/run.py
    PYTHONPATH=src modal run modal/run.py::launch --tasks manifests/heldout.txt --arms flat,fresh --seed 0 --cap 8000
    python scripts/collect.py 0 8000          # pulls the volume into runs/main_s0_<arm>.jsonl
"""
import json, os, tempfile, time
import modal

URL = open(os.path.join(os.path.dirname(__file__), "url.txt")).read().strip() if os.path.exists(os.path.join(os.path.dirname(__file__), "url.txt")) else ""
img = (modal.Image.debian_slim(python_version="3.12").pip_install("swebench==4.1.0", "datasets", "httpx")
       .env({"G4_URL": URL}).add_local_python_source("gpaper"))
app = modal.App("kaggle-g4paper-run")
results = modal.Volume.from_name("kaggle-g4paper-results", create_if_missing=True)


def sandbox_image(iid):
    return modal.Image.from_registry(f"swebench/sweb.eval.x86_64.{iid.replace('__', '_1776_').lower()}:latest", add_python="3.11")


def result_path(iid, arm, seed, cap, rep=""):
    return f"s{seed}_c{cap}{('_' + rep) if rep else ''}/{arm}/{iid}.json"


@app.function(image=img, timeout=6 * 3600, max_containers=80, cpu=1, memory=2048, volumes={"/results": results})
def run_task(iid: str, arm: str, seed: int = 0, cap: int = 12000, max_steps: int = 80, rep: str = "",
             max_tokens: int = 1200, empty_fix: str = ""):
    from datasets import load_dataset
    from swebench.harness.test_spec.test_spec import make_test_spec
    from swebench.harness.grading import get_eval_report
    from gpaper.agent import Agent
    t0 = time.time()
    inst = next(r for r in load_dataset("princeton-nlp/SWE-bench_Verified", split="test") if r["instance_id"] == iid)
    spec = make_test_spec(inst, namespace="swebench")
    sb_app = modal.App.lookup("kaggle-g4paper-run", create_if_missing=True)
    sb = modal.Sandbox.create(image=sandbox_image(iid), app=sb_app, timeout=6 * 3600, cpu=2, memory=8192)
    pre = "source /opt/miniconda3/bin/activate testbed && cd /testbed && "

    def run(cmd, timeout=180):
        p = sb.exec("bash", "-c", pre + cmd, timeout=timeout, text=False)
        out = (p.stdout.read() + p.stderr.read()).decode("utf-8", "replace"); p.wait()
        return out, p.returncode

    def write(path, text):
        p = sb.exec("bash", "-c", f"cat > {path}")
        p.stdin.write(text.encode()); p.stdin.write_eof(); p.stdin.drain(); p.wait()

    res = dict(iid=iid, arm=arm, seed=seed, cap=cap, rep=rep, max_tokens=max_tokens, empty_fix=empty_fix)
    try:
        if arm in ("gold", "empty"):
            patch = inst["patch"] if arm == "gold" else ""
            res["status"] = arm
        else:
            ag = Agent(os.environ["G4_URL"], run, inst["problem_statement"], arm, cap_tokens=cap, max_steps=max_steps, seed=seed,
                       max_tokens=max_tokens, empty_fix=empty_fix)
            res["status"], res["steps"] = ag.solve()
            res["totals"], res["log"] = ag.totals, ag.log
            patch, _ = run("git diff", 60)
        res["patch_chars"] = len(patch)
        if patch.strip() and arm in ("gold", "empty"):
            write("/tmp/p.diff", patch)
            _, rc = run("git apply -v /tmp/p.diff")
            res["applied"] = rc == 0
        write("/tmp/eval.sh", spec.eval_script)
        t = time.time()
        out, _ = run("bash /tmp/eval.sh", 1800)
        res["test_s"] = time.time() - t
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f: f.write(out)
        report = get_eval_report(spec, dict(instance_id=iid, model_name_or_path=arm, model_patch=patch), f.name, include_tests_status=True)
        res["resolved"] = report[iid]["resolved"]
    except Exception as e:
        res["error"] = repr(e)[:500]
    finally:
        sb.terminate()
    res["wall_s"] = time.time() - t0
    p = "/results/" + result_path(iid, arm, seed, cap, rep)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(res, f)
    results.commit()
    return res


def finished(seed, cap, rep=""):
    """(iid, arm) pairs with a non-error result on the volume."""
    done = set()
    prefix = f"s{seed}_c{cap}" + (f"_{rep}" if rep else "")
    try:
        entries = results.listdir(prefix, recursive=True)
    except Exception:
        return done
    for e in entries:
        if not e.path.endswith(".json"):
            continue
        r = json.loads(b"".join(results.read_file(e.path)))
        if not r.get("error"):
            done.add((r["iid"], r["arm"]))
    return done


def local_done(seed, cap):
    done = set()
    import glob
    for f in glob.glob(f"runs/main_s{seed}_*.jsonl"):
        for l in open(f):
            r = json.loads(l)
            if not r.get("error") and int(r["cap"]) == cap:
                done.add((r["iid"], r["arm"]))
    return done


@app.local_entrypoint()
def launch(tasks: str, arms: str, seed: int = 0, cap: int = 12000, rep: str = "", max_tokens: int = 1200, empty_fix: str = ""):
    """Spawn every missing (task, arm) job on the deployed app and exit.

    Re-running is safe only when no job for these arms is still in flight: the done set is built
    from landed results, so in-flight jobs look missing and get spawned twice (the collector keeps
    the first result to land)."""
    fn = modal.Function.from_name("kaggle-g4paper-run", "run_task")
    ids = open(tasks).read().split() if os.path.exists(tasks) else tasks.split(",")
    done = (local_done(seed, cap) if not rep else set()) | finished(seed, cap, rep)
    jobs = [(t, a) for t in ids for a in arms.split(",") if (t, a) not in done]
    print(f"{len(done)} already done, spawning {len(jobs)}")
    for t, a in jobs:
        fn.spawn(t, a, seed, cap, 80, rep, max_tokens, empty_fix)
    print("spawned", len(jobs))


@app.local_entrypoint()
def main(tasks: str, arms: str, seed: int = 0, cap: int = 12000, out: str = "runs/out.jsonl"):
    """Attached mode (dies with the local client). Kept for smoke tests."""
    os.makedirs(os.path.dirname(out), exist_ok=True)
    done = set()
    if os.path.exists(out):
        for l in open(out):
            r = json.loads(l)
            if not r.get("error"): done.add((r["iid"], r["arm"], r["seed"], r["cap"]))
    ids = [t for t in open(tasks).read().split() ] if os.path.exists(tasks) else tasks.split(",")
    jobs = [(t, a, seed, cap) for t in ids for a in arms.split(",") if (t, a, seed, cap) not in done]
    with open(out, "a") as f:
        for r in run_task.starmap(jobs, order_outputs=False):
            f.write(json.dumps(r) + "\n"); f.flush()
            print({k: r.get(k) for k in ("iid", "arm", "status", "resolved", "steps", "error", "wall_s")})
