---
name: reviewer2-second-opinion
description: Run the reviewer2 academic-paper review pipeline as an independent second opinion, including background launch, status, resume, optional replication-code audit, and handoff into multi-review synthesis. Use for reviewer2 CLI runs, reviewer2 status, or adding reviewer2 to an academic review ensemble; do not use for ordinary code review.
---

# reviewer2 second opinion

Use reviewer2 as an independent adversarial review branch. Preserve its raw report; do not rewrite it into the primary review or expose other reviewers' conclusions before it finishes.

## Run modes

- **Manual:** launch, inspect status, and collect the report independently.
- **Ensemble:** launch reviewer2 alongside the two blind `academic-paper-review` branches, then wait at the synthesis barrier until all three reports exist.
- **Code-aware:** when replication code is supplied, pass `--code-dir`. reviewer2 runs its Divergence Hunter, Bug Hunter, and Data Archaeologist followed by consolidation and verification. Treat this as one code-audit pipeline, not three independent reviewers.

In the preferred ensemble lineup, reviewer2 is Review C. Reviews A and B are chosen explicitly by the user for each run; the default recommendation is Sol + Kimi when available, with Claude offered as the main alternative.

## Before launch

1. Resolve the paper PDF, optional supplementary PDFs, optional replication-code directory, and whether math auditing is wanted.
2. Explain that a full run can take hours and requires external model calls. An explicit request for the reviewer2 or full ensemble run authorizes launch; otherwise confirm before starting.
3. Run the helper's `check` command. It verifies the installed runner, effective provider/model configuration, and authentication presence without printing secret values. Validate the PDF and optional code/supplement paths with `start --dry-run`.
4. Keep reviewer2 on its configured DeepSeek tiers unless the user explicitly supplies a different config. The repository defaults are DeepSeek V4.1 Flash for light stages and DeepSeek V4 Pro for substantive stages. The helper records the effective models and refuses a non-DeepSeek configuration unless `--allow-non-deepseek` makes the override explicit.

The helper is [scripts/reviewer2_job.py](scripts/reviewer2_job.py). Run it directly or with Python:

From the reviewer2 checkout:

```bash
.agents/skills/reviewer2-second-opinion/scripts/reviewer2_job.py check
.agents/skills/reviewer2-second-opinion/scripts/reviewer2_job.py start PAPER.pdf
.agents/skills/reviewer2-second-opinion/scripts/reviewer2_job.py status RUN_DIR
```

Use `start --help` for supplements, math, code, configuration, and run-directory flags. The helper uses a durable run directory, explicit reviewer2 work directory, timestamped state, a combined log, and `caffeinate` when available. A failed or interrupted run must be resumed from an explicit pipeline checkpoint: inspect `status` and `work/pipeline_execution.log`, identify the first failed/incomplete stage, and supply that stage number. The helper deliberately refuses a blind stage-0 “resume,” which would overwrite earlier work.

```bash
.agents/skills/reviewer2-second-opinion/scripts/reviewer2_job.py resume RUN_DIR --start-stage STAGE
```

Never launch two processes against the same run directory. Use `stop RUN_DIR` only for a job created by this helper.

## Collect and hand off

When status is `complete`:

1. Preserve `review.txt`, `reviewer2.log`, `job.json`, `state.json`, and the `work/` directory.
2. Read the raw report and, when present, `work/01n_code_list.txt`.
3. Normalize every academic comment into a tagged Review C compatible with `academic-paper-review`. Record `reviewer: reviewer2`, the effective fast and strong models from `job.json`, and a link/path to the raw report. At most three highest-consequence findings become Essential Points; retain every remaining finding as a Suggestion and preserve a raw-to-normalized ID map. Never silently drop a comment.
4. Keep code findings in a separate code ledger. Compare them with a direct-source `pi-review` only when replication code was supplied.
5. Return the normalized Review C to the ensemble synthesis. Ranking and revision decisions belong to `reviewer2-ensemble` (or an installed `academic-paper-review`); post-sign-off implementation belongs to `reviewer2-review-response` (or `review-response-plan`), not this skill.

On failure, report the exit code, log tail, last completed stage, and exact checkpoint-based resume command. Authentication failures stop immediately; rate-limit retries are finite by default.

Background execution is durable, but synthesis is autonomous only while an orchestrating agent session or external scheduler is alive. In manual use, return later, invoke `status`, and then collect the completed artifact; do not claim the background job can wake a closed agent session by itself.
