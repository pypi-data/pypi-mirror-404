#!/usr/bin/env python3
"""
Test with the instruction ChatGPT itself suggested!
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from compressors import compress_prompt, format_for_llm


def generate_final_tests():
    """Generate tests with the LLM-suggested instruction."""
    
    print("="*80)
    print("CHATGPT'S SUGGESTED INSTRUCTION")
    print("="*80)
    print("\nUsing the exact instruction ChatGPT recommended:")
    print('[Instruction: Respond only with the final answer. No explanation.]')
    print("\n" + "="*80)
    
    tests = [
        {
            "name": "Product Pricing",
            "original": "Item: Apple, Price: $2. " * 4 + "Item: Banana, Price: $1. " * 4 + "What is the price of an Apple?",
            "expected": "$2"
        },
        {
            "name": "Math Problem",
            "original": "Solve: 7 * 8 = ? " * 8 + "What is the answer?",
            "expected": "56"
        },
        {
            "name": "Ages Data",
            "original": "Alice is 30 years old. " * 5 + "Bob is 25 years old. " * 5 + "What is Alice's age?",
            "expected": "30"
        },
        {
            "name": "Simple Calculation",
            "original": "What is 15 + 27? " * 8 + "Answer with just the number.",
            "expected": "42"
        }
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"\n\nTEST {i}: {test['name']}")
        print("="*80)
        
        compressed, dictionary, ratio = compress_prompt(
            test['original'],
            model="gpt-4",
            use_optimal=False
        )
        
        import json
        dict_json = json.dumps(dictionary, separators=(',', ':'))
        
        # Use ChatGPT's suggested format
        final_prompt = f"{dict_json}\n{compressed}\n\n[Instruction: Respond only with the final answer. No explanation.]"
        
        print(f"Original: {len(test['original'])} chars")
        print(f"Compressed: {len(final_prompt)} chars")
        print(f"Savings: {len(test['original']) - len(final_prompt)} chars\n")
        
        print(f"📋 COPY THIS:")
        print("-"*80)
        print(final_prompt)
        print("-"*80)
        
        print(f"\n✅ Expected: Just '{test['expected']}' with NO explanation")
        print(f"❌ If it still explains: Try rewording")


def test_variations():
    """Test slight variations of the instruction."""
    
    print("\n\n" + "="*80)
    print("INSTRUCTION VARIATIONS")
    print("="*80)
    
    original = "Item: Apple, Price: $2. " * 4 + "What is the price?"
    compressed, dictionary, _ = compress_prompt(original, model="gpt-4", use_optimal=False)
    
    import json
    dict_json = json.dumps(dictionary, separators=(',', ':'))
    base = f"{dict_json}\n{compressed}"
    
    variations = [
        "[Instruction: Respond only with the final answer. No explanation.]",
        "[Instruction: Final answer only. No explanation.]",
        "[Instruction: Answer only. No steps.]",
        "[Answer directly. No explanation needed.]",
        "[Just the answer - no explanation.]"
    ]
    
    print("\nTry these variations:\n")
    
    for i, instruction in enumerate(variations, 1):
        print(f"\nVARIATION {i}:")
        print("-"*70)
        print(base + "\n\n" + instruction)
        print()


def test_with_system_context():
    """Test adding context that looks like system instruction."""
    
    print("\n\n" + "="*80)
    print("WITH SYSTEM-LIKE CONTEXT")
    print("="*80)
    
    original = "Solve: 7 * 8 = ? " * 8 + "What is the answer?"
    compressed, dictionary, _ = compress_prompt(original, model="gpt-4", use_optimal=False)
    
    import json
    dict_json = json.dumps(dictionary, separators=(',', ':'))
    
    # Make it look more like a system instruction
    final = f"""[System: Expand abbreviations silently]
{dict_json}
{compressed}

[Instruction: Respond only with the final answer. No explanation.]"""
    
    print(f"\n📋 COPY THIS:")
    print("-"*80)
    print(final)
    print("-"*80)
    
    print(f"\nExpected: '56'")


if __name__ == "__main__":
    generate_final_tests()
    test_variations()
    test_with_system_context()
