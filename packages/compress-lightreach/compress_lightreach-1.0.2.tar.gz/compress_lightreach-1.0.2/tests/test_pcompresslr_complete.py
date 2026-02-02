"""
Tests for SDK v0.2.0 messages-first complete() call.
"""

import os
from unittest.mock import patch

import pytest

from pcompresslr import LightReach


@patch.dict(os.environ, {"PCOMPRESLR_API_KEY": "test-api-key"})
@patch("pcompresslr.api_client.PcompresslrAPIClient.complete")
def test_complete_messages_first_calls_v2(mock_complete):
    mock_complete.return_value = {
        "decompressed_response": "ok",
        "compression_stats": {},
        "llm_stats": {},
        "warnings": [],
    }

    client = LightReach()

    res = client.complete(
        messages=[{"role": "user", "content": "hello"}],
        model="gpt-4",
        provider="openai",
        compression_config={"compress_user": True, "compress_only_last_n_user": 1},
        compress_output=True,
        use_optimal=True,
    )

    assert res["decompressed_response"] == "ok"

    _, kwargs = mock_complete.call_args
    assert kwargs["model"] == "gpt-4"
    assert kwargs["llm_provider"] == "openai"
    assert kwargs["messages"] == [{"role": "user", "content": "hello"}]
    assert kwargs["compression_config"]["compress_user"] is True
    assert kwargs["compress_output"] is True
    assert kwargs["algorithm"] == "optimal"


@patch.dict(os.environ, {"PCOMPRESLR_API_KEY": "test-api-key"})
def test_complete_requires_messages():
    client = LightReach()
    with pytest.raises(TypeError):
        # missing required positional arg
        client.complete()  # type: ignore[misc]




