#!/usr/bin/env python3
"""
Test: Can LLMs understand compressed text WITHOUT a dictionary?
(Using only context clues)
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


def test_no_dictionary():
    """Test if LLM can figure it out from context alone."""
    
    print("="*80)
    print("RADICAL TEST: NO DICTIONARY")
    print("="*80)
    print("\nCan LLMs understand compressed text from context alone?")
    print("No legend, no abbreviations note, no dictionary.")
    print("\n" + "="*80)
    
    tests = [
        {
            "name": "Obvious Repetition",
            "prompt": "The capital of France is Paris. " * 5 + "What is the capital of France?",
            "compressed": "The capital of France is Paris. (repeated 5x) What is the capital of France?",
            "expected": "Paris"
        },
        {
            "name": "Clear Pattern",
            "prompt": "Alice: age 30, score 95. Bob: age 25, score 87. What is Alice's score?",
            "expected": "95"
        },
        {
            "name": "Natural Abbreviation",
            "prompt": "Apple: $2, Banana: $1, Orange: $3. Apple: $2, Banana: $1. What's the price of an Apple?",
            "expected": "$2"
        }
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"\n\nTEST {i}: {test['name']}")
        print("="*80)
        
        if 'compressed' in test:
            prompt = test['compressed']
        else:
            prompt = test['prompt']
        
        print(f"\n📋 COPY THIS (NO DICTIONARY):")
        print("-"*80)
        print(prompt)
        print("-"*80)
        
        print(f"\nExpected: '{test['expected']}'")
        print("Question: Does LLM answer naturally without explaining anything?")


def test_inline_expansion():
    """Test inline expansion style."""
    
    print("\n\n" + "="*80)
    print("ALTERNATIVE: INLINE FIRST OCCURRENCE")
    print("="*80)
    print("\nDefine abbreviations by using full form first, then abbreviated.")
    
    test = """Alice (A) is 30 years old. Bob (B) is 25 years old. A lives in NYC. B lives in LA. What is A's age?"""
    
    print(f"\n📋 COPY THIS:")
    print("-"*80)
    print(test)
    print("-"*80)
    print("\nExpected: '30'")
    print("LLM should understand A=Alice, B=Bob from context")


def reality_check():
    """Reality check: Maybe we need to decompress server-side."""
    
    print("\n\n" + "="*80)
    print("REALITY CHECK")
    print("="*80)
    
    print("""
The Problem:
- Show dictionary → LLM explains decompression
- No dictionary → LLM might not understand
- Any explicit format → LLM mentions it

Possible Solutions:

1. ACCEPT IT: Let LLM explain (users might not care)
   Pros: Works, accurate
   Cons: Wastes some tokens on explanation

2. DECOMPRESS SERVER-SIDE: We expand before sending to LLM
   Pros: LLM never sees compressed format
   Cons: Doesn't save tokens in LLM API call (only in storage/transmission)

3. USE SYSTEM PROMPTS: For providers that support it
   Pros: Can instruct silence
   Cons: Doesn't work everywhere, conflicts with user prompts

4. NATURAL ABBREVIATIONS: No dictionary, rely on context
   Pros: Looks natural
   Cons: Unreliable, might not work

5. HYBRID: Compress for storage, decompress for LLM calls
   Pros: Best of both worlds
   Cons: Doesn't reduce LLM API costs

Which approach does the USER actually want?
- Reduce storage? → Compress, decompress before API call
- Reduce API tokens? → Need LLM to understand compression silently
- Both? → Need format that LLMs process transparently (hard!)
""")


def generate_natural_test():
    """Generate most natural-looking test."""
    
    print("\n\n" + "="*80)
    print("MOST NATURAL FORMAT")
    print("="*80)
    
    test = """Given: x='Hello', y='World'

Output: x y x y x y

What did I output?"""
    
    print(f"\n📋 COPY THIS:")
    print("-"*80)
    print(test)
    print("-"*80)
    
    print("\nExpected: 'Hello World Hello World Hello World'")
    print("This looks like normal variable substitution")


if __name__ == "__main__":
    test_no_dictionary()
    test_inline_expansion()
    generate_natural_test()
    reality_check()
