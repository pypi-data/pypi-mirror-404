"""Proxy request/response models."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ProxyRequest(BaseModel):
    """Proxy request model for AI provider requests."""
    
    model: str = Field(..., description="Model ID (e.g., 'gpt-4', 'claude-3-opus')")
    messages: List[Dict[str, Any]] = Field(..., description="Chat messages following OpenAI chat format")
    token_type: str = Field(default="text", description="Metric category: 'text', 'image', 'audio'")
    flat_price_usd: Optional[float] = Field(default=None, description="Optional fixed price per request")


class ProxyResponse(BaseModel):
    """Proxy response model for AI provider responses."""
    
    model: str
    token_type: str
    created_at: str
    completion_text: str
    price_usd: Optional[str] = Field(default=None, description="Price in USD (may be None if pricing not available)")
    price_source: str = Field(default="usage", description="'flat' or 'usage'")
    api_mode: str = Field(default="byok", description="'byok' (Bring Your Own Key) or 'shared' (MetricAI Shared API)")
    provider_key_used: Optional[str] = Field(default=None, description="'user' (BYOK) or 'metricai' (Shared API)")
    
    # Token counts
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    thought_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None
    
    # Input token breakdowns
    prompt_text_tokens: Optional[int] = None
    prompt_audio_tokens: Optional[int] = None
    prompt_image_tokens: Optional[int] = None
    prompt_video_tokens: Optional[int] = None
    
    # Output token breakdowns
    completion_text_tokens: Optional[int] = None
    completion_audio_tokens: Optional[int] = None
    
    # Prediction tokens (Grok)
    accepted_prediction_tokens: Optional[int] = None
    rejected_prediction_tokens: Optional[int] = None
    
    # Raw provider-specific fields
    raw_provider_data: Dict[str, Any] = Field(default_factory=dict)
    provider_input_tokens: Optional[int] = None
    provider_output_tokens: Optional[int] = None
    provider_prompt_token_count: Optional[int] = None
    provider_candidates_token_count: Optional[int] = None
    provider_total_token_count: Optional[int] = None

    # Token metadata - available token types, model modes, thinking config
    token_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata about token types, model modes, and thinking configuration",
    )
