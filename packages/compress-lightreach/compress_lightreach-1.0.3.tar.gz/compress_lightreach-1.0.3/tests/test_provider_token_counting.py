from unittest.mock import patch, Mock

from api.token_counter import count_tokens_detailed
from api.provider_token_counting.google_token_counter import _normalize_google_model


def test_google_model_normalization():
    assert _normalize_google_model("google/gemini-2.0-flash") == "models/gemini-2.0-flash"
    assert _normalize_google_model("gemini-2.0-flash") == "models/gemini-2.0-flash"
    assert _normalize_google_model("models/gemini-2.0-flash") == "models/gemini-2.0-flash"


def test_google_exact_token_counting_with_cache():
    mock_resp = Mock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"totalTokens": 123}

    with patch("api.provider_token_counting.google_token_counter.requests.post", return_value=mock_resp) as p:
        r1 = count_tokens_detailed(
            text="hello",
            model="google/gemini-2.0-flash",
            provider="google",
            provider_api_key="fake-key",
        )
        assert r1.tokens == 123
        assert r1.exact is True
        assert r1.source == "google_countTokens"

        # Second call should hit cache (no second HTTP call)
        r2 = count_tokens_detailed(
            text="hello",
            model="google/gemini-2.0-flash",
            provider="google",
            provider_api_key="fake-key",
        )
        assert r2 == r1
        assert p.call_count == 1


def test_google_falls_back_to_estimate_without_key():
    r = count_tokens_detailed(text="abcde", model="google/gemini-2.0-flash", provider="google", provider_api_key=None)
    assert r.tokens == 2
    assert r.exact is False
    assert r.source == "estimate_chars_4"


def test_anthropic_exact_token_counting():
    mock_resp = Mock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"input_tokens": 55}

    # Patch the HTTP request AND the model mapping used by AnthropicClient.
    with (
        patch("api.provider_token_counting.anthropic_token_counter.requests.post", return_value=mock_resp),
        patch("api.provider_token_counting.anthropic_token_counter.AnthropicClient") as C,
    ):
        inst = C.return_value
        inst.BASE_URL = "https://api.anthropic.com/v1"
        inst._get_model_id.return_value = "claude-3-opus-20240229"

        r = count_tokens_detailed(
            text="hello",
            model="anthropic/claude-3-opus",
            provider="anthropic",
            provider_api_key="fake-key",
        )
        assert r.tokens == 55
        assert r.exact is True
        assert r.source == "anthropic_countTokens"


def test_hf_tokenizer_counting_uses_transformers_when_available():
    with (
        patch("api.token_counter.TRANSFORMERS_AVAILABLE", True),
        patch("api.token_counter.count_tokens_hf", return_value=4) as c,
    ):
        r = count_tokens_detailed(
            text="hello",
            model="mistralai/Mistral-7B-Instruct-v0.2",
            provider=None,
            provider_api_key=None,
        )
        assert r.tokens == 4
        assert r.exact is True
        assert r.source == "hf_tokenizer:mistralai/Mistral-7B-Instruct-v0.2"
        c.assert_called_once()


def test_hf_tokenizer_falls_back_to_estimate_on_error():
    with (
        patch("api.token_counter.TRANSFORMERS_AVAILABLE", True),
        patch(
            "api.token_counter.count_tokens_hf",
            side_effect=__import__("api.provider_token_counting.hf_tokenizer_counter", fromlist=["HFTokenizerCountError"]).HFTokenizerCountError(
                "boom"
            ),
        ),
    ):
        r = count_tokens_detailed(
            text="abcde",
            model="mistralai/Mistral-7B-Instruct-v0.2",
            provider=None,
            provider_api_key=None,
        )
        assert r.tokens == 2
        assert r.exact is False
        assert r.source == "estimate_chars_4"


