"""
Command-line interface for PCompressLR.
"""

import sys
import os
from .api_client import PcompresslrAPIClient, APIKeyError, RateLimitError, APIRequestError


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: pcompresslr <prompt> [--greedy-only|--optimal-only]")
        print("\nExample:")
        print('  pcompresslr "hello world hello world hello world"')
        print('  pcompresslr "your prompt here" --greedy-only  # Only greedy')
        print('  pcompresslr "your prompt here" --optimal-only  # Only optimal')
        print("\nNote: Requires PCOMPRESLR_API_KEY environment variable")
        return
    
    prompt = " ".join(sys.argv[1:])
    show_greedy = True
    show_optimal = True
    
    if prompt.endswith("--greedy-only"):
        prompt = " ".join(sys.argv[1:-1])
        show_optimal = False
    elif prompt.endswith("--optimal-only"):
        prompt = " ".join(sys.argv[1:-1])
        show_greedy = False
    
    # Get API key from environment
    api_key = os.getenv("PCOMPRESLR_API_KEY")
    if not api_key:
        print("❌ Error: PCOMPRESLR_API_KEY environment variable is required.")
        print("\nTo get an API key, visit https://compress.lightreach.io")
        print("Then set it with: export PCOMPRESLR_API_KEY=your-key-here")
        sys.exit(1)
    
    # Initialize API client
    try:
        client = PcompresslrAPIClient(api_key=api_key)
    except APIKeyError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    print(f"Original prompt: {prompt!r}")
    print(f"Length: {len(prompt)} characters\n")
    print("=" * 80)
    
    # Run both compressors and compare
    results = {}
    
    if show_greedy:
        print("\n🔹 GREEDY COMPRESSOR (Fast, ~99% optimal)")
        print("-" * 80)
        try:
            result_greedy = client.compress(
                prompt=prompt,
                model="gpt-4",
                algorithm="greedy"
            )
            
            compressed_greedy = result_greedy["compressed"]
            dict_greedy = result_greedy["dictionary"]
            ratio_greedy = result_greedy["compression_ratio"]
            llm_format_greedy = result_greedy["llm_format"]
            
            # Verify decompression
            decompress_result = client.decompress(llm_format_greedy)
            decompressed_greedy = decompress_result["decompressed"]
            
            results['greedy'] = {
                'compressed': compressed_greedy,
                'dict': dict_greedy,
                'ratio': ratio_greedy,
                'llm_format': llm_format_greedy,
                'decompressed': decompressed_greedy
            }
            
            print(f"Compressed: {compressed_greedy!r}")
            print(f"Dictionary: {dict_greedy}")
            print(f"Compression ratio: {ratio_greedy:.2%}")
            print(f"LLM-ready format length: {len(llm_format_greedy)} chars")
            print(f"Processing time: {result_greedy['processing_time_ms']:.2f}ms")
            if decompressed_greedy == prompt:
                print("✅ Decompression verified")
            else:
                print("❌ Decompression failed")
        except RateLimitError as e:
            print(f"❌ Rate limit exceeded: {e}")
        except APIRequestError as e:
            print(f"❌ API error: {e}")
    
    if show_optimal:
        print("\n🔸 OPTIMAL COMPRESSOR (DP, O(n²), globally optimal)")
        print("-" * 80)
        try:
            result_optimal = client.compress(
                prompt=prompt,
                model="gpt-4",
                algorithm="optimal"
            )
            
            compressed_optimal = result_optimal["compressed"]
            dict_optimal = result_optimal["dictionary"]
            ratio_optimal = result_optimal["compression_ratio"]
            llm_format_optimal = result_optimal["llm_format"]
            
            # Verify decompression
            decompress_result = client.decompress(llm_format_optimal)
            decompressed_optimal = decompress_result["decompressed"]
            
            results['optimal'] = {
                'compressed': compressed_optimal,
                'dict': dict_optimal,
                'ratio': ratio_optimal,
                'llm_format': llm_format_optimal,
                'decompressed': decompressed_optimal
            }
            
            print(f"Compressed: {compressed_optimal!r}")
            print(f"Dictionary: {dict_optimal}")
            print(f"Compression ratio: {ratio_optimal:.2%}")
            print(f"LLM-ready format length: {len(llm_format_optimal)} chars")
            print(f"Processing time: {result_optimal['processing_time_ms']:.2f}ms")
            if decompressed_optimal == prompt:
                print("✅ Decompression verified")
            else:
                print("❌ Decompression failed")
        except RateLimitError as e:
            print(f"❌ Rate limit exceeded: {e}")
        except APIRequestError as e:
            print(f"❌ API error: {e}")
    
    # Comparison if both were run
    if show_greedy and show_optimal and 'greedy' in results and 'optimal' in results:
        print("\n" + "=" * 80)
        print("📊 COMPARISON")
        print("-" * 80)
        ratio_diff = ratio_optimal - ratio_greedy
        if ratio_diff < 0:
            print(f"✅ Optimal is {abs(ratio_diff):.2%} better (smaller ratio)")
        elif ratio_diff > 0:
            print(f"✅ Greedy is {ratio_diff:.2%} better (smaller ratio)")
        else:
            print("✅ Both produce identical compression ratios")
        
        print(f"\nGreedy ratio: {ratio_greedy:.2%}")
        print(f"Optimal ratio: {ratio_optimal:.2%}")
        print(f"Difference: {ratio_diff:+.2%}")
        
        if len(dict_greedy) != len(dict_optimal):
            print(f"\nDictionary size: Greedy={len(dict_greedy)}, Optimal={len(dict_optimal)}")


if __name__ == "__main__":
    main()

