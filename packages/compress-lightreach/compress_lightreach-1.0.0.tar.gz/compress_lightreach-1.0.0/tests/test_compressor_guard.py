"""
Unit tests for compressor safety/guard behavior.

These tests do NOT require a running backend server or network access.
They validate that compression never returns a worse-than-original payload,
and that we still compress when repetition is large enough to amortize overhead.
"""

import pytest

from compressors.utils import compress_prompt, format_for_llm, decompress_llm_format
from compressors.base_compressor import TIKTOKEN_AVAILABLE


def _count_tokens_openai(text: str, model: str = "gpt-4") -> int:
    """Token counter used only for assertions when tiktoken is available."""
    import tiktoken

    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


@pytest.mark.parametrize("use_optimal", [False, True])
def test_guard_returns_original_for_small_repeats_openai(use_optimal: bool):
    """
    Regression test:
    Short repeats can trick candidate scoring into producing a dict entry,
    but the full PCLRv1 wrapper overhead can make the final payload larger.
    We must return the original prompt (empty dict) in that case.
    """
    if not TIKTOKEN_AVAILABLE:
        pytest.skip("tiktoken not available; OpenAI exact-token guard path not active")

    prompt = (
        "You are LightReach, a prompt compression assistant. "
        "Rewrite the following workflow summary to highlight setup steps, critical prompts, "
        "and placeholders for variables. Keep the tone concise and technical, and format the output "
        "for LLM ingestion. "
        + ("you " * 18).strip()
        + " hey how are you hey"
    ).strip()

    compressed, d, _ratio = compress_prompt(prompt, model="gpt-4", use_optimal=use_optimal)
    llm_format = format_for_llm(compressed, d)

    # If it isn't strictly smaller (in tokens), it must be returned unchanged.
    assert compressed == prompt
    assert d == {}
    assert llm_format == prompt


@pytest.mark.parametrize("use_optimal", [False, True])
def test_compresses_large_repetition_when_worth_it(use_optimal: bool):
    """
    Ensure we still compress when repetition is large enough to provide real net savings.
    """
    block = "\n\nSYSTEM RULES:\n- Always answer in bullet points\n- Never include URLs\n- Be concise\n"
    prompt = "You are LightReach. Follow the rules below." + (block * 12) + "\nNow: summarize this text." + (block * 12)

    compressed, d, _ratio = compress_prompt(prompt, model="gpt-4", use_optimal=use_optimal)
    llm_format = format_for_llm(compressed, d)

    assert isinstance(d, dict)
    assert len(d) >= 1
    assert llm_format.startswith("PCLRv1|DICT_LEN:")

    # Savings check: prefer token-based when available, otherwise fall back to characters.
    if TIKTOKEN_AVAILABLE:
        assert _count_tokens_openai(llm_format, "gpt-4") < _count_tokens_openai(prompt, "gpt-4")
    else:
        assert len(llm_format) < len(prompt)

    # Round-trip sanity (LLM-format decompress returns the original prompt content)
    assert decompress_llm_format(llm_format) == prompt


@pytest.mark.parametrize("use_optimal", [False, True])
def test_guard_never_expands_without_exact_tokenizer(use_optimal: bool):
    """
    For non-OpenAI models (no exact tokenizer), the guard falls back to char-length checks.
    It should never return a payload longer than the original.
    """
    # Pick a model name that won't be treated as OpenAI.
    model = "anthropic/claude-3-5-sonnet"
    prompt = "short short short short short"  # repeated but small

    compressed, d, _ratio = compress_prompt(prompt, model=model, use_optimal=use_optimal)
    llm_format = format_for_llm(compressed, d)

    assert len(llm_format) <= len(prompt)




