"""
Comprehensive tests for detailed token tracking across LLM providers.

These tests ensure accurate token extraction and cost calculation across all providers,
including cache hits, reasoning tokens, and other provider-specific features.
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
import json

from api.llm import OpenAIClient, AnthropicClient, GoogleGeminiClient
from api.llm.base import LLMResponse
from api.services.pricing_service import TokenPrices, calculate_detailed_cost, DetailedCostBreakdown


class TestOpenAITokenExtraction:
    """Test OpenAI client token extraction including cache and reasoning tokens."""
    
    def test_basic_token_extraction(self):
        """Test basic token extraction without cache or reasoning."""
        client = OpenAIClient()
        
        mock_response = {
            "id": "chatcmpl-123",
            "model": "gpt-4o",
            "created": 1234567890,
            "choices": [{
                "message": {"content": "Hello, world!", "role": "assistant"},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = mock_response
            
            response = client.complete(
                prompt="Test",
                model="gpt-4o",
                api_key="test-key"
            )
            
            assert response.input_tokens == 10
            assert response.output_tokens == 5
            assert response.cached_input_tokens == 0
            assert response.reasoning_tokens == 0
            assert response.raw_usage == mock_response["usage"]
    
    def test_cached_tokens_extraction(self):
        """Test extraction of cached tokens (prompt caching)."""
        client = OpenAIClient()
        
        mock_response = {
            "id": "chatcmpl-456",
            "model": "gpt-4o",
            "created": 1234567890,
            "choices": [{
                "message": {"content": "Cached response", "role": "assistant"},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 1000,
                "completion_tokens": 50,
                "total_tokens": 1050,
                "prompt_tokens_details": {
                    "cached_tokens": 800,
                    "audio_tokens": 0
                },
                "completion_tokens_details": {
                    "reasoning_tokens": 0,
                    "audio_tokens": 0
                }
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = mock_response
            
            response = client.complete(
                prompt="Test",
                model="gpt-4o",
                api_key="test-key"
            )
            
            assert response.input_tokens == 1000
            assert response.output_tokens == 50
            assert response.cached_input_tokens == 800
            assert response.reasoning_tokens == 0
    
    def test_reasoning_tokens_extraction(self):
        """Test extraction of reasoning tokens (o1/o3 models)."""
        client = OpenAIClient()
        
        mock_response = {
            "id": "chatcmpl-789",
            "model": "o1-preview",
            "created": 1234567890,
            "choices": [{
                "message": {"content": "Reasoned answer", "role": "assistant"},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 500,
                "total_tokens": 600,
                "prompt_tokens_details": {
                    "cached_tokens": 0,
                    "audio_tokens": 0
                },
                "completion_tokens_details": {
                    "reasoning_tokens": 400,
                    "audio_tokens": 0
                }
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = mock_response
            
            response = client.complete(
                prompt="Test",
                model="o1-preview",
                api_key="test-key"
            )
            
            assert response.input_tokens == 100
            assert response.output_tokens == 500
            assert response.reasoning_tokens == 400
            assert response.cached_input_tokens == 0


class TestAnthropicTokenExtraction:
    """Test Anthropic client token extraction including cache reads and writes."""
    
    def test_cache_read_extraction(self):
        """Test extraction of Anthropic cache read tokens."""
        client = AnthropicClient()
        
        mock_response = {
            "id": "msg-123",
            "model": "claude-sonnet-4",
            "content": [{"type": "text", "text": "Cached response"}],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 2000,
                "output_tokens": 100,
                "cache_read_input_tokens": 1500,
                "cache_creation_input_tokens": 0
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = mock_response
            
            response = client.complete(
                prompt="Test",
                model="claude-sonnet-4",
                api_key="test-key"
            )
            
            assert response.input_tokens == 2000
            assert response.output_tokens == 100
            assert response.cached_input_tokens == 1500
            assert response.cache_creation_input_tokens == 0
    
    def test_cache_creation_extraction(self):
        """Test extraction of Anthropic cache creation tokens."""
        client = AnthropicClient()
        
        mock_response = {
            "id": "msg-456",
            "model": "claude-sonnet-4",
            "content": [{"type": "text", "text": "First request"}],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 3000,
                "output_tokens": 150,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 2500
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = mock_response
            
            response = client.complete(
                prompt="Test",
                model="claude-sonnet-4",
                api_key="test-key"
            )
            
            assert response.input_tokens == 3000
            assert response.output_tokens == 150
            assert response.cached_input_tokens == 0
            assert response.cache_creation_input_tokens == 2500


class TestGoogleTokenExtraction:
    """Test Google Gemini client token extraction including cache."""
    
    def test_cached_content_extraction(self):
        """Test extraction of Google cached content tokens."""
        client = GoogleGeminiClient()
        
        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Response from Gemini"}]
                },
                "finishReason": "STOP"
            }],
            "usageMetadata": {
                "promptTokenCount": 500,
                "candidatesTokenCount": 50,
                "totalTokenCount": 550,
                "cachedContentTokenCount": 400
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = mock_response
            
            response = client.complete(
                prompt="Test",
                model="gemini-2.0-flash",
                api_key="test-key"
            )
            
            assert response.input_tokens == 500
            assert response.output_tokens == 50
            assert response.cached_input_tokens == 400


class TestDetailedCostCalculation:
    """Test accurate cost calculation with cache awareness."""
    
    def test_basic_cost_no_cache(self):
        """Test basic cost calculation without cache."""
        prices = TokenPrices(
            model_id="openai/gpt-4o",
            input_price_per_token=Decimal("0.0000025"),
            output_price_per_token=Decimal("0.00001"),
        )
        
        breakdown = calculate_detailed_cost(
            input_tokens=1000,
            output_tokens=500,
            prices=prices
        )
        
        # 1000 * 0.0000025 + 500 * 0.00001 = 0.0025 + 0.005 = 0.0075
        assert breakdown.total_cost == Decimal("0.0075")
        assert breakdown.cache_savings == Decimal("0")
    
    def test_cost_with_cache_savings(self):
        """Test cost calculation with cache hits showing savings."""
        prices = TokenPrices(
            model_id="openai/gpt-4o",
            input_price_per_token=Decimal("0.0000025"),
            output_price_per_token=Decimal("0.00001"),
            cache_read_price_per_token=Decimal("0.00000125"),  # 50% discount
        )
        
        breakdown = calculate_detailed_cost(
            input_tokens=1000,
            output_tokens=500,
            cached_input_tokens=800,
            prices=prices
        )
        
        # Non-cached: (1000 - 800) = 200 * 0.0000025 = 0.0005
        # Cached: 800 * 0.00000125 = 0.001
        # Output: 500 * 0.00001 = 0.005
        # Total: 0.0065
        assert breakdown.total_cost == Decimal("0.0065")
        
        # Savings: 800 * (0.0000025 - 0.00000125) = 800 * 0.00000125 = 0.001
        assert breakdown.cache_savings == Decimal("0.001")
    
    def test_anthropic_cache_creation_cost(self):
        """Test Anthropic cache creation adds to cost."""
        prices = TokenPrices(
            model_id="anthropic/claude-sonnet-4",
            input_price_per_token=Decimal("0.000003"),
            output_price_per_token=Decimal("0.000015"),
            cache_read_price_per_token=Decimal("0.0000003"),  # 90% discount
            cache_write_price_per_token=Decimal("0.00000375"),  # 25% markup
        )
        
        breakdown = calculate_detailed_cost(
            input_tokens=3000,
            output_tokens=150,
            cache_creation_tokens=2500,
            prices=prices
        )
        
        # Input: 3000 * 0.000003 = 0.009
        # Output: 150 * 0.000015 = 0.00225
        # Cache creation: 2500 * 0.00000375 = 0.009375
        # Total: 0.020625
        expected = Decimal("0.009") + Decimal("0.00225") + Decimal("0.009375")
        assert breakdown.total_cost == expected
    
    def test_massive_cache_savings(self):
        """Test realistic scenario with large cache hit."""
        prices = TokenPrices(
            model_id="anthropic/claude-sonnet-4",
            input_price_per_token=Decimal("0.000003"),
            output_price_per_token=Decimal("0.000015"),
            cache_read_price_per_token=Decimal("0.0000003"),  # 90% discount
        )
        
        breakdown = calculate_detailed_cost(
            input_tokens=50000,
            output_tokens=1000,
            cached_input_tokens=45000,  # 90% cache hit!
            prices=prices
        )
        
        # Non-cached: 5000 * 0.000003 = 0.015
        # Cached: 45000 * 0.0000003 = 0.0135
        # Output: 1000 * 0.000015 = 0.015
        # Total: 0.0435
        expected = Decimal("0.015") + Decimal("0.0135") + Decimal("0.015")
        assert breakdown.total_cost == expected
        
        # Savings: 45000 * (0.000003 - 0.0000003) = 45000 * 0.0000027 = 0.1215
        expected_savings = Decimal("45000") * (Decimal("0.000003") - Decimal("0.0000003"))
        assert breakdown.cache_savings == expected_savings
        
        # Verify massive savings percentage
        would_have_paid = Decimal("50000") * Decimal("0.000003") + Decimal("0.015")
        savings_percent = (expected_savings / would_have_paid) * 100
        assert savings_percent > 70  # Over 70% savings!


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_missing_token_details_graceful_degradation(self):
        """Test that missing token details don't break extraction."""
        client = OpenAIClient()
        
        # Old-style response without detailed token info
        mock_response = {
            "id": "chatcmpl-old",
            "model": "gpt-3.5-turbo",
            "created": 1234567890,
            "choices": [{
                "message": {"content": "Basic response", "role": "assistant"},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 10,
                "total_tokens": 30
                # No prompt_tokens_details or completion_tokens_details
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = mock_response
            
            response = client.complete(
                prompt="Test",
                model="gpt-3.5-turbo",
                api_key="test-key"
            )
            
            # Should extract basic tokens and default detailed tokens to 0
            assert response.input_tokens == 20
            assert response.output_tokens == 10
            assert response.cached_input_tokens == 0
            assert response.reasoning_tokens == 0
    
    def test_cost_without_cache_pricing(self):
        """Test cost calculation when cache pricing not available."""
        prices = TokenPrices(
            model_id="some-model",
            input_price_per_token=Decimal("0.000001"),
            output_price_per_token=Decimal("0.000002"),
            # No cache pricing
        )
        
        # Should fall back to standard input pricing for cached tokens
        breakdown = calculate_detailed_cost(
            input_tokens=1000,
            output_tokens=500,
            cached_input_tokens=500,
            prices=prices
        )
        
        # All input charged at standard rate when cache price not available
        # Input: 1000 * 0.000001 = 0.001
        # Output: 500 * 0.000002 = 0.001
        # Total: 0.002
        assert breakdown.total_cost == Decimal("0.002")
        assert breakdown.cache_savings == Decimal("0")  # No savings without cache pricing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
