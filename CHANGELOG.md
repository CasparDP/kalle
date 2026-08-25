# Changelog

## 1.1.0 — 2026-08-23

- Added a provider-agnostic OpenAI-compatible backend with configurable fast
  and strong model tiers; the fork defaults to DeepSeek V4 Flash/Pro through
  Ollama Cloud.
- Added durable background execution, explicit checkpoint resume, effective
  model provenance, and portable agent skills for multi-model review workflows.
- Added optional replication-code and literature-enrichment integrations.
- Mathpix requests now set `metadata.improve_mathpix: false`, opting out of
  Mathpix data retention for service improvement.

## 1.0.1

- Forked from the upstream reviewer2 v1.0.1 release.
