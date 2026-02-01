"""
ObservaMax SDK for Python

Example:
    >>> from observamax import ObservaMax
    >>> client = ObservaMax(api_key="om_live_...")
    >>> monitors = client.monitors.list()
"""

from .client import ObservaMax
from .models import (
    Monitor,
    Alert,
    UptimeStats,
    CreateMonitorInput,
    UpdateMonitorInput,
    PaginatedResponse,
)
from .exceptions import ObservaMaxError, ApiError

__version__ = "1.0.0"
__all__ = [
    "ObservaMax",
    "Monitor",
    "Alert",
    "UptimeStats",
    "CreateMonitorInput",
    "UpdateMonitorInput",
    "PaginatedResponse",
    "ObservaMaxError",
    "ApiError",
]
