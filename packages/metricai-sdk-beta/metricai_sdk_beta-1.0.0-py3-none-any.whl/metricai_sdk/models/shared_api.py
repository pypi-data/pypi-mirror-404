"""Shared API models for token info, provider list, and catalog."""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class SharedAPIModelInfo(BaseModel):
    """Single model entry in Shared API token info (model id + pricing)."""

    model: str = Field(..., description="Model identifier (e.g. gpt-4o, claude-3-5-sonnet)")
    pricing: Optional[float] = Field(None, description="Price per token (input) or per unit for image/audio")


class TokenInfoRequest(BaseModel):
    """Request for Shared API token pricing info."""

    provider: str = Field(
        ...,
        description="Provider name: 'openai', 'claude', 'gemini', or 'grok'",
    )
    model: Optional[str] = Field(
        None,
        description="Optional model name to get specific pricing",
    )
    token_type: str = Field(
        default="text",
        description="Token type: 'text', 'image', or 'audio'",
    )


class TokenInfoResponse(BaseModel):
    """Response from Shared API token-info endpoint."""

    provider: str
    provider_available: bool
    available_models: Optional[List[SharedAPIModelInfo]] = None
    model_pricing: Optional[Dict[str, Optional[float]]] = None
    message: str


class SharedAPIProviderDetail(BaseModel):
    """Single provider in Shared API providers list."""

    provider_id: str
    display_name: str
    description: str
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    documentation_url: Optional[str] = None
    available: bool = True
    model_count: int = 0
    available_models: List[str] = Field(default_factory=list)
    default_model: Optional[str] = None
    token_types: List[str] = Field(default_factory=list)
    modalities: List[str] = Field(default_factory=list)
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_audio: bool = False


class SharedAPIProvidersResponse(BaseModel):
    """Response from GET /v1/shared-api/providers."""

    shared_api_available: bool
    providers: List[SharedAPIProviderDetail]
    message: str


class ProviderCatalogEntry(BaseModel):
    """Single provider in Shared API catalog."""

    provider_id: str
    display_name: str
    description: str
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    documentation_url: Optional[str] = None
    supported_token_types: List[str] = Field(default_factory=list)
    supported_modalities: List[str] = Field(default_factory=list)
    available_models: List[str] = Field(default_factory=list)
    default_model: Optional[str] = None
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_audio: bool = False
    pricing_info_url: Optional[str] = None
    is_active: bool = True
    is_available_via_shared_api: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SharedAPICatalogResponse(BaseModel):
    """Response from GET /v1/shared-api/catalog."""

    providers: List[ProviderCatalogEntry]
    total_count: int
    available_via_shared_api: int
