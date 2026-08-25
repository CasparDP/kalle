---
name: reviewer2-review-response
description: Turn reviewer2 ensemble sign-off ledgers into traceable, verified manuscript and code revisions. Use after the user approves specific academic or code-review findings; never use to implement pending comments before sign-off.
---

# reviewer2 review response

## Triage

1. Preserve every approved comment ID. Do not merge comments merely because
   their fixes overlap.
2. Classify work as coding or writing, immediate or dependent on new results,
   and must-do, should-do, or evidence-backed pushback.
3. Maintain a source-of-truth ledger: comment ID, approved action, owner/model,
   expected artifact, status, evidence, and verifier verdict.
4. Ask about ambiguity that would materially change the response.

## Execute after sign-off

Keep coding and writing work packages separate. A producer must not verify its
own output when another model family is available.

- **Results gate:** do manuscript/response numbers trace to the produced code
  output and requested specification?
- **Adequacy gate:** does the artifact actually answer the approved comment?
  Record `<ID>: ADEQUATE | PARTIAL | INADEQUATE | reason`.

PARTIAL or INADEQUATE reopens the work package. Only passing items may enter a
response letter. Be transparent about errors, push back only with evidence,
and never promise work that was not run.
