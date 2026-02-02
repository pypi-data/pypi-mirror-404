"""
Tests for the complete endpoint.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from api.main import app
from api.database import get_db
from api.auth import get_authenticated_subscription
from api.llm.base import LLMResponse, LLMAPIKeyError, LLMRateLimitError, LLMRequestError


def _override_auth_and_db(subscription, db):
    async def _sub_override():
        return subscription

    def _db_override():
        yield db

    app.dependency_overrides[get_authenticated_subscription] = _sub_override
    app.dependency_overrides[get_db] = _db_override


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    return db


@pytest.fixture
def mock_api_key():
    """Mock API key record."""
    api_key = Mock()
    api_key.id = 1
    api_key.subscription = Mock()
    api_key.subscription.id = 1
    api_key.subscription.status = "active"
    api_key.subscription.user_id = None
    api_key.subscription.plan = Mock()
    api_key.subscription.plan.allows_greedy = True
    api_key.subscription.plan.allows_optimal = True
    api_key.subscription.plan.tokens_per_month = 1000000
    api_key.subscription.plan.has_full_analytics = False
    api_key.subscription.billing_cycle_end = Mock()
    api_key.subscription.billing_cycle_end.date.return_value = "2024-12-31"
    return api_key


class TestCompleteEndpoint:
    """Test complete endpoint."""
    
    @patch('api.token_utils.count_tokens_with_metadata')
    @patch('api.routes.complete.count_tokens_for_compression_stats')
    @patch('api.routes.complete.OpenAIClient')
    @patch('api.routes.complete.compress_prompt')
    @patch('api.routes.complete.format_for_llm')
    @patch('api.routes.complete.decompress_llm_format')
    @patch('api.routes.complete.check_token_limit')
    @patch('api.routes.complete.increment_usage')
    def test_complete_with_openai(
        self,
        mock_increment_usage,
        mock_check_token_limit,
        mock_decompress,
        mock_format,
        mock_compress,
        mock_openai_client,
        mock_count_tokens_stats,
        mock_count_tokens_meta,
        client,
        mock_db,
        mock_api_key
    ):
        """Test complete endpoint with OpenAI."""
        # Setup mocks
        _override_auth_and_db(mock_api_key.subscription, mock_db)
        mock_check_token_limit.return_value = (True, 1000)
        mock_count_tokens_stats.return_value = {
            "original_tokens": 10,
            "compressed_tokens": 5,
            "token_savings": 5,
            "token_count_exact": False,
            "token_count_source": "estimated",
        }
        mock_count_tokens_meta.return_value = Mock(tokens=10, exact=False, source="estimated")
        
        # Mock compression
        mock_compress.return_value = ("compressed", {"@": "test"}, 0.8)
        mock_format.return_value = "PCLRv1|DICT_LEN:12|{\"@\":\"test\"}|PROMPT_LEN:10|compressed"
        
        # Mock LLM response
        mock_llm_response = LLMResponse(
            text="This is a test response",
            input_tokens=10,
            output_tokens=5,
            model="gpt-4",
            finish_reason="stop"
        )
        mock_client_instance = Mock()
        mock_client_instance.complete.return_value = mock_llm_response
        mock_openai_client.return_value = mock_client_instance
        
        # Make request
        try:
            response = client.post(
                "/api/v1/complete",
                json={
                    "prompt": "test prompt",
                    "model": "gpt-4",
                    "llm_provider": "openai",
                    "llm_api_key": "sk-test-key",
                    "compress": True,
                    "compress_output": False,
                },
                headers={"X-API-Key": "test-api-key"}
            )
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert "decompressed_response" in data
        assert data["decompressed_response"] == "This is a test response"
        assert "compression_stats" in data
        assert "llm_stats" in data
        assert data["llm_stats"]["provider"] == "openai"
        assert data["llm_stats"]["model"] == "gpt-4"
    
    @patch('api.token_utils.count_tokens_with_metadata')
    @patch('api.routes.complete.count_tokens_for_compression_stats')
    @patch('api.routes.complete.AnthropicClient')
    @patch('api.routes.complete.compress_prompt')
    @patch('api.routes.complete.format_for_llm')
    @patch('api.routes.complete.check_token_limit')
    @patch('api.routes.complete.increment_usage')
    def test_complete_with_anthropic(
        self,
        mock_increment_usage,
        mock_check_token_limit,
        mock_format,
        mock_compress,
        mock_anthropic_client,
        mock_count_tokens_stats,
        mock_count_tokens_meta,
        client,
        mock_db,
        mock_api_key
    ):
        """Test complete endpoint with Anthropic."""
        # Setup mocks
        _override_auth_and_db(mock_api_key.subscription, mock_db)
        mock_check_token_limit.return_value = (True, 1000)
        mock_count_tokens_stats.return_value = {
            "original_tokens": 10,
            "compressed_tokens": 5,
            "token_savings": 5,
            "token_count_exact": False,
            "token_count_source": "estimated",
        }
        mock_count_tokens_meta.return_value = Mock(tokens=10, exact=False, source="estimated")
        
        # Mock compression
        mock_compress.return_value = ("compressed", {"@": "test"}, 0.8)
        mock_format.return_value = "PCLRv1|DICT_LEN:12|{\"@\":\"test\"}|PROMPT_LEN:10|compressed"
        
        # Mock LLM response
        mock_llm_response = LLMResponse(
            text="This is a Claude response",
            input_tokens=10,
            output_tokens=5,
            model="claude-3-opus-20240229",
            finish_reason="end_turn"
        )
        mock_client_instance = Mock()
        mock_client_instance.complete.return_value = mock_llm_response
        mock_anthropic_client.return_value = mock_client_instance
        
        # Make request
        try:
            response = client.post(
                "/api/v1/complete",
                json={
                    "prompt": "test prompt",
                    "model": "claude-3-opus",
                    "llm_provider": "anthropic",
                    "llm_api_key": "sk-ant-test-key",
                    "compress": True,
                    "compress_output": False,
                },
                headers={"X-API-Key": "test-api-key"}
            )
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert data["decompressed_response"] == "This is a Claude response"
        assert data["llm_stats"]["provider"] == "anthropic"

    @patch('api.token_utils.count_tokens_with_metadata')
    @patch('api.routes.complete.count_tokens_for_compression_stats')
    @patch('api.routes.complete.AnthropicClient')
    @patch('api.routes.complete.compress_prompt')
    @patch('api.routes.complete.format_for_llm')
    @patch('api.routes.complete.check_token_limit')
    @patch('api.routes.complete.increment_usage')
    def test_anthropic_translation_system_is_top_level(
        self,
        mock_increment_usage,
        mock_check_token_limit,
        mock_format,
        mock_compress,
        mock_anthropic_client,
        mock_count_tokens_stats,
        mock_count_tokens_meta,
        client,
        mock_db,
        mock_api_key
    ):
        """
        Feature 0.5: when targeting Anthropic, system messages should become top-level `system`,
        and `messages` should exclude `system` roles.
        """
        _override_auth_and_db(mock_api_key.subscription, mock_db)
        mock_check_token_limit.return_value = (True, 1000)
        mock_count_tokens_stats.return_value = {
            "original_tokens": 10,
            "compressed_tokens": 5,
            "token_savings": 5,
            "token_count_exact": False,
            "token_count_source": "estimated",
        }
        mock_count_tokens_meta.return_value = Mock(tokens=10, exact=False, source="estimated")
        mock_compress.return_value = ("compressed", {"@": "x"}, 0.8)
        mock_format.return_value = "PCLRv1|DICT_LEN:10|{\"@\":\"x\"}|PROMPT_LEN:10|compressed"

        mock_llm_response = LLMResponse(
            text="ok",
            input_tokens=10,
            output_tokens=5,
            model="claude-3-opus-20240229",
            finish_reason="end_turn",
        )
        mock_client_instance = Mock()
        mock_client_instance.complete.return_value = mock_llm_response
        mock_anthropic_client.return_value = mock_client_instance

        try:
            response = client.post(
                "/api/v1/complete",
                json={
                    "messages": [
                        {"role": "system", "content": "sys rules"},
                        {"role": "user", "content": "hello"},
                    ],
                    "model": "claude-3-opus",
                    "llm_provider": "anthropic",
                    "llm_api_key": "sk-ant-test-key",
                    "compress": True,
                },
                headers={"X-API-Key": "test-api-key"},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        # Ensure system passed separately and messages contain only user/assistant
        call = mock_client_instance.complete.call_args
        assert call is not None
        kwargs = call.kwargs
        assert kwargs.get("system_prompt") == "sys rules"
        assert kwargs.get("messages") == [
            {"role": "user", "content": "PCLRv1|DICT_LEN:10|{\"@\":\"x\"}|PROMPT_LEN:10|compressed"}
        ]
    
    @patch('api.routes.complete.OpenAIClient')
    def test_complete_with_invalid_llm_key(
        self,
        mock_openai_client,
        client,
        mock_db,
        mock_api_key
    ):
        """Test complete endpoint with invalid LLM API key."""
        # Setup mocks
        _override_auth_and_db(mock_api_key.subscription, mock_db)
        
        # Mock LLM client to raise API key error
        mock_client_instance = Mock()
        mock_client_instance.complete.side_effect = LLMAPIKeyError("Invalid API key")
        mock_openai_client.return_value = mock_client_instance
        
        # Make request
        try:
            response = client.post(
                "/api/v1/complete",
                json={
                    "prompt": "test prompt",
                    "model": "gpt-4",
                    "llm_provider": "openai",
                    "llm_api_key": "invalid-key",
                    "compress": False,
                },
                headers={"X-API-Key": "test-api-key"}
            )
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]
    
    @patch('api.routes.complete.OpenAIClient')
    def test_complete_with_rate_limit(
        self,
        mock_openai_client,
        client,
        mock_db,
        mock_api_key
    ):
        """Test complete endpoint with rate limit error."""
        # Setup mocks
        _override_auth_and_db(mock_api_key.subscription, mock_db)
        
        # Mock LLM client to raise rate limit error
        mock_client_instance = Mock()
        mock_client_instance.complete.side_effect = LLMRateLimitError("Rate limit exceeded")
        mock_openai_client.return_value = mock_client_instance
        
        # Make request
        try:
            response = client.post(
                "/api/v1/complete",
                json={
                    "prompt": "test prompt",
                    "model": "gpt-4",
                    "llm_provider": "openai",
                    "llm_api_key": "sk-test-key",
                    "compress": False,
                },
                headers={"X-API-Key": "test-api-key"}
            )
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == 429
    
    @patch('api.token_utils.count_tokens_with_metadata')
    @patch('api.routes.complete.count_tokens_for_compression_stats')
    @patch('api.routes.complete.OpenAIClient')
    @patch('api.routes.complete.compress_prompt')
    @patch('api.routes.complete.format_for_llm')
    @patch('api.routes.complete.decompress_llm_format')
    @patch('api.routes.complete.check_token_limit')
    @patch('api.routes.complete.increment_usage')
    def test_complete_with_output_compression(
        self,
        mock_increment_usage,
        mock_check_token_limit,
        mock_decompress,
        mock_format,
        mock_compress,
        mock_openai_client,
        mock_count_tokens_stats,
        mock_count_tokens_meta,
        client,
        mock_db,
        mock_api_key
    ):
        """Test complete endpoint with output compression."""
        # Setup mocks
        _override_auth_and_db(mock_api_key.subscription, mock_db)
        mock_check_token_limit.return_value = (True, 1000)
        mock_count_tokens_stats.return_value = {
            "original_tokens": 10,
            "compressed_tokens": 5,
            "token_savings": 5,
            "token_count_exact": False,
            "token_count_source": "estimated",
        }
        mock_count_tokens_meta.return_value = Mock(tokens=10, exact=False, source="estimated")
        
        # Mock compression
        mock_compress.return_value = ("compressed", {"@": "test"}, 0.8)
        mock_format.return_value = "PCLRv1|DICT_LEN:12|{\"@\":\"test\"}|PROMPT_LEN:10|compressed"
        
        # Mock LLM response (compressed format)
        mock_llm_response = LLMResponse(
            text="PCLRv1|DICT_LEN:16|{\"@\":\"response\"}|PROMPT_LEN:15|compressed text",
            input_tokens=10,
            output_tokens=5,
            model="gpt-4",
            finish_reason="stop"
        )
        mock_client_instance = Mock()
        mock_client_instance.complete.return_value = mock_llm_response
        mock_openai_client.return_value = mock_client_instance
        
        # Mock decompression
        mock_decompress.return_value = "This is the decompressed response"
        
        # Make request
        try:
            response = client.post(
                "/api/v1/complete",
                json={
                    "prompt": "test prompt",
                    "model": "gpt-4",
                    "llm_provider": "openai",
                    "llm_api_key": "sk-test-key",
                    "compress": True,
                    "compress_output": True,
                },
                headers={"X-API-Key": "test-api-key"}
            )
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert data["decompressed_response"] == "This is the decompressed response"
        mock_decompress.assert_called_once()
    
    @patch('api.token_utils.count_tokens_with_metadata')
    @patch('api.routes.complete.OpenAIClient')
    def test_complete_without_compression(
        self,
        mock_openai_client,
        mock_count_tokens_meta,
        client,
        mock_db,
        mock_api_key
    ):
        """Test complete endpoint without compression."""
        # Setup mocks
        _override_auth_and_db(mock_api_key.subscription, mock_db)
        mock_count_tokens_meta.return_value = Mock(tokens=10, exact=False, source="estimated")
        
        # Mock LLM response
        mock_llm_response = LLMResponse(
            text="Direct response",
            input_tokens=10,
            output_tokens=5,
            model="gpt-4",
            finish_reason="stop"
        )
        mock_client_instance = Mock()
        mock_client_instance.complete.return_value = mock_llm_response
        mock_openai_client.return_value = mock_client_instance
        
        # Make request
        try:
            response = client.post(
                "/api/v1/complete",
                json={
                    "prompt": "test prompt",
                    "model": "gpt-4",
                    "llm_provider": "openai",
                    "llm_api_key": "sk-test-key",
                    "compress": False,
                },
                headers={"X-API-Key": "test-api-key"}
            )
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert data["decompressed_response"] == "Direct response"
        assert data["compression_stats"]["compression_enabled"] is False

    @patch('api.token_utils.count_tokens_with_metadata')
    @patch('api.routes.complete.count_tokens_for_compression_stats')
    @patch('api.routes.complete.OpenAIClient')
    @patch('api.routes.complete.compress_prompt')
    @patch('api.routes.complete.format_for_llm')
    @patch('api.routes.complete.check_token_limit')
    @patch('api.routes.complete.increment_usage')
    def test_complete_with_messages_only_last_user_compressed(
        self,
        mock_increment_usage,
        mock_check_token_limit,
        mock_format,
        mock_compress,
        mock_openai_client,
        mock_count_tokens_stats,
        mock_count_tokens_meta,
        client,
        mock_db,
        mock_api_key,
    ):
        """
        Feature 0.5 default: only compress the last user message, do NOT compress system.
        """
        _override_auth_and_db(mock_api_key.subscription, mock_db)
        mock_check_token_limit.return_value = (True, 1000)
        mock_count_tokens_stats.return_value = {
            "original_tokens": 10,
            "compressed_tokens": 5,
            "token_savings": 5,
            "token_count_exact": False,
            "token_count_source": "estimated",
        }
        mock_count_tokens_meta.return_value = Mock(tokens=10, exact=False, source="estimated")

        mock_compress.return_value = ("compressed", {"@": "x"}, 0.8)
        mock_format.return_value = "PCLRv1|DICT_LEN:10|{\"@\":\"x\"}|PROMPT_LEN:10|compressed"

        mock_llm_response = LLMResponse(
            text="ok",
            input_tokens=10,
            output_tokens=5,
            model="gpt-4",
            finish_reason="stop",
        )
        mock_client_instance = Mock()
        mock_client_instance.complete.return_value = mock_llm_response
        mock_openai_client.return_value = mock_client_instance

        try:
            response = client.post(
                "/api/v1/complete",
                json={
                    "messages": [
                        {"role": "system", "content": "sys"},
                        {"role": "user", "content": "first"},
                        {"role": "assistant", "content": "a1"},
                        {"role": "user", "content": "last user"},
                    ],
                    "model": "gpt-4",
                    "llm_provider": "openai",
                    "llm_api_key": "sk-test-key",
                    "compress": True,
                    "algorithm": "greedy",
                },
                headers={"X-API-Key": "test-api-key"},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        # Only the last user message is compressed by default → one compression call
        assert mock_compress.call_count == 1

