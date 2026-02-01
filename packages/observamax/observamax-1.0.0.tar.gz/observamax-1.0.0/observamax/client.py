"""
ObservaMax API Client
"""

from typing import Optional, List, Dict, Any, Literal
import httpx

from .models import (
    Monitor,
    Alert,
    UptimeStats,
    CreateMonitorInput,
    UpdateMonitorInput,
    PaginatedResponse,
    PaginationMeta,
)
from .exceptions import (
    ApiError,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


class HttpClient:
    """Low-level HTTP client for API requests"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://observamax.com/api/v1",
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an API request"""
        response = self._client.request(
            method=method,
            url=path,
            params=params,
            json=json,
        )

        if response.status_code == 401:
            raise AuthenticationError("Invalid or expired API key", 401)
        if response.status_code == 403:
            raise PermissionError("Permission denied", 403)
        if response.status_code == 404:
            raise NotFoundError("Resource not found", 404)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )
        if response.status_code == 400:
            data = response.json()
            raise ValidationError(
                data.get("error", "Validation error"),
                details=data.get("details"),
            )
        if not response.is_success:
            data = response.json()
            raise ApiError(
                data.get("error", f"Request failed with status {response.status_code}"),
                response.status_code,
            )

        return response.json()

    def close(self):
        """Close the HTTP client"""
        self._client.close()


class MonitorsApi:
    """Monitors API"""

    def __init__(self, client: HttpClient):
        self._client = client

    def list(
        self,
        page: int = 1,
        limit: int = 50,
    ) -> PaginatedResponse[Monitor]:
        """
        List all monitors

        Args:
            page: Page number (default: 1)
            limit: Items per page (default: 50)

        Returns:
            Paginated list of monitors
        """
        data = self._client.request(
            "GET",
            "/monitors",
            params={"page": page, "limit": limit},
        )
        return PaginatedResponse(
            data=[Monitor.model_validate(m) for m in data["data"]],
            meta=PaginationMeta.model_validate(data["meta"]),
        )

    def get(self, monitor_id: str) -> Monitor:
        """
        Get a monitor by ID

        Args:
            monitor_id: Monitor ID

        Returns:
            Monitor details
        """
        data = self._client.request("GET", f"/monitors/{monitor_id}")
        return Monitor.model_validate(data)

    def create(self, input: CreateMonitorInput) -> Monitor:
        """
        Create a new monitor

        Args:
            input: Monitor configuration

        Returns:
            Created monitor
        """
        data = self._client.request(
            "POST",
            "/monitors",
            json=input.model_dump(by_alias=True, exclude_none=True),
        )
        return Monitor.model_validate(data)

    def update(self, monitor_id: str, input: UpdateMonitorInput) -> Monitor:
        """
        Update a monitor

        Args:
            monitor_id: Monitor ID
            input: Fields to update

        Returns:
            Updated monitor
        """
        data = self._client.request(
            "PATCH",
            f"/monitors/{monitor_id}",
            json=input.model_dump(by_alias=True, exclude_none=True),
        )
        return Monitor.model_validate(data)

    def delete(self, monitor_id: str) -> None:
        """
        Delete a monitor

        Args:
            monitor_id: Monitor ID
        """
        self._client.request("DELETE", f"/monitors/{monitor_id}")

    def pause(self, monitor_id: str) -> Monitor:
        """
        Pause a monitor

        Args:
            monitor_id: Monitor ID

        Returns:
            Updated monitor
        """
        return self.update(monitor_id, UpdateMonitorInput(is_enabled=False))

    def resume(self, monitor_id: str) -> Monitor:
        """
        Resume a paused monitor

        Args:
            monitor_id: Monitor ID

        Returns:
            Updated monitor
        """
        return self.update(monitor_id, UpdateMonitorInput(is_enabled=True))


class AlertsApi:
    """Alerts API"""

    def __init__(self, client: HttpClient):
        self._client = client

    def list(
        self,
        page: int = 1,
        limit: int = 50,
    ) -> PaginatedResponse[Alert]:
        """
        List all alerts

        Args:
            page: Page number (default: 1)
            limit: Items per page (default: 50)

        Returns:
            Paginated list of alerts
        """
        data = self._client.request(
            "GET",
            "/alerts",
            params={"page": page, "limit": limit},
        )
        return PaginatedResponse(
            data=[Alert.model_validate(a) for a in data["data"]],
            meta=PaginationMeta.model_validate(data["meta"]),
        )

    def get(self, alert_id: str) -> Alert:
        """
        Get an alert by ID

        Args:
            alert_id: Alert ID

        Returns:
            Alert details
        """
        data = self._client.request("GET", f"/alerts/{alert_id}")
        return Alert.model_validate(data)

    def acknowledge(self, alert_id: str) -> Alert:
        """
        Acknowledge an alert

        Args:
            alert_id: Alert ID

        Returns:
            Updated alert
        """
        data = self._client.request("POST", f"/alerts/{alert_id}/acknowledge")
        return Alert.model_validate(data)

    def resolve(self, alert_id: str) -> Alert:
        """
        Resolve an alert

        Args:
            alert_id: Alert ID

        Returns:
            Updated alert
        """
        data = self._client.request("POST", f"/alerts/{alert_id}/resolve")
        return Alert.model_validate(data)


class UptimeApi:
    """Uptime API"""

    def __init__(self, client: HttpClient):
        self._client = client

    def get_stats(
        self,
        period: Literal["24h", "7d", "30d"] = "24h",
    ) -> List[UptimeStats]:
        """
        Get uptime statistics for all monitors

        Args:
            period: Time period (24h, 7d, 30d)

        Returns:
            List of uptime statistics
        """
        data = self._client.request(
            "GET",
            "/uptime",
            params={"period": period},
        )
        return [UptimeStats.model_validate(s) for s in data]

    def get_monitor_stats(
        self,
        monitor_id: str,
        period: Literal["24h", "7d", "30d"] = "24h",
    ) -> UptimeStats:
        """
        Get uptime statistics for a specific monitor

        Args:
            monitor_id: Monitor ID
            period: Time period (24h, 7d, 30d)

        Returns:
            Uptime statistics
        """
        data = self._client.request(
            "GET",
            f"/monitors/{monitor_id}/uptime",
            params={"period": period},
        )
        return UptimeStats.model_validate(data)


class ObservaMax:
    """
    ObservaMax API Client

    Example:
        >>> from observamax import ObservaMax
        >>> client = ObservaMax(api_key="om_live_...")
        >>> monitors = client.monitors.list()
        >>> for monitor in monitors.data:
        ...     print(f"{monitor.name}: {monitor.last_status}")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://observamax.com/api/v1",
        timeout: float = 30.0,
    ):
        """
        Initialize the ObservaMax client

        Args:
            api_key: Your ObservaMax API key
            base_url: API base URL (default: https://observamax.com/api/v1)
            timeout: Request timeout in seconds (default: 30)
        """
        if not api_key:
            raise ValueError("API key is required")

        self._client = HttpClient(api_key, base_url, timeout)
        self.monitors = MonitorsApi(self._client)
        self.alerts = AlertsApi(self._client)
        self.uptime = UptimeApi(self._client)

    def close(self):
        """Close the client and release resources"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
