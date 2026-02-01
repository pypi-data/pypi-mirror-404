"""Wallet models."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class WalletBalance(BaseModel):
    """Wallet balance model."""
    
    user_id: str
    balance_usd: str  # Decimal as string


class LedgerEntry(BaseModel):
    """Ledger entry model."""
    
    transaction_id: str
    user_id: str
    amount_usd: str  # Decimal as string
    description: str
    transaction_type: str
    created_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LedgerResponse(BaseModel):
    """Response model for ledger list."""
    
    entries: list[LedgerEntry]


class AddFundsRequest(BaseModel):
    """Request model for adding funds."""
    
    amount_usd: float = Field(..., gt=0, description="Amount to add in USD")
    description: Optional[str] = Field(default="Manual deposit", description="Optional description")
