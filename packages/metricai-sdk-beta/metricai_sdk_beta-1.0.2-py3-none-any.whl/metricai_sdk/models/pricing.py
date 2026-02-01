"""Pricing models."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ModelPricingOverride(BaseModel):
    """Model-specific pricing override."""

    model: str
    markup_percentage: float
    enabled: bool


class GlobalMarkup(BaseModel):
    """Global markup configuration."""

    default_markup_percentage: float
    updated_at: str


class PricingConfig(BaseModel):
    """Pricing configuration model matching the backend response."""

    global_markup: GlobalMarkup
    model_overrides: List[ModelPricingOverride] = Field(default_factory=list)
    pricing_table: Dict[str, Any] = Field(default_factory=dict)


class UpdateGlobalMarkupRequest(BaseModel):
    """Request model for updating global markup."""

    default_markup_percentage: float = Field(
        ...,
        ge=0,
        description="New default markup percentage",
    )


class UpdateModelPricingRequest(BaseModel):
    """Request model for updating model pricing."""

    markup_percentage: float = Field(
        ...,
        ge=0,
        description="Custom markup percentage for this model",
    )
    enabled: bool = Field(
        default=True,
        description="Whether this override is active",
    )


class TokenRate(BaseModel):
    """Token rate model matching /pricing/rates response."""

    model: str
    provider: str
    markup_percentage: float

    # Base rates per 1k tokens
    input_per_1k: Optional[float] = None
    cached_input_per_1k: Optional[float] = None
    output_per_1k: Optional[float] = None

    # Final user rates per 1k tokens (after markup)
    your_input_rate: Optional[float] = None
    your_cached_input_rate: Optional[float] = None
    your_output_rate: Optional[float] = None


class TokenRates(BaseModel):
    """Token rates response model."""

    rates: List[TokenRate]
    summary: Dict[str, Any] = Field(default_factory=dict)

