#!/usr/bin/env python3
"""
Test more implicit compression formats that don't scream "I'M COMPRESSED!"
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from compressors import compress_prompt


def format_implicit_v1(compressed: str, dictionary: dict) -> str:
    """
    More natural format - looks like abbreviations/shorthand.
    Format: [Dictionary as natural text]\n\n[Compressed text]
    """
    if not dictionary:
        return compressed
    
    # Make dictionary look like natural abbreviations
    dict_parts = []
    for key, value in dictionary.items():
        dict_parts.append(f"{key}='{value}'")
    
    dict_text = "Abbreviations: " + ", ".join(dict_parts)
    
    return f"{dict_text}\n\n{compressed}"


def format_implicit_v2(compressed: str, dictionary: dict) -> str:
    """
    Even more implicit - inline definitions.
    Format: Let X='...' and Y='...'. [compressed text using X, Y]
    """
    if not dictionary:
        return compressed
    
    dict_parts = []
    for key, value in dictionary.items():
        dict_parts.append(f"{key}='{value}'")
    
    return "Where " + ", ".join(dict_parts) + ": " + compressed


def format_implicit_v3(compressed: str, dictionary: dict) -> str:
    """
    Super minimal - just prefix with definitions.
    """
    if not dictionary:
        return compressed
    
    # Ultra compact
    dict_json = str(dictionary).replace("'", '"')
    return f"[{dict_json}] {compressed}"


def format_no_prefix(compressed: str, dictionary: dict) -> str:
    """
    Just dictionary + text, no metadata.
    """
    if not dictionary:
        return compressed
    
    import json
    dict_json = json.dumps(dictionary, separators=(',', ':'))
    return f"{dict_json}\n{compressed}"


def generate_implicit_tests():
    """Test different implicit formats."""
    
    original = "Item: Apple, Price: $2. " * 4 + "Item: Banana, Price: $1. " * 4 + "What is the price of an Apple?"
    
    compressed, dictionary, ratio = compress_prompt(
        original,
        model="gpt-4",
        use_optimal=False
    )
    
    print("="*80)
    print("IMPLICIT COMPRESSION FORMATS (No PCLRv1 prefix)")
    print("="*80)
    print("\nOriginal prompt:")
    print(f"  {original[:100]}...")
    print(f"\nLength: {len(original)} chars")
    print("\n" + "="*80)
    
    formats = [
        ("Format 1: Abbreviations Style", format_implicit_v1(compressed, dictionary)),
        ("Format 2: Where/Let Style", format_implicit_v2(compressed, dictionary)),
        ("Format 3: Bracketed Dict", format_implicit_v3(compressed, dictionary)),
        ("Format 4: JSON + Text", format_no_prefix(compressed, dictionary)),
    ]
    
    for i, (name, formatted) in enumerate(formats, 1):
        print(f"\n\n{'='*80}")
        print(f"TEST {i}: {name}")
        print("="*80)
        print(f"\nLength: {len(formatted)} chars (vs {len(original)} original)")
        print(f"Savings: {len(original) - len(formatted)} chars")
        
        print(f"\n📋 COPY THIS INTO CHATGPT:")
        print("-"*80)
        print(formatted)
        print("-"*80)
        
        print(f"\nExpected: '$2'")
        print("Goal: LLM should answer naturally without mentioning format")


def test_math_problem():
    """Test with math problem."""
    
    print("\n\n" + "="*80)
    print("MATH PROBLEM TEST")
    print("="*80)
    
    original = "Solve: 7 * 8 = ? " * 8 + "What is the answer?"
    
    compressed, dictionary, ratio = compress_prompt(
        original,
        model="gpt-4",
        use_optimal=False
    )
    
    # Test format 2 (Where style)
    formatted = format_implicit_v2(compressed, dictionary)
    
    print(f"\nOriginal: {original[:80]}...")
    print(f"\n📋 COPY THIS:")
    print("-"*80)
    print(formatted)
    print("-"*80)
    print("\nExpected: '56'")


def analyze_overhead():
    """Analyze overhead of different formats."""
    
    print("\n\n" + "="*80)
    print("FORMAT OVERHEAD ANALYSIS")
    print("="*80)
    
    # Sample dictionary
    dictionary = {"@": ", Price: $", "#": ". Item:"}
    compressed = "Item: Apple@2# Apple@2# Banana@1#"
    
    import json
    
    formats = {
        "PCLRv1 (current)": f"PCLRv1|DICT_LEN:{len(json.dumps(dictionary))}|{json.dumps(dictionary)}|PROMPT_LEN:{len(compressed)}|{compressed}",
        "Abbreviations": format_implicit_v1(compressed, dictionary),
        "Where style": format_implicit_v2(compressed, dictionary),
        "Bracketed": format_implicit_v3(compressed, dictionary),
        "JSON only": format_no_prefix(compressed, dictionary),
    }
    
    print("\nOverhead comparison for same compressed content:")
    print("-"*80)
    
    baseline = len(compressed) + len(json.dumps(dictionary))
    
    for name, formatted in formats.items():
        overhead = len(formatted) - baseline
        print(f"{name:20s}: {len(formatted):3d} chars (+{overhead:2d} overhead)")
    
    print("-"*80)
    print(f"Compressed content: {baseline} chars")
    print("\nConclusion: PCLRv1 prefix adds 30-40 chars of pure overhead!")


if __name__ == "__main__":
    generate_implicit_tests()
    test_math_problem()
    analyze_overhead()
