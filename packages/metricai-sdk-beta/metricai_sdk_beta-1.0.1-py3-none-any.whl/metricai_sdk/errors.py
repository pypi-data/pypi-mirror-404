"""Custom exception classes for MetricAI SDK."""

from typing import Optional, Dict, Any


class MetricAIError(Exception):
    """Base exception for all SDK errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.status_code:
            return f"{self.status_code}: {self.message}"
        return self.message


class AuthenticationError(MetricAIError):
    """401 Unauthorized - Invalid or missing auth token."""
    
    def __init__(self, message: str, response: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, response=response)


class NotFoundError(MetricAIError):
    """404 Not Found - Resource doesn't exist."""
    
    def __init__(self, message: str, response: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, response=response)


class ValidationError(MetricAIError):
    """400 Bad Request - Invalid input parameters."""
    
    def __init__(self, message: str, response: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, response=response)


class RateLimitError(MetricAIError):
    """429 Too Many Requests - Rate limit exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=429, response=response)
        self.retry_after = retry_after


class ServerError(MetricAIError):
    """5xx Server Error - Backend issue."""
    
    def __init__(self, message: str, status_code: int = 500, response: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status_code, response=response)
