# Changelog

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
