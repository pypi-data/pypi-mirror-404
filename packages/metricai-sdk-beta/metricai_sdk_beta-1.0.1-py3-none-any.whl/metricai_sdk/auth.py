"""Helpers to obtain Firebase ID tokens and create users for use with MetricAIClient."""

import os
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from metricai_sdk.models import UserProfile

import httpx

from metricai_sdk.errors import AuthenticationError, ValidationError


FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
FIREBASE_SIGNUP_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
FIREBASE_REFRESH_URL = "https://securetoken.googleapis.com/v1/token"

# Backend URL (default for client). Override with METRICAI_BASE_URL.
DEFAULT_METRICAI_BASE_URL = "https://metricai-backend-epadd3mwtq-uc.a.run.app"
# Backend URL used for auth (login/refresh) — same as base URL.
DEFAULT_METRICAI_AUTH_BASE_URL = "https://metricai-backend-epadd3mwtq-uc.a.run.app"

def get_firebase_token(
    email: str,
    password: str,
    *,
    firebase_api_key: Optional[str] = None,
    timeout: float = 30.0,
) -> str:
    """Sign in with email/password and return a Firebase ID token.

    Calls Firebase Auth REST API (signInWithPassword). Use the returned token
    as ``firebase_token`` when creating ``MetricAIClient`` for user-scoped
    endpoints (profile, wallet, API keys, providers, payments).

    The Firebase Web API key is the public key from your Firebase project
    (Project settings → General → Web API Key). For MetricAI users, use the
    key provided in MetricAI docs or dashboard.

    Args:
        email: User email address.
        password: User password.
        firebase_api_key: Firebase Web API key. If not set, reads from
            env ``FIREBASE_WEB_API_KEY`` or ``METRICAI_FIREBASE_WEB_API_KEY``.
        timeout: Request timeout in seconds.

    Returns:
        Firebase ID token (JWT string). Pass to ``MetricAIClient(firebase_token=...)``.

    Raises:
        ValidationError: Missing API key or invalid email/password format.
        AuthenticationError: Invalid email or password (Firebase auth failed).

    Example:
        >>> from metricai_sdk import MetricAIClient, get_firebase_token
        >>> token = get_firebase_token("user@example.com", "secret", firebase_api_key="...")
        >>> client = MetricAIClient(firebase_token=token, api_key="...")
        >>> balance = client.wallet.get_balance()
    """
    key = _get_firebase_api_key(firebase_api_key)
    email = (email or "").strip()
    if not email:
        raise ValidationError("email must be non-empty.")
    if not password:
        raise ValidationError("password must be non-empty.")

    url = f"{FIREBASE_AUTH_URL}?key={key}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
    except httpx.TimeoutException as e:
        raise ValidationError(f"Firebase auth request timed out: {e}") from e
    except httpx.RequestError as e:
        raise ValidationError(f"Firebase auth request failed: {e}") from e

    data = response.json() if response.content else {}

    if not response.is_success:
        err = data.get("error", {})
        msg = err.get("message", response.text or f"HTTP {response.status_code}")
        # Map Firebase error codes to SDK errors
        if response.status_code == 400:
            if "INVALID_LOGIN_CREDENTIALS" in str(msg) or "EMAIL_NOT_FOUND" in str(msg) or "INVALID_PASSWORD" in str(msg):
                raise AuthenticationError(f"Invalid email or password: {msg}", response=data)
            raise ValidationError(f"Firebase auth error: {msg}", response=data)
        if response.status_code == 401:
            raise AuthenticationError(f"Firebase auth failed: {msg}", response=data)
        raise AuthenticationError(f"Firebase auth failed: {msg}", response=data)

    id_token = data.get("idToken")
    if not id_token:
        raise AuthenticationError("Firebase response missing idToken", response=data)

    return id_token


def get_firebase_token_with_refresh(
    email: str,
    password: str,
    *,
    firebase_api_key: Optional[str] = None,
    timeout: float = 30.0,
) -> Tuple[str, str]:
    """Sign in with email/password and return both ID token and refresh token.

    Use this for long-lived sessions: store the refresh token securely and call
    ``refresh_firebase_token(refresh_token)`` before the ID token expires (~1 hour)
    or when you get 401, then use the new ID token with ``MetricAIClient``.

    Args:
        email: User email address.
        password: User password.
        firebase_api_key: Firebase Web API key (or env METRICAI_FIREBASE_WEB_API_KEY).
        timeout: Request timeout in seconds.

    Returns:
        (id_token, refresh_token). Use id_token with MetricAIClient; store
        refresh_token and pass to refresh_firebase_token when needed.
    """
    key = _get_firebase_api_key(firebase_api_key)
    email = (email or "").strip()
    if not email:
        raise ValidationError("email must be non-empty.")
    if not password:
        raise ValidationError("password must be non-empty.")

    url = f"{FIREBASE_AUTH_URL}?key={key}"
    payload = {"email": email, "password": password, "returnSecureToken": True}

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
    except httpx.TimeoutException as e:
        raise ValidationError(f"Firebase auth request timed out: {e}") from e
    except httpx.RequestError as e:
        raise ValidationError(f"Firebase auth request failed: {e}") from e

    data = response.json() if response.content else {}
    if not response.is_success:
        err = data.get("error", {})
        msg = err.get("message", response.text or f"HTTP {response.status_code}")
        if response.status_code == 400:
            if "INVALID_LOGIN_CREDENTIALS" in str(msg) or "EMAIL_NOT_FOUND" in str(msg) or "INVALID_PASSWORD" in str(msg):
                raise AuthenticationError(f"Invalid email or password: {msg}", response=data)
            raise ValidationError(f"Firebase auth error: {msg}", response=data)
        raise AuthenticationError(f"Firebase auth failed: {msg}", response=data)

    id_token = data.get("idToken")
    refresh_token = data.get("refreshToken")
    if not id_token or not refresh_token:
        raise AuthenticationError("Firebase response missing idToken or refreshToken", response=data)
    return (id_token, refresh_token)


def refresh_firebase_token(
    refresh_token: str,
    *,
    firebase_api_key: Optional[str] = None,
    timeout: float = 30.0,
) -> str:
    """Exchange a Firebase refresh token for a new ID token.

    Firebase ID tokens expire in about 1 hour. Use the refresh token (returned
    from sign-in/sign-up when using ``get_firebase_token_with_refresh`` or
    ``create_firebase_user_with_refresh``) to get a new ID token without
    re-entering the password.

    Args:
        refresh_token: Firebase refresh token from a previous sign-in/sign-up.
        firebase_api_key: Firebase Web API key. If not set, reads from env
            ``FIREBASE_WEB_API_KEY`` or ``METRICAI_FIREBASE_WEB_API_KEY``.
        timeout: Request timeout in seconds.

    Returns:
        New Firebase ID token (JWT string). Pass to ``MetricAIClient(firebase_token=...)``.

    Raises:
        ValidationError: Missing API key or empty refresh token.
        AuthenticationError: Refresh token invalid or expired (user must sign in again).

    Example:
        >>> # On first sign-in, get and store the refresh token (e.g. get_firebase_token_with_refresh).
        >>> # Before the ID token expires (~1 hour) or when you get 401:
        >>> new_token = refresh_firebase_token(stored_refresh_token, firebase_api_key="...")
        >>> client = MetricAIClient(firebase_token=new_token, api_key="...")
    """
    key = _get_firebase_api_key(firebase_api_key)
    refresh_token = (refresh_token or "").strip()
    if not refresh_token:
        raise ValidationError("refresh_token must be non-empty.")

    url = f"{FIREBASE_REFRESH_URL}?key={key}"
    # Firebase expects application/x-www-form-urlencoded
    payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except httpx.TimeoutException as e:
        raise ValidationError(f"Firebase refresh request timed out: {e}") from e
    except httpx.RequestError as e:
        raise ValidationError(f"Firebase refresh request failed: {e}") from e

    data = response.json() if response.content else {}

    if not response.is_success:
        err = data.get("error", {})
        msg = err.get("message", response.text or f"HTTP {response.status_code}")
        if response.status_code in (400, 401):
            raise AuthenticationError(
                f"Refresh failed (token may be expired or invalid): {msg}",
                response=data,
            )
        raise AuthenticationError(f"Firebase refresh failed: {msg}", response=data)

    # securetoken.googleapis.com returns "id_token" (underscore)
    id_token = data.get("id_token") or data.get("idToken")
    if not id_token:
        raise AuthenticationError("Firebase response missing id_token", response=data)
    return id_token


def _get_firebase_api_key(firebase_api_key: Optional[str]) -> str:
    # Resolution order: explicit argument, then env vars. No default key in SDK.
    key = (
        firebase_api_key
        or os.environ.get("METRICAI_FIREBASE_WEB_API_KEY")
        or os.environ.get("FIREBASE_WEB_API_KEY")
    )
    if not key or not key.strip():
        raise ValidationError(
            "Firebase Web API key required. Set firebase_api_key=... or env "
            "METRICAI_FIREBASE_WEB_API_KEY / FIREBASE_WEB_API_KEY."
        )
    return key.strip()


def create_firebase_user(
    email: str,
    password: str,
    *,
    display_name: Optional[str] = None,
    firebase_api_key: Optional[str] = None,
    timeout: float = 30.0,
) -> str:
    """Create a new Firebase user (sign up) and return a Firebase ID token.

    First-time users do not need a token beforehand: Firebase returns the ID
    token in the sign-up response; this function returns that token.

    Calls Firebase Auth REST API (signUp). Use the returned token as
    ``firebase_token`` when creating ``MetricAIClient``. Then call
    ``client.user.get_profile()`` to create the MetricAI profile (get_profile
    creates the profile if it doesn't exist).

    Args:
        email: User email address.
        password: User password (Firebase requires at least 6 characters).
        display_name: Optional display name for the new user.
        firebase_api_key: Firebase Web API key. If not set, reads from
            env ``FIREBASE_WEB_API_KEY`` or ``METRICAI_FIREBASE_WEB_API_KEY``.
        timeout: Request timeout in seconds.

    Returns:
        Firebase ID token (JWT string). Pass to ``MetricAIClient(firebase_token=...)``.

    Raises:
        ValidationError: Missing API key, invalid email/password, or password too short.
        AuthenticationError: Sign-up failed (e.g. email already in use).

    Example:
        >>> from metricai_sdk import MetricAIClient, create_firebase_user
        >>> token = create_firebase_user("new@example.com", "secret123", display_name="New User", ...)
        >>> client = MetricAIClient(firebase_token=token, api_key="...")
        >>> profile = client.user.get_profile()  # creates MetricAI profile on first use
    """
    key = _get_firebase_api_key(firebase_api_key)
    email = (email or "").strip()
    if not email:
        raise ValidationError("email must be non-empty.")
    if not password:
        raise ValidationError("password must be non-empty.")
    if len(password) < 6:
        raise ValidationError("password must be at least 6 characters (Firebase requirement).")

    url = f"{FIREBASE_SIGNUP_URL}?key={key}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }
    if display_name is not None and (display_name or "").strip():
        payload["displayName"] = display_name.strip()

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
    except httpx.TimeoutException as e:
        raise ValidationError(f"Firebase sign-up request timed out: {e}") from e
    except httpx.RequestError as e:
        raise ValidationError(f"Firebase sign-up request failed: {e}") from e

    data = response.json() if response.content else {}

    if not response.is_success:
        err = data.get("error", {})
        msg = err.get("message", response.text or f"HTTP {response.status_code}")
        if response.status_code == 400:
            if "EMAIL_EXISTS" in str(msg):
                raise AuthenticationError(f"Email already in use: {msg}", response=data)
            raise ValidationError(f"Firebase sign-up error: {msg}", response=data)
        if response.status_code == 401:
            raise AuthenticationError(f"Firebase sign-up failed: {msg}", response=data)
        raise AuthenticationError(f"Firebase sign-up failed: {msg}", response=data)

    id_token = data.get("idToken")
    if not id_token:
        raise AuthenticationError("Firebase response missing idToken", response=data)
    return id_token


def create_firebase_user_with_refresh(
    email: str,
    password: str,
    *,
    display_name: Optional[str] = None,
    firebase_api_key: Optional[str] = None,
    timeout: float = 30.0,
) -> Tuple[str, str]:
    """Create a Firebase user (sign up) and return both ID token and refresh token.

    Use this for long-lived sessions: store the refresh token securely and call
    ``refresh_firebase_token(refresh_token)`` before the ID token expires (~1 hour)
    or when you get 401.

    Args:
        email: User email address.
        password: User password (at least 6 characters).
        display_name: Optional display name.
        firebase_api_key: Firebase Web API key (or env).
        timeout: Request timeout in seconds.

    Returns:
        (id_token, refresh_token). Use id_token with MetricAIClient; store
        refresh_token and pass to refresh_firebase_token when needed.
    """
    key = _get_firebase_api_key(firebase_api_key)
    email = (email or "").strip()
    if not email:
        raise ValidationError("email must be non-empty.")
    if not password:
        raise ValidationError("password must be non-empty.")
    if len(password) < 6:
        raise ValidationError("password must be at least 6 characters (Firebase requirement).")

    url = f"{FIREBASE_SIGNUP_URL}?key={key}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    if display_name is not None and (display_name or "").strip():
        payload["displayName"] = display_name.strip()

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
    except httpx.TimeoutException as e:
        raise ValidationError(f"Firebase sign-up request timed out: {e}") from e
    except httpx.RequestError as e:
        raise ValidationError(f"Firebase sign-up request failed: {e}") from e

    data = response.json() if response.content else {}
    if not response.is_success:
        err = data.get("error", {})
        msg = err.get("message", response.text or f"HTTP {response.status_code}")
        if response.status_code == 400:
            if "EMAIL_EXISTS" in str(msg):
                raise AuthenticationError(f"Email already in use: {msg}", response=data)
            raise ValidationError(f"Firebase sign-up error: {msg}", response=data)
        raise AuthenticationError(f"Firebase sign-up failed: {msg}", response=data)

    id_token = data.get("idToken")
    refresh_token = data.get("refreshToken")
    if not id_token or not refresh_token:
        raise AuthenticationError("Firebase response missing idToken or refreshToken", response=data)
    return (id_token, refresh_token)


def create_user_and_profile(
    email: str,
    password: str,
    *,
    display_name: Optional[str] = None,
    firebase_api_key: Optional[str] = None,
    metricai_api_key: Optional[str] = None,
    metricai_base_url: Optional[str] = None,
    timeout: float = 30.0,
) -> Tuple[str, Optional["UserProfile"]]:
    """Create a Firebase user and (optionally) their MetricAI profile in one flow.

    First-time users do not need a token beforehand: the token comes from the
    sign-up response.

    1. Creates the user in Firebase (sign up) and gets an ID token from the response.
    2. If ``metricai_api_key`` is provided, creates a client and calls
       ``get_profile()``, which creates the MetricAI profile on first use,
       and returns the profile; otherwise returns ``(token, None)``.

    Args:
        email: User email address.
        password: User password (at least 6 characters).
        display_name: Optional display name (Firebase and profile).
        firebase_api_key: Firebase Web API key (or env METRICAI_FIREBASE_WEB_API_KEY).
        metricai_api_key: If set, also create MetricAI profile by calling get_profile().
        metricai_base_url: Optional MetricAI API base URL (default if not set).
        timeout: Request timeout in seconds.

    Returns:
        ``(firebase_id_token, user_profile)``. ``user_profile`` is ``None`` if
        ``metricai_api_key`` was not provided.

    Raises:
        ValidationError: Missing/invalid inputs or password too short.
        AuthenticationError: Email already in use or sign-up failed.

    Example:
        >>> from metricai_sdk import create_user_and_profile
        >>> token, profile = create_user_and_profile(
        ...     "new@example.com", "secret123",
        ...     display_name="New User",
        ...     metricai_api_key="...",
        ... )
        >>> print(profile.user_id, profile.display_name)
    """
    token = create_firebase_user(
        email=email,
        password=password,
        display_name=display_name,
        firebase_api_key=firebase_api_key,
        timeout=timeout,
    )
    if not metricai_api_key or not metricai_api_key.strip():
        return (token, None)

    from metricai_sdk import MetricAIClient
    from metricai_sdk.models import UserProfile

    client = MetricAIClient(
        firebase_token=token,
        api_key=metricai_api_key.strip(),
        base_url=metricai_base_url,
    )
    try:
        profile = client.user.get_profile()
        return (token, profile)
    finally:
        client.close()


def _metricai_base_url(override: Optional[str] = None) -> str:
    """Resolve MetricAI API base URL (for client)."""
    url = (
        (override or "").strip().rstrip("/")
        or os.environ.get("METRICAI_BASE_URL", "").strip().rstrip("/")
        or DEFAULT_METRICAI_BASE_URL
    )
    return url or DEFAULT_METRICAI_BASE_URL


def _metricai_auth_base_url(override: Optional[str] = None) -> str:
    """Resolve base URL for auth (login/refresh). Uses backend by default so login works."""
    url = (
        (override or "").strip().rstrip("/")
        or os.environ.get("METRICAI_AUTH_BASE_URL", "").strip().rstrip("/")
        or os.environ.get("METRICAI_BASE_URL", "").strip().rstrip("/")
        or DEFAULT_METRICAI_AUTH_BASE_URL
    )
    return url or DEFAULT_METRICAI_AUTH_BASE_URL


def login(
    email: str,
    password: str,
    *,
    base_url: Optional[str] = None,
    timeout: float = 30.0,
) -> str:
    """Sign in with email and password via the MetricAI backend and return a Firebase ID token.
    
    Uses the fixed MetricAI backend URL. Users only need to pass email and password;
    no Firebase Web API key or API URL is required.
    
    Args:
        email: User email address.
        password: User password.
        base_url: Optional MetricAI API base URL (defaults to production gateway).
        timeout: Request timeout in seconds.
    
    Returns:
        Firebase ID token (JWT string). Pass to ``MetricAIClient(firebase_token=...)``.
    
    Raises:
        ValidationError: Invalid email/password format.
        AuthenticationError: Invalid email or password (backend auth failed).
    
    Example:
        >>> from metricai_sdk import MetricAIClient, login
        >>> token = login("user@example.com", "password123")
        >>> client = MetricAIClient(firebase_token=token, api_key="...")
    """
    return get_firebase_token_from_api(
        email, password, api_base_url=base_url, timeout=timeout
    )


def get_firebase_token_from_api(
    email: str,
    password: str,
    *,
    api_base_url: Optional[str] = None,
    timeout: float = 30.0,
) -> str:
    """Sign in via MetricAI backend (or custom API) and return a Firebase ID token.
    
    By default uses the fixed MetricAI backend URL. Pass ``api_base_url`` only if
    you use a custom backend. This way SDK users don't need the Firebase Web API key.
    
    Backend contract:
        POST {api_base_url}/api/auth/login
        Body: {"email": "...", "password": "..."}
        Response: {"idToken": "...", "refreshToken": "...", "expiresIn": "3600"}
    
    Args:
        email: User email address.
        password: User password.
        api_base_url: Optional base URL (defaults to MetricAI backend).
        timeout: Request timeout in seconds.
    
    Returns:
        Firebase ID token (JWT string). Pass to ``MetricAIClient(firebase_token=...)``.
    
    Raises:
        ValidationError: Invalid email/password format.
        AuthenticationError: Invalid email or password (backend auth failed).
    
    Example:
        >>> from metricai_sdk import MetricAIClient, login
        >>> token = login("user@example.com", "password123")
        >>> client = MetricAIClient(firebase_token=token, api_key="...")
    """
    api_base_url = _metricai_auth_base_url(api_base_url)
    
    email = (email or "").strip()
    if not email:
        raise ValidationError("email must be non-empty.")
    if not password:
        raise ValidationError("password must be non-empty.")
    
    url = f"{api_base_url}/api/auth/login"
    payload = {
        "email": email,
        "password": password,
    }
    
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
    except httpx.TimeoutException as e:
        raise ValidationError(f"API request timed out: {e}") from e
    except httpx.RequestError as e:
        raise ValidationError(f"API request failed: {e}") from e
    
    data = response.json() if response.content else {}
    
    if not response.is_success:
        error_msg = _extract_error_message(data, response)
        full_msg = f"Login failed: POST {url} → {response.status_code} {error_msg}"
        
        # Helpful message if endpoint doesn't exist (404)
        if response.status_code == 404:
            full_msg += (
                "\n\nNote: The MetricAI backend needs to expose POST /api/auth/login "
                "that wraps Firebase sign-in. See examples/login_api_server.py for a reference implementation."
            )
            raise AuthenticationError(full_msg, response=data)
        
        if response.status_code == 400:
            raise ValidationError(full_msg, response=data)
        if response.status_code == 401:
            raise AuthenticationError(full_msg, response=data)
        raise AuthenticationError(full_msg, response=data)
    
    id_token = data.get("idToken")
    if not id_token:
        raise AuthenticationError("API response missing idToken", response=data)
    
    return id_token


def _extract_error_message(data: dict, response: httpx.Response) -> str:
    """Get a readable error string from API response."""
    if isinstance(data.get("error"), dict):
        return data["error"].get("message", str(data["error"]))
    if isinstance(data.get("error"), str):
        return data["error"]
    if data.get("message"):
        return str(data["message"])
    if response.text:
        return response.text[:200]
    return f"HTTP {response.status_code}"


def get_firebase_token_from_api_with_refresh(
    email: str,
    password: str,
    *,
    api_base_url: Optional[str] = None,
    timeout: float = 30.0,
) -> Tuple[str, str]:
    """Sign in via MetricAI backend (or custom API) and return both ID token and refresh token.
    
    Similar to ``get_firebase_token_from_api`` but also returns the refresh token
    for long-lived sessions. Use ``refresh_firebase_token_from_api`` to get a new
    ID token when it expires. Uses fixed MetricAI backend URL by default.
    
    Args:
        email: User email address.
        password: User password.
        api_base_url: Optional base URL (defaults to MetricAI backend).
        timeout: Request timeout in seconds.
    
    Returns:
        (id_token, refresh_token). Use id_token with MetricAIClient; store
        refresh_token and pass to refresh_firebase_token_from_api when needed.
    
    Raises:
        ValidationError: Invalid email/password format.
        AuthenticationError: Invalid email or password (backend auth failed).
    """
    api_base_url = _metricai_auth_base_url(api_base_url)
    
    email = (email or "").strip()
    if not email:
        raise ValidationError("email must be non-empty.")
    if not password:
        raise ValidationError("password must be non-empty.")
    
    url = f"{api_base_url}/api/auth/login"
    payload = {
        "email": email,
        "password": password,
    }
    
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
    except httpx.TimeoutException as e:
        raise ValidationError(f"API request timed out: {e}") from e
    except httpx.RequestError as e:
        raise ValidationError(f"API request failed: {e}") from e
    
    data = response.json() if response.content else {}
    
    if not response.is_success:
        error_msg = data.get("error", response.text or f"HTTP {response.status_code}")
        if response.status_code == 400:
            raise ValidationError(f"API error: {error_msg}", response=data)
        if response.status_code == 401:
            raise AuthenticationError(f"Invalid email or password: {error_msg}", response=data)
        raise AuthenticationError(f"API error: {error_msg}", response=data)
    
    id_token = data.get("idToken")
    refresh_token = data.get("refreshToken")
    
    if not id_token:
        raise AuthenticationError("API response missing idToken", response=data)
    if not refresh_token:
        raise AuthenticationError("API response missing refreshToken", response=data)
    
    return (id_token, refresh_token)


def refresh_firebase_token_from_api(
    refresh_token: str,
    *,
    api_base_url: Optional[str] = None,
    timeout: float = 30.0,
) -> str:
    """Refresh a Firebase ID token via the MetricAI backend.
    
    Calls the MetricAI backend (or custom API) to exchange a refresh token for a
    new ID token. Use this when the ID token expires (~1 hour). Uses fixed
    MetricAI backend URL by default.
    
    Backend contract:
        POST {api_base_url}/api/auth/refresh
        Body: {"refreshToken": "..."}
        Response: {"idToken": "...", "expiresIn": "3600"}
    
    Args:
        refresh_token: Firebase refresh token from a previous sign-in.
        api_base_url: Optional base URL (defaults to MetricAI backend).
        timeout: Request timeout in seconds.
    
    Returns:
        New Firebase ID token (JWT string). Pass to ``MetricAIClient(firebase_token=...)``.
    
    Raises:
        ValidationError: Empty refresh token.
        AuthenticationError: Refresh token invalid or expired (user must sign in again).
    """
    api_base_url = _metricai_auth_base_url(api_base_url)
    
    refresh_token = (refresh_token or "").strip()
    if not refresh_token:
        raise ValidationError("refresh_token must be non-empty.")
    
    url = f"{api_base_url}/api/auth/refresh"
    payload = {
        "refreshToken": refresh_token,
    }
    
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
    except httpx.TimeoutException as e:
        raise ValidationError(f"API request timed out: {e}") from e
    except httpx.RequestError as e:
        raise ValidationError(f"API request failed: {e}") from e
    
    data = response.json() if response.content else {}
    
    if not response.is_success:
        error_msg = data.get("error", response.text or f"HTTP {response.status_code}")
        if response.status_code == 400:
            raise ValidationError(f"API error: {error_msg}", response=data)
        if response.status_code == 401:
            raise AuthenticationError(f"Refresh token invalid or expired: {error_msg}", response=data)
        raise AuthenticationError(f"API error: {error_msg}", response=data)
    
    id_token = data.get("idToken")
    if not id_token:
        raise AuthenticationError("API response missing idToken", response=data)
    
    return id_token
