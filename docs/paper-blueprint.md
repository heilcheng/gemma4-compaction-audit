# Paper blueprint

Planning document, 4 November 2026. All result fields below are deliberately unfilled. This is not a finished or submission-ready paper.

## Working title

**Does Evidence Freshness Help Small Coding Agents? A Controlled Gemma 4 Study**

Subtitle: **A controlled empirical study and reproducible evaluation resource**

If only the diagnostic audit succeeds, use a narrower title such as **Auditing Tool-History Compaction in Gemma Coding Agents**. If results are inconclusive, the title and abstract should say pilot or reproduction rather than imply a successful new method.

## Intended contribution

Isolate whether freshness metadata changes a small Gemma agent's behavior when the retained evidence body is held fixed, without automatic submission gates or rollbacks. Add observation masking and corrected summarization as practical baselines, executable repair outcomes and complete cost accounting. Attribute shared-state replay and state-bound evidence to prior work. The possible original contribution is a demonstrated behavior, boundary condition or measurement bias in natural compaction, together with a reusable audit resource.

## Abstract drafting frame, about 150 words

Small coding agents retain a limited working history while navigating, editing and testing repositories. Existing compaction studies show that retained information, repair success and physical inference cost need not move together. We study [EXACT GEMMA CHECKPOINT] on [N] held-out repository issues using [FROZEN HARNESS], comparing identical evidence memories with and without source-state validity metadata under [BUDGET]. Observation masking and corrected summarization provide practical baselines. We measure executable issue resolution, [COST METRICS] and [MECHANISM METRICS]. Relative to flat evidence memory, freshness metadata changes resolution by [EFFECT WITH CONFIDENCE INTERVAL] and costs [MEASURED DIFFERENCE]. A secondary [N]-task checkpoint study [MEASURED FINDING]. These results support [NARROW CONCLUSION] within [EXPLICIT SCOPE], while [MAIN LIMITATION]. We release [ACTUAL PUBLIC RESOURCE CONTENTS AND LINK].

Only turn this frame into prose after results exist. Do not fill it with expected gains.

## Word allocation

| Component | Target words |
|---|---:|
| Abstract | 150 |
| Introduction and research questions | 300 |
| Closest related work and distinction | 350 |
| Methods and policy definitions | 450 |
| Experimental protocol | 550 |
| Results and failure analysis | 650 |
| Limitations and conclusion | 250 |
| **Total** | **2,700** |

The remaining 300 words cover captions, headings and necessary clarifications. References are excluded under organizer guidance. Keep essential evidence in the main text; appendices are supplementary.

## Questions and hypotheses to freeze

- RQ1: Does freshness metadata change held-out repair success when the retained evidence body is fixed and no mechanical admission/rollback gate is used?
- RQ2: How does corrected summarization compare when its own generation and cache effects are counted?
- RQ3, secondary: How do the evidence policies compare with inexpensive observation masking, and when do their costs outweigh any repair benefit?
- Audit question: Does the reported tool-event omission occur in the exact pinned ADK/competition version? Current upstream source includes the events; do not describe the historical report as a universal current bug.

These are questions, not promised conclusions. Do not select the winning policy after looking at held-out outcomes and retroactively call that comparison primary.

## Main table to populate

| Policy | Tasks | Resolved | Difference vs flat evidence, 95% CI | Generated tokens | GPU service time | All-in run cost |
|---|---:|---:|---|---:|---:|---:|
| Observation masking | TBD | TBD | TBD | TBD | TBD | TBD |
| Corrected summarization | TBD | TBD | TBD | TBD | TBD | TBD |
| Flat evidence memory | TBD | TBD | Reference | TBD | TBD | TBD |
| Evidence memory + freshness | TBD | TBD | TBD | TBD | TBD | TBD |

Add paired wins/losses, infrastructure failures and actual memory occupancy in the text or a compact supplementary table. Explain the allocation of shared server cost. Do not report only cost per successful task while hiding unsuccessful attempts.

## Figures and evidence

1. A quality/cost plot with uncertainty, showing measured resolution against total cost or server time. Plot real observations only.
2. A compact breakdown of decode, prefill, summarization, tools and environment overhead, restricted to counters actually available.
3. One trace example chosen by a disclosed rule: what was observed, what memory retained, and what happened next. Avoid inferring a causal mechanism from a single anecdote.

A diagram can show the shared inputs and the memory-policy intervention. It should make clear that the evaluator's tests and reference patch are outside the agent loop.

## Related-work obligations

- [How Do Small Coding Agents Use Code Graphs and Embeddings?](https://arxiv.org/abs/2610.33958): established Gemma graph-tool ablations; explains why this paper does not claim generic graph novelty.
- [Compact-Bench](https://arxiv.org/abs/2610.31710): attribute the shared-state continuation approach and distinguish its scope from this experiment.
- [The Physical Cost of Context](https://arxiv.org/abs/2610.34763): attribute the cache-aware cost motivation and explain the actual accounting used here.
- [Assay](https://arxiv.org/abs/2609.36170) and [Looping Is Not Reliability](https://arxiv.org/abs/2607.24604): attribute state-bound evidence and freshness concepts. Explain any simplification in our deterministic implementation.
- Cite the agent harness, SWE-bench, exact Gemma checkpoint, and the Kaggle competition. Treat forum reports as motivation, not independently established research results.

Verify complete author lists, versions and publication details before generating the final bibliography.

## Limitations that must remain visible

Limited task/repository coverage; possible benchmark exposure during model training; one main checkpoint and quantization; uncertainty around small differences; imposed working-context budget; imperfect test coverage; differences between the independent harness and Kaggle; and the limited meaning of a short M1 demonstration. State which expected ablations were omitted and why.

## Fast verification package

Include frozen manifests and configuration hashes, event-serialization fixtures, environment checks, policy implementations, per-task outcome/cost records, figure-generation code and a small smoke test. A notebook should regenerate published tables quickly from saved results. A separate documented command should launch full inference and grading. Publish only data and traces whose licenses and competition terms permit redistribution.

## Final submission checks

Confirm the actual word count, public accessibility of links, absence of placeholders, consistency of sample sizes across figures, correspondence between every headline number and saved results, appropriate prior-work attribution, and a genuinely submitted Kaggle Writeup. Aim for a complete submission on November 11 and finalize by November 12 at 20:00 Singapore time.
