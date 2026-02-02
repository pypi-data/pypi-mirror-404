"""
Test script for sending compressed prompts to ChatGPT.

This script compresses a prompt and formats it with instructions
that ChatGPT can follow to decompress and use it.
"""

import sys
import os
from pathlib import Path

# Add current directory (backend) to Python path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from compressors import compress_prompt, format_for_llm, decompress_llm_format

def format_for_chatgpt(prompt: str, include_instructions: bool = True) -> tuple:
    """
    Compress a prompt and format it for ChatGPT testing.
    
    Args:
        prompt: The original prompt to compress
        include_instructions: Whether to include decompression instructions
    
    Returns:
        Tuple of (formatted_string, compression_ratio)
    """
    # Compress the prompt
    compressed, dict_data, ratio = compress_prompt(prompt, model="gpt-4", use_optimal=False)
    llm_format = format_for_llm(compressed, dict_data)
    
    if include_instructions:
        # Format with minimal instructions for ChatGPT
        formatted = (
            "Decompress the framed prompt format:\n"
            "- If it starts with 'PCLRv1|DICT_LEN:', parse the JSON dictionary and expand placeholders in PROMPT.\n"
            "- Otherwise, treat it as plain text.\n\n"
            f"{llm_format}"
        )
    else:
        # Just the compressed prompt without instructions
        formatted = llm_format
    
    return formatted, ratio


def run_chatgpt_prompt(original_prompt: str, include_instructions: bool = True):
    """
    Create a test prompt for ChatGPT and display it.
    
    Args:
        original_prompt: The original prompt to compress
        include_instructions: Whether to include decompression instructions
    """
    print("=" * 80)
    print("CHATGPT TEST - Compressed Prompt")
    print("=" * 80)
    print(f"\nOriginal prompt ({len(original_prompt)} characters):")
    print("-" * 80)
    print(original_prompt)
    print("-" * 80)
    
    # Compress and format
    formatted, ratio = format_for_chatgpt(original_prompt, include_instructions)
    
    # Extract just the compressed prompt (without instructions) for accurate stats
    compressed, dict_data, _ = compress_prompt(original_prompt, model="gpt-4", use_optimal=False)
    compressed_only = format_for_llm(compressed, dict_data)
    
    print(f"\nCompression statistics:")
    print(f"  Original size: {len(original_prompt)} characters")
    print(f"  Compressed prompt size: {len(compressed_only)} characters")
    print(f"  Compression ratio: {ratio:.2%}")
    print(f"  Space saved (prompt only): {len(original_prompt) - len(compressed_only)} characters")
    if include_instructions:
        print(f"  Total formatted size (with instructions): {len(formatted)} characters")
    
    print("\n" + "=" * 80)
    print("FORMATTED PROMPT FOR CHATGPT:")
    print("=" * 80)
    print("\n" + formatted)
    print("\n" + "=" * 80)
    
    # Verify decompression works
    print("\nVerification:")
    print("-" * 80)
    compressed, dict_data, _ = compress_prompt(original_prompt, model="gpt-4", use_optimal=False)
    compressed_only = format_for_llm(compressed, dict_data)
    decompressed = decompress_llm_format(compressed_only)
    
    if decompressed == original_prompt:
        print("✅ Decompression test passed - compressed prompt can be correctly decompressed")
    else:
        print("❌ Decompression test failed")
        print(f"Original: {original_prompt[:100]}...")
        print(f"Decompressed: {decompressed[:100]}...")
    
    print("\n" + "=" * 80)
    print("INSTRUCTIONS:")
    print("=" * 80)
    print("1. Copy the 'FORMATTED PROMPT FOR CHATGPT' section above")
    print("2. Paste it into ChatGPT")
    print("3. ChatGPT should decompress the prompt and respond to it")
    print("=" * 80)
    
    return formatted


def main():
    """Main function with example prompts."""
    
    # Example prompts to test
    example_prompts = [
        "Write a short story about a robot learning to paint. The robot should discover that art is about emotion, not just technique. Include a moment where the robot creates something beautiful by accident.",
        "Explain quantum computing in simple terms. What makes it different from classical computing? Give an example of a problem that quantum computers can solve more efficiently.",
        "The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog.",
    ]
    
    if len(sys.argv) > 1:
        # Use command line argument as prompt
        prompt = " ".join(sys.argv[1:])
        run_chatgpt_prompt(prompt)
    else:
        # Use first example prompt
        print("No prompt provided. Using example prompt.")
        print("Usage: python test_chatgpt.py 'Your prompt here'")
        print("\n" + "=" * 80 + "\n")
        run_chatgpt_prompt(example_prompts[0])


if __name__ == "__main__":
    main()

