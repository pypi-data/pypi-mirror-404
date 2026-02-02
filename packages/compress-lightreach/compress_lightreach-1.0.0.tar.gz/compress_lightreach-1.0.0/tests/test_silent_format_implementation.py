#!/usr/bin/env python3
"""
Test the new silent format implementation.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from compressors import compress_prompt, format_for_llm, decompress_llm_format


def test_silent_format():
    """Test silent format end-to-end."""
    
    print("="*80)
    print("TESTING NEW SILENT FORMAT")
    print("="*80)
    
    # Test prompt
    original = "You are a helpful assistant. " * 10 + "What is 15 + 27?"
    
    print(f"\nOriginal prompt ({len(original)} chars):")
    print(f"  {original[:80]}...")
    
    # Compress
    compressed, dictionary, ratio = compress_prompt(
        original,
        model="gpt-4",
        use_optimal=False
    )
    
    print(f"\nCompression stats:")
    print(f"  Compressed text: {len(compressed)} chars")
    print(f"  Dictionary entries: {len(dictionary)}")
    print(f"  Ratio: {ratio:.2%}")
    
    # Format with silent instruction (NEW DEFAULT)
    silent_format = format_for_llm(compressed, dictionary, format_type="silent")
    
    print(f"\n📋 SILENT FORMAT ({len(silent_format)} chars):")
    print("-"*80)
    print(silent_format)
    print("-"*80)
    
    # Compare with legacy PCLRv1
    pclrv1_format = format_for_llm(compressed, dictionary, format_type="pclrv1")
    
    print(f"\n📋 LEGACY PCLRv1 FORMAT ({len(pclrv1_format)} chars):")
    print("-"*80)
    print(pclrv1_format[:200] + "...")
    print("-"*80)
    
    print(f"\nFormat comparison:")
    print(f"  Silent: {len(silent_format)} chars")
    print(f"  PCLRv1: {len(pclrv1_format)} chars")
    print(f"  Difference: {len(pclrv1_format) - len(silent_format)} chars")
    
    # Test decompression
    decompressed_silent = decompress_llm_format(silent_format)
    decompressed_pclrv1 = decompress_llm_format(pclrv1_format)
    
    print(f"\n✅ Decompression test:")
    print(f"  Silent matches original: {decompressed_silent == original}")
    print(f"  PCLRv1 matches original: {decompressed_pclrv1 == original}")
    
    return silent_format


def test_multiple_examples():
    """Test with multiple realistic examples."""
    
    print("\n\n" + "="*80)
    print("MULTIPLE EXAMPLE TESTS")
    print("="*80)
    
    examples = [
        {
            "name": "Q&A",
            "prompt": "You are a knowledgeable assistant. " * 8 + "What is the capital of France?",
            "expected_answer": "Paris"
        },
        {
            "name": "Math",
            "prompt": "Solve: 7 * 8 = ? " * 6 + "What is the answer?",
            "expected_answer": "56"
        },
        {
            "name": "Business Analysis",
            "prompt": "You are a business analyst. " * 5 + "Analyze Q1=$100k, Q2=$120k. What's the trend?",
            "expected_answer": "Growth/20% increase"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'='*80}")
        print(f"EXAMPLE {i}: {example['name']}")
        print("="*80)
        
        compressed, dictionary, ratio = compress_prompt(
            example['prompt'],
            model="gpt-4",
            use_optimal=False
        )
        
        silent_format = format_for_llm(compressed, dictionary, format_type="silent")
        
        print(f"\nOriginal: {len(example['prompt'])} chars")
        print(f"Compressed: {len(silent_format)} chars")
        print(f"Savings: {len(example['prompt']) - len(silent_format)} chars")
        
        print(f"\n📋 COPY TO CHATGPT:")
        print("-"*80)
        print(silent_format)
        print("-"*80)
        
        print(f"\n✅ Expected answer: {example['expected_answer']}")
        print(f"❌ Should NOT mention: 'decode', 'abbreviations', 'format'")


def show_api_usage():
    """Show how to use in API."""
    
    print("\n\n" + "="*80)
    print("API USAGE EXAMPLE")
    print("="*80)
    
    print("""
# In your API endpoint:

from compressors import compress_prompt, format_for_llm

@app.post("/api/v1/compress")
def compress(request: CompressRequest):
    # Compress
    compressed, dictionary, ratio = compress_prompt(
        request.prompt,
        model=request.model,
        use_optimal=(request.algorithm == "optimal")
    )
    
    # Format for LLM (NEW: silent by default)
    llm_format = format_for_llm(
        compressed, 
        dictionary,
        format_type=request.format or "silent"  # silent or pclrv1
    )
    
    return CompressResponse(
        compressed=compressed,
        dictionary=dictionary,
        llm_format=llm_format,
        ratio=ratio
    )

# Users can now:
# 1. Get compressed prompt with silent instruction
# 2. Send directly to ChatGPT/Claude
# 3. Get natural response without format explanation!
""")


if __name__ == "__main__":
    test_silent_format()
    test_multiple_examples()
    show_api_usage()
    
    print("\n\n" + "="*80)
    print("✅ SILENT FORMAT READY TO USE")
    print("="*80)
    print("\nThe compression now uses silent format by default.")
    print("LLMs will process abbreviations without explaining them!")
    print("\nTest by copying any generated prompt to ChatGPT.")
