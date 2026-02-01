"""User resource."""

from metricai_sdk.http import HTTPClient
from metricai_sdk.models.user import UserProfile, UpdateProfileRequest


class UserResource:
    """User profile resource."""
    
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def get_profile(self) -> UserProfile:
        """Get user profile. Creates the MetricAI profile on first use (no separate create endpoint).
        
        Returns:
            User profile
        """
        response = self._http.get("/user/profile", use_firebase_auth=True)
        return UserProfile(**response)
    
    def update_profile(
        self,
        display_name: str = None,
        preferences: dict = None,
        onboarding_completed: bool = None,
    ) -> UserProfile:
        """Update user profile.
        
        Args:
            display_name: User display name
            preferences: User preferences dict
            onboarding_completed: Onboarding completion status
        
        Returns:
            Updated user profile
        """
        request = UpdateProfileRequest(
            display_name=display_name,
            preferences=preferences,
            onboarding_completed=onboarding_completed,
        )
        response = self._http.put(
            "/user/profile",
            use_firebase_auth=True,
            json_data=request.model_dump(exclude_none=True),
        )
        return UserProfile(**response)
    
    def complete_onboarding(self) -> dict:
        """Mark user onboarding as complete.
        
        Returns:
            Success response
        """
        return self._http.post("/user/profile/onboarding-complete", use_firebase_auth=True)
    
    def test_auth(self) -> dict:
        """Test authentication.
        
        Returns:
            Authentication test response
        """
        return self._http.get("/test-auth", use_firebase_auth=True)
