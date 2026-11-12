# Related work distinction notes

Read 8 Nov 2026 via WebFetch, a summarising fetcher, so re-check any figure before it goes in the paper. Full HTML: Looping, Assay, Complexity Trap. Abstract pages only: Compact-Bench (first fetch failed with a domain-verification error, retry worked) and Benchmarks Are Compaction-Friendly.

## Per-paper record

**Looping Is Not Reliability** (arXiv 2607.24604v3, cs.CL, 4 Oct 2026). Authors: Xueping Gao, Jianwei Yang, Qiang Yang (all Alibaba Cloud Computing, Hangzhou). Venue: AgenticDev '26 workshop, Munich, 12-16 Oct 2026, DOI 10.1145/3843282.3844438.
- Cells: (a) 30 HumanEval repairs x 6 evidence conditions x 5 seeds x 3 forced revisions = 900 trajectories, Qwen2.5-7B-Instruct. (b) Common-state: 27 tasks x 5 seeds, 2,430 single-step branches (1,215 at 7B, 1,215 at 14B). (c) Online comparison: 27 tasks x 2 start states x 5 seeds x 2 arms (540 rollouts, 7B). (d) Repository agent: 24 bugs, 9 Python projects, 288 rollouts per stack (24x2x2x3) on Qwen2.5-14B, Qwen2.5-Coder-32B-AWQ, Qwen3-Coder-Next-FP8, Devstral Small 2 24B; two 576-rollout Devstral factorials (state binding x admission/rollback x certification; contract OFF/ON x revision limit 1/3/5/8).
- Test behaviour: trajectory studies use forced revision, stated as not the behaviour of adaptive agents. Repo agent has a `test` action capped at six visible tests; commit gate run by the harness. Does not report how often agents run tests unprompted. No context compaction variable (only passing mention of long-context pressure).

**Assay: Claims That Decay With the Code** (arXiv 2609.36170v1, cs.SE, 28 Sep 2026, no venue). Authors: Om Shankar Tiwari (Google), Tangi Vass (OMNI3ai), Gagan Deep Singh (Glinr Studios).
- Cells: Express, Flask, Gin, Axum, FastAPI and Assay itself; E1 token cost of a 600-token brief, E2 incremental indexing, E3 binding strategies (100 trials per k in {1..32}), E4 twelve-file Python project with 12 scripted scenarios (3 honest, 9 adversarial), E5 change size; one private dogfooding change. No model in the loop.
- Test behaviour: scripted doer only; no agent test-running rates. Authors say a model-in-the-loop study on SWE-bench Verified, with and without brief and gate, is designed and "will" be preregistered; no results. This study may appear alongside ours.

**The Complexity Trap** (arXiv 2508.21433v3, cs.SE, v3 27 Oct 2025). Authors: Tobias Lindenbauer, Igor Slinko, Ludwig Felder, Egor Bogomolov, Yaroslav Zharov (JetBrains Research; TUM). Venue: page header names the workshop Deep Learning for Code in the Agentic Era; not independently confirmed.
- Cells: SWE-agent on SWE-bench Verified, 500 instances, five configs (Qwen3-32B, Qwen3-32B thinking, Qwen3-Coder 480B, Gemini 2.5 Flash, Gemini 2.5 Flash thinking); Raw vs masking (M=10) vs LLM summary (N=21, M=10); 250-turn limit. OpenHands check on 50 instances; hybrid on Qwen3-Coder 480B Verified-50; GPT-4.1-mini sensitivity on a 150-instance subset.
- Results: masking roughly halves cost and matches summarisation in four of five configs (Qwen3-Coder 53.4 raw, 54.8 mask, 53.8 summary). Summaries lengthen trajectories 13-15% in some models.
- Test behaviour: not measured. No unprompted test-run rate.

**Compact-Bench** (arXiv 2610.31710v2, cs.SE, v1 22 Oct, v2 28 Oct 2026, no venue). Authors: Ruopei Sun, Jianfeng Cai, Kangwen Zhao, Wengang Zhou, Houqiang Li. 35 SWE-bench repairs, 146 sessions, 106 production chains, 14 summarisers; damage 5% to 64% of 22 full-history successes; summaries keep at most 16.0% of recurring details vs 79.1% mechanical extraction. Abstract only.

**Benchmarks Are Surprisingly Compaction-Friendly** (arXiv 2610.31778v1, cs.LG, 22 Oct 2026, no venue). Authors: Jeanne Salle, Hardik Bhatnagar, Matthias Bethge, Sahar Abdelnabi, Maksym Andriushchenko. OpenCode scaffold, five strategies, three frontier models, PaperBench/ProgramBench/PostTrainBench; no method beat default self-summarisation. Abstract only.

None of the five reports how often an agent runs tests unprompted (absence in what we read, not proof).

## Related work and distinction (draft, about 350 words)

Three lines of work bear on ours. Lindenbauer et al. compared raw history, observation masking and LLM summarisation for SWE-agent on 500 SWE-bench Verified tasks across five model configurations, and found masking matched summarisation at about half the cost of the raw agent in most settings. We adopt masking and summarisation as baselines and do not claim to have introduced either. Sun et al. (Compact-Bench) replay full-history and summary continuations from the same repository state on 35 SWE-bench repairs and show that summaries often lose the progress needed to finish, while Salle et al. find that on long-horizon benchmarks other than SWE-bench, default self-summarisation is hard to beat and that constraints stored nowhere else are what compaction loses. Neither study varies metadata on retained test evidence.

The closest work is by Gao et al., who bind verifier evidence to exact source and suite hashes and show, in forced three-revision loops on HumanEval and in a 24-bug repository study over four open models, that stale diagnostics change repair behaviour. Their repository agent has a test action, but they do not report how often it uses it unprompted, and they do not study context compaction. Tiwari et al. (Assay) invalidate claims when the code in their dependency cone changes, but evaluate with scripted experiments and no model in the loop, and defer agent evaluation to future work. The idea of tying test evidence to a workspace state is therefore theirs, and we use a whole-workspace fingerprint as a simpler stand-in rather than presenting it as new.

What we add is a measurement and a controlled comparison in a regime these papers do not cover. Using a Gemma 4 12B agent with an 8K working context on 145 SWE-bench Verified tasks, we record how much test evidence reaches the compaction step under natural, unforced agent behaviour, and compare flat evidence records with the same records plus a freshness tag and a length-matched neutral tag, alongside masking and summarisation. In pilots the agent ran tests in only 11 to 14 of about 600 steps, which bounds what any freshness metadata can do. We report this as a boundary condition for small agents, not as a general result about compaction.

## BibTeX

```bibtex
@misc{gao2026looping,
  title         = {Looping Is Not Reliability: State-Bound Evidence and Typed Revision Contracts for Agentic Code Repair},
  author        = {Gao, Xueping and Yang, Jianwei and Yang, Qiang},
  year          = {2026},
  eprint        = {2607.24604},
  archivePrefix = {arXiv},
  note          = {AgenticDev '26, Munich. DOI 10.1145/3843282.3844438}
}
@misc{tiwari2026assay,
  title         = {Assay: Claims That Decay With the Code. Content-Addressed Evidence Graphs for Accountable AI-Assisted Software Delivery},
  author        = {Tiwari, Om Shankar and Vass, Tangi and Singh, Gagan Deep},
  year          = {2026},
  eprint        = {2609.36170},
  archivePrefix = {arXiv}
}
@misc{lindenbauer2025complexity,
  title         = {The Complexity Trap: Simple Observation Masking Is as Efficient as LLM Summarization for Agent Context Management},
  author        = {Lindenbauer, Tobias and Slinko, Igor and Felder, Ludwig and Bogomolov, Egor and Zharov, Yaroslav},
  year          = {2025},
  eprint        = {2508.21433},
  archivePrefix = {arXiv}
}
@misc{sun2026compactbench,
  title         = {Compact-Bench: Measuring What Context Compaction Costs Long-Horizon Coding Agents},
  author        = {Sun, Ruopei and Cai, Jianfeng and Zhao, Kangwen and Zhou, Wengang and Li, Houqiang},
  year          = {2026},
  eprint        = {2610.31710},
  archivePrefix = {arXiv}
}
@misc{salle2026compaction,
  title         = {Benchmarks Are Surprisingly Compaction-Friendly},
  author        = {Salle, Jeanne and Bhatnagar, Hardik and Bethge, Matthias and Abdelnabi, Sahar and Andriushchenko, Maksym},
  year          = {2026},
  eprint        = {2610.31778},
  archivePrefix = {arXiv}
}
```

## Not verified

- Complexity Trap venue (page header only); year 2025 inferred from the v3 date.
- Compact-Bench and Salle et al.: abstracts only, so nothing about their test behaviour.

## Internal comparison point (not a published result)

The main-track session reports, from its own Modal traces of Gemma 4 31B on the 129 public competition tasks with graph tools and a prompt that asks for verification: any test command (pytest, unittest, tox) in 41 of 129 runs (32%) and 42 of 129 (33%) for two call-cap settings, and 15 of 59 (25%) for a stripped-tools bundle. These are any-test-command counts, not counts of the right test file, under a different harness and task set. Our 12B agent ran any test in 3 of 23 and 4 of 21 dev tasks. Usable in the paper only as "a 31B agent under a verification prompt in a separate harness reached 25 to 33%", with the harness difference stated.
