#!/usr/bin/env python3
"""
Test if silent format works for REAL conversational prompts.
Not just simple Q&A - actual user conversations.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from compressors import compress_prompt
import json


def format_silent(compressed: str, dictionary: dict) -> str:
    """Format with silent instruction."""
    if not dictionary:
        return compressed
    
    dict_json = json.dumps(dictionary, separators=(',', ':'))
    return f"{dict_json}\n{compressed}\n\n[Instruction: Respond only with the final answer. No explanation.]"


def test_code_generation():
    """Test with code generation request."""
    
    print("="*80)
    print("TEST 1: CODE GENERATION (Realistic)")
    print("="*80)
    
    original = """You are an expert Python developer. You are an expert Python developer. You are an expert Python developer. You are an expert Python developer. You are an expert Python developer. 

Write a function that takes a list of numbers and returns the sum of all even numbers. Include error handling for empty lists."""
    
    compressed, dictionary, ratio = compress_prompt(original, model="gpt-4", use_optimal=False)
    final = format_silent(compressed, dictionary)
    
    print(f"\nOriginal length: {len(original)} chars")
    print(f"Compressed length: {len(final)} chars")
    print(f"Savings: {len(original) - len(final)} chars\n")
    
    print("📋 COPY THIS:")
    print("-"*80)
    print(final)
    print("-"*80)
    
    print("\n❓ QUESTION: Does ChatGPT just provide the code?")
    print("   Or does it explain 'Let me decode...' first?")
    print("\n⚠️  ISSUE: 'Respond only with final answer' might conflict")
    print("   with code generation (needs explanation usually)")


def test_creative_writing():
    """Test with creative writing request."""
    
    print("\n\n" + "="*80)
    print("TEST 2: CREATIVE WRITING")
    print("="*80)
    
    original = """You are a creative writer. You are a creative writer. You are a creative writer. You are a creative writer. You are a creative writer. You are a creative writer. 

Write a short story about a robot who discovers emotions. Keep it under 100 words."""
    
    compressed, dictionary, ratio = compress_prompt(original, model="gpt-4", use_optimal=False)
    final = format_silent(compressed, dictionary)
    
    print(f"\n📋 COPY THIS:")
    print("-"*80)
    print(final)
    print("-"*80)
    
    print("\n❓ Does it write the story? Or refuse because 'final answer only'?")
    print("   Creative tasks might need different instruction.")


def test_analysis_task():
    """Test with analysis/reasoning task."""
    
    print("\n\n" + "="*80)
    print("TEST 3: ANALYSIS TASK")
    print("="*80)
    
    original = """You are a business analyst. You are a business analyst. You are a business analyst. You are a business analyst. You are a business analyst. 

Analyze this data and provide recommendations:
- Q1 Revenue: $100k
- Q2 Revenue: $120k
- Q3 Revenue: $115k
- Q4 Revenue: $140k

What should the company focus on?"""
    
    compressed, dictionary, ratio = compress_prompt(original, model="gpt-4", use_optimal=False)
    final = format_silent(compressed, dictionary)
    
    print(f"\n📋 COPY THIS:")
    print("-"*80)
    print(final)
    print("-"*80)
    
    print("\n❓ Does it analyze properly? Or just give a one-word answer?")
    print("   'Final answer only' might be too restrictive.")


def test_multi_instruction():
    """Test with multiple instructions."""
    
    print("\n\n" + "="*80)
    print("TEST 4: MULTI-STEP INSTRUCTIONS")
    print("="*80)
    
    original = """You are a helpful assistant. You are a helpful assistant. You are a helpful assistant. You are a helpful assistant. You are a helpful assistant. 

Please do the following:
1. List three benefits of exercise
2. Explain why each is important
3. Provide one example for each"""
    
    compressed, dictionary, ratio = compress_prompt(original, model="gpt-4", use_optimal=False)
    final = format_silent(compressed, dictionary)
    
    print(f"\n📋 COPY THIS:")
    print("-"*80)
    print(final)
    print("-"*80)
    
    print("\n❓ Does it complete all steps?")
    print("   Or think 'final answer' means skip the explanation?")


def test_better_instruction_wording():
    """Test alternative instruction wordings for conversations."""
    
    print("\n\n" + "="*80)
    print("ALTERNATIVE INSTRUCTIONS FOR CONVERSATIONS")
    print("="*80)
    
    print("""
The instruction 'Respond only with the final answer' works for Q&A,
but might be too restrictive for:
- Code generation (needs explanation)
- Creative writing (IS the answer)
- Analysis (needs reasoning)

Better instructions for conversations:
""")
    
    original = """You are a helpful assistant. You are a helpful assistant. You are a helpful assistant. You are a helpful assistant. 

Write a Python function to sort a list."""
    
    compressed, dictionary, _ = compress_prompt(original, model="gpt-4", use_optimal=False)
    dict_json = json.dumps(dictionary, separators=(',', ':'))
    base = f"{dict_json}\n{compressed}"
    
    alternatives = [
        "[Instruction: Respond naturally. No need to explain the abbreviations above.]",
        "[Note: Process abbreviations silently and respond normally.]",
        "[The above uses shorthand - expand it and respond as usual.]",
        "(Expand abbreviations first, then respond naturally to the request.)",
        "[Instruction: Respond to the expanded prompt. Don't mention the abbreviation format.]"
    ]
    
    print("\n🔧 ALTERNATIVE 1: For tasks needing explanation")
    print("-"*80)
    print(base + "\n\n" + alternatives[0])
    print()
    
    print("\n🔧 ALTERNATIVE 2: Most natural")
    print("-"*80)
    print(base + "\n\n" + alternatives[1])
    print()
    
    print("\n🔧 ALTERNATIVE 3: Explicit")
    print("-"*80)
    print(base + "\n\n" + alternatives[2])
    print()
    
    print("\n🔧 ALTERNATIVE 4: Friendly")
    print("-"*80)
    print(base + "\n\n" + alternatives[3])
    print()
    
    print("\n🔧 ALTERNATIVE 5: Balanced")
    print("-"*80)
    print(base + "\n\n" + alternatives[4])
    print()


def test_chat_context():
    """Test in multi-turn conversation context."""
    
    print("\n\n" + "="*80)
    print("TEST: MULTI-TURN CONVERSATION")
    print("="*80)
    
    print("""
Scenario: User has ongoing conversation, wants to use compression
for a long prompt in the middle.

Turn 1 (User): Hi! I need help with Python.
Turn 2 (AI): Sure! What do you need?
Turn 3 (User): [COMPRESSED PROMPT]
Turn 4 (AI): ???

Will the instruction affect future turns?
""")
    
    original = """You are a Python expert. You are a Python expert. You are a Python expert. You are a Python expert. You are a Python expert. 

Explain list comprehensions with 3 examples."""
    
    compressed, dictionary, _ = compress_prompt(original, model="gpt-4", use_optimal=False)
    final = format_silent(compressed, dictionary)
    
    print("📋 COMPRESSED PROMPT FOR TURN 3:")
    print("-"*80)
    print(final)
    print("-"*80)
    
    print("\n❓ Questions:")
    print("   1. Does it respond to THIS message correctly?")
    print("   2. Does [Instruction: ...] affect NEXT messages?")
    print("   3. Should we scope instruction to this turn only?")


def test_recommended_format():
    """Show recommended format for different use cases."""
    
    print("\n\n" + "="*80)
    print("RECOMMENDED FORMATS BY USE CASE")
    print("="*80)
    
    use_cases = {
        "Simple Q&A": {
            "prompt": "Capital of France?",
            "instruction": "[Instruction: Respond only with the final answer. No explanation.]",
            "reason": "User wants just the answer"
        },
        "Code Generation": {
            "prompt": "Write a Python function...",
            "instruction": "[Instruction: Respond naturally. Don't explain the abbreviations.]",
            "reason": "Code needs context/comments"
        },
        "Creative Writing": {
            "prompt": "Write a story about...",
            "instruction": "[Instruction: Expand abbreviations and respond normally.]",
            "reason": "Story IS the answer"
        },
        "Analysis/Reasoning": {
            "prompt": "Analyze this data...",
            "instruction": "[Instruction: Process abbreviations silently, then analyze as requested.]",
            "reason": "Needs full explanation"
        },
        "Multi-step": {
            "prompt": "Do steps 1, 2, 3...",
            "instruction": "[Instruction: Respond to the full request. Don't mention abbreviations.]",
            "reason": "Each step needs completion"
        }
    }
    
    for use_case, details in use_cases.items():
        print(f"\n📝 {use_case}:")
        print(f"   Instruction: {details['instruction']}")
        print(f"   Why: {details['reason']}")


if __name__ == "__main__":
    test_code_generation()
    test_creative_writing()
    test_analysis_task()
    test_multi_instruction()
    test_better_instruction_wording()
    test_chat_context()
    test_recommended_format()
    
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("""
Key Findings to Test:

1. 'Final answer only' works for Q&A but might be too restrictive
2. Need different instructions for different use cases:
   - Q&A: 'final answer only'
   - Code/Writing: 'respond naturally'
   - Analysis: 'expand and respond'

3. In chat context, instruction might affect future turns

Recommendation:
- Make instruction configurable based on task type
- Default: '[Instruction: Respond naturally. Don't explain abbreviations.]'
- This allows full responses while staying silent about format

TEST THESE to find best wording!
""")
