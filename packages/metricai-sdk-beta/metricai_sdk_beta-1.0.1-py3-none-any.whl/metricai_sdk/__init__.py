"""MetricAI Python SDK - Official Python client for MetricAI API."""

from metricai_sdk.client import MetricAIClient
from metricai_sdk.errors import (
    MetricAIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
)
from metricai_sdk.auth import (
    login,
    get_firebase_token,
    get_firebase_token_with_refresh,
    refresh_firebase_token,
    get_firebase_token_from_api,
    get_firebase_token_from_api_with_refresh,
    refresh_firebase_token_from_api,
    create_firebase_user,
    create_firebase_user_with_refresh,
    create_user_and_profile,
)

__version__ = "1.0.1"

__all__ = [
    "MetricAIClient",
    "login",
    "get_firebase_token",
    "get_firebase_token_with_refresh",
    "refresh_firebase_token",
    "get_firebase_token_from_api",
    "get_firebase_token_from_api_with_refresh",
    "refresh_firebase_token_from_api",
    "create_firebase_user",
    "create_firebase_user_with_refresh",
    "create_user_and_profile",
    "MetricAIError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
]
