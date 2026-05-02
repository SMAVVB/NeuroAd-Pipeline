#!/usr/bin/env python3
"""
Verification test for ask_llm retry logic.

Mocks requests.post to always raise Timeout, calls ask_llm,
and asserts that it retries 3 times and returns the fallback string.
"""
import sys
import time
from unittest.mock import patch, MagicMock
from types import ModuleType

# --- Stub out ollama_api (imported by watchdog) so we don't need it here ---
sys.modules['ollama_api'] = ModuleType('ollama_api')

# --- Now import config_core ---
import config_core


def test_llm_retry_on_timeout():
    """Verify ask_llm retries 3 times on Timeout and returns fallback string."""

    call_count = 0

    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        exc = requests.exceptions.Timeout("Connection timed out")
        raise exc

    # We need requests module for the exception types
    import requests

    with patch.object(config_core, 'requests') as mock_requests:
        mock_requests.post.side_effect = mock_post
        mock_requests.exceptions = requests.exceptions

        result = config_core.ask_llm(
            system_prompt="test system",
            user_prompt="test user",
            model_name="test-model",
        )

    # Assert: retried exactly 3 times
    assert call_count == 3, f"Expected 3 calls, got {call_count}"

    # Assert: returned safe fallback string
    expected_fallback = "LLM API Error: Timeout or Unreachable"
    assert result == expected_fallback, f"Expected '{expected_fallback}', got '{result}'"

    print("PASS: ask_llm retried 3 times and returned safe fallback string.")


def test_llm_retry_returns_on_success():
    """Verify ask_llm returns content on first successful call (no unnecessary retries)."""

    call_count = 0

    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "success response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20}
        }
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    import requests

    with patch.object(config_core, 'requests') as mock_requests:
        mock_requests.post.side_effect = mock_post
        mock_requests.exceptions = requests.exceptions

        result = config_core.ask_llm(
            system_prompt="test system",
            user_prompt="test user",
            model_name="test-model",
        )

    # Assert: only 1 call made (no retries needed)
    assert call_count == 1, f"Expected 1 call on success, got {call_count}"

    # Assert: returned the content
    assert result == "success response", f"Expected 'success response', got '{result}'"

    print("PASS: ask_llm returned content on first success (no unnecessary retries).")


def test_llm_retry_exponential_backoff():
    """Verify exponential backoff delays: 5s, 10s, 20s."""

    import requests
    import time as time_module

    original_sleep = time_module.sleep
    sleep_calls = []

    def mock_sleep(duration):
        sleep_calls.append(duration)
        # Don't actually sleep during test

    def mock_post(*args, **kwargs):
        exc = requests.exceptions.Timeout("Connection timed out")
        raise exc

    with patch.object(config_core, 'requests') as mock_requests, \
         patch.object(time_module, 'sleep', side_effect=mock_sleep):
        mock_requests.post.side_effect = mock_post
        mock_requests.exceptions = requests.exceptions

        config_core.ask_llm(
            system_prompt="test",
            user_prompt="test",
            model_name="test-model",
        )

    # Expected backoff: 5 * 2^0 = 5 (after attempt 0), 5 * 2^1 = 10 (after attempt 1)
    # No sleep after the 3rd attempt since there's no next attempt
    expected_backoffs = [5, 10]
    assert sleep_calls == expected_backoffs, f"Expected backoff {expected_backoffs}, got {sleep_calls}"

    print(f"PASS: Exponential backoff verified: {sleep_calls}s delays.")


if __name__ == "__main__":
    import requests
    test_llm_retry_on_timeout()
    test_llm_retry_returns_on_success()
    test_llm_retry_exponential_backoff()
    print("\nAll tests passed!")
