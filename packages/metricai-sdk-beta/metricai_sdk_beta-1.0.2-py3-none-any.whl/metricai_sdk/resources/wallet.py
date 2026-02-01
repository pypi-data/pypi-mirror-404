"""Wallet resource."""

from typing import Optional
from metricai_sdk.http import HTTPClient
from metricai_sdk.models.wallet import WalletBalance, LedgerEntry, AddFundsRequest


class WalletResource:
    """Wallet management resource."""
    
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def get_balance(self) -> WalletBalance:
        """Get wallet balance.
        
        Returns:
            Wallet balance
        """
        response = self._http.get("/wallet/balance", use_firebase_auth=True)
        return WalletBalance(**response)
    
    def get_ledger(self, limit: Optional[int] = 100) -> list[LedgerEntry]:
        """Get wallet ledger entries.
        
        Args:
            limit: Maximum number of entries to return (default: 100)
        
        Returns:
            List of ledger entries
        """
        params = {}
        if limit is not None:
            params["limit"] = limit
        
        response = self._http.get("/wallet/ledger", use_firebase_auth=True, params=params)
        return [LedgerEntry(**entry) for entry in response.get("entries", [])]
    
    def add_funds(self, amount_usd: float, description: Optional[str] = None) -> dict:
        """Add funds to wallet (deprecated, use payments.create_order instead).
        
        Args:
            amount_usd: Amount to add in USD
            description: Optional description
        
        Returns:
            Response with updated balance
        """
        request = AddFundsRequest(amount_usd=amount_usd, description=description)
        return self._http.post(
            "/wallet/add-funds",
            use_firebase_auth=True,
            json_data=request.model_dump(),
        )
