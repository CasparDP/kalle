from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from reviewer2.config import Config, ProviderConfig
from reviewer2.core import DEFAULT_MAX_OUTPUT_TOKENS, call_llm


class _FailingCompletions:
    def __init__(self, message: str) -> None:
        self.message = message
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        raise RuntimeError(self.message)


class _RecordingCompletions:
    def __init__(self) -> None:
        self.kwargs: list[dict] = []

    def create(self, **kwargs):
        self.kwargs.append(kwargs)
        message = SimpleNamespace(content="ok")
        return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")], usage=None)


class CoreRetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = Config(
            provider=ProviderConfig(api_key="test", fast_model="fast", strong_model="strong")
        )

    def test_authentication_failure_is_not_retried(self) -> None:
        completions = _FailingCompletions("401 Unauthorized: invalid API key")
        client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        with patch("reviewer2.core._make_client", return_value=client), patch(
            "reviewer2.core.time.sleep"
        ) as sleep:
            with self.assertRaisesRegex(RuntimeError, "Authentication failed"):
                call_llm(prompt="test", max_retries=4, config=self.config)
        self.assertEqual(completions.calls, 1)
        sleep.assert_not_called()

    def test_rate_limit_is_finite_by_default(self) -> None:
        completions = _FailingCompletions("429 Too Many Requests")
        client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        with patch("reviewer2.core._make_client", return_value=client), patch(
            "reviewer2.core.time.sleep"
        ):
            with self.assertRaisesRegex(RuntimeError, "Rate limit exceeded after 2 attempts"):
                call_llm(prompt="test", max_retries=2, config=self.config)
        self.assertEqual(completions.calls, 2)

    def test_output_cap_defaults_and_stage_override(self) -> None:
        completions = _RecordingCompletions()
        client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        with patch("reviewer2.core._make_client", return_value=client):
            call_llm(prompt="test", config=self.config)
            call_llm(prompt="test", max_output_tokens=1000, config=self.config)
        self.assertEqual(completions.kwargs[0]["max_tokens"], DEFAULT_MAX_OUTPUT_TOKENS)
        self.assertEqual(completions.kwargs[1]["max_tokens"], 1000)


if __name__ == "__main__":
    unittest.main()
