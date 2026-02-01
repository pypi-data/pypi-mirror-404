"""Health check resource."""

from typing import Dict, Any
from metricai_sdk.http import HTTPClient


class HealthResource:
    """Health check resource."""
    
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def check(self) -> Dict[str, Any]:
        """Check API health.
        
        Returns:
            Health status response
        """
        return self._http.get("/", use_firebase_auth=False, use_api_key_auth=False)
    
    def health(self) -> Dict[str, Any]:
        """Get health endpoint.
        
        Returns:
            Health status response
        """
        return self._http.get("/v1/health", use_firebase_auth=False, use_api_key_auth=False)
