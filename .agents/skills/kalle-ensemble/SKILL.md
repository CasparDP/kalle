---
name: kalle-ensemble
description: Orchestrate an explicit three-branch academic-paper review using two user-selected blind strong models plus kalle as an independent branch on its default models, then synthesize a ranked sign-off ledger. Use only when the user asks for an ensemble, multi-model review, or submission hardening.
---

# kalle ensemble

Build independent evidence, not three paraphrases of one review. A normal paper
review remains single-model; activate this workflow only on explicit request.

```text
Review A (user-selected strong model) ─┐
Review B (user-selected strong model) ─┼─ barrier ─ synthesis ─ sign-off
Review C (kalle default tiers) ────┘

Optional code ─ kalle audit + independent direct-source review ─ code ledger
```

## Configure the graph

1. Ask the user to choose the exact models/providers for A and B from routes
   actually callable in the current environment. Recommend different model
   families and preferably different providers. kalle's strong tier is
   Kimi, so avoid Kimi for A and B; Sol + Claude is a useful default.
2. Record provider, exact model, reasoning setting, adapter, Review ID, and
   artifact path. Never silently substitute a failed or unavailable model.
3. Give A and B the identical paper, supplements, instructions, and output
   schema. Keep them blind to each other and to kalle. Run in parallel when
   supported, with exclusive artifacts:
   `reviews/review_<slug>_A.qmd`, `reviews/review_<slug>_B.qmd`, and raw outputs
   under `reviews/raw/`.
4. Load `kalle` and launch it as Review C. It stays on its
   effective default fast/strong tiers unless the user explicitly overrides
   them.

## Individual-review contract

Each review contains:

- a 2–3 paragraph summary of question, contribution, method, findings, and
  literature position;
- at most three truly essential points, each with a concrete proposed solution;
- all remaining findings as nonbinding suggestions; and
- a recommendation: reject, major revision, or minor revision.

Precede every comment with a hidden tag:

```text
<!-- tag: id=P1A-E1; category=research-design; severity=essential; theme=parallel_trends -->
```

Allowed categories are `contribution`, `research-design`,
`results-interpretation`, `presentation`, and `future`. At the top, preserve
metadata for paper ID/slug, review ID, reviewer, provider, exact model,
reasoning, raw source, and recommendation. Mark paper-specific claims VERIFIED,
INFERRED, or UNCERTAIN; never invent citations, coefficients, or results.

Normalize every kalle comment into Review C. Select at most three as
essential, retain all others as suggestions, and preserve a raw-to-normalized
ID map.

## Barrier and synthesis

Wait until every requested branch has produced an artifact or failed. A live
agent can wait automatically; a closed agent session requires a later status
invocation or scheduler. Preserve failed branches as coverage gaps.

Cluster findings by substance, then report:

- **Agreement:** two or more independent branches raised the concern.
- **Conflict:** diagnoses or proposed fixes materially disagree.
- **Unique:** one branch raised it.
- **Coverage gaps:** a branch or artifact could not be examined.

Rank by paper evidence, consequence if correct, actionability, and independent
agreement. Agreement supports judgment but is not a vote.

Create `reviews/comparison_<slug>.md` with this sign-off ledger:

| Rank | Severity | Theme | Comment IDs | Sources | Evidence | Proposed response | Expected artifact | Decision |
|---:|---|---|---|---|---|---|---|---|

If replication code was supplied, pass `--code-dir` to kalle and use
`kalle-pi-code-review` when available. Keep a separate code ledger with
file/line, failure mode, reproduction evidence, proposed fix, verifier, and
decision. Only verified code findings enter the unified priority overview.

Stop before editing the manuscript or code. After user sign-off, load
`kalle-review-response` to execute approved items.
