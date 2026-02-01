"""HTTP client abstraction for MetricAI SDK."""

import time
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

import httpx

from metricai_sdk.errors import (
    MetricAIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
)

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client with retry logic and error handling."""
    
    def __init__(
        self,
        base_url: str,
        firebase_token: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.firebase_token = firebase_token
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
        )
    
    def _get_headers(
        self,
        use_firebase_auth: bool = False,
        use_api_key_auth: bool = False,
        additional_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Get headers for request."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if use_firebase_auth and self.firebase_token:
            headers["Authorization"] = f"Bearer {self.firebase_token}"
        
        if use_api_key_auth and self.api_key:
            headers["X-MetricAI-API-Key"] = self.api_key
        
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses."""
        status_code = response.status_code
        error_data = None
        try:
            error_data = response.json()
            error_message = error_data.get("detail", error_data.get("message", "Unknown error"))
        except Exception:
            error_message = response.text or f"HTTP {status_code}"
        
        if status_code == 401:
            raise AuthenticationError(error_message, response=error_data)
        elif status_code == 404:
            raise NotFoundError(error_message, response=error_data)
        elif status_code == 400:
            raise ValidationError(error_message, response=error_data)
        elif status_code == 429:
            retry_after = None
            if "Retry-After" in response.headers:
                try:
                    retry_after = int(response.headers["Retry-After"])
                except ValueError:
                    pass
            raise RateLimitError(error_message, retry_after=retry_after, response=error_data)
        elif status_code >= 500:
            raise ServerError(error_message, status_code=status_code, response=error_data)
        else:
            raise MetricAIError(error_message, status_code=status_code, response=error_data)
    
    def _request(
        self,
        method: str,
        path: str,
        use_firebase_auth: bool = False,
        use_api_key_auth: bool = False,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        url = urljoin(self.base_url, path.lstrip("/"))
        headers = self._get_headers(use_firebase_auth, use_api_key_auth, additional_headers)
        
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                )
                
                if response.is_success:
                    if response.status_code == 204:  # No Content
                        return {}
                    return response.json()
                
                # Don't retry client errors (4xx) except 429
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    self._handle_error(response)
                
                # Retry server errors and rate limits
                if attempt < self.max_retries:
                    if response.status_code == 429:
                        retry_after = 1
                        if "Retry-After" in response.headers:
                            try:
                                retry_after = int(response.headers["Retry-After"])
                            except ValueError:
                                pass
                        wait_time = retry_after * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limited, retrying after {wait_time}s (attempt {attempt + 1}/{self.max_retries + 1})")
                        time.sleep(wait_time)
                    else:
                        wait_time = (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Server error, retrying after {wait_time}s (attempt {attempt + 1}/{self.max_retries + 1})")
                        time.sleep(wait_time)
                    continue
                
                self._handle_error(response)
                
            except (RateLimitError, ServerError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    if isinstance(e, RateLimitError) and e.retry_after:
                        wait_time = e.retry_after * (2 ** attempt)
                    else:
                        wait_time = (2 ** attempt)
                    logger.warning(f"Error occurred, retrying after {wait_time}s (attempt {attempt + 1}/{self.max_retries + 1})")
                    time.sleep(wait_time)
                    continue
                raise
            except Exception as e:
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt)
                    logger.warning(f"Network error, retrying after {wait_time}s (attempt {attempt + 1}/{self.max_retries + 1})")
                    time.sleep(wait_time)
                    continue
                raise MetricAIError(f"Request failed: {str(e)}")
        
        if last_exception:
            raise last_exception
        
        raise MetricAIError("Request failed after all retries")
    
    def get(
        self,
        path: str,
        use_firebase_auth: bool = False,
        use_api_key_auth: bool = False,
        params: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make GET request."""
        return self._request(
            "GET",
            path,
            use_firebase_auth=use_firebase_auth,
            use_api_key_auth=use_api_key_auth,
            params=params,
            additional_headers=additional_headers,
        )
    
    def post(
        self,
        path: str,
        use_firebase_auth: bool = False,
        use_api_key_auth: bool = False,
        json_data: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make POST request."""
        return self._request(
            "POST",
            path,
            use_firebase_auth=use_firebase_auth,
            use_api_key_auth=use_api_key_auth,
            json_data=json_data,
            additional_headers=additional_headers,
        )
    
    def put(
        self,
        path: str,
        use_firebase_auth: bool = False,
        use_api_key_auth: bool = False,
        json_data: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make PUT request."""
        return self._request(
            "PUT",
            path,
            use_firebase_auth=use_firebase_auth,
            use_api_key_auth=use_api_key_auth,
            json_data=json_data,
            additional_headers=additional_headers,
        )
    
    def delete(
        self,
        path: str,
        use_firebase_auth: bool = False,
        use_api_key_auth: bool = False,
        additional_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make DELETE request."""
        return self._request(
            "DELETE",
            path,
            use_firebase_auth=use_firebase_auth,
            use_api_key_auth=use_api_key_auth,
            additional_headers=additional_headers,
        )
    
    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
