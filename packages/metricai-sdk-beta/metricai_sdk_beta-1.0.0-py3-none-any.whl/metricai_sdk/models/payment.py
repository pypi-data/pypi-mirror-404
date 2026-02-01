"""Payment models."""

from pydantic import BaseModel, Field


class PaymentOrder(BaseModel):
    """Payment order model."""
    
    success: bool
    message: str
    order_id: str
    razorpay_order_id: str
    amount_usd: str  # Decimal as string
    amount_inr: str  # Decimal as string
    currency: str
    user_id: str
    description: str
    status: str
    created_at: str


class CreateOrderRequest(BaseModel):
    """Request model for creating payment order."""
    
    amount_usd: float = Field(..., gt=0, description="Amount to add to wallet in USD")
    description: str = Field(default="Wallet top-up", description="Payment description")


class VerifyPaymentRequest(BaseModel):
    """Request model for verifying payment."""
    
    razorpay_order_id: str = Field(..., description="Razorpay order ID")
    razorpay_payment_id: str = Field(..., description="Razorpay payment ID")
    razorpay_signature: str = Field(..., description="Razorpay payment signature")
