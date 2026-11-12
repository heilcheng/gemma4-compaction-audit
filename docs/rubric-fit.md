# Rubric fit: what each criterion gets, and what it does not

Written 8 November 2026 after pilot 2, before any held-out outcome was read. Scores are the judges' call; this records what the paper offers against each criterion and where it is thin.

| Criterion | What the paper offers | Where it is thin | What to do with remaining budget |
|---|---|---|---|
| Novelty | A measured boundary condition: a 12B Gemma agent under an 8K working context compacts in most runs (17/23 and 19/21 in pilots) but produces almost no test evidence (11–14 test steps per ~600), so freshness metadata has nothing to act on. Prior work (Looping Is Not Reliability, Assay) assumes tests are run; we measure how rarely a small agent does so unprompted, and that a one-line instruction does not change it. Controlled freshness-vs-flat comparison with a matched-length neutral tag is still run and reported. | A null result on the primary comparison. The exposure finding is new as a measurement, not as a mechanism. | Second seed on the primary pair so the null is not one draw. A 16K-cap arm to show the exposure rate is not an artifact of 8K. |
| Quality (generalization) | Policies are model-agnostic and implemented against a bash-only loop; the harness runs any OpenAI-compatible endpoint. Tasks are SWE-bench Verified across 10 repos, not competition data. | One checkpoint, one quantization, one harness. | E4B or 31B replication on a 40-task subset if time permits; otherwise state the limit. |
| Relevance | Speaks directly to the competition's deployment regime (small Gemma, limited context) and to the Kaggle forum reports about compaction. Cost accounting per run. | Does not improve a leaderboard score and does not claim to. | Add the step-type and step-limit analysis: 14/23 and 18/21 runs hit the step cap. That is the practical bottleneck a competitor would act on. |
| Verifiability | Frozen protocol (PROTOCOL.md, committed before held-out runs), seeded manifests, gold/empty preflight with listed exclusions, per-run JSON logs with every action, token counts and compaction events, public repo, notebook that regenerates every table from saved results. | Traces include repository code excerpts; publish only aggregate records plus action strings if licensing is unclear. | Reproduce a 10-task slice from a clean checkout on 12 Nov. |
| Clarity | One finding, one table, one figure, one trace example chosen by a stated rule. 2,700-word target. | Risk of hedging prose. | Write the abstract last, from the numbers. |

## Which award it fits

Overall Best Paper is the realistic target. Best New Resource is a secondary fit if the runner, policy adapters and exposure logger are packaged cleanly with a smoke test. Best New Application does not fit: no code graphs or embeddings are used.

## Title under the reframing

"Small Gemma Agents Rarely Test: Why Evidence Freshness Metadata Has Little to Act On Under Context Compaction." Subtitle: a controlled Gemma 4 12B study on SWE-bench Verified with a reusable compaction audit harness.

If the main matrix shows a real freshness effect, revert to the original title; the abstract then reports the effect with its interval.

## Interim note, 8 Nov 11:10 UTC (seed 0 at 474/725, 87 tasks complete across arms)

The held-out set behaves differently from the dev pilot: 1,733 of 19,778 steps are test steps (8.8 percent against about 2 percent in the pilots), 32 to 36 of about 95 runs per arm execute at least one test, and 18 to 26 runs per arm retain a stale test observation at a compaction. The pilot gate of eight tasks is passed. I first wrote here that the dev manifest had no django task. That was wrong: manifests/dev.txt has 9 django tasks of 23, and their pilot test-step rates were 1/274 and 5/299 against 258/3146 for held-out flat on django, so repository mix does not explain the gap and the cause is open. Correction, 8 Nov 21:30 UTC, on what the data do show: django runs execute at least one test in 27 to 29 of 65 per arm against 10 to 16 of 80 for the other repositories, but runtests.py itself appears in only 1 to 2 django runs per arm; the attempts go through pytest, manage.py test and unittest and mostly fail to find a runner. Resolved rates are 11.5 to 13.8 percent with every arm inside the bootstrap interval of flat. Title and framing are decided only after the full matrix; the "rarely test" title no longer fits as written.
