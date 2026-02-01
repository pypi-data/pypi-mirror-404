"""Payments resource."""

from metricai_sdk.http import HTTPClient
from metricai_sdk.models.payment import (
    PaymentOrder,
    CreateOrderRequest,
    VerifyPaymentRequest,
)


class PaymentsResource:
    """Payment management resource."""
    
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def create_order(self, amount_usd: float, description: str = "Wallet top-up") -> PaymentOrder:
        """Create a Razorpay payment order.
        
        Args:
            amount_usd: Amount to add to wallet in USD
            description: Payment description
        
        Returns:
            Payment order details
        """
        request = CreateOrderRequest(amount_usd=amount_usd, description=description)
        response = self._http.post(
            "/v1/payments/create-order",
            use_firebase_auth=True,
            json_data=request.model_dump(),
        )
        return PaymentOrder(**response)
    
    def verify(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> dict:
        """Verify Razorpay payment and credit wallet.
        
        Args:
            razorpay_order_id: Razorpay order ID
            razorpay_payment_id: Razorpay payment ID
            razorpay_signature: Razorpay payment signature
        
        Returns:
            Verification result
        """
        request = VerifyPaymentRequest(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
        )
        return self._http.post(
            "/v1/payments/verify",
            use_firebase_auth=True,
            json_data=request.model_dump(),
        )
