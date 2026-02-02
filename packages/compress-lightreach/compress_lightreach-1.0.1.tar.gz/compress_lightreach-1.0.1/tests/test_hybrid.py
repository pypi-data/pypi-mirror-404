"""
Test script for the Hybrid Prompt Compression Pipeline
"""

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("⚠️  tiktoken not available. Install with: pip install tiktoken")

import sys
from pathlib import Path

# Add current directory (backend) to Python path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from compressors import (
    GreedyCompressor,
    OptimalCompressor,
    compress_prompt_hybrid, 
    format_for_llm, 
    decompress_llm_format
)


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken."""
    if not TIKTOKEN_AVAILABLE:
        return 0
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))


def run_hybrid_compression(prompt: str, test_name: str = "", use_optimal: bool = False) -> bool:
    """
    Test the hybrid compression pipeline.
    """
    print(f"\n{'='*60}")
    if test_name:
        print(f"Test: {test_name}")
    else:
        print(f"Test")
    print(f"{'='*60}")
    print(f"Original prompt ({len(prompt)} chars):")
    print(f"  {prompt[:200]!r}{'...' if len(prompt) > 200 else ''}")
    
    # Count original tokens
    original_tokens = count_tokens(prompt)
    if TIKTOKEN_AVAILABLE:
        print(f"  Original tokens: {original_tokens}")
    
    # Test compression
    try:
        compressed, decompression_dict, ratio = compress_prompt_hybrid(
            prompt, 
            model="gpt-4", 
            use_optimal=use_optimal
        )
    except Exception as e:
        print(f"  ❌ COMPRESSION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\nCompressed prompt ({len(compressed)} chars):")
    print(f"  {compressed[:200]!r}{'...' if len(compressed) > 200 else ''}")
    
    # Format for LLM
    llm_format = format_for_llm(compressed, decompression_dict)
    
    print(f"\nLLM-ready format ({len(llm_format)} chars):")
    print(f"  {llm_format[:200]!r}{'...' if len(llm_format) > 200 else ''}")
    
    # Count compressed tokens
    compressed_tokens = count_tokens(compressed)
    llm_tokens = count_tokens(llm_format)
    if TIKTOKEN_AVAILABLE:
        print(f"  Compressed prompt tokens: {compressed_tokens}")
        print(f"  LLM-ready format tokens: {llm_tokens}")
        if original_tokens > 0:
            token_ratio = llm_tokens / original_tokens
            token_savings = original_tokens - llm_tokens
            print(f"  Token compression ratio: {token_ratio:.2%}")
            print(f"  Tokens saved: {token_savings}")
    
    print(f"\nReplacement dictionary ({len(decompression_dict)} entries):")
    if decompression_dict:
        for placeholder, original in sorted(decompression_dict.items()):
            placeholder_tokens = count_tokens(placeholder)
            original_tokens_sub = count_tokens(original)
            print(f"  {placeholder!r} ({placeholder_tokens} token) -> {original!r} ({original_tokens_sub} tokens)")
    else:
        print("  (no replacements)")
    
    print(f"\nCompression stats:")
    print(f"  Original size: {len(prompt)} characters")
    print(f"  Compressed size: {len(compressed)} characters")
    print(f"  LLM-ready size: {len(llm_format)} characters")
    print(f"  Compression ratio: {ratio:.2%}")
    
    # Verify placeholders are 1 token
    all_placeholders_valid = True
    for placeholder in decompression_dict.keys():
        tokens = count_tokens(placeholder)
        if tokens != 1:
            print(f"  ⚠️  WARNING: Placeholder {placeholder!r} is {tokens} tokens, should be 1")
            all_placeholders_valid = False
    
    # Verify replaced substrings are >1 token
    all_replacements_valid = True
    for original in decompression_dict.values():
        tokens = count_tokens(original)
        if tokens <= 1:
            print(f"  ⚠️  WARNING: Replaced substring {original!r} is {tokens} token(s), should be >1")
            all_replacements_valid = False
    
    if all_placeholders_valid and all_replacements_valid:
        print(f"  ✅ All placeholders are 1 token, all replacements are >1 token")
    
    # Test decompression
    try:
        decompressed = decompress_llm_format(llm_format)
    except Exception as e:
        print(f"\n  ❌ DECOMPRESSION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Validate decompression
    success = prompt == decompressed
    print(f"\nDecompression test:")
    if success:
        print(f"  ✅ PASS: Original matches decompressed")
    else:
        print(f"  ❌ FAIL: Original does not match decompressed")
        print(f"  Original length: {len(prompt)}")
        print(f"  Decompressed length: {len(decompressed)}")
        if len(prompt) == len(decompressed):
            # Find first difference
            for i, (a, b) in enumerate(zip(prompt, decompressed)):
                if a != b:
                    print(f"  First difference at position {i}: {a!r} vs {b!r}")
                    print(f"  Context: ...{prompt[max(0,i-10):i+10]}...")
                    break
    
    return success and all_placeholders_valid and all_replacements_valid


def main():
    """Run comprehensive tests."""
    print("="*60)
    print("Hybrid Prompt Compression Pipeline Test Suite")
    print("="*60)
    if TIKTOKEN_AVAILABLE:
        print("✓ Token counting enabled (tiktoken)")
    else:
        print("⚠️  Token counting disabled (tiktoken not installed)")
    
    # Test cases
    test_cases = [
        ("Write a short story about a robot learning to paint. The robot should discover that art is about emotion, not just technique. The robot learns that art is about emotion.",
         "Robot story with repetition"),
        ("the quick brown fox jumps over the lazy dog the quick brown fox jumps over the lazy dog",
         "Repeated phrase"),
        ("hello world hello world hello world",
         "Simple repetition"),
        ("This is a test. This is a test. This is a test.",
         "Sentence repetition"),
        ("The cat sat on the mat. The cat sat on the mat. The cat sat on the mat.",
         "Long phrase repetition"),
        ("abababababababababab",
         "Pattern repetition"),
    ]
    
    results = []
    for prompt, name in test_cases:
        success = run_hybrid_compression(prompt, name, use_optimal=False)
        results.append((name or prompt[:30], success))
    
    # Print summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

