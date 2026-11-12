"""No-network check of the context policies. Pytest-style; also runnable as a script.

    uv run --with pytest python -m pytest -q tests scripts/smoke_local.py

It drives gpaper.memory directly, then drives the real Agent loop with a canned model and a
canned shell, so no Modal endpoint, sandbox or GPU is touched. The Agent only needs httpx for
its (unused here) HTTP client, so a stub is installed when httpx is not importable.
"""
import re
import subprocess
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    import httpx  # noqa: F401
except ImportError:
    stub = types.ModuleType("httpx")
    stub.Client = lambda *a, **k: None
    sys.modules["httpx"] = stub

from gpaper import agent as agent_mod
from gpaper.memory import Memory, fingerprint, mask_observations


def fake_run_factory():
    """A run(cmd, timeout) callable with canned outputs. A `sed -i` command changes the state."""
    state = {"fp": "S0"}

    def run(cmd, timeout=180):
        if cmd == agent_mod.FP_CMD:
            return state["fp"] + "\n", 0
        if "sed -i" in cmd:
            state["fp"] = "S1"
            return "", 0
        if "pytest" in cmd:
            return "1 failed, 3 passed\n", 1
        if cmd.startswith("cat "):
            return "def f():\n    return 1\n", 0
        return "ok\n", 0

    return run


def test_fake_run_contract():
    run = fake_run_factory()
    assert run(agent_mod.FP_CMD)[0].strip() == "S0"
    assert run("pytest tests/test_a.py")[1] == 1
    run("sed -i s/1/2/ a.py")
    assert run(agent_mod.FP_CMD)[0].strip() == "S1"


def test_memory_tags_and_shared_body():
    m = Memory()
    m.add("test", "1 failed", "S0")
    m.add("edit", "patched f()", "S1")
    m.add("read", "def f(): ...", "S1")
    flat, fresh, ctrl = m.render_flat(), m.render_fresh("S1"), m.render_control("S1")
    body = lambda s: [line.split("] ", 1)[1] for line in s.splitlines()]
    assert body(flat) == body(fresh) == body(ctrl)
    f_lines, c_lines = fresh.splitlines(), ctrl.splitlines()
    assert f_lines[0].startswith("[#1 older code state, not validated on current]")
    assert f_lines[1].startswith("[#2 current]") and f_lines[2].startswith("[#3 current]")
    assert c_lines[0].startswith("[#1 seq-b, no validity claim made here]")
    assert c_lines[1].startswith("[#2 seq-a, no validity claim made here]")
    assert "older" not in ctrl and "current" not in ctrl and "validated" not in flat
    # a state change flips the tags without touching the evidence
    assert m.render_fresh("S9").count("older code state") == 3
    assert m.render_control("S9").count("seq-b") == 3


def test_mask_observations():
    hist = [("ls", "a b"), ("cat a", "x=1"), ("pytest", "1 failed"), ("sed", "")]
    out = mask_observations(hist, keep_recent=2)
    assert [a for a, _ in out] == [a for a, _ in hist]
    assert out[0][1] == out[1][1] == "[output omitted]"
    assert out[2:] == hist[2:]


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_fingerprint_in_temp_git_repo(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "a.py").write_text("x = 1\n")
    git(tmp_path, "add", "a.py")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
    s0 = fingerprint(tmp_path)
    assert fingerprint(tmp_path) == s0
    (tmp_path / "a.py").write_text("x = 2\n")
    s1 = fingerprint(tmp_path)
    assert s1 != s0
    (tmp_path / "a.py").write_text("x = 1\n")
    assert fingerprint(tmp_path) == s0          # same content, same state
    (tmp_path / "new.py").write_text("")
    assert fingerprint(tmp_path) != s0           # new files count
    # the agent's own git-based fingerprint command behaves the same way
    cmd = agent_mod.FP_CMD.replace("/testbed", str(tmp_path))
    fp = lambda: subprocess.run(["bash", "-c", cmd], capture_output=True, text=True).stdout.strip()
    (tmp_path / "new.py").unlink()
    before = fp()
    (tmp_path / "a.py").write_text("x = 3\n")
    assert fp() != before


def drive_agent(arm):
    """Run the real Agent loop with a canned model: read, test, edit, read, then submit.
    The compaction trigger fires once, before the last model call."""
    replies = iter([
        "look\n```bash\ncat a.py\n```",
        "test\n```bash\npytest tests/test_a.py\n```",
        "edit\n```bash\nsed -i s/1/2/ a.py\n```",
        "look again\n```bash\nls\n```",
        "done\n```bash\necho COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\n```",
    ])
    seen_msgs = []
    ag = agent_mod.Agent("http://unused", fake_run_factory(), "Fix f().", arm, cap_tokens=8000, keep=3, max_steps=10)

    def chat(messages, max_tokens=None, summ=False):
        if summ:
            return "SUMMARY: read a.py, ran tests, edited f"
        seen_msgs.append(messages)
        ag.last_prompt_tokens = 9000            # always above the cap
        return next(replies)

    ag.chat = chat
    status, steps = ag.solve()
    return ag, status, steps, seen_msgs


def evidence(msgs):
    return next((m["content"] for m in msgs if m["content"].startswith("Evidence you collected earlier")), "")


@pytest.mark.parametrize("arm", ["flat", "fresh", "ctrl", "mask", "summ"])
def test_agent_loop_exposure_and_rendering(arm):
    ag, status, steps, seen = drive_agent(arm)
    assert status == "submitted" and steps == 5
    kinds = [e["kind"] for e in ag.log if e["ev"] == "step"]
    assert kinds == ["read", "test", "edit", "read"]
    comps = [e for e in ag.log if e["ev"] == "compact"]
    assert len(comps) == 1
    # at compaction the test ran under S0 and the first read under S0, but the workspace is now S1
    assert comps[0]["stale_tests_retained"] == 1 and comps[0]["stale_reads_retained"] == 1
    last = seen[-1]
    if arm == "flat":
        assert "[#1] read:" in evidence(last) and "older" not in evidence(last)
    elif arm == "fresh":
        assert "[#1 older code state, not validated on current] read:" in evidence(last)
    elif arm == "ctrl":
        assert "[#1 seq-b, no validity claim made here] read:" in evidence(last)
    elif arm == "mask":
        text = next(m["content"] for m in last if m["content"].startswith("Earlier commands"))
        assert "$ cat a.py" in text and "def f()" not in text
    else:
        assert any(m["content"].startswith("Summary of your earlier work") for m in last)


def test_flat_fresh_ctrl_prompts_differ_only_in_tags():
    strip = lambda s: re.sub(r"^\[#\d+[^\]]*\] ", "", evidence(s), flags=re.M)
    bodies = {arm: strip(drive_agent(arm)[3][-1]) for arm in ("flat", "fresh", "ctrl")}
    assert bodies["flat"] == bodies["fresh"] == bodies["ctrl"] and bodies["flat"]


if __name__ == "__main__":
    sys.exit(pytest.main(["-q", __file__]))
