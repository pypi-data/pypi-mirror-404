"""Pricing resource."""

from metricai_sdk.http import HTTPClient
from metricai_sdk.models.pricing import (
    PricingConfig,
    UpdateGlobalMarkupRequest,
    UpdateModelPricingRequest,
    TokenRates,
)


class PricingResource:
    """Pricing management resource."""
    
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def get(self) -> PricingConfig:
        """Get current pricing configuration.
        
        Returns:
            Pricing configuration
        """
        response = self._http.get("/pricing", use_firebase_auth=True)
        return PricingConfig(**response)
    
    def update_global_markup(self, markup_percent: float) -> dict:
        """Update global markup percentage for all models.
        
        Args:
            markup_percent: New default markup percentage
        
        Returns:
            Updated markup config
        """
        request = UpdateGlobalMarkupRequest(default_markup_percentage=markup_percent)
        return self._http.put(
            "/pricing/markup",
            use_firebase_auth=True,
            json_data=request.model_dump(),
        )
    
    def update_model_pricing(
        self,
        model_id: str,
        markup_percent: float,
        enabled: bool = True,
    ) -> dict:
        """Update model-specific pricing override.
        
        Args:
            model_id: Model identifier
            markup_percent: Custom markup percentage for this model
            enabled: Whether this override is active
        
        Returns:
            Updated override
        """
        request = UpdateModelPricingRequest(
            markup_percentage=markup_percent,
            enabled=enabled,
        )
        return self._http.put(
            f"/pricing/models/{model_id}",
            use_firebase_auth=True,
            json_data=request.model_dump(),
        )
    
    def get_rates(self) -> TokenRates:
        """Get token rates for all models with markup applied.
        
        Returns:
            Token rates
        """
        response = self._http.get("/pricing/rates", use_firebase_auth=True)
        return TokenRates(**response)
