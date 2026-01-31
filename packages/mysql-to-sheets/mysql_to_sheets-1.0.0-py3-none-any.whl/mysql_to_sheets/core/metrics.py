"""Prometheus-compatible metrics collection for sync operations.

This module provides metrics tracking for monitoring sync operations,
API usage, and system health. Metrics are exposed in Prometheus format.
"""

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Counter:
    """A monotonically increasing counter metric.

    Counters track cumulative values that only go up (e.g., request counts).
    """

    name: str
    help_text: str
    labels: dict[str, str] = field(default_factory=dict)
    _value: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def inc(self, value: float = 1.0) -> None:
        """Increment the counter.

        Args:
            value: Amount to increment by (default 1).
        """
        with self._lock:
            self._value += value

    @property
    def value(self) -> float:
        """Get current counter value."""
        with self._lock:
            return self._value


@dataclass
class Gauge:
    """A metric that can go up and down.

    Gauges track current values (e.g., queue size, active connections).
    """

    name: str
    help_text: str
    labels: dict[str, str] = field(default_factory=dict)
    _value: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def set(self, value: float) -> None:
        """Set the gauge value.

        Args:
            value: The value to set.
        """
        with self._lock:
            self._value = value

    def inc(self, value: float = 1.0) -> None:
        """Increment the gauge.

        Args:
            value: Amount to increment by.
        """
        with self._lock:
            self._value += value

    def dec(self, value: float = 1.0) -> None:
        """Decrement the gauge.

        Args:
            value: Amount to decrement by.
        """
        with self._lock:
            self._value -= value

    @property
    def value(self) -> float:
        """Get current gauge value."""
        with self._lock:
            return self._value


@dataclass
class Histogram:
    """A metric that tracks distributions of values.

    Histograms track value distributions with configurable buckets.
    """

    name: str
    help_text: str
    buckets: tuple[float, ...] = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    labels: dict[str, str] = field(default_factory=dict)
    _bucket_counts: dict[float, int] = field(default_factory=dict, repr=False)
    _sum: float = 0.0
    _count: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self) -> None:
        """Initialize bucket counts."""
        self._bucket_counts = {b: 0 for b in self.buckets}
        self._bucket_counts[float("inf")] = 0

    def observe(self, value: float) -> None:
        """Record a value in the histogram.

        Args:
            value: The value to record.
        """
        with self._lock:
            self._sum += value
            self._count += 1
            for bucket in self.buckets:
                if value <= bucket:
                    self._bucket_counts[bucket] += 1
            self._bucket_counts[float("inf")] += 1

    @property
    def sum(self) -> float:
        """Get sum of all observed values."""
        with self._lock:
            return self._sum

    @property
    def count(self) -> int:
        """Get count of observations."""
        with self._lock:
            return self._count


class MetricsRegistry:
    """Registry for all application metrics.

    Provides a central place to register and retrieve metrics.
    """

    def __init__(self) -> None:
        """Initialize metrics registry."""
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._lock = threading.Lock()
        self._start_time = datetime.now(timezone.utc)

    def counter(
        self,
        name: str,
        help_text: str = "",
        labels: dict[str, str] | None = None,
    ) -> Counter:
        """Get or create a counter metric.

        Args:
            name: Metric name.
            help_text: Description of the metric.
            labels: Optional labels for the metric.

        Returns:
            Counter instance.
        """
        key = self._make_key(name, labels)
        with self._lock:
            if key not in self._counters:
                self._counters[key] = Counter(name, help_text, labels or {})
            return self._counters[key]

    def gauge(
        self,
        name: str,
        help_text: str = "",
        labels: dict[str, str] | None = None,
    ) -> Gauge:
        """Get or create a gauge metric.

        Args:
            name: Metric name.
            help_text: Description of the metric.
            labels: Optional labels for the metric.

        Returns:
            Gauge instance.
        """
        key = self._make_key(name, labels)
        with self._lock:
            if key not in self._gauges:
                self._gauges[key] = Gauge(name, help_text, labels or {})
            return self._gauges[key]

    def histogram(
        self,
        name: str,
        help_text: str = "",
        buckets: tuple[float, ...] | None = None,
        labels: dict[str, str] | None = None,
    ) -> Histogram:
        """Get or create a histogram metric.

        Args:
            name: Metric name.
            help_text: Description of the metric.
            buckets: Bucket boundaries for the histogram.
            labels: Optional labels for the metric.

        Returns:
            Histogram instance.
        """
        key = self._make_key(name, labels)
        with self._lock:
            if key not in self._histograms:
                kwargs: dict[str, Any] = {"name": name, "help_text": help_text}
                if buckets:
                    kwargs["buckets"] = buckets
                if labels:
                    kwargs["labels"] = labels
                self._histograms[key] = Histogram(**kwargs)
            return self._histograms[key]

    def _make_key(self, name: str, labels: dict[str, str] | None) -> str:
        """Create a unique key for a metric.

        Args:
            name: Metric name.
            labels: Metric labels.

        Returns:
            Unique key string.
        """
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name

    def _format_labels(self, labels: dict[str, str]) -> str:
        """Format labels for Prometheus output.

        Args:
            labels: Label dictionary.

        Returns:
            Formatted label string.
        """
        if not labels:
            return ""
        parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return "{" + ",".join(parts) + "}"

    def to_prometheus(self) -> str:
        """Export all metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string.
        """
        lines: list[str] = []

        # Process uptime
        uptime_seconds = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        lines.append("# HELP mysql_to_sheets_uptime_seconds Time since application started")
        lines.append("# TYPE mysql_to_sheets_uptime_seconds gauge")
        lines.append(f"mysql_to_sheets_uptime_seconds {uptime_seconds}")
        lines.append("")

        # Process counters
        with self._lock:
            counter_names = set(c.name for c in self._counters.values())
            for name in sorted(counter_names):
                counters = [c for c in self._counters.values() if c.name == name]
                if counters:
                    lines.append(f"# HELP {name} {counters[0].help_text}")
                    lines.append(f"# TYPE {name} counter")
                    for counter in counters:
                        label_str = self._format_labels(counter.labels)
                        lines.append(f"{name}{label_str} {counter.value}")
                    lines.append("")

            # Process gauges
            gauge_names = set(g.name for g in self._gauges.values())
            for name in sorted(gauge_names):
                gauges = [g for g in self._gauges.values() if g.name == name]
                if gauges:
                    lines.append(f"# HELP {name} {gauges[0].help_text}")
                    lines.append(f"# TYPE {name} gauge")
                    for gauge in gauges:
                        label_str = self._format_labels(gauge.labels)
                        lines.append(f"{name}{label_str} {gauge.value}")
                    lines.append("")

            # Process histograms
            for name, histogram in self._histograms.items():
                lines.append(f"# HELP {histogram.name} {histogram.help_text}")
                lines.append(f"# TYPE {histogram.name} histogram")
                label_str = self._format_labels(histogram.labels)
                with histogram._lock:
                    cumulative = 0
                    for bucket in sorted(histogram._bucket_counts.keys()):
                        count = histogram._bucket_counts[bucket]
                        cumulative += count if bucket != float("inf") else 0
                        bucket_label = f'le="{bucket}"' if bucket != float("inf") else 'le="+Inf"'
                        if histogram.labels:
                            full_label = (
                                "{"
                                + ",".join(
                                    [bucket_label]
                                    + [f'{k}="{v}"' for k, v in histogram.labels.items()]
                                )
                                + "}"
                            )
                        else:
                            full_label = "{" + bucket_label + "}"
                        if bucket == float("inf"):
                            lines.append(f"{histogram.name}_bucket{full_label} {histogram._count}")
                        else:
                            lines.append(f"{histogram.name}_bucket{full_label} {cumulative}")
                    lines.append(f"{histogram.name}_sum{label_str} {histogram._sum}")
                    lines.append(f"{histogram.name}_count{label_str} {histogram._count}")
                lines.append("")

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all metrics (useful for testing)."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._start_time = datetime.now(timezone.utc)


# Global metrics registry
_registry = MetricsRegistry()


def get_registry() -> MetricsRegistry:
    """Get the global metrics registry.

    Returns:
        MetricsRegistry instance.
    """
    return _registry


def reset_registry() -> None:
    """Reset the global metrics registry."""
    _registry.reset()


# Pre-defined application metrics
def get_sync_metrics() -> dict[str, Any]:
    """Get pre-configured sync operation metrics.

    Returns:
        Dictionary with counter, gauge, and histogram metrics.
    """
    registry = get_registry()

    return {
        "sync_total": registry.counter(
            "mysql_to_sheets_sync_total",
            "Total number of sync operations",
        ),
        "sync_success": registry.counter(
            "mysql_to_sheets_sync_success_total",
            "Total number of successful sync operations",
        ),
        "sync_failure": registry.counter(
            "mysql_to_sheets_sync_failure_total",
            "Total number of failed sync operations",
        ),
        "rows_synced": registry.counter(
            "mysql_to_sheets_rows_synced_total",
            "Total number of rows synced",
        ),
        "sync_duration": registry.histogram(
            "mysql_to_sheets_sync_duration_seconds",
            "Duration of sync operations in seconds",
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
        ),
        "active_syncs": registry.gauge(
            "mysql_to_sheets_active_syncs",
            "Number of currently running sync operations",
        ),
        "last_sync_timestamp": registry.gauge(
            "mysql_to_sheets_last_sync_timestamp",
            "Unix timestamp of last sync operation",
        ),
    }


class SyncTimer:
    """Context manager for timing sync operations.

    Automatically records duration and updates metrics.
    """

    def __init__(self) -> None:
        """Initialize sync timer."""
        self._start_time: float | None = None
        self._metrics = get_sync_metrics()

    def __enter__(self) -> "SyncTimer":
        """Start timing."""
        self._start_time = time.time()
        self._metrics["sync_total"].inc()
        self._metrics["active_syncs"].inc()
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: object,
    ) -> None:
        """Stop timing and record metrics."""
        if self._start_time is not None:
            duration = time.time() - self._start_time
            self._metrics["sync_duration"].observe(duration)
            self._metrics["last_sync_timestamp"].set(time.time())

        self._metrics["active_syncs"].dec()

        if exc_type is None:
            self._metrics["sync_success"].inc()
        else:
            self._metrics["sync_failure"].inc()

    def record_rows(self, count: int) -> None:
        """Record number of rows synced.

        Args:
            count: Number of rows.
        """
        self._metrics["rows_synced"].inc(count)


def get_error_metrics() -> dict[str, Any]:
    """Get pre-configured error tracking metrics.

    Returns:
        Dictionary with error counter and retry metrics.
    """
    registry = get_registry()

    return {
        "errors_total": registry.counter(
            "mysql_to_sheets_errors_total",
            "Total number of errors by code and category",
        ),
        "retry_attempts": registry.counter(
            "mysql_to_sheets_retry_attempts_total",
            "Total number of retry attempts",
        ),
        "retry_success": registry.counter(
            "mysql_to_sheets_retry_success_total",
            "Total number of successful retries",
        ),
        "retry_failure": registry.counter(
            "mysql_to_sheets_retry_failure_total",
            "Total number of failed retries (exhausted)",
        ),
        "consecutive_failures": registry.gauge(
            "mysql_to_sheets_consecutive_failures",
            "Current consecutive failure count",
        ),
    }


def record_error(
    error_code: str | None = None,
    error_category: str | None = None,
) -> None:
    """Record an error occurrence.

    Args:
        error_code: Error code (e.g., DB_201).
        error_category: Error category (e.g., transient).
    """
    registry = get_registry()

    # Main error counter
    labels = {}
    if error_code:
        labels["code"] = error_code
    if error_category:
        labels["category"] = error_category

    counter = registry.counter(
        "mysql_to_sheets_errors_total",
        "Total number of errors by code and category",
        labels=labels if labels else None,
    )
    counter.inc()


def record_retry_attempt(operation: str, success: bool) -> None:
    """Record a retry attempt.

    Args:
        operation: Name of the operation being retried.
        success: Whether the retry succeeded.
    """
    registry = get_registry()

    # Retry attempts counter
    attempts = registry.counter(
        "mysql_to_sheets_retry_attempts_total",
        "Total number of retry attempts",
        labels={"operation": operation},
    )
    attempts.inc()

    # Success/failure counters
    if success:
        success_counter = registry.counter(
            "mysql_to_sheets_retry_success_total",
            "Total number of successful retries",
            labels={"operation": operation},
        )
        success_counter.inc()
    else:
        failure_counter = registry.counter(
            "mysql_to_sheets_retry_failure_total",
            "Total number of failed retries",
            labels={"operation": operation},
        )
        failure_counter.inc()


class ConsecutiveFailureTracker:
    """Track consecutive failures for alerting.

    Use to detect sustained failures that warrant alerts.
    """

    def __init__(self, config_id: int | str | None = None) -> None:
        """Initialize failure tracker.

        Args:
            config_id: Optional config/job identifier.
        """
        self._config_id = str(config_id) if config_id else "default"
        self._count = 0
        self._registry = get_registry()

    def record_success(self) -> None:
        """Record a successful operation, resetting the counter."""
        self._count = 0
        self._update_gauge()

    def record_failure(self) -> int:
        """Record a failure and return the consecutive count.

        Returns:
            Current consecutive failure count.
        """
        self._count += 1
        self._update_gauge()
        return self._count

    def _update_gauge(self) -> None:
        """Update the metrics gauge."""
        gauge = self._registry.gauge(
            "mysql_to_sheets_consecutive_failures",
            "Current consecutive failure count",
            labels={"config_id": self._config_id},
        )
        gauge.set(self._count)

    @property
    def count(self) -> int:
        """Get current consecutive failure count."""
        return self._count


# Webhook metrics


def get_webhook_metrics() -> dict[str, Any]:
    """Get pre-configured webhook delivery metrics.

    Returns:
        Dictionary with webhook counter and gauge metrics.
    """
    registry = get_registry()

    return {
        "deliveries_total": registry.counter(
            "mysql_to_sheets_webhook_deliveries_total",
            "Total number of webhook delivery attempts",
        ),
        "deliveries_success": registry.counter(
            "mysql_to_sheets_webhook_deliveries_success_total",
            "Total number of successful webhook deliveries",
        ),
        "deliveries_failure": registry.counter(
            "mysql_to_sheets_webhook_deliveries_failure_total",
            "Total number of failed webhook deliveries",
        ),
        "consecutive_failures": registry.gauge(
            "mysql_to_sheets_webhook_consecutive_failures",
            "Current consecutive failure count per webhook",
        ),
        "unhealthy_webhooks": registry.gauge(
            "mysql_to_sheets_webhook_unhealthy_total",
            "Number of webhooks in unhealthy state",
        ),
    }


def record_webhook_delivery(
    webhook_id: int,
    success: bool,
    organization_id: int | None = None,
) -> None:
    """Record a webhook delivery attempt.

    Updates counters and consecutive failure gauge.

    Args:
        webhook_id: The webhook's unique identifier.
        success: Whether the delivery succeeded.
        organization_id: Organization owning the webhook.
    """
    registry = get_registry()

    # Main delivery counter
    labels = {"webhook_id": str(webhook_id)}
    if organization_id:
        labels["organization_id"] = str(organization_id)

    deliveries = registry.counter(
        "mysql_to_sheets_webhook_deliveries_total",
        "Total number of webhook delivery attempts",
        labels=labels,
    )
    deliveries.inc()

    if success:
        success_counter = registry.counter(
            "mysql_to_sheets_webhook_deliveries_success_total",
            "Total number of successful webhook deliveries",
            labels=labels,
        )
        success_counter.inc()
    else:
        failure_counter = registry.counter(
            "mysql_to_sheets_webhook_deliveries_failure_total",
            "Total number of failed webhook deliveries",
            labels=labels,
        )
        failure_counter.inc()


def update_webhook_health_metrics(
    webhook_id: int,
    consecutive_failures: int,
    is_healthy: bool,
) -> None:
    """Update webhook health metrics.

    Args:
        webhook_id: The webhook's unique identifier.
        consecutive_failures: Current consecutive failure count.
        is_healthy: Whether the webhook is considered healthy.
    """
    registry = get_registry()

    # Update consecutive failures gauge
    gauge = registry.gauge(
        "mysql_to_sheets_webhook_consecutive_failures",
        "Current consecutive failure count per webhook",
        labels={"webhook_id": str(webhook_id)},
    )
    gauge.set(consecutive_failures)
