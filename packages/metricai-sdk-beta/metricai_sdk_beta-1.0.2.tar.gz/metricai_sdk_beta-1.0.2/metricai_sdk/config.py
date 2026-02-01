"""Configuration management for MetricAI SDK."""

import os
from typing import Optional
from pydantic import BaseModel, Field


class MetricAIConfig(BaseModel):
    """Configuration for MetricAI client.
    
    By default, uses the backend URL directly.
    - Backend: https://metricai-backend-epadd3mwtq-uc.a.run.app (default)
    - Gateway: https://metricai-gateway-13tdjdp6.uc.gateway.dev (optional, for CORS/rate limiting)
    """
    
    base_url: str = Field(
        default="https://metricai-backend-epadd3mwtq-uc.a.run.app",
        description="Base URL for MetricAI API (defaults to backend URL)"
    )
    firebase_token: Optional[str] = Field(
        default=None,
        description="Firebase ID token for user-scoped endpoints"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="MetricAI API key for proxy endpoints"
    )
    timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests"
    )
    
    @classmethod
    def from_env(cls) -> "MetricAIConfig":
        """Create configuration from environment variables."""
        return cls(
            base_url=os.getenv("METRICAI_BASE_URL", "https://metricai-backend-epadd3mwtq-uc.a.run.app"),
            firebase_token=os.getenv("METRICAI_FIREBASE_TOKEN"),
            api_key=os.getenv("METRICAI_API_KEY"),
            timeout=float(os.getenv("METRICAI_TIMEOUT", "30.0")),
            max_retries=int(os.getenv("METRICAI_MAX_RETRIES", "3")),
        )
