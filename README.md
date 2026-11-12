# gemma4-compaction-audit

Code, protocol, results, action logs and a reply-level diagnostic for the paper "Freshness tags on stale test evidence at compaction: no detectable benefit, a run-to-run noise floor and a one-line loop fix for a Gemma 4 12B agent" (Kaggle Gemma 4 Developer Agent Paper Track, November 2026). The paper text is `paper/draft.md`, the Kaggle Writeup body (same text with figure links) is `paper/writeup.md`, and the PDF is `paper/latex/main.pdf`. Submission topic: Tasks and Benchmarks.

The harness runs a bash-only SWE-bench Verified agent loop against a Gemma 4 12B endpoint, applies one of five context policies once the prompt passes a token cap, logs how much stale test and read evidence survives each compaction (and, in the replicate, what the rendered memory held), grades the final patch with the official SWE-bench harness, and compares policies with a paired bootstrap over tasks.

## Headline numbers and where to check them

| Number in the paper | File |
|---|---|
| Table 1 (seed 0: mask 14, summ 15, flat 13, fresh 13, ctrl 15 resolved; intervals; step limit; compacted; stale test retained) | `results/summary.json` (per_seed.0), `results/per_run.csv` |
| Seed 1 (flat 16, fresh 12, ctrl 12; -2.8 [-6.9, +1.4]) | `results/summary.json` (per_seed.1) |
| Pooled fresh against flat -1.4, [-3.8, +1.0] task-clustered and [-4.5, +1.7] unit-level | `results/summary.json` (pooled_trio), `results/extra_stats.txt` |
| Flips: flat 11 of 144 between seeds; fresh 13 of 145 same seed; 6 of 29 tasks in all five passes, 13 in one | `results/eval_noise.txt`, `results/extra_stats.txt`, `results/per_run_extra.csv` |
| Tag flips with no stale test record in the fresh run: 11 of 20 over both seeds (counter zero); 168 of the 251 exposed steps lacked a current-state test; 29 of 65 django and 10 of 80 other seed-0 flat runs ran a test | `results/per_run.csv` (`stale_test_at_compact`, `n_compactions`, `any_test`), `results/eval_noise.txt` section 3 |
| Run averages 69 steps, 50 minutes, 680 completion tokens per step (resolved runs 32 steps, 20 minutes); 85 of 110 resolutions submitted; django stratum 3 wins 10 losses (sign test p = 0.09), other 5 gains 2 losses (p = 0.45); 0.9 expected among 16 exposed at the compacted-run rate 7 of 125; step mix 79/14/7 percent reads/edits/tests (seed-0 flat 4176/739/372) | `results/per_run.csv` (`steps`, `wall_s`, `completion_tokens`, `status`, `repo`), `logs/actions/` for the window counts, `results/extra_stats.txt` for step kinds |
| Discordance 0.085 (37 of 434 pairs: 11 of 144, 13 of 145, 13 of 145); 120-task SD 2.5 to 2.7; power 22 percent at 289 task-runs, about 1700 for 80 percent | `results/eval_noise.txt` (section 1 gives the three pairs; the 6 to 12 percent sampling range in the paper is a Wilson interval on 37 of 434, and the 1200 to 2300 range scales the power requirement with that interval; the exact probability of a 5-point gap on 120 tasks is 0.084 and of a 6-point gap 0.042, by summing binomial discordant counts) |
| Rerun differences +2.1 [-2.1, +6.9] (flat, seeds) and +2.1 [-2.8, +6.9] (fresh, same seed) | `python scripts/make_paper_figures.py` output, `results/extra_stats.txt` (window exposure) |
| Step-limit runs 77 to 84 percent (112 to 114 of 145 at seed 0, 113 to 121 of 144 at seed 1); seed-0 fresh resolved 0 of its 114 step-limit runs against 2 to 5 for the other arms; 32 of 972 runs past step 40 resolved (3 percent; 2 to 4 percent per arm with seeds pooled) | `results/summary.json` (step_limit), `results/extra_stats.txt` (submitted against step-limit), `results/eval_noise.txt` |
| Replies with no complete command: 46 percent of 80083 (3 percent in never-compacted runs, 48 in compacted, 39 to 49 by arm); 428 of 921 step-limit runs issued their last command by reply 40 | `logs/actions/` (a record's `steps` minus its logged step events, minus one if it submitted); `results/per_run.csv` (`completion_tokens`) for the 1200-token estimate |
| Stalls: 570 of 1159 runs end in ten or more replies with no command (13 of them resolved, 97 of the other 589); 35 percent of mask runs, 40 of summ, 52 to 54 of the evidence arms, 21 to 23 at the 16K trigger | `logs/actions/`, `python scripts/make_stall_figure.py` (Figure 5) |
| Diagnostic on 40 tasks: 1303 of 2939 replies with no command, all at the reply limit, 1235 the word thought repeated and 68 commands cut off; 23 runs stalled, none with the placeholder | `logs/diag/diag_s0_flat.jsonl.gz`, `logs/diag/dropfix_s0_flat.jsonl.gz`, `results/diag_stats.txt` |
| Corrected loop on all 145 tasks: no stalls (73 in seed-0 flat), median 70 commands per run against 31, 19 resolved against 13, +4.1 [-0.7, +9.0], 10 gained and 4 lost | `logs/diag/dropfix_s0_flat.jsonl.gz`, `results/diag_stats.txt` |
| Fresh under the corrected loop (Amendment 5): no stalls (77 in seed-0 fresh), 13 resolved (13 before), fresh against flat -4.1 [-9.7, +1.4], 5 gained and 11 lost (sign test p = 0.21); counter 27 and 34 runs, window with a result marker 21 and 27, none of the 27 resolved; 12 of 16 differing tasks with no stale test record in the fresh run | `logs/diag/dropfix_s0_fresh.jsonl.gz`, `results/diag_stats.txt` |
| Four pairs of flat and fresh passes pooled, post hoc: 64 against 49 of 579 task-runs, -2.6 [-5.0, -0.3] task-clustered, per pair 0, -4, -5, -6 tasks, 9 tasks net for fresh and 18 for flat (sign test p = 0.12) | `results/per_run.csv`, `logs/actions/`, `logs/diag/dropfix_s0_*.jsonl.gz` (computed in `scripts/recompute_from_release.py`) |
| Exposure funnel (22, 20, 16, 1 of 145; 251 of 2587 steps) | `results/extra_stats.txt`, `logs/actions/rep_r1_s0_c8000_fresh.jsonl.gz` |
| Where resolutions happen (124 never-compacted runs with 55 resolved; median submission step 14) | `results/eval_noise.txt`, `results/per_run.csv` |
| Gold preflight 142 of 145 and the three failures | `results/extra_stats.txt` |
| 16K trigger (flat 16, fresh 11; -3.4 [-8.3, +1.4]) | `results/per_run_extra.csv`, `python scripts/analyze.py 0 16000` (needs runs/) |

A few rows quote numbers that earlier drafts carried and the final text dropped for length; they still recompute.

## What it does

- **Agent loop** (`src/gpaper/agent.py`): a minimal loop in the style of mini-SWE-agent. Each reply holds one bash command. A reply with no complete bash block runs nothing, gets a one-line reminder as its observation and still counts as a step. In the main matrix the text of such a reply went back into the context as the model's own turn; with `empty_fix="drop"` (the `--empty-fix drop` option of `modal/run.py::launch`) a one-line placeholder goes back instead, which is the corrected loop of the paper's diagnostic. The agent works inside the task's `/testbed`, with at most 80 steps, a 4000 character clip on each observation and a 180 second timeout per command. It talks to any OpenAI-compatible chat endpoint and never sees the gold patch or the evaluator's tests. The system prompt is the `SYSTEM` string at the top of the file.
- **Five context policies** (`src/gpaper/memory.py` and `Agent.compact`). When the last prompt exceeds the cap, the last three steps stay verbatim and older steps go through the arm's policy:
  - `mask`: keep the actions, drop the old observations.
  - `summ`: the model writes a cumulative summary of the older steps.
  - `flat`: deterministic evidence records, one per old step, under a 9000 character ceiling.
  - `fresh`: the same records as `flat`, each tagged with whether it was produced under the current workspace fingerprint.
  - `ctrl`: the same records as `flat`, each with a coded tag (`seq-a` or `seq-b`, followed by "no validity claim made here"). The code follows the same current-or-older split as `fresh`, so `ctrl` is not a null tag: against `fresh` it compares the wording.
- **Exposure logging**: every step is classified as read, edit or test by comparing a hash of the workspace (`git diff HEAD` plus untracked files) before and after the command. At each compaction the log records how many executed test and read steps were produced under an older workspace state (an upper bound). Runs made with the replicate code also log, per step, which records sat inside the rendered 9000-character window, how many were stale tests, how many of those carried a result marker (pass, fail, OK, error), and whether a current-state test was also in the window.
- **Grading**: sandboxes come from the prebuilt `swebench` images on Modal, and resolution is decided by `swebench==4.1.0`. Controls with the gold patch and an empty patch use the same path (`--arms gold` and `--arms empty`).
- **Analysis**: `scripts/analyze.py`, `scripts/summarize.py`, `scripts/pooled_trio.py` and `scripts/extra_stats.py` apply the same exclusions and bootstrap over tasks (5000 resamples, seed 1, percentile intervals).

## Released data

- `results/summary.json`, `results/per_run.csv`: the seed-0 and seed-1 main matrix, one row per run, with the per-seed and pooled statistics.
- `results/per_run_extra.csv`: the 16K-cap arm and the same-seed replicate, one row per run.
- `results/extra_stats.txt`: exploratory and descriptive numbers quoted in the paper (gold exclusion, strata, step kinds, replicate flips, window-level exposure, unit-level bootstrap).
- `results/eval_noise.txt` (from `scripts/eval_noise.py`): noise band of a 120-task single-run score, power simulation for paired comparisons, and the behavioural probe on exposed steps. It prints rerun differences as original minus rerun (-2.1); the paper reports rerun minus original (+2.1).
- `logs/actions/*.jsonl.gz`: every run's action strings, step kinds, token counts, compaction events and (for the replicate) window descriptions. No tool outputs and no raw model replies. The action strings are the agent's own commands, so a few quote lines of repository source.
- `logs/diag/*.jsonl.gz`: the diagnostic of Amendment 4 and the pass of Amendment 5. `diag_s0_flat` holds 40 runs of the unchanged loop with every reply's completion tokens and finish reason and the full text of each reply with no command; `dropfix_s0_flat` holds 145 runs of the corrected loop in the same format, and `dropfix_s0_fresh` the fresh pass of Amendment 5 under that loop. `results/diag_stats.txt` (from `scripts/diag_stats.py`) summarises all three. A reply with no command can quote text the model had just read from the repository.
- `figures/`: the five figures in the paper (`overview`, `differences`, `flips`, `exposure_funnel`, `stall`); `figures/extra/` holds three descriptive figures not used in the paper.
- `docs/trace_django-16527.md`: a worked trace of one held-out task. The paper does not discuss it.

Raw run records with tool outputs (`runs/`) are not published.

## Setup

Python 3.10 or newer for the package and the Modal scripts (`scripts/recompute_from_release.py` also runs on 3.9). The analysis scripts use only the standard library and read `runs/*.jsonl`, which is not published; `scripts/make_figures.py` needs matplotlib and the notebook needs pandas. Running on Modal needs the `modal` CLI and a Modal profile.

```
uv run --with pytest --with httpx python -m pytest -q tests scripts/smoke_local.py
```

That command runs the unit tests and a no-network smoke test of the policies (a canned model and a canned shell drive the real agent loop). It needs no endpoint.

## Serve Gemma 4 12B on Modal

`modal/serve.py` serves `google/gemma-4-12B-it-qat-w4a16-ct` (pinned revision 1d2c2d7f) with vLLM 0.33.0 on A100-80GB (max two replicas, 32768-token context, prefix caching) and scales to zero when idle.

```
PYTHONPATH=src modal run modal/serve.py::fetch     # one-time weight download into a volume
PYTHONPATH=src modal deploy modal/serve.py         # prints the web endpoint URL
```

Put the endpoint URL, with no trailing slash, in `modal/url.txt`. `modal/run.py` reads that file at deploy time and passes it to the agent as `G4_URL`. The served model name is `gemma4-12b`. The endpoint has no authentication, so `modal/url.txt` is git-ignored and the URL should not be published. Anyone reproducing the study deploys their own copy.

## Run one task, attached

```
PYTHONPATH=src modal run modal/run.py --tasks <instance_id> --arms flat --seed 0 --cap 8000 --out runs/smoke.jsonl
```

`--tasks` takes a comma-separated list of SWE-bench Verified instance ids or a manifest file. `--arms` takes a comma-separated list. Pass `--cap` explicitly; the script default is 12000, not the 8000 used for the main matrix. Attached mode stops if the local client disconnects, so use it for smoke tests.

## Run the full matrix, detached

```
PYTHONPATH=src modal deploy modal/run.py
PYTHONPATH=src modal run modal/run.py::launch --tasks manifests/heldout.txt --arms mask,summ,flat,fresh,ctrl --seed 0 --cap 8000
python scripts/collect.py 0 8000
```

`::launch` spawns every missing (task, arm) job on the deployed app and exits. Each job writes its record to a Modal volume. `scripts/collect.py <seed> <cap> [rep]` pulls the volume, one arm per call, into `runs/main_s<seed>_<arm>.jsonl` (8000 cap), `runs/cap<cap>_s<seed>_<arm>.jsonl` (other caps), `runs/rep_<rep>_s<seed>_c<cap>_<arm>.jsonl` (replicates) or `runs/controls_heldout_<arm>.jsonl` (gold and empty); it keeps local records and replaces a local error record only when the volume holds a successful one. It calls the Modal CLI with the profile name `coglix-labs`; change that string to your own profile. Do not run `::launch` again for the same arms while jobs are still in flight, because in-flight jobs look missing and get spawned twice (the collector keeps the first result to land). The 16K arm is `--cap 16000`; the replicate is `--rep r1`; the preflight is `--arms gold`.

Task manifests are in `manifests/` (`heldout.txt` for the main matrix, `dev.txt` for the pilots). `scripts/make_manifest.py` regenerates them from SWE-bench Verified with a fixed seed, allocation in proportion to repository size, and no outcome information.

## Reproduce the paper's numbers from this release

```
python3 -I scripts/recompute_from_release.py .
```

This reads only `results/`, `logs/actions/` and `logs/diag/` (standard library, Python 3.9 or newer, about 15 seconds) and recomputes 202 numbers behind the paper (`--full` adds a slower 1-point power search as one more item): Table 1, every interval against flat, the pooled task-clustered and unit-level intervals, the flip counts, the exposure funnel, the compaction and submission-timing splits, the share of replies with no command, the stall counts by arm, the diagnostic and corrected-loop counts for both arms, the four-pair pooled interval, the discordance and 120-task noise band, the power simulation and the per-arm test shares, printing paper value against recomputed value. Everything not in this list (the resolved flags themselves, the read/edit/test classification, the pilot counts, the window-logging reconstruction) depends on the unpublished `runs/` records.

Conventions the numbers depend on: bootstrap resamples are drawn with `random.Random(1).choices(tasks, k=len(tasks))` over the sorted task list (a different draw order moves an interval end by one unit, 0.35 points at 289 task-runs); the power figures use a normal-approximation sign test on discordant pairs (|z| at or above 1.96), simulated with `random.Random(1)`; an exact binomial test gives about 16 percent power at 289 task-runs instead of 22. `results/per_run.csv` lists two seed-1 runs with `in_common=0` that the statistics exclude. In `logs/actions/`, `rep_r1_s0_c8000_fresh` is the same-seed replicate of fresh (its step events carry the `window` field; no other file does), `controls_heldout_gold` is the gold-patch preflight, and records carry no `error` field or patch.

## What a rerun costs

The recompute step above is offline and free. Rerunning the agent is not: by the ledger in `PILOT.md`, seed 0 (725 runs) cost me about $410 on Modal and seed 1 (435 runs) about $230, on two A100-80GB replicas plus one CPU sandbox per run. Those were estimates; Modal's billing for everything in this paper came to 987 dollars. The corrected loop is much cheaper to run, 18 to 24 minutes a task against 49. A rerun will not reproduce my runs one by one, because the same request seed gave a different run on this server (13 of 145 outcomes flipped); expect the arm totals to move by a few tasks.

## Regenerate tables and figures (needs the unpublished runs/)

```
python scripts/analyze.py 0 8000        # seed-0 table, exposure counts, step kinds, per-repo table
python scripts/analyze.py 1 8000        # seed 1
python scripts/analyze.py 0 16000       # 16K-cap arm
python scripts/summarize.py             # results/summary.json, per_run.csv, per_run_extra.csv
python scripts/pooled_trio.py           # pooled two-seed trio with task-clustered bootstrap
python scripts/extra_stats.py           # exploratory numbers; redirect to results/extra_stats.txt
python scripts/make_figures.py          # figures/flips and figures/extra/
python scripts/make_paper_figures.py    # figures/overview, differences, exposure_funnel
python scripts/eval_noise.py            # noise band, power, probes; redirect to results/eval_noise.txt
python scripts/make_writeup.py          # paper/writeup.md from paper/draft.md
python scripts/make_latex.py            # paper/latex/main.tex from paper/draft.md
python scripts/export_actions.py        # logs/actions/
python scripts/export_diag.py           # logs/diag/
python scripts/diag_stats.py            # diagnostic numbers; redirect to results/diag_stats.txt
python scripts/make_stall_figure.py     # figures/stall (reads only logs/, so it runs from this release)
```

`notebooks/results.ipynb` reads `results/summary.json` and `results/per_run.csv` and needs no Modal endpoint.

## File map

```
PROTOCOL.md             frozen protocol, dated amendments 1 to 5 and later notes
PILOT.md                pilot log and spend ledger
docs/                   research plan, related work, rubric-fit notes, the trace
manifests/              dev and held-out task ids
modal/serve.py          vLLM server for Gemma 4 12B
modal/run.py            sandbox, agent run and grading for one (task, arm); attached and detached entry points
src/gpaper/agent.py     the bash-only loop, compaction, exposure counters, window logging
src/gpaper/memory.py    fingerprint, evidence records, flat/fresh/ctrl renderers, observation masking
scripts/                analysis, collection, figures, export (see above)
tests/                  unit tests for the renderers and fingerprint
notebooks/results.ipynb tables and figures from the saved results
paper/draft.md          the paper (markdown); paper/writeup.md is the Kaggle Writeup body
paper/latex/            LaTeX source, bibliography and PDF
results/, figures/, logs/actions/, logs/diag/   released outputs
```

## Exclusions and amendments

The design, the exclusion rule and every deviation made during the runs are written in `PROTOCOL.md`, which was frozen before any held-out outcome was read. Two dev tasks (`psf__requests-1766` and `pylint-dev__pylint-7277`) fail the gold-patch preflight and are excluded from the dev analysis. Three held-out tasks (`psf__requests-1921`, `pylint-dev__pylint-6528`, `pylint-dev__pylint-7080`) fail it too; no arm resolved any of them, and `results/extra_stats.txt` gives the main comparisons without them. Amendment 1 is a retry of transport failures on the chat call, Amendment 2 a longer wall-clock limit, Amendment 3 the added runs (seed 1, 16K arm, gold preflight, replicate) with the order in which they were decided. Amendment 4 is the reply diagnostic and the corrected loop on flat, Amendment 5 the corrected loop on fresh. The freeze and amendment dates rest on commits in my private history, which I cannot publish because its early commits hold an endpoint address; the public tree is a single-commit export, so an outsider cannot check those dates from this repository. Please read the protocol before comparing numbers with other work.

## Limitations

- One checkpoint, one quantization, one agent loop: Gemma 4 12B QAT, 4-bit weights, default chat template, no extended thinking, temperature 0.3. Nothing here says the findings carry over to other models or agent scaffolds.
- Exposure is measured with a global workspace fingerprint, so any edit marks every earlier record as older, and a command counts as a test only if it matches a fixed pattern (pytest, runtests, unittest, manage.py test, tox, nosetests) and left the fingerprint unchanged. The compaction-time counter is an upper bound; the window-level measurements come from three single passes (the fresh replicate and the two corrected-loop passes).
- Most runs hit the 80-step limit, and the agent resolves about one task in ten, so any memory comparison at this floor is noise-dominated. The same-seed replicate shows that a request seed did not reproduce a run on this vLLM server.
- 46 percent of replies in the main matrix held no complete command, each still used one of the 80 steps, and half of all runs ended in ten or more of them. The main matrix did not save raw replies; the diagnostic did, on 40 tasks, and found the model repeating the word thought to the reply limit with the loop feeding that text back. Mask, summ and ctrl ran only under that loop. The corrected loop ran flat and fresh once each on seed 0: the stalls went away in both, flat resolved 19 and fresh 13, and one pass per arm cannot tell that gap from noise.
- Fresh never led flat in the four pairs of passes I have (seed 0, seed 1, 16K, corrected loop), and pooled it trails by 2.6 points with a task-clustered interval of [-5.0, -0.3]. I thought of that pooling after seeing the last pair, no amendment names it, the pairs differ in trigger and loop, and the interval is unadjusted. Leaving out one pair at a time gives -3.5 [-6.2, -0.9] (without seed 0), -2.5 [-5.5, +0.2] (without seed 1), -2.3 [-4.8, +0.2] (without 16K) and -2.1 [-4.6, +0.5] (without the corrected loop), so three of the four intervals include zero. Split by repository, again after the fact, the deficit is in django: fresh resolved 12 of 260 task-runs against 28 for flat, -6.2 points [-10.4, -2.7], while in the other repositories it is 37 against 36 of 319, +0.3 [-2.2, +2.8]. I treat it as a hypothesis for a preregistered rerun and not as a finding that the tag costs resolutions.
- Run logs with tool outputs include repository code excerpts and are not published. Cost figures in `PILOT.md` before 10 Nov are a ledger of estimates; the entries from 10 Nov quote Modal's billing.

## Citing

Hailey H. L. Cheng. Freshness tags on stale test evidence at compaction: no detectable benefit, a run-to-run noise floor and a one-line loop fix for a Gemma 4 12B agent. Kaggle Gemma 4 Developer Agent Paper Track, November 2026. https://github.com/heilcheng/gemma4-compaction-audit

## License

MIT. See `LICENSE`. Copyright (c) 2026 Hailey H. L. Cheng.
