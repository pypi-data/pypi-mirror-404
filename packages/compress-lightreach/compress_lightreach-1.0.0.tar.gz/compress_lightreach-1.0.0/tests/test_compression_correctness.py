"""
Comprehensive tests for compression algorithm correctness.
Tests that AI can actually interpret the compressed output correctly.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from compressors import compress_prompt, format_for_llm, decompress_llm_format
from compressors.greedy_compressor import GreedyCompressor
from compressors.optimal_compressor import OptimalCompressor

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class TestCompressionRoundtrip:
    """Test that compression -> decompression returns original text."""
    
    @pytest.mark.parametrize("algorithm", ["greedy", "optimal"])
    @pytest.mark.parametrize("prompt", [
        "hello world " * 10,
        "The quick brown fox jumps over the lazy dog. " * 5,
        "test " * 100,
        "a" * 1000,
        "Compress this prompt. " * 20 + "Different pattern here. " * 15,
        # Edge cases
        "",
        "no repetition here at all",
        "x",
        "ab ab ab ab",
        # Special characters
        "@@@###$$$%%% " * 10,
        "Line 1\nLine 2\nLine 1\nLine 2\n" * 5,
        # Unicode
        "Hello 世界 " * 10,
        "émojis 🚀🌟💻 " * 8,
    ])
    def test_roundtrip_correctness(self, algorithm, prompt):
        """Test that compress + decompress returns original."""
        use_optimal = (algorithm == "optimal")
        
        compressed, dictionary, ratio = compress_prompt(
            prompt, 
            model="gpt-4", 
            use_optimal=use_optimal
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        decompressed = decompress_llm_format(llm_format)
        
        assert decompressed == prompt, (
            f"Roundtrip failed for {algorithm}!\n"
            f"Original length: {len(prompt)}\n"
            f"Decompressed length: {len(decompressed)}\n"
            f"Dictionary: {dictionary}\n"
            f"LLM format: {llm_format[:200]}..."
        )
    
    def test_empty_prompt(self):
        """Empty prompt should return empty."""
        compressed, dictionary, ratio = compress_prompt("", model="gpt-4")
        assert compressed == ""
        assert dictionary == {}
        assert ratio == 1.0
    
    def test_no_compression_benefit(self):
        """Text with no repetition should not be compressed."""
        prompt = "abcdefghijklmnopqrstuvwxyz0123456789"
        compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4")
        
        # Should return original (no benefit to compression)
        assert compressed == prompt
        assert dictionary == {}


class TestTokenSavings:
    """Test that compression actually saves tokens."""
    
    @pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not installed")
    @pytest.mark.parametrize("prompt,min_savings", [
        ("hello world " * 50, 20),  # Should save at least 20 tokens
        ("The quick brown fox " * 30, 15),
        ("test " * 100, 50),
        ("You are a helpful assistant. " * 25, 30),
    ])
    def test_token_savings(self, prompt, min_savings):
        """Test that compression provides expected token savings."""
        import tiktoken
        encoding = tiktoken.encoding_for_model("gpt-4")
        
        original_tokens = len(encoding.encode(prompt))
        
        compressed, dictionary, ratio = compress_prompt(
            prompt, 
            model="gpt-4", 
            use_optimal=False
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        compressed_tokens = len(encoding.encode(llm_format))
        
        actual_savings = original_tokens - compressed_tokens
        
        assert actual_savings >= min_savings, (
            f"Expected at least {min_savings} token savings, got {actual_savings}\n"
            f"Original: {original_tokens} tokens\n"
            f"Compressed: {compressed_tokens} tokens\n"
            f"Ratio: {ratio:.2%}\n"
            f"Dictionary: {dictionary}"
        )
    
    @pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not installed")
    def test_compression_never_increases_tokens(self):
        """Compression should never increase token count."""
        import tiktoken
        encoding = tiktoken.encoding_for_model("gpt-4")
        
        test_prompts = [
            "hello world " * 10,
            "test " * 50,
            "The quick brown fox " * 20,
            "no repetition in this text",
            "a" * 500,
        ]
        
        for prompt in test_prompts:
            original_tokens = len(encoding.encode(prompt))
            
            compressed, dictionary, ratio = compress_prompt(
                prompt, 
                model="gpt-4", 
                use_optimal=False
            )
            
            llm_format = format_for_llm(compressed, dictionary)
            compressed_tokens = len(encoding.encode(llm_format))
            
            assert compressed_tokens <= original_tokens, (
                f"Compression increased tokens!\n"
                f"Original: {original_tokens} tokens\n"
                f"Compressed: {compressed_tokens} tokens\n"
                f"Prompt: {prompt[:100]}...\n"
                f"Dictionary: {dictionary}"
            )


class TestLLMInterpretability:
    """Test that LLM format is actually parseable and interpretable."""
    
    def test_llm_format_structure(self):
        """Test that LLM format has correct structure."""
        prompt = "hello world " * 20
        compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4")
        llm_format = format_for_llm(compressed, dictionary)
        
        if dictionary:
            # Should have silent format with JSON dictionary
            assert "[Instruction:" in llm_format
            assert "|PROMPT_LEN:" in llm_format
            
            # Should be parseable
            decompressed = decompress_llm_format(llm_format)
            assert decompressed == prompt
        else:
            # No compression, should be original
            assert llm_format == prompt
    
    def test_dictionary_format(self):
        """Test that dictionary entries are valid."""
        prompt = "test test test test"
        compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4")
        
        # All dictionary keys should be single tokens (1 char or word)
        for key, value in dictionary.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            assert len(key) >= 1
            assert len(value) >= 1
            
            # Forbidden characters should not be in keys
            forbidden = {';', '=', '|'}
            assert not any(c in forbidden for c in key)
    
    def test_placeholder_uniqueness(self):
        """Test that placeholders are unique."""
        prompt = "pattern1 " * 20 + "pattern2 " * 20 + "pattern3 " * 20
        compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4")
        
        # All dictionary keys should be unique
        assert len(dictionary) == len(set(dictionary.keys()))
        
        # Placeholders should not appear in original values
        for key, value in dictionary.items():
            for other_key in dictionary.keys():
                if key != other_key:
                    assert other_key not in value, (
                        f"Placeholder {other_key} appears in value for {key}: {value}"
                    )


class TestEdgeCases:
    """Test edge cases and potential failure modes."""
    
    def test_very_long_prompt(self):
        """Test compression of very long prompts."""
        prompt = "This is a long repeated sentence. " * 500
        compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4")
        
        llm_format = format_for_llm(compressed, dictionary)
        decompressed = decompress_llm_format(llm_format)
        
        assert decompressed == prompt
    
    def test_many_different_patterns(self):
        """Test prompt with many different repeated patterns."""
        patterns = [f"pattern{i} " for i in range(20)]
        prompt = "".join(pattern * 10 for pattern in patterns)
        
        compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4")
        
        llm_format = format_for_llm(compressed, dictionary)
        decompressed = decompress_llm_format(llm_format)
        
        assert decompressed == prompt
    
    def test_nested_patterns(self):
        """Test patterns that contain other patterns."""
        prompt = "ab " * 20 + "ab ab " * 15 + "ab ab ab " * 10
        compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4")
        
        llm_format = format_for_llm(compressed, dictionary)
        decompressed = decompress_llm_format(llm_format)
        
        assert decompressed == prompt
    
    def test_special_characters_in_prompt(self):
        """Test prompts with special characters that might be used as placeholders."""
        special_chars = "@#$%^*()[]{}\\:'\",.<>?/~`"
        prompt = f"Text with {special_chars} special chars. " * 10
        
        compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4")
        
        llm_format = format_for_llm(compressed, dictionary)
        decompressed = decompress_llm_format(llm_format)
        
        assert decompressed == prompt
    
    def test_json_like_content(self):
        """Test compression of JSON-like content."""
        prompt = '{"key": "value", "array": [1, 2, 3]} ' * 15
        compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4")
        
        llm_format = format_for_llm(compressed, dictionary)
        decompressed = decompress_llm_format(llm_format)
        
        assert decompressed == prompt


class TestModelCompatibility:
    """Test compression with different model types."""
    
    @pytest.mark.parametrize("model", [
        "gpt-4",
        "gpt-3.5-turbo",
        "gpt-4o",
        "openai/gpt-4",
        "openai/gpt-4-turbo",
        "claude-3-opus",  # Non-OpenAI model (fallback)
        "claude-3-sonnet",
    ])
    def test_different_models(self, model):
        """Test that compression works with different model specifications."""
        prompt = "hello world " * 20
        
        compressed, dictionary, ratio = compress_prompt(
            prompt, 
            model=model, 
            use_optimal=False
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        decompressed = decompress_llm_format(llm_format)
        
        assert decompressed == prompt


class TestGreedyVsOptimal:
    """Compare greedy vs optimal algorithms."""
    
    @pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not installed")
    def test_optimal_never_worse_than_greedy(self):
        """Optimal should never produce worse results than greedy."""
        import tiktoken
        encoding = tiktoken.encoding_for_model("gpt-4")
        
        test_prompts = [
            "hello world " * 30,
            "test " * 50,
            "pattern1 " * 15 + "pattern2 " * 15,
        ]
        
        for prompt in test_prompts:
            original_tokens = len(encoding.encode(prompt))
            
            # Greedy
            greedy_compressed, greedy_dict, _ = compress_prompt(
                prompt, model="gpt-4", use_optimal=False
            )
            greedy_format = format_for_llm(greedy_compressed, greedy_dict)
            greedy_tokens = len(encoding.encode(greedy_format))
            
            # Optimal
            optimal_compressed, optimal_dict, _ = compress_prompt(
                prompt, model="gpt-4", use_optimal=True
            )
            optimal_format = format_for_llm(optimal_compressed, optimal_dict)
            optimal_tokens = len(encoding.encode(optimal_format))
            
            # Optimal should be <= greedy
            assert optimal_tokens <= greedy_tokens, (
                f"Optimal produced worse result than greedy!\n"
                f"Original: {original_tokens} tokens\n"
                f"Greedy: {greedy_tokens} tokens\n"
                f"Optimal: {optimal_tokens} tokens"
            )


class TestActualLLMUsage:
    """Test by simulating actual LLM usage patterns."""
    
    def test_system_prompt_compression(self):
        """Test compressing typical system prompts."""
        system_prompt = (
            "You are a helpful assistant. " * 10 +
            "Please provide clear and concise answers. " * 8 +
            "Always be polite and professional. " * 6
        )
        
        compressed, dictionary, ratio = compress_prompt(
            system_prompt, 
            model="gpt-4"
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        decompressed = decompress_llm_format(llm_format)
        
        assert decompressed == system_prompt
        assert ratio < 0.9  # Should achieve at least 10% compression
    
    def test_repeated_instructions_compression(self):
        """Test compressing prompts with repeated instructions."""
        prompt = (
            "Step 1: Read the input carefully.\n" * 5 +
            "Step 2: Analyze the requirements.\n" * 5 +
            "Step 3: Generate a response.\n" * 5
        )
        
        compressed, dictionary, ratio = compress_prompt(
            prompt, 
            model="gpt-4"
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        decompressed = decompress_llm_format(llm_format)
        
        assert decompressed == prompt
    
    def test_code_example_compression(self):
        """Test compressing code with repeated patterns."""
        code_prompt = (
            "def process_data(data):\n    return data.strip().lower()\n\n" * 10 +
            "# Example usage:\nresult = process_data(input_data)\n" * 8
        )
        
        compressed, dictionary, ratio = compress_prompt(
            code_prompt, 
            model="gpt-4"
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        decompressed = decompress_llm_format(llm_format)
        
        assert decompressed == code_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
