"""Provider connection models."""

from typing import Optional, List
from pydantic import BaseModel, Field


class ProviderConnection(BaseModel):
    """Provider connection model."""
    
    connection_id: str
    provider: str
    name: str
    endpoint: Optional[str] = None
    region: Optional[str] = None
    connected: bool
    last_tested: Optional[str] = None
    last_used: Optional[str] = None
    total_requests: int = 0
    enabled_models: Optional[List[str]] = None
    created_at: str
    updated_at: str


class CreateProviderRequest(BaseModel):
    """Request model for creating provider connection."""
    
    provider: str = Field(..., description="Provider name: openai, claude, gemini, grok")
    name: str = Field(..., description="Custom name for the connection")
    api_key: str = Field(..., description="Provider API key")
    endpoint: Optional[str] = Field(default=None, description="Optional custom endpoint URL")
    region: Optional[str] = Field(default=None, description="Optional region")
    enabled_models: Optional[List[str]] = Field(default=None, description="Optional list of enabled model names")


class UpdateProviderRequest(BaseModel):
    """Request model for updating provider connection."""
    
    name: Optional[str] = Field(default=None, description="Custom name for the connection")
    api_key: Optional[str] = Field(default=None, description="Provider API key")
    endpoint: Optional[str] = Field(default=None, description="Optional custom endpoint URL")
    region: Optional[str] = Field(default=None, description="Optional region")
    connected: Optional[bool] = Field(default=None, description="Connection status")
    enabled_models: Optional[List[str]] = Field(default=None, description="List of enabled model names")


class TestProviderResponse(BaseModel):
    """Response model for testing provider connection."""
    
    connection_id: str
    connected: bool
    last_tested: str
    error: Optional[str] = None


class AvailableProvidersResponse(BaseModel):
    """Response model for available providers."""
    
    shared_api_available: bool
    providers: List[str]
    message: str


class ListProvidersResponse(BaseModel):
    """Response model for listing providers."""
    
    connections: list[ProviderConnection]
