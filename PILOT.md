# Pilot log

2026-11-04: repo scaffolded, docs/ holds the three plan files, src/gpaper/memory.py has the four-arm renderers (3 tests pass), Modal CLI installed, profile coglix-labs active.
Not started: mini-SWE-agent harness, Modal vLLM server, SWE-bench env preflight. No compute spent.
Gate: the pilot ($60 cap) needed my explicit go; the full $1,000 exceeded the $500 cap I had first set for this competition.

## Spend ledger (coglix-labs, apps kaggle-g4paper-*, max_containers=1, A100-80GB about $2.50/h)
- 2026-11-04 weights fetch (CPU, 30 s): ~$0.01
- 2026-11-04 first deploy failed in vLLM profile run (FlashInfer sampler needs nvcc); ~10 min GPU wasted, ~$0.50
- fix: VLLM_USE_FLASHINFER_SAMPLER=0. Smoke chat OK ("17*23=391"), cold start 320 s incl. image build, ~$0.3
- Running total estimate: ~$1.0 of the $60 pilot cap. Server scales to zero after 300 s idle.
- Endpoint in modal/url.txt (needs curl -L; model name gemma4-12b; no auth, so do not publish the URL)
Next: SWE-bench Verified env preflight (empty/gold patch controls), mini-SWE-agent on Modal sandboxes with the four policies.

## Dev pilot 1 (2026-11-05, 23 dev tasks, flat arm, cap 8K, 60 steps, no test instruction)
- Controls: gold 21/23 resolved (psf__requests-1766 and pylint-dev__pylint-7277 fail with gold, excluded), empty 0/23.
- Flat arm: 3/23 resolved (13%); 14/23 hit the 60-step limit; ~7.9 min wall per task; 5.9M prompt / 0.63M completion tokens total.
- Compaction at 8K: 17/23 tasks. But only 14 of 602 steps were test runs, 3/23 tasks ran any test, 1 task retained a stale test record. The agent almost never tests, so freshness metadata has nothing to act on.
- Pilot 2 (protocol v2): system prompt adds "after each edit, run the relevant existing tests" (same in all arms), 21 gold-sound dev tasks, flat arm. Gate: >= 8 tasks with a stale test retained at compaction, else reframe.

## Dev pilot 2 result (2026-11-08, 21 tasks, flat arm, test-after-edit line)
- 4/21 resolved, 18/21 step limit, 19/21 compacted, 11 test steps of 586, 4 tasks ran any test, 1 task retained a stale test at compaction. Gate (>=8) failed. Paper reframed; see docs/rubric-fit.md.
- Correction: pilot 1 counts recomputed from runs/dev_pilot1.jsonl are 14/23 step limit and 17/23 compacting (earlier lines said 15 and 18).

## Spend ledger update, 8 Nov 16:40 UTC (estimate, to be reconciled against the dashboard)

The earlier estimates counted only the GPU servers. Modal also bills reserved CPU and memory for the run functions (1 CPU, 2 GiB) and the sandboxes (2 CPU, 8 GiB) for their whole lifetime, about $0.18 and $0.46 per hour each at list prices. With a mean run of about 0.7 hours:
- seed 0, 725 runs plus about 40 reruns and duplicates: about 535 run-hours, about $340 for functions and sandboxes, plus about 14 hours of two A100s at about $2.50 each, about $70. Seed 0 total about $410.
- pilots, controls and smoke tests before 8 Nov: about $40.
- seed 1 (flat, fresh, ctrl, 435 runs): about $230 forecast.
Running total forecast after seed 1: about $680 of the $1,000 I released. A 16K-cap arm on flat and fresh (290 runs, about $155) fits if the dashboard confirms these figures; otherwise it runs on a half manifest.

9 Nov 01:50 UTC: the 145 fresh replicate (r1) jobs spawned at 20:14 UTC on 8 Nov never landed and the run app showed no tasks, so they were spawned again (one test job plus 144); about $80 to 95 more. 16K arm done (290 runs), gold preflight done (145).

9 Nov 06:50 UTC: all runs complete (seed 0 five arms, seed 1 trio, 16K arm, gold preflight, fresh replicate r1 with one rerun). kaggle-g4paper-serve stopped. No further GPU spend planned for this paper.

10 Nov (+08), empty-reply diagnostic (PROTOCOL.md Amendment 4). Actual Modal billing before it: kaggle-g4paper-run 798.35 and kaggle-g4paper-serve 106.78, 905.13 dollars in all, which is more than the estimates above added up to. The line "no further GPU spend planned" of 9 Nov was my own note; the budget is 1000 and the diagnostic stops before 975.

9 Nov 21:11 UTC (10 Nov 05:11 +08): phase 1 launched (label diag, 40 tasks of manifests/diag40.txt, flat, seed 0, loop unchanged, replies logged).

9 Nov 21:36 UTC (10 Nov 05:36 +08): phase 2 variant chosen with 16 of 40 phase-1 runs landed and 79 replies with no command read. 73 of the 79 are the single word "thought" repeated to the 1200-token limit (every reply starts with that word, the header of Gemma's thinking channel that leaks into the text); 6 are commands cut off inside a heredoc or a long one-liner. So a higher reply limit (candidate a) would fix 6 of 79 and make the other 73 longer. I run candidate (b) alone, label dropfix: the text of a reply with no command is replaced by "(reply had no complete bash block and was discarded)" before it goes back into the context. Nothing else changes. The resolved counts of the 16 landed runs were visible when I chose (3 resolved); the choice rests on the reply text.

9 Nov 22:05 UTC (10 Nov 06:05 +08): both phases landed, 40 runs each. Phase 1 (loop unchanged): 1303 of 2939 replies with no command (44 percent), 1235 of them the "thought" loop, 23 runs ending in ten or more such replies, 6 resolved. Phase 2 (dropfix): 288 of 2717 (11 percent), no run ending in ten or more, 5 resolved, median 72 executed commands a run against 37, and 21.6 thousand completion tokens a run against 47.4 thousand. Decision after reading these, so outside Amendment 4: run dropfix on the other 105 held-out tasks as well, to have one full flat pass under the changed loop to set beside Table 1 (compared with seed-0 flat of the main matrix on all 145). The dropfix runs are short (15 minutes), so this is about 20 dollars.

9 Nov 22:48 UTC (10 Nov 06:48 +08): the extension landed, so dropfix now covers all 145 held-out tasks (flat, seed 0, 8000 trigger). One run (scikit-learn__scikit-learn-12973) ended in a ReadTimeout and was rerun once under Amendment 1. Result: 1046 of 9434 replies with no command (11 percent), no run ending in ten or more of them (73 in seed-0 flat of the main matrix), 99 runs at the step limit (113), 46 submitted (32), 19 resolved against 13, 10 tasks gained and 4 lost, +4.1 points [-0.7, +9.0], sign test p = 0.18. On the 105 tasks outside the diagnostic 40 it is 14 against 10. Median executed commands per run 70 against 31, completion tokens 44 percent of seed-0 flat, wall time 18 minutes against 49.

9 Nov 22:51 UTC: Modal billing for the two project apps reads 948.04 dollars (kaggle-g4paper-run 833.42, kaggle-g4paper-serve 114.62; daily rows, which may lag by a little). Both apps stopped. A fresh pass under the changed loop would cost about 34 dollars and pass the 975 stop, so I do not run it; the tag comparison under the changed loop stays open and the paper says so.

11 Nov 00:50 UTC: billing for the two apps reads 948.46 (settled rows through 9 Nov). Free check on the dropfix flat logs before deciding anything: 123 of 145 runs compacted and 12 of those resolved (6 of 126 in seed-0 flat), 22 never compacted and 7 resolved (7 of 19); the counter retained a stale test record in 27 runs (25 in seed-0 flat), the window held one in 27 and one with a result marker in 21. So the changed loop leaves the tag about as much to act on as before. PROTOCOL.md Amendment 5 written: one fresh pass under the changed loop, about 34 dollars, stop at 992.

11 Nov 00:51 UTC: Amendment 5 pass launched (fresh, seed 0, 8000 trigger, label dropfix, 145 tasks), after commit 5f54c20 was pushed.

11 Nov, landed and exported by 02:58 UTC: the Amendment 5 pass, 145 runs, no infrastructure error, nothing rerun. Fresh under the changed loop: 986 of 10060 replies with no command (10 percent), no run ending in ten or more of them (77 in seed-0 fresh), 113 runs at the step limit, 32 submitted, 13 resolved (13 in seed-0 fresh, 5 gained and 5 lost). Against dropfix flat (19): -4.1 points [-9.7, +1.4], 5 gained and 11 lost, sign test p = 0.21. So the stalls went away in both arms and the resolved count rose in flat only; the two dropfix passes resolve 32 of 290 against 26 for seed-0 flat and fresh. Exposure: the counter retained a stale test record in 34 runs (2 resolved), the window held one with a result marker in 27 (none resolved, 1.5 expected at the compacted-run rate of 7 in 128). In 12 of the 16 tasks where the two arms differ the fresh run retained no stale test record. Median executed commands per run 72, 24 minutes a run.

11 Nov, after the pass landed: both apps stopped. Billing for the two apps reads 986.51 dollars (run 866.05, serve 120.46), above the 982 I expected in Amendment 5 because the fresh runs took 24 minutes each against 18 for flat, and under the 992 stop. No further runs.

11 Nov, after reading the Amendment 5 result: I noticed that fresh had not led flat in any of the four pairs of passes (seed 0: 13 against 13; seed 1: 12 against 16; 16K: 11 against 16; changed loop: 13 against 19) and pooled them: 49 against 64 of 579 task-runs, -2.6 points, task-clustered bootstrap [-5.0, -0.3]; by task 9 net for fresh and 18 net for flat, sign test p = 0.12. This pooling is not in any amendment and I chose it after seeing all four pairs, so the interval is unadjusted and post hoc. Other poolings I looked at in the same sitting: leaving out one pair at a time. With the release script's bootstrap these are -2.1 [-4.6, +0.5] (without the changed loop), -2.3 [-4.8, +0.2] (without 16K), -2.5 [-5.5, +0.2] (without seed 1, computed a little later for completeness) and -3.5 [-6.2, -0.9] (without seed 0), so three of the four include zero. The paper reports the four-pair figure with these labels and the leave-one-out range.
