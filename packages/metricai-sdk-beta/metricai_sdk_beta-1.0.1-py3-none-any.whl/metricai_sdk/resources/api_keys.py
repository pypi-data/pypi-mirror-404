"""API keys resource."""

from typing import Optional
from metricai_sdk.http import HTTPClient
from metricai_sdk.models.api_keys import (
    APIKey,
    CreateAPIKeyRequest,
    CreateAPIKeyResponse,
    ListAPIKeysResponse,
)


class APIKeysResource:
    """API key management resource."""
    
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def create(self, name: Optional[str] = None) -> CreateAPIKeyResponse:
        """Create a new API key.
        
        Args:
            name: Optional name/description for the API key
        
        Returns:
            Created API key (plain key shown only once)
        """
        request = CreateAPIKeyRequest(name=name)
        response = self._http.post(
            "/api-keys",
            use_firebase_auth=True,
            json_data=request.model_dump(exclude_none=True),
        )
        return CreateAPIKeyResponse(**response)
    
    def list(self) -> list[APIKey]:
        """List all API keys.
        
        Returns:
            List of API keys
        """
        response = self._http.get("/api-keys", use_firebase_auth=True)
        keys_response = ListAPIKeysResponse(**response)
        return keys_response.keys
    
    def revoke(self, key_id: str) -> dict:
        """Revoke an API key.
        
        Args:
            key_id: API key ID to revoke
        
        Returns:
            Success response
        """
        return self._http.delete(f"/api-keys/{key_id}", use_firebase_auth=True)
