"""
API client for PCompressLR cloud service.

SDK v0.2.0 notes:
- `complete()` is messages-first and targets POST /api/v2/complete
- Provider API keys are intentionally not accepted by the SDK (BYOK via dashboard)
"""

import os
import requests
from typing import Dict, Optional, Literal, List, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    from pathlib import Path
    
    # Try to find .env file in multiple locations:
    # 1. Backend directory (where this package is located)
    # 2. Current working directory
    # 3. backend/.env from project root
    
    # Get the directory where this file is located
    # Path(__file__) = backend/pcompresslr/api_client.py
    # .parent = backend/pcompresslr/
    # .parent = backend/
    current_file_dir = Path(__file__).parent.parent
    
    # Try loading from backend directory first
    env_paths = [
        current_file_dir / ".env",  # backend/.env
        Path.cwd() / ".env",  # Current working directory
        Path.cwd() / "backend" / ".env",  # backend/.env from project root
    ]
    
    # Try each path
    loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            loaded = True
            break
    
    # If no .env file found in specific locations, use default behavior (searches upward)
    if not loaded:
        load_dotenv()
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass
except Exception:
    # If anything goes wrong, just continue without .env loading
    pass


class PcompresslrAPIError(Exception):
    """Base exception for API errors."""
    pass


class APIKeyError(PcompresslrAPIError):
    """Exception raised when API key is invalid or missing."""
    pass


class RateLimitError(PcompresslrAPIError):
    """Exception raised when rate limit is exceeded."""
    pass


class APIRequestError(PcompresslrAPIError):
    """Exception raised for general API request errors."""
    pass


class PcompresslrAPIClient:
    """
    Client for interacting with PCompressLR cloud API.
    
    Usage:
        client = PcompresslrAPIClient(api_key="your-key")
        result = client.compress("your prompt", model="gpt-4")
    """
    
    DEFAULT_API_URL = "https://api.compress.lightreach.io"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: int = 120  # 2 minutes - complete() calls LLM which can take 30+ seconds
    ):
        """
        Initialize the API client.
        
        Args:
            api_key: API key for authentication. If not provided, will check
                    PCOMPRESLR_API_KEY environment variable.
            api_url: Base URL for the API. If not provided, uses default production URL.
                    Can also be set via PCOMPRESLR_API_URL environment variable.
                    This is primarily for internal/testing use - users should use the default.
            timeout: Request timeout in seconds (default: 10)
        
        Raises:
            APIKeyError: If API key is not provided and not found in environment
        """
        # Get API key from parameter or environment
        # Support both legacy env var and the more semantic name.
        self.api_key = api_key or os.getenv("LIGHTREACH_API_KEY") or os.getenv("PCOMPRESLR_API_KEY")
        if not self.api_key:
            raise APIKeyError(
                "API key is required. Provide it as a parameter or set "
                "PCOMPRESLR_API_KEY environment variable."
            )
        
        # Basic validation - API keys should not be empty strings
        if not self.api_key.strip():
            raise APIKeyError(
                "API key cannot be empty. Please provide a valid API key."
            )
        
        # Get API URL from parameter or environment or use default
        self.api_url = (api_url or 
                       os.getenv("PCOMPRESLR_API_URL") or 
                       self.DEFAULT_API_URL).rstrip('/')
        
        self.timeout = timeout
        
        # Create session with retry strategy
        # Note: We don't retry on 401 (invalid API key) or 4xx errors - fail fast
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,  # Reduced from 3 for faster failure
            backoff_factor=0.3,  # Reduced backoff for faster retries
            status_forcelist=[429, 500, 502, 503, 504],  # Only retry on these status codes
            allowed_methods=["POST"],
            respect_retry_after_header=True
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        try:
            from ._version import __version__ as _sdk_version
        except Exception:
            _sdk_version = "0.2.0"
        self.session.headers.update(
            {
                # Prefer standard Bearer auth, but keep X-API-Key for backward compatibility.
                "Authorization": f"Bearer {self.api_key}",
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
                "User-Agent": f"compress-lightreach-python/{_sdk_version}",
            }
        )
    
    def _make_request(
        self,
        endpoint: str,
        data: Dict,
        method: str = "POST"
    ) -> Dict:
        """
        Make an HTTP request to the API.
        
        Args:
            endpoint: API endpoint path (e.g., "/api/v1/compress")
            data: Request payload
            method: HTTP method (default: "POST")
        
        Returns:
            JSON response as dictionary
        
        Raises:
            APIKeyError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            APIRequestError: For other API errors
        """
        url = f"{self.api_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=self.timeout
            )
            
            # Handle different status codes
            if response.status_code == 401:
                try:
                    error_detail = response.json().get("detail", "Invalid API key")
                except:
                    error_detail = "Invalid API key"
                raise APIKeyError(
                    f"Authentication failed: {error_detail}. "
                    "Please check your API key at https://compress.lightreach.io"
                )
            
            elif response.status_code == 429:
                error_detail = response.json().get("detail", "Rate limit exceeded")
                raise RateLimitError(f"Rate limit exceeded: {error_detail}")
            
            elif response.status_code == 400:
                error_detail = response.json().get("detail", "Bad request")
                raise APIRequestError(f"Bad request: {error_detail}")
            
            elif response.status_code == 403:
                error_detail = response.json().get("detail", "Forbidden")
                raise APIRequestError(f"Forbidden: {error_detail}")
            
            elif not response.ok:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text or f"HTTP {response.status_code}"
                raise APIRequestError(
                    f"API request failed (HTTP {response.status_code}): {error_detail}"
                )
            
            return response.json()
        
        except requests.exceptions.Timeout:
            raise APIRequestError(
                f"Request to {url} timed out after {self.timeout} seconds. "
                "The API may be experiencing high load or may be unreachable. "
                "Please check your internet connection and try again."
            )
        
        except requests.exceptions.ConnectionError as e:
            error_msg = str(e)
            # Check if this is a timeout-related connection error
            if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                raise APIRequestError(
                    f"Failed to connect to API at {self.api_url}. "
                    f"Error: {error_msg}. "
                    "Please check your internet connection and verify the API endpoint is accessible.\n\n"
                    f"If this problem persists, please check https://compress.lightreach.io/status or contact support."
                )
            raise APIRequestError(
                f"Failed to connect to API at {self.api_url}. "
                f"Error: {error_msg}. "
                "Please check your internet connection and verify the API endpoint is accessible.\n\n"
                f"If this problem persists, please check https://compress.lightreach.io/status or contact support."
            )
        
        except (APIKeyError, RateLimitError, APIRequestError):
            # Re-raise our custom exceptions
            raise
        
        except requests.exceptions.RequestException as e:
            raise APIRequestError(f"Request failed: {str(e)}")
    
    def compress(
        self,
        prompt: str,
        model: str = "gpt-4",
        algorithm: Literal["greedy", "optimal"] = "greedy",
        tags: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Compress a prompt using the cloud API.
        
        Args:
            prompt: The prompt text to compress
            model: LLM model name for tokenization (e.g., 'gpt-4', 'gpt-3.5-turbo')
            algorithm: Compression algorithm ('greedy' or 'optimal')
            tags: Optional dictionary of tags for cost attribution (e.g., {'team': 'marketing'})
        
        Returns:
            Dictionary containing:
                - compressed: Compressed prompt text
                - dictionary: Decompression dictionary
                - llm_format: LLM-ready formatted string
                - compression_ratio: Compression ratio
                - original_size: Original size in characters
                - compressed_size: Compressed size in characters
                - processing_time_ms: Processing time in milliseconds
                - algorithm: Algorithm used
        
        Raises:
            APIKeyError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            APIRequestError: For other API errors
        """
        data = {
            "prompt": prompt,
            "model": model,
            "algorithm": algorithm
        }
        
        if tags is not None:
            data["tags"] = tags
        
        return self._make_request("/api/v1/compress", data)
    
    def decompress(self, llm_format: str) -> Dict:
        """
        Decompress an LLM-formatted compressed prompt.
        
        Args:
            llm_format: LLM-formatted compressed prompt string
        
        Returns:
            Dictionary containing:
                - decompressed: Decompressed original prompt
                - processing_time_ms: Processing time in milliseconds
        
        Raises:
            APIKeyError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            APIRequestError: For other API errors
        """
        data = {
            "llm_format": llm_format
        }
        
        return self._make_request("/api/v1/decompress", data)
    
    def health_check(self) -> Dict:
        """
        Check API health status.
        
        Returns:
            Dictionary with health status information
        
        Raises:
            APIRequestError: If health check fails
        """
        try:
            response = self.session.get(
                f"{self.api_url}/health",
                timeout=5
            )
            if response.ok:
                return response.json()
            else:
                raise APIRequestError(f"Health check failed: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise APIRequestError(f"Health check failed: {str(e)}")
    
    def complete(
        self,
        messages: List[Dict[str, Any]],
        llm_provider: Optional[Literal["openai", "anthropic", "google", "deepseek", "moonshot"]] = None,
        desired_hle: Optional[float] = None,
        compress: bool = True,
        compression_config: Optional[Dict[str, Any]] = None,
        compress_output: bool = False,
        algorithm: Literal["greedy", "optimal"] = "greedy",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None,
        max_history_messages: Optional[int] = None,
        # Deprecated parameters (v0.2.0, ignored in v1.0.0)
        model: Optional[str] = None,
        hle_target_percent: Optional[float] = None,
        min_hle_score: Optional[float] = None,
        auto_select_by_hle: Optional[bool] = None,
        same_provider_only: Optional[bool] = None,
    ) -> Dict:
        """
        Complete a conversation with intelligent model selection, compression, LLM call, and decompression.

        This targets the v2 complete endpoint (POST /api/v2/complete) with v1.0.0 intelligent routing.
        Provider API keys must be stored in your account (BYOK via dashboard).
        
        Args:
            messages: Full conversation history as list of {"role": "...", "content": "..."} objects (required)
            llm_provider: Optional provider constraint (e.g., 'openai', 'anthropic', 'google').
                         Omit to allow cross-provider cost optimization. (default: None)
            desired_hle: Optional desired HLE (Humanity's Last Exam) score for model quality (0-40, where 40 is SOTA).
                        Must not exceed admin's global or tag-level ceilings. Request will error if it does.
                        (default: None)
            compress: Whether to compress eligible messages (default: True)
            compression_config: Optional per-role compression configuration
            compress_output: Whether to request compressed output from LLM (default: False)
            algorithm: Compression algorithm: 'greedy' (fast) or 'optimal' (slower, better compression)
            temperature: LLM temperature setting (optional)
            max_tokens: Maximum tokens to generate (optional)
            tags: Optional dictionary of tags for cost attribution and tag-level HLE ceilings (e.g., {'env': 'production'})
            max_history_messages: Optional limit on conversation history length
            
            # DEPRECATED (v0.2.0, ignored):
            model: Ignored. System selects model automatically.
            hle_target_percent: Removed in v1.0.0. Use desired_hle instead.
            min_hle_score: Removed in v1.0.0. Use desired_hle instead.
            auto_select_by_hle: Removed in v1.0.0. Always auto-selects now.
            same_provider_only: Removed in v1.0.0. Use llm_provider parameter instead.
        
        Returns:
            Dictionary containing:
                - decompressed_response: Final decompressed response
                - compression_stats: Input compression statistics
                - llm_stats: LLM usage statistics
                - routing_info: Detailed routing decision (NEW in v1.0.0):
                    - selected_model: Model chosen by system
                    - selected_provider: Provider chosen by system
                    - model_hle: HLE score of selected model
                    - effective_hle: Effective HLE after applying admin ceilings (min of desired/tag/global)
                    - hle_source: "request", "tag", "global", or "none"
                    - hle_clamped: True if admin ceiling lowered engineer's desired_hle
                - warnings: Any warnings (including HLE ceiling notifications)
                - cost_estimate: Estimated USD cost
                - savings_estimate: Estimated USD savings
        
        Raises:
            APIKeyError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            APIRequestError: For configuration errors (e.g., no provider keys, HLE request exceeds ceiling)
        
        Example:
            # Basic usage (cross-provider optimization)
            response = client.complete(
                messages=[{"role": "user", "content": "Hello"}],
                desired_hle=30,
            )
            
            # Constrained to specific provider
            response = client.complete(
                messages=[{"role": "user", "content": "Hello"}],
                llm_provider="openai",
                desired_hle=35,
            )
            
            # Access routing info
            print(f"Selected: {response['routing_info']['selected_model']}")
            print(f"HLE: {response['routing_info']['model_hle']}")
            if response['routing_info']['hle_clamped']:
                print("Admin ceiling lowered your desired HLE")
        """
        if not messages or not isinstance(messages, list):
            raise ValueError("messages is required and must be a non-empty list")

        # Warn about deprecated parameters
        if model is not None:
            import warnings
            warnings.warn(
                "Parameter 'model' is deprecated in v1.0.0 and will be ignored. "
                "The system now selects models automatically based on your provider keys and HLE requirements.",
                DeprecationWarning,
                stacklevel=2
            )
        
        if any(p is not None for p in [hle_target_percent, min_hle_score, auto_select_by_hle, same_provider_only]):
            import warnings
            warnings.warn(
                "Parameters 'hle_target_percent', 'min_hle_score', 'auto_select_by_hle', and 'same_provider_only' "
                "are deprecated in v1.0.0. Use 'desired_hle' and optional 'llm_provider' instead.",
                DeprecationWarning,
                stacklevel=2
            )

        data: Dict[str, Any] = {
            "messages": messages,
            "compress": compress,
            "compress_output": compress_output,
            "algorithm": algorithm,
        }

        # v1.0.0 parameters
        if llm_provider is not None:
            data["llm_provider"] = llm_provider
        
        if desired_hle is not None:
            data["desired_hle"] = desired_hle

        if compression_config is not None:
            data["compression_config"] = compression_config

        if max_history_messages is not None:
            data["max_history_messages"] = max_history_messages
        
        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        if tags is not None:
            data["tags"] = tags

        return self._make_request("/api/v2/complete", data)

