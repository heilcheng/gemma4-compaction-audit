# Frozen protocol v2 (2026-11-08, before any held-out outcome)

Model: google/gemma-4-12B-it-qat-w4a16-ct @1d2c2d7f, vLLM 0.33.0, A100-80GB, default chat template (no extended thinking), temperature 0.3, per-run seed, max 1200 tokens per step.
Harness: own minimal bash-only loop (src/gpaper/agent.py) modelled on mini-SWE-agent; prebuilt swebench images; swebench 4.1.0 grading. Max 80 steps, 4000 char observation clip, bash timeout 180 s.
Tasks: manifests/heldout.txt (145 SWE-bench Verified, stratified by repo, seed 20261104). Dev set manifests/dev.txt (23, 2 excluded because gold fails). Tasks whose gold patch fails the preflight are excluded at analysis time and listed.
Compaction: triggers when the last prompt exceeds 8000 tokens; the last 3 steps stay verbatim; older steps go through the arm's policy.
Arms: mask (actions kept, old observations dropped), summ (Gemma summary, cumulative), flat (deterministic evidence records, 9000 char ceiling), fresh (flat + validity tag vs current workspace fingerprint), ctrl (flat + neutral tag of matched length).
Primary comparison: fresh vs flat (ctrl as sanity check on tag-length effects). Secondary: mask, summ vs flat. Metric: resolved by SWE-bench grading. Paired bootstrap over tasks.
Prompt change after pilot 1: one line asking for tests after each edit (identical across arms). Pilot 2 showed it barely changes behaviour; documented as a finding.
Exposure measure: at every compaction, count retained test/read records produced under an older workspace state.
No tuning on held-out outcomes. Infra errors are rerun; agent step limits and wrong patches count as failures.

## Amendment 1 (8 Nov, during seed 0, before any outcome was analysed)

Sixteen seed-0 runs, all django tasks, died mid-run with a JSONDecodeError when the Modal web endpoint returned a non-JSON gateway response for a long generation. The chat call now retries the identical request up to three more times (10, 20, 30 s backoff) and records each retry in the run log. Requests, prompts, decoding parameters and the agent loop are unchanged. Errored runs are re-run from scratch with the same seed under the resumable runner; the first attempt is discarded because it has no outcome.

## Amendment 2 (8 Nov 15:10 UTC, seed 0 at 714/725)

Ten seed-0 runs (sympy, scikit-learn, sphinx, pytest tasks) produced no result within the 3 hour wall-clock limit of the Modal function and sandbox; the limit is infrastructure, not part of the agent protocol (80 steps, 180 s per command, 1800 s grading). The limit is raised to 6 hours and the ten runs are re-run with the same seed. Their wall-clock times are reported so readers can see which runs needed the longer limit.

Follow-up to Amendment 2 (8 Nov 18:45 UTC): all 45 re-runs of these nine tasks (ten runs re-spawned, plus the duplicates described in the launcher note) took 0.6 to 1.33 hours of wall clock, well under the old 3 hour limit, so the first attempts most likely hung on infrastructure (a sandbox exec or an HTTP call that never returned) rather than being genuinely long runs. The 6 hour limit stays; the re-run outcomes are used as the seed-0 results for these tasks.

## Amendment 3 (9 Nov, commit ea650cd 04:13 +0800; written after seed 0 and seed 1 were analysed, so item (a) records seed 1 after the fact; the 16K arm, preflight and replicate in (b) to (d) were recorded before any of them was read)

What was frozen on 8 Nov covered seed 0 of five arms at the 8K cap, the primary comparison fresh against flat, the exposure counter and the paired task-level bootstrap. Everything below was added after the seed 0 table was read and is reported as such.

Added runs. (a) Seed 1 of flat, fresh and ctrl on the same 145 tasks, analysed with the same scripts; pooled two-seed estimates use a bootstrap that resamples tasks, keeping both seeds of a task together. (b) A 16K-cap arm of flat and fresh, seed 0. (c) A gold-patch preflight on all 145 held-out tasks; tasks whose gold patch does not resolve are listed and the main table is also given without them. (d) A same-seed replicate of the fresh arm, seed 0, run with the agent code at commit "window logging" which adds logging only: per step the workspace fingerprint, the clipped observation and a description of the rendered evidence window (records inside the 9000-character cap, stale test records among them, those carrying a result marker (the pattern matches passed, failed, OK, Ran N test, AssertionError and error), and whether a current-state test is also in the window). Prompts, decoding and the loop are unchanged. The replicate serves two purposes: an estimate of same-seed run-to-run variation, and a direct measure of what the fresh tag was shown on, which the frozen counter does not give.

Corrections to the frozen text. The exposure counter counts every executed test or read step whose fingerprint differs from the current one, whether or not its record is inside the rendered window and whether or not its output carries a result. It is an upper bound for every arm, not only for mask and summ. Step-limit runs are graded on the diff present at the limit, as the runner always did; the frozen text said they count as failures, which was imprecise. The dev manifest contains 9 django tasks; an interim note claimed otherwise and has been corrected.

Exploratory analyses, not pre-specified: fresh against ctrl; per-repository and django against non-django strata; per-arm step-kind counts and submit against step-limit decomposition of resolved runs. The trace example is the lowest-index held-out task in which seed-0 fresh retained a stale test at a compaction and fresh and flat differ in outcome.

Further corrections recorded 9 Nov after the review rounds: the frozen text called the ctrl tag "matched length"; it matches the fresh tag's length only on stale records (35 against 43 characters) and not on current ones (35 against 8), as the paper now states. "Protocol v2" names the version frozen on 8 Nov; v1 was the pre-pilot draft, replaced after pilot 1 and before any held-out run.

## Notes recorded 10 Nov after a further review round

Gold-failing tasks. The frozen text says tasks whose gold patch fails the preflight are excluded at analysis time. The paper's tables keep all 145 held-out tasks instead. No arm resolves any of the three, so no resolved count changes; the primary interval is [-4.1, +4.1] with them and [-4.2, +4.2] without (results/extra_stats.txt gives every main comparison without them).

What a step is. A step is one model reply. A reply with no complete fenced bash block executes nothing, receives a fixed one-line reminder as its observation, counts toward the 80-step limit and enters memory as a record of kind other. The run logs hold executed commands only, so these replies appear as the gap between a run's step count and its logged step events: 37226 of 80083 replies in the main matrix (46 percent). Their completion tokens average about 1200, the per-reply limit, so they look like replies cut off before the command; the raw replies were not saved. The frozen text did not describe this.

Amendment 3 heading. The heading above was reworded in commit 9eb1e23 (9 Nov 22:24 +0800), after ea650cd, to say plainly that item (a) records seed 1 after the fact.

Interim looks. Partial seed-0 results were read while seed 0 ran: docs/rubric-fit.md holds a note from 8 Nov 11:10 UTC with exposure counts at 474 of 725 runs and one from 21:30 UTC quoting resolved rates of 11.5 to 13.8 percent. The two amendments made during seed 0 change infrastructure only.

## Amendment 4 (10 Nov, written before any run it describes; post hoc and exploratory)

Why. 46 percent of replies in the main matrix carried no command and the raw replies were not saved, so I cannot say what they were. The action logs also show that these replies cluster: 630 of the 921 step-limit runs end in an unbroken run of them that lasts to the step limit. This amendment adds a small diagnostic to find out what the replies contain and whether one change to the loop removes them. Nothing here touches the confirmatory comparison.

Tasks. The first 40 of the 145 held-out tasks when instance ids are sorted by the hex SHA-256 of the id (manifests/diag40.txt). No outcome was used to pick them.

Phase 1 (label diag). Flat arm, seed 0, 8000-token trigger, the loop exactly as in the main matrix. The only change is logging: each reply's completion tokens and finish reason, and the full text of every reply with no command.

Phase 2. One or two variants of the loop on the same 40 tasks, chosen after reading the phase-1 replies and named here in advance as the candidates: (a) a higher per-reply token limit (4096 in place of 1200); (b) replacing the text of a reply with no command by a one-line placeholder before it goes back into the context; (c) both. Which one runs, and why, is recorded in PILOT.md when it is launched.

Outcomes. Share of replies with no command; number of runs that end in ten or more such replies; resolved count. Each variant is compared with phase 1 on the same tasks. With 40 tasks the resolved comparison has little power and I will report it as a count, not a test.

Spend. Actual Modal billing for the two project apps stood at 905 dollars before this amendment. The diagnostic stops before that reaches 975.

Note added after the diagnostic (10 Nov). Phase 2 ran candidate (b) alone; PILOT.md records the choice and what I had seen when I made it. After reading both phases on the 40 tasks I ran the same changed loop on the other 105 held-out tasks, so that one full flat pass under it can be set beside Table 1. That extension is not part of this amendment: it was decided with the 40-task outcomes known, and PILOT.md records it before its launch. The tag comparison was not rerun under the changed loop, because a fresh pass would have taken the billing past 975.

## Amendment 5 (11 Nov, written before the run it describes; post hoc)

Why. Every comparison of arms in the paper comes from the loop that stalls. The changed loop of Amendment 4 (label dropfix) ran on flat only, so the frozen primary comparison, fresh against flat, has not been made under it. This amendment adds the missing arm.

Run. Fresh arm, seed 0, 8000-token trigger, all 145 held-out tasks, with the loop, logging and label exactly as in the dropfix flat pass. One pass. A run that ends in an infrastructure error is rerun once under Amendment 1; nothing else is rerun.

What I had seen when I wrote this. The whole dropfix flat pass: 19 of 145 resolved, a stale test record retained by the counter in 27 runs, one with a result marker in the rendered window in 21. No fresh run under the changed loop exists yet.

Analysis, fixed now. Fresh minus flat on resolved, paired by task, with the bootstrap interval and sign test used for the primary comparison. I report it whatever it shows and call it what it is: one seed, one pass per arm, decided after the main results were known, and subject to the same run-to-run noise the paper measures. Descriptive, alongside it: runs that stall, runs at the step limit, the resolved count next to the passes of the old loop, the counter and window exposure, and outcomes in the runs where a stale test record was retained.

Spend. Billing for the two project apps reads 948.46 dollars. The 975 stop in Amendment 4 was my own margin under the 1000 dollar budget and it is why the note above says this pass was not run. I now run it: the flat pass under the same loop cost about 30 dollars, so this one should end near 982. If billing reaches 992 I stop both apps and report the runs that landed.

Note after the run (11 Nov). The pass landed with no infrastructure error and nothing was rerun. Billing ended at 986.51 dollars, above the 982 I expected because the fresh runs were longer than the flat ones, and under the 992 stop; both apps are stopped. The paper reports the analysis fixed above. It also reports a pooling of the four pairs of flat and fresh passes (seed 0, seed 1, 16K, changed loop) that I thought of after reading this result. That pooling is outside this amendment and the paper and PILOT.md label it post hoc and unadjusted.

## Provenance

The protocol was frozen in commit 7f38725 ("Protocol v2 frozen; exposure logging; resumable runner; launch main seed 0", 8 Nov 2026 12:02:18 +0800), the same commit that launched seed 0; the first seed-0 run log was created at 12:02:13 +0800. Amendment 1 is commit 5861dd5 (14:56 +0800), Amendment 2 commit a76ff7a (23:12 +0800), Amendment 3 commit ea650cd (9 Nov 04:13 +0800), Amendment 4 commit 44b8883 (10 Nov 05:06 +0800). Amendment 5 was committed on 11 Nov before its run was launched; PILOT.md gives the launch time. The pilot viability gate was written in PILOT.md before pilot 2 ran, not in this protocol. The public repository is a single-commit export of the final tree; the dated history with these commits lives in the author's private repository, whose early commits hold an unauthenticated endpoint URL, and can be shown to a reviewer on request.
