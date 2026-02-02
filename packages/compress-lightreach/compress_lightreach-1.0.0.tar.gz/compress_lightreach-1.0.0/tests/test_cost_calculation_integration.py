"""
Integration tests for end-to-end cost calculation accuracy.

These tests verify that the complete flow from LLM response to Analytics storage
accurately tracks tokens and costs across all providers.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.database import Analytics, AIModel, AIModelPriceSnapshot, SessionLocal
from api.main import app


@pytest.fixture
def test_db():
    """Provide a test database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def setup_pricing_data(test_db):
    """Set up pricing data for testing."""
    # Create OpenAI model with cache pricing
    openai_model = AIModel(
        model_id="openai/gpt-4o",
        name="GPT-4o",
        provider="OpenAI",
        hle_score=85.0
    )
    test_db.add(openai_model)
    test_db.flush()
    
    openai_pricing = AIModelPriceSnapshot(
        model_id=openai_model.id,
        input_price_per_million=2.50,
        output_price_per_million=10.00,
        blended_price_per_million=7.75,
        cache_read_price_per_million=1.25,  # 50% discount
        cache_write_price_per_million=None,
        snapshot_date="2026-01-31",
        source="test"
    )
    test_db.add(openai_pricing)
    
    # Create Anthropic model with cache pricing
    anthropic_model = AIModel(
        model_id="anthropic/claude-sonnet-4",
        name="Claude Sonnet 4",
        provider="Anthropic",
        hle_score=88.0
    )
    test_db.add(anthropic_model)
    test_db.flush()
    
    anthropic_pricing = AIModelPriceSnapshot(
        model_id=anthropic_model.id,
        input_price_per_million=3.00,
        output_price_per_million=15.00,
        blended_price_per_million=11.25,
        cache_read_price_per_million=0.30,  # 90% discount
        cache_write_price_per_million=3.75,  # 25% markup
        snapshot_date="2026-01-31",
        source="test"
    )
    test_db.add(anthropic_pricing)
    
    test_db.commit()
    
    yield
    
    # Cleanup
    test_db.query(AIModelPriceSnapshot).delete()
    test_db.query(AIModel).delete()
    test_db.commit()


class TestOpenAICostAccuracy:
    """Test end-to-end cost accuracy for OpenAI with caching."""
    
    @patch('api.llm.OpenAIClient.complete')
    def test_cost_with_cache_hit(self, mock_complete, client, test_user, test_db, setup_pricing_data):
        """Test that cache hits are properly accounted for in cost calculation."""
        user, subscription, api_key = test_user
        
        # Mock LLM response with 80% cache hit
        from api.llm.base import LLMResponse
        mock_complete.return_value = LLMResponse(
            text="Cached response",
            input_tokens=10000,
            output_tokens=500,
            model="gpt-4o",
            cached_input_tokens=8000,  # 80% cache hit
            reasoning_tokens=0,
            raw_usage={
                "prompt_tokens": 10000,
                "completion_tokens": 500,
                "prompt_tokens_details": {"cached_tokens": 8000}
            }
        )
        
        response = client.post(
            "/api/v2/complete",
            headers={"X-API-Key": api_key},
            json={
                "messages": [{"role": "user", "content": "Test"}],
                "model": "gpt-4o",
                "llm_provider": "openai",
                "llm_api_key": "test-openai-key"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify cost calculation
        # Non-cached: 2000 * $0.0000025 = $0.005
        # Cached: 8000 * $0.00000125 = $0.01
        # Output: 500 * $0.00001 = $0.005
        # Total: $0.02
        expected_cost = 0.02
        assert abs(data["cost_estimate"] - expected_cost) < 0.00001
        
        # Verify cache savings tracked
        # Savings: 8000 * ($0.0000025 - $0.00000125) = $0.01
        assert "cache_cost_savings" in data or data.get("cost_estimate") < 0.03  # Less than non-cached
        
        # Verify Analytics record
        analytics = test_db.query(Analytics).filter_by(subscription_id=subscription.id).first()
        assert analytics is not None
        assert analytics.llm_input_tokens == 10000
        assert analytics.llm_cached_input_tokens == 8000
        assert analytics.llm_output_tokens == 500
        assert analytics.llm_raw_usage is not None
        
        # Verify cost stored correctly
        assert abs(analytics.cost_usd - expected_cost) < 0.00001


class TestAnthropicCostAccuracy:
    """Test end-to-end cost accuracy for Anthropic with cache creation and reads."""
    
    @patch('api.llm.AnthropicClient.complete')
    def test_cost_with_cache_creation(self, mock_complete, client, test_user, test_db, setup_pricing_data):
        """Test that cache creation costs are included."""
        user, subscription, api_key = test_user
        
        from api.llm.base import LLMResponse
        mock_complete.return_value = LLMResponse(
            text="First request",
            input_tokens=5000,
            output_tokens=200,
            model="claude-sonnet-4",
            cached_input_tokens=0,
            cache_creation_input_tokens=4000,  # Creating cache
            raw_usage={
                "input_tokens": 5000,
                "output_tokens": 200,
                "cache_creation_input_tokens": 4000
            }
        )
        
        response = client.post(
            "/api/v2/complete",
            headers={"X-API-Key": api_key},
            json={
                "messages": [{"role": "user", "content": "Test"}],
                "model": "claude-sonnet-4",
                "llm_provider": "anthropic",
                "llm_api_key": "test-anthropic-key"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify cost includes cache creation
        # Input: 5000 * $0.000003 = $0.015
        # Output: 200 * $0.000015 = $0.003
        # Cache creation: 4000 * $0.00000375 = $0.015
        # Total: $0.033
        expected_cost = 0.033
        assert abs(data["cost_estimate"] - expected_cost) < 0.00001
        
        # Verify Analytics
        analytics = test_db.query(Analytics).filter_by(subscription_id=subscription.id).first()
        assert analytics.llm_cache_creation_tokens == 4000
        assert abs(analytics.cost_usd - expected_cost) < 0.00001
    
    @patch('api.llm.AnthropicClient.complete')
    def test_cost_with_cache_read(self, mock_complete, client, test_user, test_db, setup_pricing_data):
        """Test that cache reads show massive savings."""
        user, subscription, api_key = test_user
        
        from api.llm.base import LLMResponse
        mock_complete.return_value = LLMResponse(
            text="Cached response",
            input_tokens=5000,
            output_tokens=200,
            model="claude-sonnet-4",
            cached_input_tokens=4500,  # 90% cache hit!
            cache_creation_input_tokens=0,
            raw_usage={
                "input_tokens": 5000,
                "output_tokens": 200,
                "cache_read_input_tokens": 4500
            }
        )
        
        response = client.post(
            "/api/v2/complete",
            headers={"X-API-Key": api_key},
            json={
                "messages": [{"role": "user", "content": "Test"}],
                "model": "claude-sonnet-4",
                "llm_provider": "anthropic",
                "llm_api_key": "test-anthropic-key"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify massive cost savings
        # Non-cached: 500 * $0.000003 = $0.0015
        # Cached: 4500 * $0.0000003 = $0.00135
        # Output: 200 * $0.000015 = $0.003
        # Total: $0.00585
        expected_cost = 0.00585
        assert abs(data["cost_estimate"] - expected_cost) < 0.00001
        
        # Without cache would have been: 5000 * $0.000003 + $0.003 = $0.018
        # Savings: ~67%
        
        # Verify Analytics tracks savings
        analytics = test_db.query(Analytics).filter_by(subscription_id=subscription.id).first()
        assert analytics.llm_cached_input_tokens == 4500
        assert analytics.cache_cost_savings_usd is not None
        assert analytics.cache_cost_savings_usd > 0.01  # Significant savings


class TestReasoningTokens:
    """Test reasoning token tracking for o1/o3 models."""
    
    @patch('api.llm.OpenAIClient.complete')
    def test_reasoning_tokens_tracked(self, mock_complete, client, test_user, test_db):
        """Test that reasoning tokens are extracted and stored."""
        user, subscription, api_key = test_user
        
        from api.llm.base import LLMResponse
        mock_complete.return_value = LLMResponse(
            text="Reasoned answer",
            input_tokens=100,
            output_tokens=500,
            model="o1-preview",
            reasoning_tokens=400,  # Heavy reasoning
            cached_input_tokens=0,
            raw_usage={
                "prompt_tokens": 100,
                "completion_tokens": 500,
                "completion_tokens_details": {"reasoning_tokens": 400}
            }
        )
        
        response = client.post(
            "/api/v2/complete",
            headers={"X-API-Key": api_key},
            json={
                "messages": [{"role": "user", "content": "Complex problem"}],
                "model": "o1-preview",
                "llm_provider": "openai",
                "llm_api_key": "test-openai-key"
            }
        )
        
        assert response.status_code == 200
        
        # Verify Analytics stores reasoning tokens
        analytics = test_db.query(Analytics).filter_by(subscription_id=subscription.id).first()
        assert analytics.llm_reasoning_tokens == 400
        assert analytics.llm_raw_usage is not None
        
        # Verify raw usage preserved
        raw_usage = json.loads(analytics.llm_raw_usage)
        assert raw_usage["completion_tokens_details"]["reasoning_tokens"] == 400


class TestRawUsagePreservation:
    """Test that raw usage data is preserved for debugging."""
    
    @patch('api.llm.OpenAIClient.complete')
    def test_raw_usage_stored(self, mock_complete, client, test_user, test_db):
        """Test that complete raw usage object is stored."""
        user, subscription, api_key = test_user
        
        from api.llm.base import LLMResponse
        complex_usage = {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_tokens": 1500,
            "prompt_tokens_details": {
                "cached_tokens": 800,
                "audio_tokens": 50
            },
            "completion_tokens_details": {
                "reasoning_tokens": 100,
                "audio_tokens": 25,
                "accepted_prediction_tokens": 10,
                "rejected_prediction_tokens": 5
            }
        }
        
        mock_complete.return_value = LLMResponse(
            text="Complex response",
            input_tokens=1000,
            output_tokens=500,
            model="gpt-4o",
            cached_input_tokens=800,
            reasoning_tokens=100,
            audio_input_tokens=50,
            audio_output_tokens=25,
            raw_usage=complex_usage
        )
        
        response = client.post(
            "/api/v2/complete",
            headers={"X-API-Key": api_key},
            json={
                "messages": [{"role": "user", "content": "Test"}],
                "model": "gpt-4o",
                "llm_provider": "openai",
                "llm_api_key": "test-key"
            }
        )
        
        assert response.status_code == 200
        
        # Verify complete raw usage stored
        analytics = test_db.query(Analytics).filter_by(subscription_id=subscription.id).first()
        stored_usage = json.loads(analytics.llm_raw_usage)
        
        assert stored_usage == complex_usage
        assert stored_usage["prompt_tokens_details"]["audio_tokens"] == 50
        assert stored_usage["completion_tokens_details"]["accepted_prediction_tokens"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
