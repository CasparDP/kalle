from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from reviewer2.config import Config, ProviderConfig
from reviewer2.core import call_llm


class _FailingCompletions:
    def __init__(self, message: str) -> None:
        self.message = message
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        raise RuntimeError(self.message)


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


if __name__ == "__main__":
    unittest.main()
