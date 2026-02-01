"""Statistics resource."""

from metricai_sdk.http import HTTPClient
from metricai_sdk.models.stats import TokenStatsByModel


class StatsResource:
    """Statistics resource."""
    
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def get_token_stats(self) -> TokenStatsByModel:
        """Get consolidated token statistics grouped by model/provider.
        
        Returns:
            Token statistics by model
        """
        response = self._http.get("/stats/tokens", use_firebase_auth=True)
        return TokenStatsByModel(stats=response)
    
    def get_token_stats_by_model(self) -> TokenStatsByModel:
        """Get token statistics grouped by model (alias for get_token_stats).
        
        Returns:
            Token statistics by model
        """
        return self.get_token_stats()
