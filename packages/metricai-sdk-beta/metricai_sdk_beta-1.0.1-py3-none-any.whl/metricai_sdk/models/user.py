"""User profile models."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile model."""
    
    user_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    created_at: Optional[str] = None  # Optional because update_profile doesn't return it
    updated_at: str
    last_login: Optional[str] = None
    onboarding_completed: bool = False
    preferences: Dict[str, Any] = Field(default_factory=dict)


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile."""
    
    display_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    onboarding_completed: Optional[bool] = None
