"""Transactions resource."""

from typing import Optional
from metricai_sdk.http import HTTPClient
from metricai_sdk.models.transaction import Transaction, TransactionList


class TransactionsResource:
    """Transaction history resource."""
    
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def list(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> TransactionList:
        """Get transaction history with filtering.
        
        Args:
            limit: Maximum number of transactions (1-1000, default: 100)
            offset: Pagination offset (default: 0)
            start_date: Filter from date (ISO 8601 format, e.g., "2025-12-01")
            end_date: Filter until date (ISO 8601 format, e.g., "2025-12-31")
            model: Filter by model name (e.g., "gpt-4")
            provider: Filter by provider (openai, claude, gemini, grok)
        
        Returns:
            Transaction list
        """
        params = {
            "limit": limit,
            "offset": offset,
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if model:
            params["model"] = model
        if provider:
            params["provider"] = provider
        
        response = self._http.get("/transactions", use_firebase_auth=True, params=params)
        return TransactionList(**response)
    
    def get(self, transaction_id: str) -> Transaction:
        """Get a single transaction by ID.
        
        Args:
            transaction_id: Transaction ID
        
        Returns:
            Transaction details
        """
        response = self._http.get(f"/transactions/{transaction_id}", use_firebase_auth=True)
        return Transaction(**response)
