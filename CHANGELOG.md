# Changelog

## 2.0.0 - 2026-10-23

Breaking: the fork is renamed from `reviewer2` to `kalle`, as the upstream
NOTICE asks forks to use a different name.

- CLI command, Python package, and import path are now `kalle`
  (`poetry run kalle paper.pdf -o report.txt`).
- Environment variables are now `KALLE_*` (`KALLE_API_KEY`, `KALLE_BASE_URL`,
  `KALLE_FAST_MODEL`, `KALLE_STRONG_MODEL`, `KALLE_PROMPTS_DIR`,
  `KALLE_PRICING_CSV`, `KALLE_REPO`); config files are `./kalle.yaml` and
  `~/.config/kalle/config.yaml`. Rename the keys in an existing `.env`.
- Reports carry the header "BANG BOOM REVIEW" and a `kalle` footer. The
  summary section is now "Does It Hold Up?" (old work directories still
  render). Prompts call the reviewer persona Kalle instead of Reviewer 2.
- Agent skills are renamed: `kalle` (direct runs from an agent terminal, was
  `reviewer2-second-opinion`), `kalle-ensemble`, `kalle-pi-code-review`,
  `kalle-review-response`. The helper's run directory is now `.kalle-runs/`.

## 1.1.0 — 2026-10-21

- Added a provider-agnostic OpenAI-compatible backend with configurable fast
  and strong model tiers; the fork defaults to DeepSeek V4.1 Flash (fast) and Kimi K2.6 (strong) through
  Ollama Cloud.
- Added durable background execution, explicit checkpoint resume, effective
  model provenance, and portable agent skills for multi-model review workflows.
- Added optional replication-code and literature-enrichment integrations.
- LLM calls now cap output at 64k tokens unless a stage sets its own limit, so
  a model stuck in a repetition loop fails in minutes instead of an hour.
- Mathpix requests now set `metadata.improve_mathpix: false`, opting out of
  Mathpix data retention for service improvement.

## 1.0.1

- Forked from the upstream reviewer2 v1.0.1 release.
