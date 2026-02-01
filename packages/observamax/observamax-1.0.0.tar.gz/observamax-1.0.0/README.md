# observamax

Official Python SDK for the ObservaMax API.

## Installation

```bash
pip install observamax
```

## Quick Start

```python
import os
from observamax import ObservaMax

client = ObservaMax(api_key=os.environ["OBSERVAMAX_API_KEY"])

# List all monitors
monitors = client.monitors.list()
print(f"You have {monitors.meta.total} monitors")

for monitor in monitors.data:
    print(f"{monitor.name}: {monitor.last_status}")

# Get a specific monitor
monitor = client.monitors.get("mon_abc123")
print(f"{monitor.name}: {monitor.last_status}")

# Create a new monitor
from observamax import CreateMonitorInput

new_monitor = client.monitors.create(
    CreateMonitorInput(
        url="https://api.example.com/health",
        name="Production API",
        check_interval=5,
    )
)

# Pause a monitor
client.monitors.pause(new_monitor.id)

# Resume a monitor
client.monitors.resume(new_monitor.id)

# Get uptime statistics
stats = client.uptime.get_stats("30d")
```

## API Reference

### Monitors

```python
from observamax import CreateMonitorInput, UpdateMonitorInput

# List monitors
response = client.monitors.list(page=1, limit=50)
for monitor in response.data:
    print(monitor.name)

# Get a monitor
monitor = client.monitors.get("monitor_id")

# Create a monitor
monitor = client.monitors.create(
    CreateMonitorInput(
        url="https://example.com",
        name="My Website",
        check_interval=5,        # minutes
        expected_status_code=200,
        timeout_ms=30000,
        http_method="GET",
        tags=["production"],
    )
)

# Update a monitor
updated = client.monitors.update(
    "monitor_id",
    UpdateMonitorInput(
        name="New Name",
        check_interval=10,
    )
)

# Delete a monitor
client.monitors.delete("monitor_id")

# Pause/Resume
client.monitors.pause("monitor_id")
client.monitors.resume("monitor_id")
```

### Alerts

```python
# List alerts
alerts = client.alerts.list()

# Get an alert
alert = client.alerts.get("alert_id")

# Acknowledge an alert
client.alerts.acknowledge("alert_id")

# Resolve an alert
client.alerts.resolve("alert_id")
```

### Uptime

```python
# Get overall uptime stats
stats = client.uptime.get_stats("24h")  # or "7d", "30d"

# Get stats for a specific monitor
monitor_stats = client.uptime.get_monitor_stats("monitor_id", "7d")
```

## Error Handling

```python
from observamax import ObservaMax, ApiError, RateLimitError

try:
    monitor = client.monitors.get("invalid_id")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ApiError as e:
    print(f"API Error: {e.message} (status: {e.status_code})")
```

## Context Manager

```python
with ObservaMax(api_key="om_live_...") as client:
    monitors = client.monitors.list()
    # Client is automatically closed when exiting the context
```

## Configuration

```python
client = ObservaMax(
    api_key="om_live_...",
    base_url="https://observamax.com/api/v1",  # default
    timeout=30.0,  # 30 seconds, default
)
```

## License

MIT
