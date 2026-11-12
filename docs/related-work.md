# Annotated related work: Gemma coding-agent paper

Research performed through gstack browse on 3–4 November 2026. All factual summaries below come from inspected primary arXiv pages, and the most consequential comparisons also use full HTML papers. Claims are the authors' reported findings, not independently reproduced results. This is a targeted review, not proof that a topic is novel.

## Recommendation

A generic graph-assisted Gemma agent, context ledger, identical-state compaction replay, or source-version-bound test ledger cannot credibly be presented as a new idea. Direct 2026 predecessors exist for all four. A feasible nine-day contribution is a narrowly specified empirical study of how *small Gemma agents* respond to evidence loss and freshness information under limited contexts, using established mechanisms and measuring effectiveness and actual compute cost. This is an empirical extension with uncertain award competitiveness, not an invention claim.

Strong candidate question: **When context must be compacted, does source-state validity metadata help small Gemma agents use past test evidence, after controlling for evidence content, serialization, token budget, and intervention from mechanical gates?** Compare a flat evidence ledger with the exact same ledger plus validity metadata, and include repaired serialization + summarization and observation masking. Keep admission/rollback gates out of the main contrast, or factor them explicitly, because blocking submissions can manufacture lower error rates by eliminating completions.

The Kaggle serialization report is version-specific evidence to investigate. A source-level inspection on November 4 found current upstream ADK already includes function calls and responses. The competition package version has not been inspected. [Current source](https://github.com/google/adk-python/blob/main/src/google/adk/apps/llm_event_summarizer.py)

## Closest collisions: evidence validity and compaction

1. **Looping Is Not Reliability: State-Bound Evidence and Typed Revision Contracts for Agentic Code Repair** — Xueping Gao, Jianwei Yang, Qiang Yang. July 2026, v3 October 4. [Abstract](https://arxiv.org/abs/2607.24604), [full text inspected](https://arxiv.org/html/2607.24604v3).
   - Already binds verifier evidence to exact source and suite hashes; preserves last-known-good checkpoints; studies stale versus current diagnostic traces from identical frozen programs.
   - Controlled study: Qwen2.5-7B-Instruct, 30 HumanEval repairs, six evidence conditions, five seeds, 900 forced three-revision trajectories. Common-state study: 27 tasks, 1,215 branches at 7B plus 1,215 at 14B, including length-matched nonactionable evidence.
   - Repository study: 24 historical bugs across nine Python projects, current/stale diagnostics × contract OFF/ON × three seeds. Four stacks: Qwen2.5-14B, Qwen2.5-Coder-32B-AWQ, Qwen3-Coder-Next-FP8, Devstral Small 2 24B. Devstral factorials separate state binding, admission/rollback, certification, and revision budgets. Severe completion floors; repository factorials are not Holm-significant.
   - Gap still plausible: ordinary compaction, Gemma-family response to *metadata*, and budget-quality effects without a bundled mechanical gate. Do not claim first causal stale-evidence study, first state binding, or first same-state evaluation. Another 20–30-bug study with the same manipulation would be weak differentiation.

2. **Assay: Claims That Decay With the Code. Content-Addressed Evidence Graphs for Accountable AI-Assisted Software Delivery** — Om Shankar Tiwari, Tangi Vass, Gagan Deep Singh. September 28, 2026. [Abstract](https://arxiv.org/abs/2609.36170), [full text inspected](https://arxiv.org/html/2609.36170v1).
   - Test/behavior claims are bound to the Merkle hash of their dependency cone. Code/dependency changes invalidate claims. Includes an append-only ledger, compact situation brief, mechanical gate, and incremental indexer.
   - Evaluation uses scripted experiments on five public repositories, with **no model in the loop**. The paper explicitly leaves agent-performance evaluation to future work.
   - Opportunity: evaluate behavioral effects and costs with real small Gemma agents. Reusing the binding concept is appropriate; claiming to invent it is not. Avoid dependency-cone construction as a nine-day prerequisite; whole-source-tree hashes are conservative and much simpler.

3. **Compact-Bench: Measuring What Context Compaction Costs Long-Horizon Coding Agents** — Ruopei Sun et al. October 22, updated October 28, 2026. [Abstract](https://arxiv.org/abs/2610.31710), [full text inspected](https://arxiv.org/html/2610.31710v2).
   - Already compares full-history and summary continuations from the **same working-tree snapshot**. 35 SWE-bench repairs, 146 sessions, 106 production chains; 14 summarizers; fixed Kimi-K3 continuation agent.
   - Initial phase up to ten steps, paired continuation up to eight; future recurring details and progress-state disorder also measured. Mechanical extraction is a retention reference, not proof of better task completion.
   - Reproduction limitation: package excludes cached task histories/snapshots and private session payloads, so fresh trajectories are needed. Per-tool truncation (200 chars for task-preservation summarizer input) is part of its fixed pipeline and may materially affect generalization.
   - Gap: live Gemma compaction with evidence validity contrasts and real cost, not novel branch replay or generic detail preservation. Cite its paired protocol and report both damage and rescue, not only aggregate accuracy.

4. **The Physical Cost of Context: Quality-Constrained Resource Accounting for Coding Agents** — Zhongming Yu et al. October 26, 2026. [Abstract inspected](https://arxiv.org/abs/2610.34763).
   - Shows that lower prompt-token counts can increase executed prefill by invalidating prefix caches; includes 450 localization cases, 900-cell resource study, mini-SWE-agent on 100 Verified issues.
   - Must measure billed GPU time/wall time, uncached prefill if available, peak memory, and useful completions. Do not equate token reduction with dollar reduction.

5. **Reducing Cost of LLM Agents with Trajectory Reduction (AgentDiet)** — [arXiv](https://arxiv.org/abs/2509.23586), [full text inspected](https://arxiv.org/html/2509.23586v1).
   - Uses a cheaper LLM to reduce useless, redundant, and **expired** information in a sliding window, preserving recent events and older cached prefixes. Expired information is already an explicit category.
   - Need distinguish deterministic source-state validity from heuristic removal of expired information. A ledger that merely removes old logs is not new.

6. **The Complexity Trap: Simple Observation Masking Is as Efficient as LLM Summarization for Agent Context Management** — [arXiv abstract inspected via title search](https://arxiv.org/abs/2508.21433).
   - SWE-agent/SWE-bench Verified comparison across five model configurations. Simple old-observation masking competitive with LLM summaries; hybrid variant studied. Masking is a required inexpensive baseline.

7. **SWE-Pruner: Self-Adaptive Context Pruning for Coding Agents** — [arXiv abstract inspected via title search](https://arxiv.org/abs/2601.16746). Task-aware 0.6B skimmer selects relevant code lines guided by an agent-provided goal.
   **SWE-Pruner Pro: The Coder LLM Already Knows What to Prune** — [arXiv abstract inspected via title search](https://arxiv.org/abs/2607.18213). Uses a small head on the coder's internal states. These are selection/pruning competitors, but implementing/training them from scratch is unnecessary for a short mechanism study. Describe the scope difference.

8. **Scaling Long-Horizon LLM Agent via Context-Folding** — [arXiv abstract inspected via title search](https://arxiv.org/abs/2510.11967). Learned branching/folding and FoldGRPO, including SWE. Not a feasible nine-day RL baseline to reproduce from scratch.
   **ReFold: Training-Free Reversible Inter-Turn Context Folding for Long-Horizon Agents** — [arXiv abstract inspected via title search](https://arxiv.org/abs/2610.07863). Deduplicates/folds rendered context, keeps underlying history recoverable, batches prefix rewrites. Reversibility and cache-aware rendering are also prior art.

9. **Benchmarks Are Surprisingly Compaction-Friendly** — [arXiv abstract inspected via search](https://arxiv.org/abs/2610.31778). Fixed OpenCode scaffold, five strategies, three frontier models, three long-horizon benchmarks. Argues recoverable on-disk progress makes many benchmarks tolerant of compaction while unrecorded constraints are lost. Important limitation: SWE test outcomes alone may miss loss of operating constraints.

10. **Compaction Laundering: Provenance Destruction in Context-Compacting Coding Agents** — [arXiv abstract inspected via search](https://arxiv.org/abs/2610.29869). Studies loss of message-role provenance during flattening. Supports preserving event types/roles; distinct from source-state freshness. Avoid a general claim that preserving provenance in compaction is new.

## Graph/repository alternatives are also crowded

11. **How Do Small Coding Agents Use Code Graphs and Embeddings?** — Saurav Bellam. October 25, 2026. [Abstract](https://arxiv.org/abs/2610.33958), [full text inspected](https://arxiv.org/html/2610.33958v1).
    - Direct Gemma collision: 79k localization episodes, grep/embeddings/graph/all tool ablations, 160 depth-balanced tasks and all 500 SWE-bench Verified tasks; Qwen scale curve plus Gemma 4 E2B/E4B and a problematic partial 12B run.
    - Studies tool uptake, depth, seed variability, output canonicalization, forced tools, larger budgets, weak embeddings, fixed-model downstream repair, and linear probes.
    - Explicit open question: expose ranked multihop paths/closures instead of raw neighborhoods, or train chaining. Raw graph outputs often truncate and agents seldom chain.
    - A path-preserving compiler with same-node flat rendering and path-shuffle controls is more distinct than graph-vs-grep, but novelty still needs checking against next items.

12. **RepoNav: From Snippet Retrieval to File-Centered Repository Navigation for Code Agents** — [abstract inspected](https://arxiv.org/abs/2609.08355). Already isolates organized evidence from simply more evidence. Accepted EMNLP 2026 according to paper.
13. **LARGER: Lexically Anchored Repository Graph Exploration and Retrieval** — [abstract inspected](https://arxiv.org/abs/2605.16352). Already combines lexical anchoring and confidence-filtered local graph expansion within existing search loops.
14. **How Much Static Structure Do Code Agents Need? A Study of Deterministic Anchoring (CodeAnchor)** — [abstract inspected](https://arxiv.org/abs/2606.26979). Studies static topology injected as comments, granularity, directionality, variance, and repository scale. Accepted ISSTA 2026 according to paper.
15. **LocAgent: Graph-Guided LLM Agents for Code Localization** — [abstract inspected](https://arxiv.org/abs/2503.09089). Heterogeneous code graph; graph-guided localization; 32B fine-tuning; downstream resolution. Baseline conceptual predecessor.
16. **RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph** — [abstract inspected](https://arxiv.org/abs/2410.14684). Repository graph plug-in evaluated across agents and benchmarks; ICLR 2025.

## Additional leads, title verified only

Do not summarize their methods without inspecting them:
- [PACMI: Provenance-Aware Cascading Memory Invalidation for Long-Term LLM Agents](https://arxiv.org/abs/2610.05732)
- [SWE-Shift: Evaluating Coding Agents in Evolving Workspaces](https://arxiv.org/abs/2610.32196)
- [Fresh Memory, Stale Plans: Derivation Currency for Distributed LLM-Agent Memory](https://arxiv.org/abs/2609.03340)
- [Stratum: Repository Memory for Coding Agents Beyond the Context Window](https://arxiv.org/abs/2610.36153)


## Review limits

This targeted review supports rejecting broad invention claims and designing a narrow empirical extension. It does not prove that the remaining question is unprecedented. Authors' numerical claims were not reproduced. Inspect and pin exact paper/code versions before implementing baselines. The final experiment and budget are specified in the accompanying research plan.
