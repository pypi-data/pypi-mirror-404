"""Statistics models."""

from typing import Dict, Any
from pydantic import BaseModel


class TokenStatsByModel(BaseModel):
    """Token statistics grouped by model."""
    
    # This is a flexible model that matches the backend response structure
    # The actual structure may vary, so we use Dict[str, Any]
    stats: Dict[str, Any] = {}
