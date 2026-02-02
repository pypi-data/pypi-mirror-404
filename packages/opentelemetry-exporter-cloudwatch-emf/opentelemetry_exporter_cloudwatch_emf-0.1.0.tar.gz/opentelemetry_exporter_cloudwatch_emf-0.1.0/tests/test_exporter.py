"""Tests for CloudWatch EMF Exporter."""

import io
import json
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from opentelemetry_exporter_cloudwatch_emf import CloudWatchEMFExporter
from opentelemetry_exporter_cloudwatch_emf.units import map_unit


class TestUnitMapping:
    """Test unit mapping from OpenTelemetry to CloudWatch."""

    def test_time_units(self):
        assert map_unit("s") == "Seconds"
        assert map_unit("ms") == "Milliseconds"
        assert map_unit("us") == "Microseconds"

    def test_byte_units(self):
        assert map_unit("By") == "Bytes"
        assert map_unit("KiBy") == "Kilobytes"
        assert map_unit("MiBy") == "Megabytes"
        assert map_unit("GiBy") == "Gigabytes"

    def test_count_units(self):
        assert map_unit("1") == "Count"
        assert map_unit("{request}") == "Count"
        assert map_unit("{error}") == "Count"

    def test_percent_unit(self):
        assert map_unit("%") == "Percent"

    def test_unknown_unit(self):
        assert map_unit("unknown") == "None"
        assert map_unit("foobar") == "None"

    def test_none_unit(self):
        assert map_unit(None) == "None"
        assert map_unit("") == "None"


class TestCloudWatchEMFExporter:
    """Test CloudWatch EMF Exporter."""

    def test_init_valid_namespace(self):
        exporter = CloudWatchEMFExporter(namespace="MyApp")
        assert exporter._namespace == "MyApp"

    def test_init_empty_namespace_raises(self):
        with pytest.raises(ValueError, match="namespace must be 1-256"):
            CloudWatchEMFExporter(namespace="")

    def test_init_long_namespace_raises(self):
        with pytest.raises(ValueError, match="namespace must be 1-256"):
            CloudWatchEMFExporter(namespace="x" * 257)

    def test_init_invalid_storage_resolution_raises(self):
        with pytest.raises(ValueError, match="storage_resolution must be 1 or 60"):
            CloudWatchEMFExporter(namespace="MyApp", storage_resolution=30)

    def test_init_invalid_max_dimensions_raises(self):
        with pytest.raises(ValueError, match="max_dimensions must be 0-30"):
            CloudWatchEMFExporter(namespace="MyApp", max_dimensions=31)

    def test_custom_output_stream(self):
        output = io.StringIO()
        exporter = CloudWatchEMFExporter(namespace="MyApp", output=output)
        assert exporter._output is output

    def test_custom_timestamp_fn(self):
        exporter = CloudWatchEMFExporter(
            namespace="MyApp",
            timestamp_fn=lambda: 1234567890000,
        )
        assert exporter._timestamp_fn() == 1234567890000


class TestEMFDocumentGeneration:
    """Test EMF document structure."""

    def create_exporter(self, output: io.StringIO) -> CloudWatchEMFExporter:
        return CloudWatchEMFExporter(
            namespace="TestNamespace",
            output=output,
            timestamp_fn=lambda: 1700000000000,
        )

    def test_build_emf_document_structure(self):
        output = io.StringIO()
        exporter = self.create_exporter(output)

        emf = exporter._build_emf_document(
            metric_name="request_count",
            metric_value=42,
            metric_unit="1",
            dimensions={"service": "api", "environment": "prod"},
        )

        # Check _aws metadata
        assert "_aws" in emf
        assert emf["_aws"]["Timestamp"] == 1700000000000
        assert "CloudWatchMetrics" in emf["_aws"]

        # Check metrics definition
        cw_metrics = emf["_aws"]["CloudWatchMetrics"][0]
        assert cw_metrics["Namespace"] == "TestNamespace"
        assert cw_metrics["Dimensions"] == [["service", "environment"]]
        assert cw_metrics["Metrics"][0]["Name"] == "request_count"
        assert cw_metrics["Metrics"][0]["Unit"] == "Count"

        # Check values at root
        assert emf["request_count"] == 42
        assert emf["service"] == "api"
        assert emf["environment"] == "prod"

    def test_build_emf_document_no_dimensions(self):
        output = io.StringIO()
        exporter = self.create_exporter(output)

        emf = exporter._build_emf_document(
            metric_name="total_requests",
            metric_value=100,
            metric_unit="1",
            dimensions={},
        )

        cw_metrics = emf["_aws"]["CloudWatchMetrics"][0]
        assert cw_metrics["Dimensions"] == [[]]

    def test_storage_resolution_high(self):
        output = io.StringIO()
        exporter = CloudWatchEMFExporter(
            namespace="TestNamespace",
            output=output,
            storage_resolution=1,
        )

        emf = exporter._build_emf_document(
            metric_name="latency",
            metric_value=50,
            metric_unit="ms",
            dimensions={},
        )

        metrics = emf["_aws"]["CloudWatchMetrics"][0]["Metrics"][0]
        assert metrics["StorageResolution"] == 1


class TestDimensionHandling:
    """Test dimension building and sanitization."""

    def test_sanitize_dimension_name_dots(self):
        exporter = CloudWatchEMFExporter(namespace="Test")
        assert exporter._sanitize_dimension_name("service.name") == "service_name"

    def test_sanitize_dimension_name_slashes(self):
        exporter = CloudWatchEMFExporter(namespace="Test")
        assert exporter._sanitize_dimension_name("http/method") == "http_method"

    def test_sanitize_dimension_name_special_chars(self):
        exporter = CloudWatchEMFExporter(namespace="Test")
        assert exporter._sanitize_dimension_name("foo@bar#baz") == "foobarbaz"

    def test_sanitize_dimension_name_length_limit(self):
        exporter = CloudWatchEMFExporter(namespace="Test")
        long_name = "x" * 300
        sanitized = exporter._sanitize_dimension_name(long_name)
        assert len(sanitized) == 250

    def test_dimension_keys_filter(self):
        output = io.StringIO()
        exporter = CloudWatchEMFExporter(
            namespace="Test",
            output=output,
            dimension_keys=["service", "environment"],
        )

        dimensions = exporter._build_dimensions(
            point_attrs={"service": "api", "host": "server1", "region": "us-west-2"},
            resource_attrs={"environment": "prod"},
        )

        assert dimensions == {"service": "api", "environment": "prod"}
        assert "host" not in dimensions
        assert "region" not in dimensions

    def test_max_dimensions_limit(self):
        output = io.StringIO()
        exporter = CloudWatchEMFExporter(
            namespace="Test",
            output=output,
            max_dimensions=2,
        )

        dimensions = exporter._build_dimensions(
            point_attrs={"a": "1", "b": "2", "c": "3", "d": "4"},
            resource_attrs={},
        )

        assert len(dimensions) == 2


class TestExportFlow:
    """Test the export method with mock metrics data."""

    def create_mock_metrics_data(
        self,
        metric_name: str = "test_metric",
        metric_value: float = 1.0,
        metric_unit: str = "1",
        attributes: Dict[str, Any] = None,
    ) -> MagicMock:
        """Create a mock MetricsData structure."""
        if attributes is None:
            attributes = {}

        # Create mock data point
        data_point = MagicMock()
        data_point.value = metric_value
        data_point.attributes = attributes

        # Create mock Sum data
        sum_data = MagicMock()
        sum_data.data_points = [data_point]

        # Create mock metric
        metric = MagicMock()
        metric.name = metric_name
        metric.unit = metric_unit
        metric.data = sum_data

        # Make data look like Sum type
        from opentelemetry.sdk.metrics.export import Sum

        metric.data.__class__ = Sum

        # Create mock scope metrics
        scope_metrics = MagicMock()
        scope_metrics.metrics = [metric]

        # Create mock resource
        resource = MagicMock()
        resource.attributes = {"service.name": "test-service"}

        # Create mock resource metrics
        resource_metrics = MagicMock()
        resource_metrics.resource = resource
        resource_metrics.scope_metrics = [scope_metrics]

        # Create mock metrics data
        metrics_data = MagicMock()
        metrics_data.resource_metrics = [resource_metrics]

        return metrics_data

    def test_export_writes_emf_json(self):
        output = io.StringIO()
        exporter = CloudWatchEMFExporter(
            namespace="TestApp",
            output=output,
            timestamp_fn=lambda: 1700000000000,
        )

        metrics_data = self.create_mock_metrics_data(
            metric_name="request_count",
            metric_value=42,
            attributes={"endpoint": "/api"},
        )

        from opentelemetry.sdk.metrics.export import MetricExportResult

        result = exporter.export(metrics_data)

        assert result == MetricExportResult.SUCCESS

        output.seek(0)
        line = output.readline()
        emf = json.loads(line)

        assert emf["_aws"]["Timestamp"] == 1700000000000
        assert emf["_aws"]["CloudWatchMetrics"][0]["Namespace"] == "TestApp"
        assert emf["request_count"] == 42

    def test_export_after_shutdown_fails(self):
        output = io.StringIO()
        exporter = CloudWatchEMFExporter(namespace="Test", output=output)
        exporter.shutdown()

        metrics_data = self.create_mock_metrics_data()

        from opentelemetry.sdk.metrics.export import MetricExportResult

        result = exporter.export(metrics_data)
        assert result == MetricExportResult.FAILURE


class TestHistogramExport:
    """Test histogram metric export."""

    def create_mock_histogram_data(
        self,
        metric_name: str = "latency",
        metric_unit: str = "ms",
        count: int = 100,
        sum_value: float = 5000.0,
        min_value: float = 10.0,
        max_value: float = 200.0,
        attributes: Dict[str, Any] = None,
    ) -> MagicMock:
        """Create a mock MetricsData with histogram data."""
        if attributes is None:
            attributes = {}

        # Create mock histogram data point
        data_point = MagicMock()
        data_point.count = count
        data_point.sum = sum_value
        data_point.min = min_value
        data_point.max = max_value
        data_point.attributes = attributes

        # Create mock Histogram data
        histogram_data = MagicMock()
        histogram_data.data_points = [data_point]

        # Create mock metric
        metric = MagicMock()
        metric.name = metric_name
        metric.unit = metric_unit
        metric.data = histogram_data

        # Make data look like Histogram type
        from opentelemetry.sdk.metrics.export import Histogram

        metric.data.__class__ = Histogram

        # Create mock scope metrics
        scope_metrics = MagicMock()
        scope_metrics.metrics = [metric]

        # Create mock resource
        resource = MagicMock()
        resource.attributes = {"service.name": "test-service"}

        # Create mock resource metrics
        resource_metrics = MagicMock()
        resource_metrics.resource = resource
        resource_metrics.scope_metrics = [scope_metrics]

        # Create mock metrics data
        metrics_data = MagicMock()
        metrics_data.resource_metrics = [resource_metrics]

        return metrics_data

    def test_histogram_export_creates_four_metrics(self):
        output = io.StringIO()
        exporter = CloudWatchEMFExporter(
            namespace="TestApp",
            output=output,
            timestamp_fn=lambda: 1700000000000,
        )

        metrics_data = self.create_mock_histogram_data(
            metric_name="request_latency",
            metric_unit="ms",
            count=50,
            sum_value=2500.0,
            min_value=5.0,
            max_value=150.0,
            attributes={"endpoint": "/api"},
        )

        from opentelemetry.sdk.metrics.export import MetricExportResult

        result = exporter.export(metrics_data)

        assert result == MetricExportResult.SUCCESS

        output.seek(0)
        line = output.readline()
        emf = json.loads(line)

        # Check that all four histogram metrics are present
        assert emf["request_latency_count"] == 50
        assert emf["request_latency_sum"] == 2500.0
        assert emf["request_latency_min"] == 5.0
        assert emf["request_latency_max"] == 150.0

        # Check metrics definition
        cw_metrics = emf["_aws"]["CloudWatchMetrics"][0]
        metric_names = [m["Name"] for m in cw_metrics["Metrics"]]
        assert "request_latency_count" in metric_names
        assert "request_latency_sum" in metric_names
        assert "request_latency_min" in metric_names
        assert "request_latency_max" in metric_names

    def test_histogram_count_uses_count_unit(self):
        output = io.StringIO()
        exporter = CloudWatchEMFExporter(
            namespace="TestApp",
            output=output,
            timestamp_fn=lambda: 1700000000000,
        )

        metrics_data = self.create_mock_histogram_data()

        exporter.export(metrics_data)

        output.seek(0)
        emf = json.loads(output.readline())

        cw_metrics = emf["_aws"]["CloudWatchMetrics"][0]
        metrics_by_name = {m["Name"]: m for m in cw_metrics["Metrics"]}

        # Count should always use "Count" unit
        assert metrics_by_name["latency_count"]["Unit"] == "Count"
        # Sum/min/max should use the metric's unit
        assert metrics_by_name["latency_sum"]["Unit"] == "Milliseconds"
        assert metrics_by_name["latency_min"]["Unit"] == "Milliseconds"
        assert metrics_by_name["latency_max"]["Unit"] == "Milliseconds"

    def test_histogram_with_zero_count_skips_count_metric(self):
        output = io.StringIO()
        exporter = CloudWatchEMFExporter(
            namespace="TestApp",
            output=output,
            timestamp_fn=lambda: 1700000000000,
        )

        metrics_data = self.create_mock_histogram_data(count=0)

        exporter.export(metrics_data)

        output.seek(0)
        emf = json.loads(output.readline())

        # Count metric should not be present when count is 0
        assert "latency_count" not in emf

    def test_histogram_with_none_values(self):
        output = io.StringIO()
        exporter = CloudWatchEMFExporter(
            namespace="TestApp",
            output=output,
            timestamp_fn=lambda: 1700000000000,
        )

        # Create histogram with None min/max (can happen with no observations)
        metrics_data = self.create_mock_histogram_data(
            count=0,
            sum_value=None,
            min_value=None,
            max_value=None,
        )

        exporter.export(metrics_data)

        output.seek(0)
        content = output.read()

        # Should still produce valid output (possibly empty if all values are None/0)
        if content.strip():
            emf = json.loads(content.strip())
            # Should not contain None values as metric values
            assert "latency_count" not in emf or emf.get("latency_count") != 0


class TestForceFlushAndShutdown:
    """Test force_flush and shutdown methods."""

    def test_force_flush_returns_true(self):
        output = io.StringIO()
        exporter = CloudWatchEMFExporter(namespace="Test", output=output)
        assert exporter.force_flush() is True

    def test_shutdown_sets_flag(self):
        output = io.StringIO()
        exporter = CloudWatchEMFExporter(namespace="Test", output=output)
        assert exporter._shutdown is False
        exporter.shutdown()
        assert exporter._shutdown is True


class TestThreadSafety:
    """Test thread safety of the exporter."""

    def test_shutdown_is_thread_safe(self):
        import threading

        output = io.StringIO()
        exporter = CloudWatchEMFExporter(namespace="Test", output=output)

        # Verify lock exists
        assert hasattr(exporter, "_lock")
        assert isinstance(exporter._lock, type(threading.Lock()))

    def test_concurrent_export_and_shutdown(self):
        import threading

        output = io.StringIO()
        exporter = CloudWatchEMFExporter(namespace="Test", output=output)

        results = []

        def do_shutdown():
            exporter.shutdown()

        def do_export():
            # Create minimal mock metrics data
            metrics_data = MagicMock()
            metrics_data.resource_metrics = []
            result = exporter.export(metrics_data)
            results.append(result)

        threads = [
            threading.Thread(target=do_shutdown),
            threading.Thread(target=do_export),
            threading.Thread(target=do_export),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should complete without errors
        assert exporter._shutdown is True
