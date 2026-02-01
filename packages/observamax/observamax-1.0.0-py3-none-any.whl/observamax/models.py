"""
ObservaMax SDK Models
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field
from enum import Enum


class MonitorStatus(str, Enum):
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    PENDING = "pending"


class MonitorType(str, Enum):
    HTTP = "http"
    HEARTBEAT = "heartbeat"
    TCP = "tcp"
    DNS = "dns"
    PING = "ping"


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    HEAD = "HEAD"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class AlertType(str, Enum):
    DOWN = "down"
    UP = "up"
    DEGRADED = "degraded"
    CHANGE = "change"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Monitor(BaseModel):
    """Represents a monitored endpoint"""

    id: str
    name: Optional[str] = None
    url: str
    check_interval: int = Field(alias="checkInterval")
    is_enabled: bool = Field(alias="isEnabled")
    last_status: MonitorStatus = Field(alias="lastStatus")
    last_checked_at: Optional[datetime] = Field(alias="lastCheckedAt", default=None)
    uptime_24h: Optional[float] = Field(alias="uptime24h", default=None)
    avg_response_time: Optional[float] = Field(alias="avgResponseTime", default=None)
    monitor_type: MonitorType = Field(alias="monitorType")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        populate_by_name = True


class CreateMonitorInput(BaseModel):
    """Input for creating a new monitor"""

    url: str
    name: Optional[str] = None
    check_interval: int = Field(default=5, alias="checkInterval")
    expected_status_code: int = Field(default=200, alias="expectedStatusCode")
    timeout_ms: int = Field(default=30000, alias="timeoutMs")
    http_method: HttpMethod = Field(default=HttpMethod.GET, alias="httpMethod")
    http_headers: Optional[Dict[str, str]] = Field(default=None, alias="httpHeaders")
    tags: Optional[List[str]] = None

    class Config:
        populate_by_name = True


class UpdateMonitorInput(BaseModel):
    """Input for updating a monitor"""

    name: Optional[str] = None
    check_interval: Optional[int] = Field(default=None, alias="checkInterval")
    is_enabled: Optional[bool] = Field(default=None, alias="isEnabled")
    expected_status_code: Optional[int] = Field(default=None, alias="expectedStatusCode")
    timeout_ms: Optional[int] = Field(default=None, alias="timeoutMs")

    class Config:
        populate_by_name = True


class Alert(BaseModel):
    """Represents an alert"""

    id: str
    monitor_id: str = Field(alias="monitorId")
    alert_type: AlertType = Field(alias="alertType")
    severity: Severity
    title: str
    message: str
    created_at: datetime = Field(alias="createdAt")
    acknowledged_at: Optional[datetime] = Field(alias="acknowledgedAt", default=None)
    resolved_at: Optional[datetime] = Field(alias="resolvedAt", default=None)

    class Config:
        populate_by_name = True


class UptimeStats(BaseModel):
    """Uptime statistics for a monitor"""

    monitor_id: str = Field(alias="monitorId")
    period: str
    uptime: float
    total_checks: int = Field(alias="totalChecks")
    successful_checks: int = Field(alias="successfulChecks")
    failed_checks: int = Field(alias="failedChecks")
    avg_response_time: float = Field(alias="avgResponseTime")
    p95_response_time: float = Field(alias="p95ResponseTime")

    class Config:
        populate_by_name = True


T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata"""

    total: int
    page: int
    limit: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response"""

    data: List[T]
    meta: PaginationMeta
