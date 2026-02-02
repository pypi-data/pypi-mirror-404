#!/usr/bin/env python3
"""
Test: Append instruction to compressed prompt telling LLM to respond naturally.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from compressors import compress_prompt, format_for_llm


def add_silent_instruction(compressed_format: str, style: str = "simple") -> str:
    """Add instruction to respond naturally."""
    
    instructions = {
        "simple": "\n\n(Expand abbreviations and respond naturally to the question.)",
        
        "direct": "\n\n[Instruction: Replace abbreviations with their values and respond as you normally would.]",
        
        "natural": "\n\n(Note: After expanding the shorthand above, respond to the question as if you received the full text.)",
        
        "minimal": "\n\nRespond naturally after expanding.",
        
        "imperative": "\n\nExpand the abbreviations silently and answer the question.",
        
        "chat": "\n\n(Just answer the question - no need to explain the abbreviations)",
    }
    
    return compressed_format + instructions.get(style, instructions["simple"])


def generate_tests():
    """Generate tests with different instruction styles."""
    
    print("="*80)
    print("EMBEDDED SILENT INSTRUCTIONS")
    print("="*80)
    print("\nThese prompts include instructions to respond naturally.")
    print("Testing different instruction styles.")
    print("\n" + "="*80)
    
    # Test prompt
    original = "Item: Apple, Price: $2. " * 4 + "Item: Banana, Price: $1. " * 4 + "What is the price of an Apple?"
    
    compressed, dictionary, ratio = compress_prompt(
        original,
        model="gpt-4",
        use_optimal=False
    )
    
    # Use simple format without PCLRv1
    import json
    dict_json = json.dumps(dictionary, separators=(',', ':'))
    base_format = f"{dict_json}\n{compressed}"
    
    styles = ["simple", "direct", "natural", "minimal", "imperative", "chat"]
    
    for i, style in enumerate(styles, 1):
        final_prompt = add_silent_instruction(base_format, style)
        
        print(f"\n\nTEST {i}: {style.upper()} style")
        print("="*80)
        
        print(f"\n📋 COPY THIS:")
        print("-"*80)
        print(final_prompt)
        print("-"*80)
        
        print(f"\n✓ Expected: '$2' (no explanation)")
        print(f"✗ If it still explains format → Try next style")


def test_math_with_instruction():
    """Test math problem with instruction."""
    
    print("\n\n" + "="*80)
    print("MATH PROBLEM WITH INSTRUCTION")
    print("="*80)
    
    original = "Solve: 7 * 8 = ? " * 8 + "What is the answer?"
    
    compressed, dictionary, ratio = compress_prompt(
        original,
        model="gpt-4",
        use_optimal=False
    )
    
    import json
    dict_json = json.dumps(dictionary, separators=(',', ':'))
    base_format = f"{dict_json}\n{compressed}"
    
    # Try the most direct instruction
    final = base_format + "\n\n(Expand and answer - don't explain the format)"
    
    print(f"\n📋 COPY THIS:")
    print("-"*80)
    print(final)
    print("-"*80)
    
    print(f"\nExpected: '56' with no explanation of format")


def test_ultra_minimal():
    """Test with ultra-minimal instruction."""
    
    print("\n\n" + "="*80)
    print("ULTRA MINIMAL INSTRUCTION")
    print("="*80)
    
    original = "Alice is 30 years old. " * 5 + "Bob is 25 years old. " * 5 + "What is Alice's age?"
    
    compressed, dictionary, ratio = compress_prompt(
        original,
        model="gpt-4",
        use_optimal=False
    )
    
    import json
    dict_json = json.dumps(dictionary, separators=(',', ':'))
    
    # Just dict + text + minimal note
    final = f"{dict_json}\n{compressed}\n\n(Answer naturally)"
    
    print(f"\n📋 COPY THIS:")
    print("-"*80)
    print(final)
    print("-"*80)
    
    print(f"\nExpected: '30' - plain answer, no format explanation")


def test_different_phrasings():
    """Test various ways to phrase the instruction."""
    
    print("\n\n" + "="*80)
    print("ALTERNATIVE PHRASINGS")
    print("="*80)
    
    original = "Apple: $2. " * 4 + "Banana: $1. " * 4 + "What's the Apple price?"
    
    compressed, dictionary, ratio = compress_prompt(
        original,
        model="gpt-4", 
        use_optimal=False
    )
    
    import json
    dict_json = json.dumps(dictionary, separators=(',', ':'))
    base = f"{dict_json}\n{compressed}"
    
    instructions = [
        "(Answer directly)",
        "(No need to show work)",
        "(Just the answer please)",
        "(Respond as normal)",
        "(Skip explanation)",
    ]
    
    print("\nTry these different instruction phrasings:\n")
    
    for i, inst in enumerate(instructions, 1):
        final = base + "\n\n" + inst
        print(f"{i}. {inst}")
        print("-"*60)
        print(final)
        print()


if __name__ == "__main__":
    generate_tests()
    test_math_with_instruction()
    test_ultra_minimal()
    test_different_phrasings()
