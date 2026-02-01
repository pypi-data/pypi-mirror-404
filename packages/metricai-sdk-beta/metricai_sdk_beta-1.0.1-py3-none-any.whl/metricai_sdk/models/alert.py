"""Alert models."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class Alert(BaseModel):
    """Alert model matching the backend alert response."""

    # Backend returns "id" – expose it as "alert_id" in the SDK
    alert_id: str = Field(alias="id")

    type: str
    severity: str
    status: str
    message: str
    model: Optional[str] = None
    provider: Optional[str] = None
    threshold: Optional[Dict[str, Any]] = None
    current_value: Optional[float] = None

    # Backend returns "timestamp" – expose it as "created_at" in the SDK
    created_at: str = Field(alias="timestamp")

    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class AlertRule(BaseModel):
    """Alert rule model matching the backend rule response."""

    # Backend returns "id" – expose it as "rule_id" in the SDK
    rule_id: str = Field(alias="id")

    name: str
    condition: str
    severity: str
    notification_channels: List[str]
    enabled: bool
    created_at: str
    updated_at: str

    # Structured condition fields for custom cost alerts
    metric: Optional[str] = None
    operator: Optional[str] = None
    threshold_value: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True)


class CreateAlertRequest(BaseModel):
    """Request model for creating alert."""

    type: str = Field(..., description="Alert type: error_rate, latency, cost, anomaly, availability, quota")
    severity: str = Field(..., description="Severity level: critical, warning, or info")
    message: str = Field(..., description="Human-readable alert message")
    model: Optional[str] = Field(None, description="Model name if alert is model-specific")
    provider: Optional[str] = Field(None, description="Provider name if alert is provider-specific")
    threshold: Optional[Dict[str, Any]] = Field(None, description="Threshold that was exceeded")
    current_value: Optional[float] = Field(None, description="Current metric value that triggered the alert")


class CreateAlertRuleRequest(BaseModel):
    """Request model for creating alert rule.

    Supports both legacy string conditions and structured cost alerts.
    """

    name: str = Field(..., description="Human-readable rule name")
    # Legacy condition string (still supported)
    condition: Optional[str] = Field(
        None,
        description="Alert condition expression (e.g., 'error_rate > 1%')",
    )
    severity: str = Field(..., description="Severity level: critical, warning, or info")
    notification_channels: List[str] = Field(
        ...,
        description="Notification channels: email, webhook, slack, dashboard",
    )

    # Structured condition fields (for custom cost alerts)
    metric: Optional[str] = Field(
        None,
        description="Metric name: wallet_balance, daily_cost, weekly_cost, monthly_cost, total_cost",
    )
    operator: Optional[str] = Field(
        None,
        description="Comparison operator: >, <, >=, <=, ==, !=",
    )
    threshold_value: Optional[float] = Field(
        None,
        description="Threshold value (e.g., 1.0 for $1)",
    )


class UpdateAlertRequest(BaseModel):
    """Request model for updating alert."""

    status: Optional[str] = Field(None, description="New status: active, acknowledged, or resolved")
    message: Optional[str] = Field(None, description="Updated message")


class ListAlertsResponse(BaseModel):
    """Response model for listing alerts."""

    alerts: List[Alert]
    summary: Dict[str, Any] = Field(default_factory=dict)


class AcknowledgeAlertResponse(BaseModel):
    """Response model for acknowledging an alert."""

    success: bool
    alert_id: str
    status: str
    acknowledged_at: Optional[str] = None


class ResolveAlertResponse(BaseModel):
    """Response model for resolving an alert."""

    success: bool
    alert_id: str
    status: str
    resolved_at: Optional[str] = None

