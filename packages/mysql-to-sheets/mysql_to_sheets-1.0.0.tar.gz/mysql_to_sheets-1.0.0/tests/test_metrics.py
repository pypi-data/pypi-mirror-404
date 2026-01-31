"""Tests for Prometheus metrics collection.

Some tests require real time.sleep to test duration measurement.
"""

import time

import pytest

from mysql_to_sheets.core.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsRegistry,
    SyncTimer,
    get_registry,
    get_sync_metrics,
    reset_registry,
)


class TestCounter:
    """Tests for Counter metric class."""

    def test_counter_initialization(self) -> None:
        """Test counter initializes with zero value."""
        counter = Counter(name="test_counter", help_text="Test counter")
        assert counter.value == 0.0

    def test_counter_increment_default(self) -> None:
        """Test counter increments by 1 by default."""
        counter = Counter(name="test_counter", help_text="Test counter")
        counter.inc()
        assert counter.value == 1.0

    def test_counter_increment_custom_value(self) -> None:
        """Test counter increments by custom value."""
        counter = Counter(name="test_counter", help_text="Test counter")
        counter.inc(5.0)
        assert counter.value == 5.0

    def test_counter_multiple_increments(self) -> None:
        """Test counter accumulates multiple increments."""
        counter = Counter(name="test_counter", help_text="Test counter")
        counter.inc(1.0)
        counter.inc(2.0)
        counter.inc(3.0)
        assert counter.value == 6.0

    def test_counter_with_labels(self) -> None:
        """Test counter with labels."""
        counter = Counter(
            name="test_counter",
            help_text="Test counter",
            labels={"method": "POST", "status": "200"},
        )
        assert counter.labels == {"method": "POST", "status": "200"}


class TestGauge:
    """Tests for Gauge metric class."""

    def test_gauge_initialization(self) -> None:
        """Test gauge initializes with zero value."""
        gauge = Gauge(name="test_gauge", help_text="Test gauge")
        assert gauge.value == 0.0

    def test_gauge_set(self) -> None:
        """Test gauge set method."""
        gauge = Gauge(name="test_gauge", help_text="Test gauge")
        gauge.set(42.0)
        assert gauge.value == 42.0

    def test_gauge_increment(self) -> None:
        """Test gauge increment."""
        gauge = Gauge(name="test_gauge", help_text="Test gauge")
        gauge.set(10.0)
        gauge.inc(5.0)
        assert gauge.value == 15.0

    def test_gauge_decrement(self) -> None:
        """Test gauge decrement."""
        gauge = Gauge(name="test_gauge", help_text="Test gauge")
        gauge.set(10.0)
        gauge.dec(3.0)
        assert gauge.value == 7.0

    def test_gauge_increment_default(self) -> None:
        """Test gauge increments by 1 by default."""
        gauge = Gauge(name="test_gauge", help_text="Test gauge")
        gauge.inc()
        assert gauge.value == 1.0

    def test_gauge_decrement_default(self) -> None:
        """Test gauge decrements by 1 by default."""
        gauge = Gauge(name="test_gauge", help_text="Test gauge")
        gauge.set(5.0)
        gauge.dec()
        assert gauge.value == 4.0

    def test_gauge_can_go_negative(self) -> None:
        """Test gauge can have negative values."""
        gauge = Gauge(name="test_gauge", help_text="Test gauge")
        gauge.dec(5.0)
        assert gauge.value == -5.0


class TestHistogram:
    """Tests for Histogram metric class."""

    def test_histogram_initialization(self) -> None:
        """Test histogram initializes with zero sum and count."""
        histogram = Histogram(name="test_histogram", help_text="Test histogram")
        assert histogram.sum == 0.0
        assert histogram.count == 0

    def test_histogram_observe(self) -> None:
        """Test histogram observe method."""
        histogram = Histogram(name="test_histogram", help_text="Test histogram")
        histogram.observe(1.5)
        assert histogram.sum == 1.5
        assert histogram.count == 1

    def test_histogram_multiple_observations(self) -> None:
        """Test histogram with multiple observations."""
        histogram = Histogram(name="test_histogram", help_text="Test histogram")
        histogram.observe(1.0)
        histogram.observe(2.0)
        histogram.observe(3.0)
        assert histogram.sum == 6.0
        assert histogram.count == 3

    def test_histogram_custom_buckets(self) -> None:
        """Test histogram with custom buckets."""
        histogram = Histogram(
            name="test_histogram",
            help_text="Test histogram",
            buckets=(0.1, 0.5, 1.0, 5.0),
        )
        assert histogram.buckets == (0.1, 0.5, 1.0, 5.0)

    def test_histogram_bucket_counting(self) -> None:
        """Test histogram correctly counts bucket entries."""
        histogram = Histogram(
            name="test_histogram",
            help_text="Test histogram",
            buckets=(1.0, 5.0, 10.0),
        )
        histogram.observe(0.5)  # Goes into 1.0 bucket
        histogram.observe(3.0)  # Goes into 5.0 bucket
        histogram.observe(7.0)  # Goes into 10.0 bucket
        histogram.observe(15.0)  # Goes into +Inf bucket only

        assert histogram.count == 4
        assert histogram.sum == 25.5  # 0.5 + 3.0 + 7.0 + 15.0


class TestMetricsRegistry:
    """Tests for MetricsRegistry class."""

    def setup_method(self) -> None:
        """Reset registry before each test."""
        reset_registry()

    def test_registry_counter_creation(self) -> None:
        """Test registry creates counters."""
        registry = MetricsRegistry()
        counter = registry.counter("test_counter", "Test counter")
        assert isinstance(counter, Counter)
        assert counter.name == "test_counter"

    def test_registry_counter_reuse(self) -> None:
        """Test registry returns same counter for same name."""
        registry = MetricsRegistry()
        counter1 = registry.counter("test_counter", "Test counter")
        counter2 = registry.counter("test_counter", "Test counter")
        assert counter1 is counter2

    def test_registry_gauge_creation(self) -> None:
        """Test registry creates gauges."""
        registry = MetricsRegistry()
        gauge = registry.gauge("test_gauge", "Test gauge")
        assert isinstance(gauge, Gauge)
        assert gauge.name == "test_gauge"

    def test_registry_histogram_creation(self) -> None:
        """Test registry creates histograms."""
        registry = MetricsRegistry()
        histogram = registry.histogram("test_histogram", "Test histogram")
        assert isinstance(histogram, Histogram)
        assert histogram.name == "test_histogram"

    def test_registry_histogram_with_custom_buckets(self) -> None:
        """Test registry creates histograms with custom buckets."""
        registry = MetricsRegistry()
        histogram = registry.histogram(
            "test_histogram",
            "Test histogram",
            buckets=(0.1, 0.5, 1.0),
        )
        assert histogram.buckets == (0.1, 0.5, 1.0)

    def test_registry_with_labels(self) -> None:
        """Test registry handles metrics with labels."""
        registry = MetricsRegistry()
        counter1 = registry.counter("requests", "Requests", labels={"method": "GET"})
        counter2 = registry.counter("requests", "Requests", labels={"method": "POST"})

        # Different labels should create different counters
        assert counter1 is not counter2
        counter1.inc()
        assert counter1.value == 1.0
        assert counter2.value == 0.0

    def test_registry_to_prometheus_basic(self) -> None:
        """Test Prometheus format output."""
        registry = MetricsRegistry()
        counter = registry.counter("test_total", "Test counter")
        counter.inc(5.0)

        output = registry.to_prometheus()

        assert "# HELP test_total Test counter" in output
        assert "# TYPE test_total counter" in output
        assert "test_total 5.0" in output

    def test_registry_to_prometheus_with_labels(self) -> None:
        """Test Prometheus format with labels."""
        registry = MetricsRegistry()
        counter = registry.counter(
            "requests_total",
            "Total requests",
            labels={"method": "GET"},
        )
        counter.inc()

        output = registry.to_prometheus()

        assert 'requests_total{method="GET"} 1.0' in output

    def test_registry_to_prometheus_includes_uptime(self) -> None:
        """Test Prometheus output includes uptime gauge."""
        registry = MetricsRegistry()
        output = registry.to_prometheus()

        assert "mysql_to_sheets_uptime_seconds" in output
        assert "# TYPE mysql_to_sheets_uptime_seconds gauge" in output

    def test_registry_reset(self) -> None:
        """Test registry reset clears all metrics."""
        registry = MetricsRegistry()
        registry.counter("test_counter", "Test").inc()
        registry.gauge("test_gauge", "Test").set(5.0)

        registry.reset()

        # After reset, getting same metric should return new instance with 0
        counter = registry.counter("test_counter", "Test")
        assert counter.value == 0.0

    def test_registry_histogram_prometheus_output(self) -> None:
        """Test histogram Prometheus format."""
        registry = MetricsRegistry()
        histogram = registry.histogram(
            "request_duration",
            "Request duration",
            buckets=(0.1, 0.5, 1.0),
        )
        histogram.observe(0.3)
        histogram.observe(0.7)

        output = registry.to_prometheus()

        assert "request_duration_bucket" in output
        assert "request_duration_sum" in output
        assert "request_duration_count" in output


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def setup_method(self) -> None:
        """Reset registry before each test."""
        reset_registry()

    def test_get_registry_returns_singleton(self) -> None:
        """Test get_registry returns same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_reset_registry_clears_metrics(self) -> None:
        """Test reset_registry clears all metrics."""
        registry = get_registry()
        registry.counter("test", "Test").inc()

        reset_registry()

        # New counter should start at 0
        registry = get_registry()
        counter = registry.counter("test", "Test")
        assert counter.value == 0.0


class TestSyncMetrics:
    """Tests for pre-defined sync metrics."""

    def setup_method(self) -> None:
        """Reset registry before each test."""
        reset_registry()

    def test_get_sync_metrics_returns_all_metrics(self) -> None:
        """Test get_sync_metrics returns expected metrics."""
        metrics = get_sync_metrics()

        assert "sync_total" in metrics
        assert "sync_success" in metrics
        assert "sync_failure" in metrics
        assert "rows_synced" in metrics
        assert "sync_duration" in metrics
        assert "active_syncs" in metrics
        assert "last_sync_timestamp" in metrics

    def test_sync_metrics_types(self) -> None:
        """Test sync metrics have correct types."""
        metrics = get_sync_metrics()

        assert isinstance(metrics["sync_total"], Counter)
        assert isinstance(metrics["sync_success"], Counter)
        assert isinstance(metrics["sync_failure"], Counter)
        assert isinstance(metrics["rows_synced"], Counter)
        assert isinstance(metrics["sync_duration"], Histogram)
        assert isinstance(metrics["active_syncs"], Gauge)
        assert isinstance(metrics["last_sync_timestamp"], Gauge)


class TestSyncTimer:
    """Tests for SyncTimer context manager."""

    def setup_method(self) -> None:
        """Reset registry before each test."""
        reset_registry()

    def test_sync_timer_increments_total(self) -> None:
        """Test SyncTimer increments sync_total on entry."""
        metrics = get_sync_metrics()

        with SyncTimer():
            pass

        assert metrics["sync_total"].value == 1.0

    def test_sync_timer_tracks_active_syncs(self) -> None:
        """Test SyncTimer tracks active syncs."""
        metrics = get_sync_metrics()

        with SyncTimer():
            assert metrics["active_syncs"].value == 1.0

        assert metrics["active_syncs"].value == 0.0

    def test_sync_timer_records_success(self) -> None:
        """Test SyncTimer records success on normal exit."""
        metrics = get_sync_metrics()

        with SyncTimer():
            pass

        assert metrics["sync_success"].value == 1.0
        assert metrics["sync_failure"].value == 0.0

    def test_sync_timer_records_failure_on_exception(self) -> None:
        """Test SyncTimer records failure on exception."""
        metrics = get_sync_metrics()

        try:
            with SyncTimer():
                raise ValueError("Test error")
        except ValueError:
            pass

        assert metrics["sync_success"].value == 0.0
        assert metrics["sync_failure"].value == 1.0

    @pytest.mark.slow
    def test_sync_timer_records_duration(self) -> None:
        """Test SyncTimer records duration.

        This test requires real time.sleep to verify duration measurement.
        """
        metrics = get_sync_metrics()

        with SyncTimer():
            time.sleep(0.1)

        # Duration should be recorded
        assert metrics["sync_duration"].count == 1
        assert metrics["sync_duration"].sum >= 0.1

    def test_sync_timer_updates_last_sync_timestamp(self) -> None:
        """Test SyncTimer updates last_sync_timestamp."""
        metrics = get_sync_metrics()

        before = time.time()
        with SyncTimer():
            pass
        after = time.time()

        timestamp = metrics["last_sync_timestamp"].value
        assert before <= timestamp <= after

    def test_sync_timer_record_rows(self) -> None:
        """Test SyncTimer record_rows method."""
        metrics = get_sync_metrics()

        with SyncTimer() as timer:
            timer.record_rows(100)

        assert metrics["rows_synced"].value == 100.0

    def test_sync_timer_record_rows_multiple(self) -> None:
        """Test SyncTimer accumulates rows from multiple calls."""
        metrics = get_sync_metrics()

        with SyncTimer() as timer:
            timer.record_rows(50)
            timer.record_rows(50)

        assert metrics["rows_synced"].value == 100.0
