"""Transaction models."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """Transaction model."""
    
    transaction_id: str
    user_id: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    price_usd: str  # Decimal as string
    created_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaginationInfo(BaseModel):
    """Pagination information."""
    
    total: int
    limit: int
    offset: int
    has_more: bool


class TransactionList(BaseModel):
    """Transaction list response model."""
    
    transactions: list[Transaction]
    pagination: PaginationInfo
