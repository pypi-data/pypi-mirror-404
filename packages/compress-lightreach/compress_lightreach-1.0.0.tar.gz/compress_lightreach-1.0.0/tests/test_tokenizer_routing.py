"""
Tests for provider-aware tokenization behavior.

We only have tiktoken in this repo, so:
- OpenAI model strings should use tiktoken (exact tokens_are_exact=True in compressors).
- Non-OpenAI model strings should NOT silently fall back to cl100k_base for “exact” behavior.
  They should use the text-based compressor path and an estimated token counter.
"""

from compressors.greedy_compressor import GreedyCompressor
from api.token_utils import count_tokens


def test_openai_model_uses_tiktoken_exact_path():
    prompt = "hello world hello world hello world"
    c = GreedyCompressor(prompt, model="gpt-4")
    assert c.encoding is not None
    assert c.tokens_are_exact is True


def test_openrouter_openai_model_id_uses_tiktoken_exact_path():
    prompt = "hello world hello world hello world"
    c = GreedyCompressor(prompt, model="openai/gpt-4-turbo")
    assert c.encoding is not None
    assert c.tokens_are_exact is True


def test_claude_model_uses_estimated_path_and_still_compresses_losslessly():
    prompt = "abc abc abc abc abc"
    c = GreedyCompressor(prompt, model="anthropic/claude-3-opus")
    # No “exact” tokenizer available in this repo for Claude.
    assert c.tokens_are_exact is False
    # GreedyCompressor should fall back to text-based compression and still be lossless.
    compressed, d = c.compress()
    decompressed = c.decompress(compressed, d)
    assert decompressed == prompt


def test_token_utils_does_not_use_cl100k_for_non_openai_models():
    # This should use the estimator path (non-zero for short strings).
    assert count_tokens("x", model="anthropic/claude-3-opus") == 1
    assert count_tokens("abcd", model="anthropic/claude-3-opus") == 1
    assert count_tokens("abcde", model="anthropic/claude-3-opus") == 2




