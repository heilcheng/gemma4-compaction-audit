# Gemma 4 Paper Track: research decision and nine-day plan

Prepared 4 November 2026, Singapore time. Sources were inspected on 3–4 November using gstack browse. This is a research plan; no experiment results, model throughput measurements, or prize probabilities are claimed. No paid compute has been launched.

## Recommendation

Build one carefully controlled empirical paper and an executable audit resource around **memory policies for small Gemma coding agents**. Start with a capped $60 feasibility study. Keep the full project within $1,000 unless measured results justify a specific extension.

Working title: **Does Evidence Freshness Help Small Coding Agents? A Controlled Gemma 4 Study**.

The primary question is: **When a small Gemma agent's history is compressed, does explicitly marking which retained observations belong to the current code state improve repair enough to justify the cost?** Compare identical evidence records with and without freshness metadata. Observation masking and corrected summarization provide practical baselines. This isolates a narrower question than whether a new memory bundle outperforms a default prompt.

This is an empirical and resource contribution. Graph retrieval, shared-state replay, memory ledgers, and evidence invalidation already have close prior work. We should not present any of those as inventions. A credible contribution would be a reproducible finding about the Gemma deployment regime, supported by corrected baselines, real test outcomes, and an audit bundle others can run.

There is enough time and compute for a useful submission. There is not yet evidence that this topic will produce a prize-level finding. The first day must establish both a functioning experiment and a meaningful failure mechanism before the remaining budget is committed.

## Competition facts that change the strategy

- The deadline is **12 November 2026, 23:59 UTC**, which is **13 November, 07:59 Singapore time**. Plan to submit a complete version on **11 November**, with a final internal cutoff of **12 November, 20:00 Singapore time**. An inspected discussion requests an extension; it is not an announcement of one.
- The paper track accepts original, unpublished research without a main-leaderboard entry. Its five equally weighted criteria are novelty, quality/generalization, relevance, verifiability, and clarity. A small, defensible experiment can therefore be more valuable than a complicated agent with an unexplained score.
- The main text limit is 3,000 words. The organizer clarified that references are excluded and appendices are supplementary rather than guaranteed reading. Keep captions within a conservative main-text allowance.
- Awards are $15,000 for overall best paper, $10,000 for a new resource, and $10,000 for a new application. An organizer says every submission is considered across the awards. An empirical paper plus a usable audit resource fits this structure; it does not guarantee either award.
- A saved draft is insufficient: the Writeup must be submitted. A public notebook and linked PDF are optional. The organizer says a fast verification mode is useful and the whole expensive pipeline need not run by default.
- The main prediction competition runs until December 2 and has its own model/harness restrictions. Those dates should not be used for the paper plan. Expo highlighting is an opportunity associated with this competition, not acceptance to the NeurIPS main proceedings.

Sources: [paper overview](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/overview), [word-count clarification](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/749546), [award and notebook clarification](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/750338), [extension request](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/755176), [main competition](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview).

## What the Kaggle discussions actually tell us

These are leads to reproduce, not established experimental results from our project.

| Inspected discussion | Report | Consequence for our plan |
|---|---|---|
| [Tool events missing from compaction](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/754783) | A participant reports that an ADK summarizer formats text but omits function calls and responses. | Current upstream source already includes both. Check the competition's pinned version; do not present the forum report as a current universal bug. |
| [Four runtime traces](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/755291) | A small FastAPI audit attributes substantial time to decoding and identifies repeated reads and prefill spikes. | Log decode, prefill, tools, setup and retries separately. Its reported token rate is not a forecast for our Modal server. |
| [27 FastAPI collection failures](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/753370) | A participant reports missing dependencies preventing test collection. | Validate each selected environment with empty and reference patches before freezing the evaluation set. Do not silently remove failures after seeing model outcomes. |
| [AST-guided verification](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/754697) | A submission claims gains from targeted code extraction, test feedback and syntax checks. | Generic AST plus verification is already represented. The claimed gains were not independently reproduced here. |
| [Trap-25/context reset](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/751430) | A submission describes reset policies, a negative-constraint ledger and adaptive thinking. | A renamed loop-breaking ledger would have substantial overlap. Its small diagnostic tasks should not be treated as equivalent to full repository repair. |
| [External data and GitHub code](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/751804) | The host allows GitHub sharing and external evaluation when the entrant has the necessary rights. | A public benchmark and public repository are viable. Preserve original licenses and avoid redistributing competition data merely because the code is public. |

The public competition dataset contains **129 development tasks from four repositories**, not 500 tasks. It includes reference patches and evaluator tests; neither may enter the held-out agent's context. The described download is about 22.42 GB. Actual files require joining/accepting the competition rules. I read the public description, not the gated harness or task archive. The Writeups listing was also unavailable to a signed-out visitor, so this is not an exhaustive review of all competing papers. [Dataset description](https://www.kaggle.com/competitions/gemma-4-developer-agent/data)

## Literature findings and novelty boundaries

| Closest work | What is already covered | What we must avoid claiming |
|---|---|---|
| [How Do Small Coding Agents Use Code Graphs and Embeddings?](https://arxiv.org/abs/2610.33958), October 2026 | Tool-set ablations across ten models, including three Gemma 4 sizes; localization and downstream repair; limited multihop tool use. | That graph-versus-grep or small-model graph benefit is a fresh question by itself. |
| [Compact-Bench](https://arxiv.org/abs/2610.31710), October 2026 | Full-history and summarized continuations from shared repository states; information retention and compaction damage. | That branching from an identical checkpoint is our new evaluation method. |
| [The Physical Cost of Context](https://arxiv.org/abs/2610.34763), October 2026 | Token reduction can destroy prefix reuse and increase executed work; includes repository-agent experiments. | That fewer prompt tokens necessarily means cheaper inference, or that noticing cache effects is new. |
| [Assay: Claims That Decay With the Code](https://arxiv.org/abs/2609.36170), September 2026 | Content-addressed evidence and invalidation when dependencies change. | That attaching tests to code versions is a new concept. |
| [Looping Is Not Reliability](https://arxiv.org/abs/2607.24604), revised October 2026 | State-bound verifier evidence, stale/current trace interventions, common-state branches and a 14B replication. | That stale evidence or its causal replay test has not been studied. |

These sources rule out several initially attractive ideas. The remaining proposed contribution is narrower: isolate the behavioral effect of freshness metadata during Gemma compaction, without an automatic gate that blocks submission or rolls code back. Assay evaluates scripted repository scenarios without a model in the loop. Looping Is Not Reliability already provides substantial agent evidence, including state-binding and gate ablations, so the proposed natural-compaction setting and controlled evidence body must be distinguished carefully. **Changing the model name alone is insufficient novelty.** Before implementation, map the exact experimental cells in the closest papers against ours; if the comparison is already answered, position the work as reproduction or change the question before spending heavily.

A source-level check of [current ADK's summarizer](https://github.com/google/adk-python/blob/main/src/google/adk/apps/llm_event_summarizer.py) found explicit handling of both function calls and function responses. This establishes current upstream behavior in the inspected source, not the version installed by Kaggle or a runtime reproduction. It removes the alleged omission as a sound basis for claiming a new fix.

## Alternatives and decision

| Direction | Nine-day assessment | Decision |
|---|---|---|
| Memory correctness and measured efficiency, with an audit resource | Reuses existing agents and evaluators; supports both empirical and resource contributions. Novelty depends on a material, reproducible finding. | Recommended first pilot. |
| Ranked multihop graph paths under a fixed evidence budget | Could follow a limitation in the graph-tools paper. Must distinguish path organization from extra evidence and compare against existing graph-navigation methods. | Backup only if a sharply distinct experiment can be specified within Day 1. |
| Freshness-aware memory as a new method | Direct overlap with Assay and Looping Is Not Reliability. | Use as an attributed baseline/ablation, not the central invention. |
| New RL or broad fine-tuning pipeline | Infrastructure, training stability and data attribution would consume the schedule. | Keep off the critical path. |

Do not spend several days repeatedly pivoting to new topics. At the end of Day 1 choose one empirical question, or explicitly choose a modest reproduction/resource report.

## Experimental protocol

### Model, harness and data

Use **Gemma 4 12B instruction-tuned QAT W4A16** as the initial cloud checkpoint. Freeze its exact revision, tokenizer, chat template, thinking mode, quantization, inference version and decoding settings after the pilot. Add E4B only for a bounded replication once the main comparison is complete. The official QAT checkpoint exists, and the main competition lists this model family. [Google checkpoint](https://huggingface.co/google/gemma-4-12B-it-qat-w4a16-ct), [deployment guide](https://gemma.ai/deployment/vllm/).

Use an existing mini-SWE-agent/SWE-bench evaluation path for the principal experiment. Implement only the memory-policy hook and instrumentation. Separately test ADK event serialization with minimal fixtures and, where access permits, the pinned competition harness. Do not call a mini-SWE-agent run an official Kaggle leaderboard result. [mini-SWE-agent](https://mini-swe-agent.com/latest/usage/swebench/), [official evaluation guide](https://www.swebench.com/SWE-bench/guides/evaluation/).

Preferred external-data design: 20 development tasks and **150 disjoint held-out tasks** sampled reproducibly from SWE-bench Verified, stratified by repository. Freeze the manifest after environment preflight and before treatment outcomes. This is a target subject to measured cost. If using only Kaggle's 129 public tasks, reserve development tasks and report the smaller remaining sample; do not pretend it supports 150 independent held-out cases.

A 30–40-task competition-data replication is optional and should replace another optional run, not silently expand the budget. Access and environment repair must not become the main experiment's dependency.

### Four main arms

1. **Observation masking:** retain the configured recent tool observations and action history, with an explicit and fixed truncation policy.
2. **Corrected summarization:** serialize text, tool calls and tool responses correctly, then summarize with the same Gemma checkpoint. Include summarizer inference in the cost.
3. **Flat evidence memory:** deterministically retain observed file excerpts, edit outcomes and test evidence, preserving their chronology and provenance.
4. **Evidence memory with freshness metadata:** retain the same records as arm 3 and expose whether their source state matches the current workspace. Associate reads with file hashes and test runs with the source/configuration state at execution. Use a conservative global version for tests; avoid dependency-graph invalidation engineering. An older result means “not validated on the current state,” not “the test now fails.”

All arms receive the same issue, tools, initial repository, agent prompt, context cap, output-token cap and action limit. Memory construction must use only information available to the running agent. Reference fixes, evaluator tests, post-hoc failure labels and Claude-generated hints stay outside runtime inputs.

Predeclare **freshness metadata versus flat evidence memory** as the primary comparison. Masking and corrected summarization are practical baselines. Do not force retesting, block patch submission or automatically roll back changes in the metadata arm: those would change the intervention. A broken serializer, if reproduced, belongs in a labeled diagnostic experiment, never as the sole headline comparison.

Use a common memory-token ceiling and report actual occupancy. For the primary freshness comparison, keep the evidence body fixed and use a tokenizer-checked neutral metadata control so the treatment does not simply receive more source evidence. Neutral record IDs must preserve the baseline's chronology; do not delete information it would ordinarily possess. Do not describe different occupancy under the same ceiling as exact token matching. Include newly created source/configuration files and edits made through shell commands in workspace fingerprints, and measure hashing overhead.

Select a realistic working-context threshold on development runs, initially exploring 8K and 16K as constrained deployment settings. Freeze one primary setting. These are experimental working budgets, not claims about the model's maximum advertised context. If natural compaction is rare, report that and narrow the claim; do not secretly force failures with an implausibly tiny window.

### Measurements and inference

The primary outcome is **executable issue resolution** under the frozen agent budget. Use identical paired tasks and seeds. Report paired win/loss counts and confidence intervals, not only aggregate percentages.

Record generated tokens including thinking and summary tokens, logical prompt tokens, cached and uncached prefill where exposed, model time, tool/test time, cold-start time, total server uptime, peak memory and actual charges. If the serving stack cannot expose cache counters, say so and use directly measured total time/cost; do not invent an energy estimate.

Report success and cost jointly. Lower cost with a lower solve rate is a tradeoff. Do not claim equivalent quality from a nonsignificant difference. With 150 tasks and around 20% paired disagreement, a near-zero difference has an illustrative 95% uncertainty of roughly ±7 percentage points. This study cannot confidently establish tiny improvements.

Repeated seeds and multiple checkpoints from one task are not independent tasks. Bootstrap by original task, show repository-level results, and limit generalization if only a few repositories contribute. One seed across all 150 tasks is the minimum; repeat the primary pair on 50 predetermined tasks only if resources permit.

Replay is a secondary mechanism study using an established protocol: choose the first eligible compaction checkpoint by a trace-only rule, snapshot filesystem and tool state, and resume the policies from that same state. Target 40 unique-task checkpoints × four policies = 160 continuations. Preserve process state or ensure no background process is active. If fewer checkpoints qualify, report that denominator instead of selecting favorable cases. Replay outcomes are conditional continuation results, not full-agent solve rates. Deliberately injected stale evidence, if studied, is a separate stress test and cannot establish natural prevalence.

### Validity and automation

- Run empty-patch and reference-patch grading controls in isolated evaluator environments before freezing the sample. Log exclusions and reasons.
- Use unique evaluator run IDs for every arm/seed/revision; cached results can otherwise survive a changed patch.
- Keep a complete audit trail: manifests, software/model revisions, prompts, raw tool events, policy outputs, patches, grader logs and per-run cost records.
- Use a persistent job queue with bounded retries and checkpoints. Retry infrastructure faults under a common rule; count agent timeouts and wrong patches as outcomes.
- Close task environments when complete. Stop or scale down inference when the queue is empty. Continuous automation does not mean keeping every resource alive for nine days.
- Use Claude Code for implementation, review and writing. The evaluated solver remains Gemma. Claude Max has usage limits; the experiment queue must continue without requiring a live coding assistant. [Claude plan guidance](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)

## Hardware and money

The M1 Max is useful for development, analysis and a small local inference demonstration. Use x86 cloud environments for primary repository tests to avoid ARM container compatibility becoming a research project. A 4-bit 12B model is a sensible local pilot, but actual memory, latency and context capacity must be measured. Community MLX conversions and cloud compressed-tensors checkpoints should not be pooled as identical experimental conditions. [Gemma memory and model guidance](https://gemma.ai/models/gemma-4/), [MLX deployment](https://gemma.ai/deployment/mlx/).

Rates inspected on November 3: Modal A100 80GB is $2.4984/GPU-hour; L40S is $1.9512; H100 is $3.9492. Host CPU/RAM are additional. An example A100 service using four physical CPU cores and 32 GiB host RAM totals about **$2.943/hour** at standard rates. Sandboxes use higher CPU/RAM rates than ordinary functions. Choose hardware using measured dollars per finished trajectory. [Modal pricing](https://modal.com/pricing)

| Allocation | Maximum planned amount |
|---|---:|
| Day-one model/environment pilot | $60 |
| Primary inference, up to roughly 120 example A100 server-hours | $354 |
| Agent task environments | $143 |
| Independent final grading | $71 |
| Builds, storage and network allowance | $55 |
| Optional second-model/seed replication | $117 |
| Contingency retained until core analysis is complete | $200 |
| **Total envelope** | **$1,000** |

This is a spending allocation, not a measured quote. Credits, tax, account usage and region modifiers are not assumed. Core target: 600 full trajectories plus 160 continuations. At an illustrative 10,000 generated tokens per run and measured aggregate effective throughput of 20 tokens/second, that is about 106 server-hours; at 20,000 tokens it is about 211 hours. The latter does not fit the primary allocation or schedule without changes. Count prefill, idle time and summary calls when measuring effective throughput. If the pilot forecast is too high, retain all 150 tasks for the primary pair and preselect a smaller common task subset for both practical baselines; disclose the different denominators and compare baselines only on their shared subset.

Forecast both money and completion time after the pilot. More CPU workers do not multiply the throughput of a saturated GPU. Add a second endpoint only if it shortens the critical path within the same aggregate budget. Expansion above $1,000 should buy a predeclared replication or tighter estimate, not unbounded hyperparameter exploration.

## Nine-day schedule, Singapore time

| Date | Work and acceptance condition |
|---|---|
| **Nov 4, Day 1** | Read closest methods in full; pin model/harness; reproduce or reject serializer report; run 10–20 development tasks. Demonstrate grading controls, valid tool calls, complete cost logs and natural compaction incidence. Stop the pilot near $60. |
| **Nov 5, Day 2** | Implement and inspect all four policies. Freeze manifests, one primary comparison, budget, retry rules and analysis script. Record a timestamped protocol. One complete run per arm must pass the plumbing checks. |
| **Nov 6, Day 3** | Start the main paired matrix; grade incrementally. Forecast finish time from actual throughput. Reduce optional work before reducing the primary comparison. |
| **Nov 7, Day 4** | Continue evaluation. Freeze all method changes; investigate only infrastructure faults. Draft introduction, related work and methods from the frozen protocol. |
| **Nov 8, Day 5** | Complete most main runs. Begin predetermined checkpoint continuations. Inspect missing logs and evaluator anomalies without tuning on outcomes. |
| **Nov 9, Day 6** | Finish core runs and replay. Compute paired estimates, cost breakdowns and failure taxonomy. Decide whether results support a method-comparison paper, a narrower resource/audit paper, or only a pilot. |
| **Nov 10, Day 7** | Optional E4B or second-seed replication only if the forecast remains within budget and the core result is complete. Measure a small local M1 inference run separately. |
| **Nov 11, Day 8** | Finalize figures and a main text under 3,000 words. Package the audit resource and fast verification notebook. Submit a complete version if ready. |
| **Nov 12, Day 9** | Reproduce a small slice from clean configuration; verify public links, licenses, word count and submission state. Final internal cutoff: **20:00 SGT**. |

## Go/no-go decisions

At the end of Day 1, continue only if the evaluated pipeline works, the cost forecast is credible, and the proposed comparison is not a duplicate. A practical relevance flag is whether several of the 20 development trajectories reach compaction and retain evidence from before an edit. This is a diagnostic gate, not a significance test or proof of a widespread defect.

If serialization is already fixed, say so and use the corrected behavior in all main arms. If no meaningful compaction occurs, stop claiming that it is the dominant bottleneck. If the closest work already answers the exact question, make the paper an explicit reproduction with a useful resource, or choose the graph-path backup immediately.

By Day 6, an underpowered null result is not evidence of equivalence. A narrow negative finding can be useful if it identifies a reproducible boundary or measurement bias; an inconclusive pilot should be described as one. Do not manufacture a positive story by dropping tasks, switching the primary metric, or comparing only against a defective baseline.

## Submission package

Deliver one clear finding, one primary results table, one quality/cost figure, and one small mechanism example. The public resource should contain a configuration-driven runner, environment preflight checks, event-serialization fixtures, memory-policy adapters, trace/cost schemas, frozen manifests, and a notebook that regenerates reported tables from saved aggregate results. Expensive reruns should be explicit commands, not required for a quick verification.

Release original code and permitted derived artifacts with clear licenses. Keep competition raw data behind its required access path unless redistribution is expressly allowed. The paper itself should state exact model revisions, sample sizes, exclusions, budget accounting, limitations and what did not work. No numerical result belongs in the abstract until it has been measured.
