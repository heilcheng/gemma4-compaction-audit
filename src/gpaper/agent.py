"""Minimal mini-SWE-agent-style loop with swappable compaction policies.

The loop talks to a vLLM OpenAI endpoint and to a `run(cmd, timeout) -> (output, rc)` callable
that executes bash inside the task's /testbed. Nothing here sees gold patches or evaluator tests.
"""
from __future__ import annotations
import re, time, json
import httpx
from .memory import Memory

SYSTEM = """You are fixing a bug in the repository at /testbed. Work only through bash.
Each reply must contain a short thought and exactly ONE bash command in a ```bash block.
You see the command output on the next turn. Edit files with sed, python or cat heredocs.
After each edit, run the relevant existing tests (for example pytest on the touched module) to check it. Do not modify existing tests. When the fix is done and you have checked it, reply with a block
containing only: echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"""

RESULT_RE = re.compile(r"passed|failed|FAILED|PASSED|OK\b|Ran \d+ test|AssertionError|error", re.I)
TEST_RE = re.compile(r"pytest|runtests|unittest|manage\.py test|tox|nosetests")
FP_CMD = ("cd /testbed && (git diff HEAD; git ls-files -o --exclude-standard | grep -v -e __pycache__ -e '\\.pyc$' "
          "| xargs -r sha256sum) | sha256sum | cut -c1-16")


def parse_action(text: str):
    m = re.findall(r"```(?:bash|sh)?\n(.*?)```", text, re.S)
    return m[0].strip() if m else None


def clip(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n // 2] + "\n...[truncated]...\n" + s[-n // 2:]


class Agent:
    def __init__(self, url, run, issue, arm, cap_tokens=12000, keep=3, max_steps=60, mem_chars=9000,
                 temperature=0.3, seed=0, max_tokens=1200, model="gemma4-12b", obs_chars=4000,
                 empty_fix=""):
        self.url, self.run, self.issue, self.arm = url, run, issue, arm
        self.cap, self.keep, self.max_steps, self.mem_chars = cap_tokens, keep, max_steps, mem_chars
        self.temperature, self.seed, self.max_tokens, self.model, self.obs_chars = temperature, seed, max_tokens, model, obs_chars
        self.steps: list[dict] = []        # verbatim recent steps: {thought, action, obs, kind, state}
        self.mem = Memory()
        self.summary = ""
        self.masked: list[dict] = []       # mask arm: aged steps with observations removed
        self.log: list[dict] = []
        self.http = httpx.Client(timeout=900, follow_redirects=True)
        self.totals = dict(prompt=0, completion=0, model_s=0.0, tool_s=0.0, calls=0, summ_prompt=0, summ_completion=0, summ_s=0.0)
        self.last_prompt_tokens = 0
        self.last_reply: dict = {}
        self.empty_fix = empty_fix         # "" keeps the paper's loop; "drop" is the 10 Nov post hoc variant
        self.win = None
        self.seen: list[tuple[str, str]] = []   # (kind, state) of every executed step, for exposure counts

    # ---- model ----
    def chat(self, messages, max_tokens=None, summ=False):
        t = time.time()
        body = dict(model=self.model, messages=messages, temperature=self.temperature, seed=self.seed,
                    max_tokens=max_tokens or self.max_tokens)
        # The Modal web endpoint sometimes answers a long generation with a non-JSON gateway
        # response (seen as JSONDecodeError on django tasks). Retry the identical request; the
        # request itself is unchanged, so this is transport recovery, not a protocol change.
        for attempt in range(4):
            resp = self.http.post(self.url + "/v1/chat/completions", json=body)
            try:
                r = resp.json()
                if "usage" in r:
                    break
            except ValueError:
                pass
            self.log.append(dict(ev="retry", attempt=attempt, status=resp.status_code, body=resp.text[:200]))
            if attempt == 3:
                raise RuntimeError(f"chat failed after retries: HTTP {resp.status_code} {resp.text[:200]!r}")
            time.sleep(10 * (attempt + 1))
        dt = time.time() - t
        u = r["usage"]
        k = "summ_" if summ else ""
        self.totals[k + "prompt"] += u["prompt_tokens"]; self.totals[k + "completion"] += u["completion_tokens"]
        self.totals["summ_s" if summ else "model_s"] += dt
        if not summ:
            self.totals["calls"] += 1; self.last_prompt_tokens = u["prompt_tokens"]
            self.last_reply = dict(completion_tokens=u["completion_tokens"], finish=r["choices"][0].get("finish_reason"))
        return r["choices"][0]["message"]["content"] or ""

    # ---- context ----
    def build(self):
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "Issue:\n" + self.issue}]
        if self.arm == "summ" and self.summary:
            msgs.append({"role": "user", "content": "Summary of your earlier work:\n" + self.summary})
        elif self.arm == "mask" and self.masked:
            msgs.append({"role": "user", "content": "Earlier commands (outputs omitted):\n" + "\n".join(
                f"$ {s['action']}" for s in self.masked[-40:])})
        elif self.arm in ("flat", "fresh", "ctrl") and self.mem.records:
            cur = self.state
            body = {"flat": self.mem.render_flat, "fresh": lambda: self.mem.render_fresh(cur),
                    "ctrl": lambda: self.mem.render_control(cur)}[self.arm]()
            self.win = self.window(cur)
            if len(body) > self.mem_chars:
                body = "...[older records dropped]...\n" + body[-self.mem_chars:]
            msgs.append({"role": "user", "content": "Evidence you collected earlier:\n" + body})
        for s in self.steps:
            msgs.append({"role": "assistant", "content": s["raw"]})
            msgs.append({"role": "user", "content": "Output:\n" + s["obs"]})
        return msgs

    def window(self, cur):
        """What the rendered evidence body actually shows after the character cap: counts of records in the
        window, stale test records in it, stale test records in it whose text carries a pass/fail marker,
        and whether a test from the current workspace state is also in the window. Logged, not shown."""
        used, inwin = 0, []
        for r in reversed(self.mem.records):
            used += len(r.text) + 60          # tag and kind prefix, approximate
            if used > self.mem_chars:
                break
            inwin.append(r)
        stale_t = [r for r in inwin if r.kind == "test" and r.state != cur]
        return dict(records=len(self.mem.records), in_window=len(inwin),
                    stale_tests=len(stale_t),
                    stale_tests_with_result=sum(bool(RESULT_RE.search(r.text)) for r in stale_t),
                    current_test_in_window=any(r.kind == "test" and r.state == cur for r in inwin))

    def compact(self):
        old, self.steps = self.steps[:-self.keep], self.steps[-self.keep:]
        if not old:
            return
        stale_tests = sum(1 for k, st in self.seen if k == "test" and st != self.state)
        stale_reads = sum(1 for k, st in self.seen if k == "read" and st != self.state)
        if self.arm in ("flat", "fresh", "ctrl"):
            for s in old:
                lim = 900 if s["kind"] == "test" else 500
                txt = f"$ {s['action']}\n" + (s["obs"][-lim:] if s["kind"] == "test" else s["obs"][:lim])
                self.mem.add(s["kind"], txt, s["state"])
        elif self.arm == "mask":
            self.masked += old
        elif self.arm == "summ":
            text = "\n".join(f"$ {s['action']}\n{clip(s['obs'], 1500)}" for s in old)
            p = ("Update the running summary of a bug-fixing session. Keep: files read and what they contain, edits made, "
                 "test results, current hypothesis. Be concise (under 300 words).\n\nPrevious summary:\n"
                 + (self.summary or "(none)") + "\n\nNew steps:\n" + text)
            self.summary = self.chat([{"role": "user", "content": p}], max_tokens=700, summ=True)
        self.log.append(dict(ev="compact", step=len(self.log), n_old=len(old), stale_tests_retained=stale_tests, stale_reads_retained=stale_reads, n_seen=len(self.seen),
                             records=len(self.mem.records), prompt_tokens=self.last_prompt_tokens,
                             window=self.window(self.state) if self.arm in ("flat", "fresh", "ctrl") else None))

    # ---- main loop ----
    def execute(self, cmd):
        t = time.time()
        out, rc = self.run(cmd, 180)
        self.totals["tool_s"] += time.time() - t
        return clip(out, self.obs_chars)

    def solve(self):
        self.state, _ = self.run(FP_CMD, 60); self.state = self.state.strip()
        for i in range(self.max_steps):
            if self.last_prompt_tokens > self.cap and len(self.steps) > self.keep:
                self.compact()
            raw = self.chat(self.build())
            act = parse_action(raw)
            if act is None:
                # logged only: what a reply with no command was (added 10 Nov for the empty-reply diagnostic)
                self.log.append(dict(ev="empty", i=i, prompt_tokens=self.last_prompt_tokens, raw=raw, **self.last_reply))
                if self.empty_fix == "drop":
                    raw = "(reply had no complete bash block and was discarded)"
                self.steps.append(dict(raw=raw, action="(none)", obs="Reply with one ```bash block.", kind="other", state=self.state)); continue
            if "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" in act:
                return "submitted", i + 1
            obs = self.execute(act)
            new, _ = self.run(FP_CMD, 60); new = new.strip()
            kind = "edit" if new != self.state else ("test" if TEST_RE.search(act) else "read")
            self.state = new
            self.seen.append((kind, new))
            self.steps.append(dict(raw=raw, action=act, obs=obs, kind=kind, state=new))
            self.log.append(dict(ev="step", i=i, kind=kind, prompt_tokens=self.last_prompt_tokens, action=act[:200],
                                 state=new, obs=obs, window=self.win, **self.last_reply))
        return "step_limit", self.max_steps
