"""Main MetricAI client class."""

from typing import Optional

from metricai_sdk.config import MetricAIConfig
from metricai_sdk.http import HTTPClient
from metricai_sdk.resources.health import HealthResource
from metricai_sdk.resources.user import UserResource
from metricai_sdk.resources.wallet import WalletResource
from metricai_sdk.resources.api_keys import APIKeysResource
from metricai_sdk.resources.providers import ProvidersResource
from metricai_sdk.resources.proxy import ProxyResource
from metricai_sdk.resources.payments import PaymentsResource
from metricai_sdk.resources.stats import StatsResource
from metricai_sdk.resources.transactions import TransactionsResource
from metricai_sdk.resources.pricing import PricingResource
from metricai_sdk.resources.alerts import AlertsResource
from metricai_sdk.resources.shared_api import SharedAPIResource


class MetricAIClient:
    """Main client for MetricAI API."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        firebase_token: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize MetricAI client.
        
        Args:
            base_url: Base URL for MetricAI API (defaults to production)
            firebase_token: Firebase ID token for user-scoped endpoints
            api_key: MetricAI API key for proxy endpoints
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retries (default: 3)
        """
        config = MetricAIConfig(
            base_url=base_url or "https://metricai-backend-epadd3mwtq-uc.a.run.app",
            firebase_token=firebase_token,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        
        self._http = HTTPClient(
            base_url=config.base_url,
            firebase_token=config.firebase_token,
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )
        
        # Initialize resources
        self.health = HealthResource(self._http)
        self.user = UserResource(self._http)
        self.wallet = WalletResource(self._http)
        self.api_keys = APIKeysResource(self._http)
        self.providers = ProvidersResource(self._http)
        self.proxy = ProxyResource(self._http)
        self.payments = PaymentsResource(self._http)
        self.stats = StatsResource(self._http)
        self.transactions = TransactionsResource(self._http)
        self.pricing = PricingResource(self._http)
        self.alerts = AlertsResource(self._http)
        self.shared_api = SharedAPIResource(self._http)
    
    @classmethod
    def from_env(cls) -> "MetricAIClient":
        """Create client from environment variables.
        
        Environment variables:
            METRICAI_BASE_URL: Base URL (optional)
            METRICAI_FIREBASE_TOKEN: Firebase ID token (optional)
            METRICAI_API_KEY: MetricAI API key (optional)
            METRICAI_TIMEOUT: Request timeout in seconds (optional, default: 30.0)
            METRICAI_MAX_RETRIES: Maximum retries (optional, default: 3)
        """
        config = MetricAIConfig.from_env()
        return cls(
            base_url=config.base_url,
            firebase_token=config.firebase_token,
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )
    
    def close(self) -> None:
        """Close HTTP client connections."""
        self._http.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
