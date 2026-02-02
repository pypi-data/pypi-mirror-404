"""
Test package installation and basic functionality.

This test verifies that:
1. The package can be installed
2. Core dependencies are available
3. The package can be imported
4. Basic compression works
5. CLI entry point is available
6. Optional API dependencies work when installed
"""

import sys
import subprocess
import pytest
from pathlib import Path

# Add current directory (backend) to Python path for compressors tests
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


def test_core_package_imports():
    """Test that compressors module can be imported (backend-only, not in package)."""
    try:
        import compressors
        assert hasattr(compressors, 'compress_prompt')
        assert hasattr(compressors, 'format_for_llm')
        assert hasattr(compressors, 'decompress_llm_format')
        assert hasattr(compressors, 'GreedyCompressor')
        assert hasattr(compressors, 'OptimalCompressor')
    except ImportError as e:
        pytest.fail(f"Failed to import compressors: {e}")


def test_pcompresslr_package_import():
    """Test that pcompresslr package can be imported."""
    try:
        import pcompresslr
        assert hasattr(pcompresslr, '__version__')
        assert hasattr(pcompresslr, 'LightReach')
        assert hasattr(pcompresslr, 'Pcompresslr')  # alias (breaking API vs v0.1.x)
        assert hasattr(pcompresslr, 'Message')
        assert hasattr(pcompresslr, 'CompressionConfig')
        assert hasattr(pcompresslr, 'PcompresslrAPIClient')
        assert hasattr(pcompresslr, 'APIKeyError')
        # Version is defined in pcompresslr._version; keep test resilient to releases.
        from pcompresslr._version import __version__ as expected
        assert pcompresslr.__version__ == expected
    except ImportError:
        pytest.skip("pcompresslr package not installed (run: pip install -e .)")


def test_required_dependency_tiktoken():
    """Test that required dependency tiktoken is available."""
    try:
        import tiktoken
        assert tiktoken is not None
    except ImportError:
        pytest.fail("Required dependency 'tiktoken' is not installed")


def test_basic_compression_functionality():
    """Test that basic compression works (using backend compressors)."""
    from compressors import compress_prompt, format_for_llm, decompress_llm_format
    
    # Simple test prompt with repetition
    prompt = "hello world hello world hello world"
    
    # Test greedy compression
    compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4", use_optimal=False)
    
    assert isinstance(compressed, str)
    assert isinstance(dictionary, dict)
    assert isinstance(ratio, float)
    assert ratio > 0  # Compression ratio should be positive (can be > 1.0 if compression doesn't help)
    
    # Test LLM formatting
    llm_format = format_for_llm(compressed, dictionary)
    assert isinstance(llm_format, str)
    # If dictionary is empty, format_for_llm returns just the compressed string.
    # Otherwise, it should be the robust framed format.
    if dictionary:
        assert llm_format.startswith("PCLRv1|DICT_LEN:")
        assert "|PROMPT_LEN:" in llm_format
    
    # Test decompression
    decompressed = decompress_llm_format(llm_format)
    assert decompressed == prompt, "Decompression should restore original prompt"


def test_optimal_compression_functionality():
    """Test that optimal compression works."""
    from compressors import compress_prompt, format_for_llm, decompress_llm_format
    
    prompt = "test test test test test"
    
    # Test optimal compression
    compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4", use_optimal=True)
    
    assert isinstance(compressed, str)
    assert isinstance(dictionary, dict)
    assert isinstance(ratio, float)
    assert ratio > 0  # Compression ratio should be positive (can be > 1.0 if compression doesn't help)
    
    # Verify decompression
    llm_format = format_for_llm(compressed, dictionary)
    decompressed = decompress_llm_format(llm_format)
    assert decompressed == prompt


def test_compressor_classes():
    """Test that compressor classes can be instantiated and used."""
    from compressors import GreedyCompressor, OptimalCompressor
    
    prompt = "repeat repeat repeat"
    
    # Test GreedyCompressor
    greedy = GreedyCompressor(prompt, model="gpt-4")
    compressed_greedy, dict_greedy = greedy.compress()
    assert isinstance(compressed_greedy, str)
    assert isinstance(dict_greedy, dict)
    
    # Test OptimalCompressor
    optimal = OptimalCompressor(prompt, model="gpt-4")
    compressed_optimal, dict_optimal = optimal.compress()
    assert isinstance(compressed_optimal, str)
    assert isinstance(dict_optimal, dict)


def test_empty_prompt():
    """Test handling of empty prompts."""
    from compressors import compress_prompt, format_for_llm, decompress_llm_format
    
    prompt = ""
    compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4")
    
    assert compressed == ""
    assert dictionary == {}
    assert ratio == 1.0
    
    llm_format = format_for_llm(compressed, dictionary)
    decompressed = decompress_llm_format(llm_format)
    assert decompressed == prompt


def test_no_repetition_prompt():
    """Test prompt with no repetition (should still work)."""
    from compressors import compress_prompt, format_for_llm, decompress_llm_format
    
    prompt = "This is a unique prompt with no repetition at all"
    compressed, dictionary, ratio = compress_prompt(prompt, model="gpt-4")
    
    # Should still return valid results
    assert isinstance(compressed, str)
    assert isinstance(dictionary, dict)
    
    # Decompression should work
    llm_format = format_for_llm(compressed, dictionary)
    decompressed = decompress_llm_format(llm_format)
    assert decompressed == prompt


def test_cli_entry_point_available():
    """Test that CLI entry point is available (if package is installed)."""
    try:
        # Try to import the CLI module
        from pcompresslr.cli import main
        assert callable(main)
    except ImportError:
        pytest.skip("pcompresslr package not installed (run: pip install -e .)")


def test_cli_command_execution():
    """Test that CLI command can be executed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pcompresslr.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # CLI should either show help or usage (exit code 0 or 1 is fine)
        assert result.returncode in [0, 1, 2]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("CLI entry point not available (install package: pip install -e .)")


def test_optional_api_dependencies():
    """Test that optional API dependencies can be imported if installed."""
    try:
        import fastapi
        import uvicorn
        import pydantic
        # If we get here, optional dependencies are installed
        assert True
    except ImportError:
        # This is expected if [api] extras aren't installed
        pytest.skip("Optional API dependencies not installed (install with: pip install pcompresslr[api])")


def test_version_info():
    """Test that version information is accessible."""
    try:
        import pcompresslr
        assert hasattr(pcompresslr, '__version__')
        version = pcompresslr.__version__
        assert isinstance(version, str)
        from pcompresslr._version import __version__ as expected
        assert version == expected
    except ImportError:
        # Try compressors module instead
        import compressors
        # Version might not be in compressors, that's okay
        pass


def test_package_structure():
    """Test that package has correct structure."""
    try:
        import pcompresslr
        # Should have main class and API client
        assert hasattr(pcompresslr, 'LightReach')
        assert hasattr(pcompresslr, 'Pcompresslr')
        assert hasattr(pcompresslr, 'PcompresslrAPIClient')
        assert hasattr(pcompresslr, 'APIKeyError')
        assert hasattr(pcompresslr, 'RateLimitError')
        assert hasattr(pcompresslr, '__version__')
    except ImportError:
        pytest.skip("pcompresslr package not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

