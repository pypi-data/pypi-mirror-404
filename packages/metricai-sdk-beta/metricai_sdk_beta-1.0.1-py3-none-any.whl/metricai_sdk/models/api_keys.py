"""API key models."""

from typing import Optional
from pydantic import BaseModel, Field


class APIKey(BaseModel):
    """API key model."""
    
    key_id: str
    name: Optional[str] = None
    created_at: str
    last_used: Optional[str] = None


class CreateAPIKeyRequest(BaseModel):
    """Request model for creating API key."""
    
    name: Optional[str] = Field(default=None, description="Optional name/description for the API key")


class CreateAPIKeyResponse(BaseModel):
    """Response model for creating API key."""
    
    api_key: str  # Plain key (shown only once)
    key_id: str
    name: Optional[str] = None
    created_at: str
    warning: str


class ListAPIKeysResponse(BaseModel):
    """Response model for listing API keys."""
    
    keys: list[APIKey]
