"""
Tests for LLM client implementations.
"""

import pytest
from unittest.mock import Mock, patch
import requests

from api.llm.openai_client import OpenAIClient
from api.llm.anthropic_client import AnthropicClient
from api.llm.base import LLMAPIKeyError, LLMRateLimitError, LLMRequestError


class TestOpenAIClient:
    """Test OpenAI client."""
    
    @patch('api.llm.openai_client.requests.post')
    def test_complete_success(self, mock_post):
        """Test successful completion."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        mock_post.return_value = mock_response
        
        client = OpenAIClient()
        result = client.complete(
            prompt="test prompt",
            model="gpt-4",
            api_key="sk-test-key"
        )
        
        assert result.text == "This is a test response"
        assert result.input_tokens == 10
        assert result.output_tokens == 5
        assert result.model == "gpt-4"
        assert result.finish_reason == "stop"
    
    @patch('api.llm.openai_client.requests.post')
    def test_complete_invalid_key(self, mock_post):
        """Test completion with invalid API key."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid API key",
                "type": "invalid_request_error"
            }
        }
        mock_post.return_value = mock_response
        
        client = OpenAIClient()
        with pytest.raises(LLMAPIKeyError):
            client.complete(
                prompt="test prompt",
                model="gpt-4",
                api_key="invalid-key"
            )
    
    @patch('api.llm.openai_client.requests.post')
    def test_complete_rate_limit(self, mock_post):
        """Test completion with rate limit."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {
                "message": "Rate limit exceeded",
                "type": "rate_limit_error"
            }
        }
        mock_post.return_value = mock_response
        
        client = OpenAIClient()
        with pytest.raises(LLMRateLimitError):
            client.complete(
                prompt="test prompt",
                model="gpt-4",
                api_key="sk-test-key"
            )
    
    @patch('api.llm.openai_client.requests.post')
    def test_complete_with_temperature(self, mock_post):
        """Test completion with temperature parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "response"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "model": "gpt-4"
        }
        mock_post.return_value = mock_response
        
        client = OpenAIClient()
        client.complete(
            prompt="test",
            model="gpt-4",
            api_key="sk-test",
            temperature=0.7
        )
        
        # Verify temperature was included in request
        call_args = mock_post.call_args
        assert "temperature" in call_args[1]["json"]
        assert call_args[1]["json"]["temperature"] == 0.7


class TestAnthropicClient:
    """Test Anthropic client."""
    
    @patch('api.llm.anthropic_client.requests.post')
    def test_complete_success(self, mock_post):
        """Test successful completion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "msg-123",
            "type": "message",
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": "This is a Claude response"
            }],
            "model": "claude-3-opus-20240229",
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5
            }
        }
        mock_post.return_value = mock_response
        
        client = AnthropicClient()
        result = client.complete(
            prompt="test prompt",
            model="claude-3-opus",
            api_key="sk-ant-test-key",
            max_tokens=100
        )
        
        assert result.text == "This is a Claude response"
        assert result.input_tokens == 10
        assert result.output_tokens == 5
        assert result.model == "claude-3-opus-20240229"
        assert result.finish_reason == "end_turn"
    
    @patch('api.llm.anthropic_client.requests.post')
    def test_complete_invalid_key(self, mock_post):
        """Test completion with invalid API key."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid API key"
            }
        }
        mock_post.return_value = mock_response
        
        client = AnthropicClient()
        with pytest.raises(LLMAPIKeyError):
            client.complete(
                prompt="test prompt",
                model="claude-3-opus",
                api_key="invalid-key",
                max_tokens=100
            )
    
    @patch('api.llm.anthropic_client.requests.post')
    def test_model_mapping(self, mock_post):
        """Test model name mapping."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "response"}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "model": "claude-3-opus-20240229"
        }
        mock_post.return_value = mock_response
        
        client = AnthropicClient()
        client.complete(
            prompt="test",
            model="claude-3-opus",  # User-friendly name
            api_key="sk-ant-test",
            max_tokens=100
        )
        
        # Verify API model ID was used
        call_args = mock_post.call_args
        assert call_args[1]["json"]["model"] == "claude-3-opus-20240229"
    
    @patch('api.llm.anthropic_client.requests.post')
    def test_claude_4_models(self, mock_post):
        """Test Claude 4 model name mapping."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "response"}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "model": "claude-opus-4-20250514"
        }
        mock_post.return_value = mock_response
        
        client = AnthropicClient()
        
        # Test various Claude 4 naming conventions
        test_models = [
            "claude-opus-4.1",
            "claude-opus-4",
            "claude-4-opus-4.1",
            "claude-4-opus",
            "claude-sonnet-4.5",
            "claude-sonnet-4",
            "claude-haiku-4.5",
        ]
        
        for model_name in test_models:
            client.complete(
                prompt="test",
                model=model_name,
                api_key="sk-ant-test",
                max_tokens=100
            )
            
            # Verify model was mapped (not passed through as-is)
            call_args = mock_post.call_args
            mapped_model = call_args[1]["json"]["model"]
            assert mapped_model != model_name  # Should be mapped to API ID
            assert "claude" in mapped_model.lower()  # Should still be a Claude model
    
    @patch('api.llm.anthropic_client.requests.post')
    def test_default_max_tokens(self, mock_post):
        """Test that max_tokens defaults to 1024 if not provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "response"}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "model": "claude-3-haiku-20240307"
        }
        mock_post.return_value = mock_response
        
        client = AnthropicClient()
        client.complete(
            prompt="test",
            model="claude-3-haiku",
            api_key="sk-ant-test"
            # max_tokens not provided
        )
        
        # Verify default max_tokens was used
        call_args = mock_post.call_args
        assert call_args[1]["json"]["max_tokens"] == 1024

