"""
SDK entry point for interacting with the LightReach/Compress API.

v0.2.0 is a breaking release:
- `complete()` is messages-first and targets POST /api/v2/complete
- Provider API keys are not accepted by this SDK (BYOK via dashboard)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Sequence, Union

from .api_client import PcompresslrAPIClient, APIKeyError, RateLimitError, APIRequestError


MessageRole = Literal["system", "developer", "user", "assistant"]


@dataclass(frozen=True)
class Message:
    """One chat message."""

    role: MessageRole
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class CompressionConfig:
    """Per-role compression configuration (matches backend `CompleteRequest.CompressionConfig`)."""

    compress_system: bool = False
    compress_user: bool = True
    compress_assistant: bool = False
    compress_only_last_n_user: Optional[int] = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compress_system": self.compress_system,
            "compress_user": self.compress_user,
            "compress_assistant": self.compress_assistant,
            "compress_only_last_n_user": self.compress_only_last_n_user,
        }


class LightReach:
    """
    LightReach SDK client.

    Authentication uses your LightReach/Compress API key via `X-API-Key`
    (env var: `PCOMPRESLR_API_KEY`).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        *,
        default_model: str = "gpt-4",
        default_provider: Literal["openai", "anthropic", "google"] = "openai",
        use_optimal: bool = False,
    ):
        self.default_model = default_model
        self.default_provider = default_provider
        self.use_optimal = use_optimal
        self.api_client = PcompresslrAPIClient(api_key=api_key, api_url=api_url)

    def get_api_url(self) -> str:
        return self.api_client.api_url

    def complete(
        self,
        messages: Sequence[Union[Message, Dict[str, Any]]],
        *,
        model: Optional[str] = None,
        provider: Optional[Literal["openai", "anthropic", "google"]] = None,
        compress: bool = True,
        compression_config: Optional[Union[CompressionConfig, Dict[str, Any]]] = None,
        compress_output: bool = False,
        use_optimal: Optional[bool] = None,
        # HLE-based selection / guardrails
        hle_target_percent: Optional[float] = None,
        min_hle_score: Optional[float] = None,
        auto_select_by_hle: bool = False,
        same_provider_only: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None,
        max_history_messages: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Complete a conversation with compression and routing via POST /api/v2/complete.

        Provider keys are not accepted here. If you've configured provider keys
        in the LightReach dashboard, the server will use them automatically.
        """

        normalized: List[Dict[str, Any]] = []
        for m in messages:
            if isinstance(m, Message):
                normalized.append(m.to_dict())
            elif isinstance(m, dict):
                normalized.append({"role": m.get("role"), "content": m.get("content")})
            else:
                raise TypeError("Each message must be a Message or dict")

        cfg_dict: Optional[Dict[str, Any]] = None
        if compression_config is not None:
            if isinstance(compression_config, CompressionConfig):
                cfg_dict = compression_config.to_dict()
            elif isinstance(compression_config, dict):
                cfg_dict = dict(compression_config)
            else:
                raise TypeError("compression_config must be a CompressionConfig or dict")

        algorithm = "optimal" if (use_optimal if use_optimal is not None else self.use_optimal) else "greedy"

        try:
            resp = self.api_client.complete(
                messages=normalized,
                model=model or self.default_model,
                llm_provider=provider or self.default_provider,
                compress=compress,
                compression_config=cfg_dict,
                compress_output=compress_output,
                algorithm=algorithm,
                hle_target_percent=hle_target_percent,
                min_hle_score=min_hle_score,
                auto_select_by_hle=auto_select_by_hle,
                same_provider_only=same_provider_only,
                temperature=temperature,
                max_tokens=max_tokens,
                tags=tags,
                max_history_messages=max_history_messages,
            )
            # Add helpful aliases to better match the Feature 0.6 spec without breaking backend response.
            # We do NOT fabricate cost estimates here since the API response does not include pricing data.
            if isinstance(resp, dict):
                resp.setdefault("text", resp.get("decompressed_response"))
                cs = resp.get("compression_stats") or {}
                ls = resp.get("llm_stats") or {}
                resp.setdefault("tokens_saved", cs.get("token_savings"))
                resp.setdefault("tokens_used", ls.get("total_tokens"))
                resp.setdefault("compression_ratio", cs.get("compression_ratio"))
                resp.setdefault("cost_estimate", None)
                resp.setdefault("savings_estimate", None)
            return resp
        except APIKeyError as e:
            raise APIKeyError(
                f"{str(e)}\n\n"
                "To get an API key, visit https://compress.lightreach.io or "
                "set the PCOMPRESLR_API_KEY environment variable."
            ) from e
        except RateLimitError as e:
            raise RateLimitError(
                f"{str(e)}\n\n"
                "You've exceeded your rate limit. Please wait before making more requests, "
                "or upgrade your subscription plan."
            ) from e
        except APIRequestError as e:
            raise APIRequestError(
                f"{str(e)}\n\n"
                "If this problem persists, please check https://compress.lightreach.io/status "
                "or contact support."
            ) from e

    def compress(
        self,
        text: str,
        *,
        model: Optional[str] = None,
        algorithm: Literal["greedy", "optimal"] = "greedy",
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Compress text without making an LLM call (POST /api/v1/compress)."""

        return self.api_client.compress(prompt=text, model=model or self.default_model, algorithm=algorithm, tags=tags)


# Backwards import name (the API is still a breaking change vs v0.1.x).
Pcompresslr = LightReach

