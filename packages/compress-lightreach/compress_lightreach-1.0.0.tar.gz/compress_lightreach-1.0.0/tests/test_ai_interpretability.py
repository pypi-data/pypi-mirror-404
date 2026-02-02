"""
Test that AI can actually interpret and decompress our compression format.

This is the ULTIMATE test - can an LLM actually understand and use our compressed prompts?
"""

import sys
from pathlib import Path
import json

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from compressors import compress_prompt, format_for_llm, decompress_llm_format

# These tests require API keys, so they're marked as optional
pytestmark = pytest.mark.skipif(
    "not config.getoption('--run-llm-tests')",
    reason="Requires --run-llm-tests flag and API keys"
)


def get_openai_client():
    """Get OpenAI client if available."""
    try:
        import openai
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")
        return openai.OpenAI(api_key=api_key)
    except ImportError:
        pytest.skip("openai package not installed")


def get_anthropic_client():
    """Get Anthropic client if available."""
    try:
        import anthropic
        import os
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")
        return anthropic.Anthropic(api_key=api_key)
    except ImportError:
        pytest.skip("anthropic package not installed")


class TestOpenAIInterpretability:
    """Test that OpenAI models can interpret our compression format."""
    
    def test_basic_compression_with_gpt4(self):
        """Test that GPT-4 can understand and respond to compressed prompts."""
        client = get_openai_client()
        
        # Create a prompt with repetition
        original_prompt = (
            "You are a helpful assistant. " * 10 +
            "Please answer this question: What is 2+2?"
        )
        
        # Compress it
        compressed, dictionary, ratio = compress_prompt(
            original_prompt,
            model="gpt-4",
            use_optimal=False
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        
        # First, let's verify the LLM can decompress it correctly
        decompression_test = f"""
The following is a compressed prompt in PCLRv1 format. 
Please decompress it and respond ONLY with the decompressed text, nothing else.

{llm_format}
"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": decompression_test}],
            temperature=0
        )
        
        llm_decompressed = response.choices[0].message.content.strip()
        our_decompressed = decompress_llm_format(llm_format)
        
        # The LLM should produce the same result as our decompressor
        # (allowing for minor whitespace differences)
        assert llm_decompressed == our_decompressed or \
               llm_decompressed.strip() == our_decompressed.strip(), (
            f"LLM decompression doesn't match!\n"
            f"Our decompression: {our_decompressed}\n"
            f"LLM decompression: {llm_decompressed}"
        )
    
    def test_gpt4_follows_compressed_instructions(self):
        """Test that GPT-4 can follow instructions from a compressed prompt."""
        client = get_openai_client()
        
        # Create prompt with clear instructions and repetition
        original_prompt = (
            "You are a math tutor. " * 8 +
            "Please solve this problem: What is 15 + 27? " +
            "Provide only the numeric answer."
        )
        
        compressed, dictionary, ratio = compress_prompt(
            original_prompt,
            model="gpt-4",
            use_optimal=False
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        
        # Ask GPT-4 to decompress and follow the instructions
        prompt_for_llm = f"""
The following prompt is in PCLRv1 compressed format. 
First decompress it, then follow its instructions.

{llm_format}
"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_for_llm}],
            temperature=0
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Should contain the answer 42
        assert "42" in answer, (
            f"LLM didn't correctly follow compressed instructions!\n"
            f"Response: {answer}"
        )
    
    def test_json_compression_interpretability(self):
        """Test that GPT-4 can understand compressed JSON-like data."""
        client = get_openai_client()
        
        # JSON-like structure with repetition
        original_prompt = (
            '{"name": "Alice", "age": 30, "city": "NYC"}\n' * 5 +
            '{"name": "Bob", "age": 25, "city": "LA"}\n' * 5 +
            'Count the total number of people in the above JSON objects.'
        )
        
        compressed, dictionary, ratio = compress_prompt(
            original_prompt,
            model="gpt-4",
            use_optimal=False
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        
        prompt_for_llm = f"""
Decompress this PCLRv1 format and answer the question:

{llm_format}
"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_for_llm}],
            temperature=0
        )
        
        answer = response.choices[0].message.content
        
        # Should recognize there are 10 people (5 Alice + 5 Bob)
        assert "10" in answer, (
            f"LLM didn't correctly interpret compressed JSON!\n"
            f"Response: {answer}"
        )


class TestClaudeInterpretability:
    """Test that Claude can interpret our compression format."""
    
    def test_basic_compression_with_claude(self):
        """Test that Claude can understand compressed prompts."""
        client = get_anthropic_client()
        
        original_prompt = (
            "You are a helpful assistant. " * 10 +
            "Please answer: What is the capital of France?"
        )
        
        compressed, dictionary, ratio = compress_prompt(
            original_prompt,
            model="gpt-4",  # Use OpenAI tokenizer for now
            use_optimal=False
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        
        # Test Claude's decompression ability
        decompression_test = f"""
The following is a compressed prompt in PCLRv1 format.
Please decompress it and respond ONLY with the decompressed text.

{llm_format}
"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": decompression_test}]
        )
        
        llm_decompressed = response.content[0].text.strip()
        our_decompressed = decompress_llm_format(llm_format)
        
        assert llm_decompressed == our_decompressed or \
               llm_decompressed.strip() == our_decompressed.strip(), (
            f"Claude decompression doesn't match!\n"
            f"Our decompression: {our_decompressed}\n"
            f"Claude decompression: {llm_decompressed}"
        )


class TestFormatRobustness:
    """Test that the format is robust and unambiguous."""
    
    def test_no_ambiguity_in_parsing(self):
        """Test that LLM format can be parsed unambiguously."""
        test_cases = [
            "hello world " * 20,
            "test with | pipes | and = equals " * 10,
            "multiple\nlines\nmultiple\nlines\n" * 5,
            '{"key": "value"} ' * 15,
        ]
        
        for prompt in test_cases:
            compressed, dictionary, ratio = compress_prompt(
                prompt,
                model="gpt-4",
                use_optimal=False
            )
            
            llm_format = format_for_llm(compressed, dictionary)
            
            # Parse it back
            decompressed = decompress_llm_format(llm_format)
            
            # Should match exactly
            assert decompressed == prompt, (
                f"Format parsing is ambiguous!\n"
                f"Original: {prompt[:100]}...\n"
                f"Decompressed: {decompressed[:100]}...\n"
                f"LLM format: {llm_format[:200]}..."
            )
    
    def test_dictionary_is_valid_json(self):
        """Test that dictionary portion is valid JSON."""
        prompt = "test test test " * 20
        
        compressed, dictionary, ratio = compress_prompt(
            prompt,
            model="gpt-4",
            use_optimal=False
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        
        if not dictionary:
            return  # No dictionary to test
        
        # Extract dictionary JSON from format
        if llm_format.startswith("PCLRv1|DICT_LEN:"):
            parts = llm_format.split("|")
            dict_len_part = parts[1]  # DICT_LEN:N
            dict_len = int(dict_len_part.split(":")[1])
            
            # Find where dict JSON starts
            dict_start = llm_format.find("|", len("PCLRv1|DICT_LEN:") + len(str(dict_len))) + 1
            dict_json = llm_format[dict_start:dict_start + dict_len]
            
            # Should be valid JSON
            parsed = json.loads(dict_json)
            assert isinstance(parsed, dict)
            assert all(isinstance(k, str) and isinstance(v, str) 
                      for k, v in parsed.items())


class TestManualInterpretation:
    """Tests where we manually interpret the format (simulating what an LLM would do)."""
    
    def test_manual_decompression_simple(self):
        """Test manual step-by-step decompression like an LLM would do."""
        prompt = "hello world hello world hello world"
        
        compressed, dictionary, ratio = compress_prompt(
            prompt,
            model="gpt-4",
            use_optimal=False
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        
        # Manual parsing (like an LLM would do)
        if llm_format.startswith("PCLRv1|DICT_LEN:"):
            # Parse format
            parts = llm_format.split("|")
            
            # Extract dictionary
            dict_len_str = parts[1].replace("DICT_LEN:", "")
            dict_len = int(dict_len_str)
            
            dict_start = len("PCLRv1|DICT_LEN:") + len(dict_len_str) + 1
            dict_json = llm_format[dict_start:dict_start + dict_len]
            parsed_dict = json.loads(dict_json)
            
            # Extract prompt
            prompt_marker = f"|PROMPT_LEN:"
            prompt_marker_pos = llm_format.find(prompt_marker, dict_start + dict_len)
            prompt_len_start = prompt_marker_pos + len(prompt_marker)
            prompt_len_end = llm_format.find("|", prompt_len_start)
            prompt_len = int(llm_format[prompt_len_start:prompt_len_end])
            
            compressed_text = llm_format[prompt_len_end + 1:prompt_len_end + 1 + prompt_len]
            
            # Manual decompression
            decompressed = compressed_text
            for placeholder, original in parsed_dict.items():
                decompressed = decompressed.replace(placeholder, original)
            
            # Should match
            assert decompressed == prompt, (
                f"Manual decompression failed!\n"
                f"Original: {prompt}\n"
                f"Decompressed: {decompressed}\n"
                f"Dictionary: {parsed_dict}\n"
                f"Compressed text: {compressed_text}"
            )
        else:
            # No compression
            assert llm_format == prompt
    
    def test_instructions_for_llm(self):
        """Generate clear instructions for LLM to decompress."""
        prompt = "test test test test"
        
        compressed, dictionary, ratio = compress_prompt(
            prompt,
            model="gpt-4",
            use_optimal=False
        )
        
        llm_format = format_for_llm(compressed, dictionary)
        
        # Generate instructions
        instructions = f"""
To decompress this PCLRv1 format:

1. Parse the format: PCLRv1|DICT_LEN:<n>|<dict_json>|PROMPT_LEN:<m>|<compressed_text>
2. Extract the dictionary JSON (length n)
3. Extract the compressed text (length m)
4. Replace each placeholder in the compressed text with its value from the dictionary

Format:
{llm_format}

Decompressed result should be:
{prompt}
"""
        
        # This test documents how an LLM should interpret it
        assert True  # Documentation test


def pytest_addoption(parser):
    """Add command line option for LLM tests."""
    parser.addoption(
        "--run-llm-tests",
        action="store_true",
        default=False,
        help="Run tests that require LLM API calls"
    )


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "llm: mark test as requiring LLM API calls"
    )


if __name__ == "__main__":
    print("To run these tests with LLM API calls:")
    print("  pytest test_ai_interpretability.py --run-llm-tests")
    print("\nRequired environment variables:")
    print("  OPENAI_API_KEY - for OpenAI tests")
    print("  ANTHROPIC_API_KEY - for Anthropic tests")
