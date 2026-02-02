"""
Focused tests for cost_estimate / savings_estimate fields on complete endpoints.

Important: We avoid FastAPI TestClient here because starlette.testclient requires httpx.
We call the endpoint function directly.
"""

import asyncio
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

import pytest
from starlette.requests import Request

from api.llm.base import LLMResponse
from api.services.pricing_service import TokenPrices


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_subscription():
    sub = Mock()
    sub.id = 1
    sub.status = "active"
    sub.user_id = None
    sub.plan = Mock()
    sub.plan.allows_greedy = True
    sub.plan.allows_optimal = True
    sub.plan.tokens_per_month = 1000000
    sub.plan.has_full_analytics = False
    sub.billing_cycle_end = Mock()
    sub.billing_cycle_end.date.return_value = "2024-12-31"
    return sub


class TestCompleteCostEstimates:
    @patch("api.routes.complete.get_latest_token_prices")
    @patch("api.routes.complete.OpenAIClient")
    @patch("api.routes.complete.count_tokens_for_compression_stats")
    @patch("api.routes.complete.format_for_llm")
    @patch("api.routes.complete.compress_prompt")
    @patch("api.routes.complete.check_token_limit")
    @patch("api.routes.complete.increment_usage")
    def test_v2_complete_returns_cost_fields(
        self,
        _mock_increment_usage,
        mock_check_token_limit,
        mock_compress,
        mock_format,
        mock_count_tokens_stats,
        mock_openai_client,
        mock_get_prices,
        mock_db,
        mock_subscription,
    ):
        mock_check_token_limit.return_value = (True, 1000)
        mock_count_tokens_stats.return_value = {
            "original_tokens": 20,
            "compressed_tokens": 10,
            "token_savings": 10,
            "compression_ratio": 0.5,
            "token_count_exact": False,
            "token_count_source": "estimated",
        }
        mock_compress.return_value = ("compressed", {"@": "x"}, 0.5)
        mock_format.return_value = "PCLRv1|DICT_LEN:2|{}|PROMPT_LEN:10|compressed"

        mock_llm_response = LLMResponse(
            text="hello",
            input_tokens=10,
            output_tokens=5,
            model="gpt-4",
            finish_reason="stop",
        )
        mock_client_instance = Mock()
        mock_client_instance.complete.return_value = mock_llm_response
        mock_openai_client.return_value = mock_client_instance

        mock_get_prices.return_value = TokenPrices(
            model_id="openai/gpt-4",
            input_price_per_token=Decimal("10") / Decimal("1000000"),
            output_price_per_token=Decimal("30") / Decimal("1000000"),
            snapshot_date_iso="2026-01-01T00:00:00+00:00",
        )

        from api.routes.complete_v2 import complete_v2_endpoint, CompleteRequestV2

        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/v2/complete",
                "headers": [],
            }
        )

        req_model = CompleteRequestV2(
            messages=[{"role": "user", "content": "test prompt"}],
            model="gpt-4",
            llm_provider="openai",
            llm_api_key="sk-test-key",
            compress=True,
            algorithm="greedy",
        )

        res = asyncio.run(
            complete_v2_endpoint(
                request=request,
                complete_request=req_model,
                subscription=mock_subscription,
                db=mock_db,
            )
        )
        data = res.model_dump()

        assert data["model_used"] == "gpt-4"
        assert data["provider_used"] == "openai"
        assert data["was_routed"] is False
        assert data["text"] == data["decompressed_response"]
        assert data["tokens_used"] == 15
        assert data["tokens_saved"] == 10

        # cost_estimate = 10*10e-6 + 5*30e-6 = 0.00025
        assert data["cost_estimate"] == pytest.approx(0.00025, rel=0, abs=1e-6)
        # baseline input tokens = original_tokens=20 → baseline = 20*10e-6 + 5*30e-6 = 0.00035
        # savings = 0.00010
        assert data["savings_estimate"] == pytest.approx(0.00010, rel=0, abs=1e-6)




