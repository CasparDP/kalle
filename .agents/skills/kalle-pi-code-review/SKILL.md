---
name: kalle-pi-code-review
description: Run an optional independent direct-source replication-code review through pi and Ollama, save the raw report, and return findings to kalle's code sign-off ledger. Use only when replication code is supplied or the user explicitly requests a pi code review.
---

# kalle pi code review

This branch reviews source code directly and independently of kalle's
compiled-code audit. It is optional: if pi or the selected Ollama model is not
available, record a coverage gap rather than silently substituting the
synthesizer.

1. Confirm `pi` is callable and select a model. Default to
   `${KALLE_PI_MODEL:-glm-5.2:cloud}` only when it exists in the local pi
   catalog. Keep pi standalone with `--no-session -ne -ns -nc -nt`.
2. Run a one-word handshake before attaching substantial code.
3. Use [reviewer-prompt.md](reviewer-prompt.md) as the system prompt. Attach the
   unmodified source files, describe their purpose/language, and request a
   skeptic or security disposition for high-stakes analysis.
4. Bound the invocation to five minutes; retry a timeout once. Never retry
   authentication failure indefinitely.
5. Save the raw report to
   `quality_reports/YYYY-MM-DD_pi_review_<slug>.md` and preserve model/provider
   metadata.
6. Verify major findings against the cited file/line and an executable
   reproduction where feasible. Return them to the separate code ledger; do
   not implement before user sign-off.

Handshake example:

```bash
pi -p --provider ollama-cloud --model glm-5.2:cloud --no-session -ne -ns -nc -nt \
  "Reply with exactly one word: PONG"
```
