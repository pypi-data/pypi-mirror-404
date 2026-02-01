"""Proxy resource for LLM API calls."""

from typing import Optional, Dict, Any, List
from metricai_sdk.http import HTTPClient
from metricai_sdk.models.proxy import ProxyRequest, ProxyResponse


class ProxyResource:
    """Proxy resource for AI provider requests.

    Supports BYOK (Bring Your Own Key) via provider_api_key, or Shared API by omitting
    it so the backend uses MetricAI's shared keys (charges your MetricAI wallet).
    """

    def __init__(self, http: HTTPClient):
        self._http = http
        self.openai = OpenAIProxy(self._http)
        self.claude = ClaudeProxy(self._http)
        self.gemini = GeminiProxy(self._http)
        self.grok = GrokProxy(self._http)

    def get_openai_info(self) -> dict:
        """Get OpenAI endpoint info.
        
        Returns:
            Endpoint information
        """
        return self._http.get("/v1/proxy/openai", use_api_key_auth=True)


class OpenAIProxy:
    """OpenAI proxy resource."""
    
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def chat_completions(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        token_type: str = "text",
        flat_price_usd: Optional[float] = None,
        provider_api_key: Optional[str] = None,
        **kwargs,
    ) -> ProxyResponse:
        """Create OpenAI chat completion.
        
        Args:
            model: Model ID (e.g., 'gpt-4', 'gpt-3.5-turbo')
            messages: Chat messages following OpenAI format
            token_type: Metric category ('text', 'image', 'audio')
            flat_price_usd: Optional fixed price per request
            provider_api_key: Optional provider API key (uses shared if not provided)
            **kwargs: Additional OpenAI API parameters
        
        Returns:
            Proxy response with completion and token usage
        """
        request_data = ProxyRequest(
            model=model,
            messages=messages,
            token_type=token_type,
            flat_price_usd=flat_price_usd,
        ).model_dump(exclude_none=True)
        
        # Merge additional OpenAI parameters
        request_data.update(kwargs)
        
        headers = {}
        if provider_api_key:
            headers["X-OpenAI-API-Key"] = provider_api_key
        
        response = self._http.post(
            "/v1/proxy/openai",
            use_api_key_auth=True,
            json_data=request_data,
            additional_headers=headers,
        )
        return ProxyResponse(**response)


class ClaudeProxy:
    """Claude proxy resource."""
    
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def messages(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        token_type: str = "text",
        flat_price_usd: Optional[float] = None,
        provider_api_key: Optional[str] = None,
        **kwargs,
    ) -> ProxyResponse:
        """Create Claude message.
        
        Args:
            model: Model ID (e.g., 'claude-3-opus-20240229')
            messages: Chat messages following Anthropic format
            token_type: Metric category ('text', 'image', 'audio')
            flat_price_usd: Optional fixed price per request
            provider_api_key: Optional provider API key (uses shared if not provided)
            **kwargs: Additional Anthropic API parameters
        
        Returns:
            Proxy response with completion and token usage
        """
        request_data = ProxyRequest(
            model=model,
            messages=messages,
            token_type=token_type,
            flat_price_usd=flat_price_usd,
        ).model_dump(exclude_none=True)
        
        # Merge additional Anthropic parameters
        request_data.update(kwargs)
        
        headers = {}
        if provider_api_key:
            headers["X-Anthropic-API-Key"] = provider_api_key
        
        response = self._http.post(
            "/v1/proxy/claude",
            use_api_key_auth=True,
            json_data=request_data,
            additional_headers=headers,
        )
        return ProxyResponse(**response)


class GeminiProxy:
    """Gemini proxy resource."""
    
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def generate_content(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        token_type: str = "text",
        flat_price_usd: Optional[float] = None,
        provider_api_key: Optional[str] = None,
        **kwargs,
    ) -> ProxyResponse:
        """Generate Gemini content.
        
        Args:
            model: Model ID (e.g., 'gemini-pro')
            messages: Chat messages
            token_type: Metric category ('text', 'image', 'audio')
            flat_price_usd: Optional fixed price per request
            provider_api_key: Optional provider API key (uses shared if not provided)
            **kwargs: Additional Gemini API parameters
        
        Returns:
            Proxy response with completion and token usage
        """
        request_data = ProxyRequest(
            model=model,
            messages=messages,
            token_type=token_type,
            flat_price_usd=flat_price_usd,
        ).model_dump(exclude_none=True)
        
        # Merge additional Gemini parameters
        request_data.update(kwargs)
        
        headers = {}
        if provider_api_key:
            headers["X-Google-API-Key"] = provider_api_key
        
        response = self._http.post(
            "/v1/proxy/gemini",
            use_api_key_auth=True,
            json_data=request_data,
            additional_headers=headers,
        )
        return ProxyResponse(**response)


class GrokProxy:
    """Grok (xAI) proxy resource."""

    def __init__(self, http: HTTPClient):
        self._http = http

    def chat_completions(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        token_type: str = "text",
        flat_price_usd: Optional[float] = None,
        provider_api_key: Optional[str] = None,
        **kwargs,
    ) -> ProxyResponse:
        """Create Grok chat completion.

        Args:
            model: Model ID (e.g., 'grok-2', 'grok-2-vision')
            messages: Chat messages following OpenAI-style format
            token_type: Metric category ('text', 'image', 'audio')
            flat_price_usd: Optional fixed price per request
            provider_api_key: Optional xAI API key (omit to use Shared API)
            **kwargs: Additional Grok API parameters

        Returns:
            Proxy response with completion and token usage (api_mode: 'byok' or 'shared')
        """
        request_data = ProxyRequest(
            model=model,
            messages=messages,
            token_type=token_type,
            flat_price_usd=flat_price_usd,
        ).model_dump(exclude_none=True)

        request_data.update(kwargs)

        headers = {}
        if provider_api_key:
            headers["X-Grok-API-Key"] = provider_api_key

        response = self._http.post(
            "/v1/proxy/grok",
            use_api_key_auth=True,
            json_data=request_data,
            additional_headers=headers,
        )
        return ProxyResponse(**response)
