"""Shared API resource – token info, provider list, and catalog (MetricAI API key auth)."""

from typing import Optional
from metricai_sdk.http import HTTPClient
from metricai_sdk.models.shared_api import (
    TokenInfoRequest,
    TokenInfoResponse,
    SharedAPIProvidersResponse,
    SharedAPICatalogResponse,
)


class SharedAPIResource:
    """Shared API resource for token pricing and provider catalog.

    Use Shared API when you do not provide a provider API key (BYOK). The backend
    uses MetricAI's shared provider keys and charges your MetricAI wallet. All
    endpoints require your MetricAI API key (X-MetricAI-API-Key or api_key in client).
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    def get_token_info(
        self,
        provider: str,
        model: Optional[str] = None,
        token_type: str = "text",
    ) -> TokenInfoResponse:
        """Get token pricing for a provider in Shared API mode.

        Args:
            provider: Provider name: 'openai', 'claude', 'gemini', or 'grok'
            model: Optional model name for specific pricing
            token_type: 'text', 'image', or 'audio'

        Returns:
            TokenInfoResponse with provider_available, available_models, model_pricing
        """
        request = TokenInfoRequest(
            provider=provider,
            model=model,
            token_type=token_type,
        )
        response = self._http.post(
            "/v1/shared-api/token-info",
            use_api_key_auth=True,
            json_data=request.model_dump(exclude_none=True),
        )
        return TokenInfoResponse(**response)

    def list_providers(self) -> SharedAPIProvidersResponse:
        """List providers available via Shared API (no provider key needed).

        Returns:
            SharedAPIProvidersResponse with providers and shared_api_available
        """
        response = self._http.get(
            "/v1/shared-api/providers",
            use_api_key_auth=True,
        )
        return SharedAPIProvidersResponse(**response)

    def get_catalog(
        self,
        include_inactive: bool = False,
    ) -> SharedAPICatalogResponse:
        """Get full provider catalog with Shared API availability.

        Args:
            include_inactive: Include inactive providers (default False)

        Returns:
            SharedAPICatalogResponse with providers and counts
        """
        params = {}
        if include_inactive:
            params["include_inactive"] = "true"
        response = self._http.get(
            "/v1/shared-api/catalog",
            use_api_key_auth=True,
            params=params if params else None,
        )
        return SharedAPICatalogResponse(**response)
