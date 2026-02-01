"""Providers resource."""

from typing import Optional, List
from metricai_sdk.http import HTTPClient
from metricai_sdk.models.provider import (
    ProviderConnection,
    CreateProviderRequest,
    UpdateProviderRequest,
    TestProviderResponse,
    AvailableProvidersResponse,
    ListProvidersResponse,
)


class ProvidersResource:
    """Provider connection management resource."""
    
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def create(
        self,
        provider: str,
        name: str,
        api_key: str,
        endpoint: Optional[str] = None,
        region: Optional[str] = None,
        enabled_models: Optional[List[str]] = None,
    ) -> ProviderConnection:
        """Create a new provider connection.
        
        Args:
            provider: Provider name (openai, claude, gemini, grok)
            name: Custom name for the connection
            api_key: Provider API key
            endpoint: Optional custom endpoint URL
            region: Optional region
            enabled_models: Optional list of enabled model names
        
        Returns:
            Created provider connection
        """
        request = CreateProviderRequest(
            provider=provider,
            name=name,
            api_key=api_key,
            endpoint=endpoint,
            region=region,
            enabled_models=enabled_models,
        )
        response = self._http.post(
            "/providers",
            use_firebase_auth=True,
            json_data=request.model_dump(exclude_none=True),
        )
        return ProviderConnection(**response)
    
    def list(self) -> List[ProviderConnection]:
        """List all provider connections.
        
        Returns:
            List of provider connections
        """
        response = self._http.get("/providers", use_firebase_auth=True)
        providers_response = ListProvidersResponse(**response)
        return providers_response.connections
    
    def get(self, provider_id: str) -> ProviderConnection:
        """Get a specific provider connection.
        
        Args:
            provider_id: Provider connection ID
        
        Returns:
            Provider connection
        """
        response = self._http.get(f"/providers/{provider_id}", use_firebase_auth=True)
        return ProviderConnection(**response)
    
    def update(
        self,
        provider_id: str,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        region: Optional[str] = None,
        connected: Optional[bool] = None,
        enabled_models: Optional[List[str]] = None,
    ) -> ProviderConnection:
        """Update a provider connection.
        
        Args:
            provider_id: Provider connection ID
            name: Custom name for the connection
            api_key: Provider API key
            endpoint: Optional custom endpoint URL
            region: Optional region
            connected: Connection status
            enabled_models: List of enabled model names
        
        Returns:
            Updated provider connection
        """
        request = UpdateProviderRequest(
            name=name,
            api_key=api_key,
            endpoint=endpoint,
            region=region,
            connected=connected,
            enabled_models=enabled_models,
        )
        response = self._http.put(
            f"/providers/{provider_id}",
            use_firebase_auth=True,
            json_data=request.model_dump(exclude_none=True),
        )
        return ProviderConnection(**response)
    
    def delete(self, provider_id: str) -> dict:
        """Delete a provider connection.
        
        Args:
            provider_id: Provider connection ID
        
        Returns:
            Success response
        """
        return self._http.delete(f"/providers/{provider_id}", use_firebase_auth=True)
    
    def test(self, provider_id: str) -> TestProviderResponse:
        """Test a provider connection.
        
        Args:
            provider_id: Provider connection ID
        
        Returns:
            Test result
        """
        response = self._http.post(f"/providers/{provider_id}/test", use_firebase_auth=True)
        return TestProviderResponse(**response)
    
    def get_available(self) -> AvailableProvidersResponse:
        """Get list of providers available via Shared API mode.
        
        Returns:
            Available providers response
        """
        response = self._http.get("/v1/providers/available", use_firebase_auth=False, use_api_key_auth=False)
        return AvailableProvidersResponse(**response)
