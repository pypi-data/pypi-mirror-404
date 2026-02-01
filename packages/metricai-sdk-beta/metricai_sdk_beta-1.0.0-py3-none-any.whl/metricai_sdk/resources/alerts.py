"""Alerts resource."""

from typing import List, Optional
from metricai_sdk.http import HTTPClient
from metricai_sdk.models.alert import (
    Alert,
    AlertRule,
    CreateAlertRequest,
    CreateAlertRuleRequest,
    UpdateAlertRequest,
    ListAlertsResponse,
    AcknowledgeAlertResponse,
    ResolveAlertResponse,
)


class AlertsResource:
    """Alert management resource."""

    def __init__(self, http: HTTPClient):
        self._http = http

    def list(
        self,
        status: Optional[str] = None,
        type: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[Alert]:
        """List alerts with optional filtering.

        Args:
            status: Filter by status (active, acknowledged, resolved)
            type: Filter by alert type (error_rate, latency, cost, anomaly, availability, quota)
            severity: Filter by severity level (critical, warning, info)

        Returns:
            List of alerts
        """
        params = {}
        if status:
            params["status"] = status
        if type:
            params["type"] = type
        if severity:
            params["severity"] = severity

        response = self._http.get("/alerts", use_firebase_auth=True, params=params)
        alerts_response = ListAlertsResponse(**response)
        return alerts_response.alerts

    def create_rule(
        self,
        name: str,
        condition: Optional[str],
        severity: str,
        notification_channels: List[str],
        metric: Optional[str] = None,
        operator: Optional[str] = None,
        threshold_value: Optional[float] = None,
    ) -> AlertRule:
        """Create a new alert rule.

        Args:
            name: Human-readable rule name
            condition: Legacy alert condition expression (e.g., 'error_rate > 1%')
            severity: Severity level (critical, warning, info)
            notification_channels: Notification channels (email, webhook, slack, dashboard)
            metric: Metric name for structured cost alerts
            operator: Comparison operator for structured cost alerts
            threshold_value: Threshold value for structured cost alerts

        Returns:
            Created alert rule
        """
        request = CreateAlertRuleRequest(
            name=name,
            condition=condition,
            severity=severity,
            notification_channels=notification_channels,
            metric=metric,
            operator=operator,
            threshold_value=threshold_value,
        )
        response = self._http.post(
            "/alerts/rules",
            use_firebase_auth=True,
            json_data=request.model_dump(exclude_none=True),
        )
        return AlertRule(**response)

    def create(
        self,
        type: str,
        severity: str,
        message: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        threshold: Optional[dict] = None,
        current_value: Optional[float] = None,
    ) -> Alert:
        """Create a new alert (for testing/manual creation).

        Args:
            type: Alert type (error_rate, latency, cost, anomaly, availability, quota)
            severity: Severity level (critical, warning, info)
            message: Human-readable alert message
            model: Model name if alert is model-specific
            provider: Provider name if alert is provider-specific
            threshold: Threshold that was exceeded
            current_value: Current metric value that triggered the alert

        Returns:
            Created alert
        """
        request = CreateAlertRequest(
            type=type,
            severity=severity,
            message=message,
            model=model,
            provider=provider,
            threshold=threshold,
            current_value=current_value,
        )
        response = self._http.post(
            "/alerts",
            use_firebase_auth=True,
            json_data=request.model_dump(exclude_none=True),
        )
        return Alert(**response)

    def update(
        self,
        alert_id: str,
        status: Optional[str] = None,
        message: Optional[str] = None,
    ) -> Alert:
        """Update an alert.

        Args:
            alert_id: Alert ID to update
            status: New status (active, acknowledged, resolved)
            message: Updated message

        Returns:
            Updated alert
        """
        request = UpdateAlertRequest(status=status, message=message)
        response = self._http.put(
            f"/alerts/{alert_id}",
            use_firebase_auth=True,
            json_data=request.model_dump(exclude_none=True),
        )
        return Alert(**response)

    def acknowledge(self, alert_id: str) -> AcknowledgeAlertResponse:
        """Acknowledge an alert.

        Args:
            alert_id: Alert ID to acknowledge

        Returns:
            AcknowledgeAlertResponse with status information
        """
        response = self._http.post(
            f"/alerts/{alert_id}/acknowledge",
            use_firebase_auth=True,
        )
        return AcknowledgeAlertResponse(**response)

    def resolve(self, alert_id: str) -> ResolveAlertResponse:
        """Resolve an alert.

        Args:
            alert_id: Alert ID to resolve

        Returns:
            ResolveAlertResponse with status information
        """
        response = self._http.post(
            f"/alerts/{alert_id}/resolve",
            use_firebase_auth=True,
        )
        return ResolveAlertResponse(**response)

