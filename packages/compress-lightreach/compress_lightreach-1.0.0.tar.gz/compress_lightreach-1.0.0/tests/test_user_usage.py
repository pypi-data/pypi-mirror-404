"""
Minimal end-user usage examples for SDK v0.2.0 (messages-first).
"""

import os
from unittest.mock import patch

import pytest

from pcompresslr import LightReach


@patch.dict(os.environ, {"PCOMPRESLR_API_KEY": "test-api-key"})
@patch("pcompresslr.api_client.PcompresslrAPIClient.complete")
def test_user_can_call_complete_with_messages(mock_complete):
    mock_complete.return_value = {
        "decompressed_response": "ok",
        "compression_stats": {},
        "llm_stats": {},
        "warnings": [],
    }

    client = LightReach()
    res = client.complete(
        messages=[
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"},
        ],
        model="gpt-4",
        provider="openai",
        compression_config={"compress_user": True, "compress_only_last_n_user": 1},
    )

    assert res["decompressed_response"] == "ok"


def test_missing_api_key_raises():
    # Ensure env var isn't present in this test
    old = os.environ.pop("PCOMPRESLR_API_KEY", None)
    try:
        with pytest.raises(Exception):
            LightReach(api_key=None)
    finally:
        if old is not None:
            os.environ["PCOMPRESLR_API_KEY"] = old




