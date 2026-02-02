"""
SDK v0.2.0: output compression flag is forwarded to the API.
"""

import os
from unittest.mock import patch

from pcompresslr import LightReach


@patch.dict(os.environ, {"PCOMPRESLR_API_KEY": "test-api-key"})
@patch("pcompresslr.api_client.PcompresslrAPIClient.complete")
def test_compress_output_forwarded(mock_complete):
    mock_complete.return_value = {
        "decompressed_response": "ok",
        "compression_stats": {},
        "llm_stats": {},
        "warnings": [],
    }

    client = LightReach()
    client.complete(messages=[{"role": "user", "content": "hello"}], compress_output=True)

    _, kwargs = mock_complete.call_args
    assert kwargs["compress_output"] is True




