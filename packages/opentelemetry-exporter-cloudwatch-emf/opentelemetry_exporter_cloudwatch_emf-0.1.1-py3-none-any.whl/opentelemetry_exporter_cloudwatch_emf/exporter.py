"""CloudWatch EMF Exporter for OpenTelemetry metrics.

Converts OpenTelemetry metrics to CloudWatch Embedded Metric Format (EMF) and
prints to stdout. CloudWatch Logs automatically parses EMF and creates metrics.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, TextIO

from opentelemetry.sdk.metrics._internal.instrument import (
    Counter,
    Histogram as HistogramInstrument,
    ObservableCounter,
    ObservableGauge,
    ObservableUpDownCounter,
    UpDownCounter,
)
from opentelemetry.sdk.metrics._internal.point import Metric
from opentelemetry.sdk.metrics.export import (
    AggregationTemporality,
    Gauge,
    Histogram,
    HistogramDataPoint,
    MetricExporter,
    MetricExportResult,
    MetricsData,
    NumberDataPoint,
    Sum,
)

from opentelemetry_exporter_cloudwatch_emf.units import map_unit

logger = logging.getLogger(__name__)


class CloudWatchEMFExporter(MetricExporter):
    """OpenTelemetry metrics exporter using CloudWatch Embedded Metric Format.

    This exporter converts OpenTelemetry metrics to EMF JSON and prints them
    to stdout (or a custom output). When running in AWS environments,
    CloudWatch Logs automatically parses EMF and creates CloudWatch Metrics.

    Args:
        namespace: CloudWatch metrics namespace (required, 1-256 chars)
        output: Output stream for EMF JSON (default: sys.stdout)
        timestamp_fn: Function returning epoch milliseconds (default: current time)
        dimension_keys: List of resource/metric attribute keys to use as dimensions.
                       If None, uses all attributes (be careful of cardinality).
        max_dimensions: Maximum dimensions per metric (CloudWatch limit is 30)
        storage_resolution: 1 for high-resolution (sub-minute), 60 for standard

    Example:
        >>> exporter = CloudWatchEMFExporter(namespace="MyApp")
        >>> reader = PeriodicExportingMetricReader(exporter)
        >>> provider = MeterProvider(metric_readers=[reader])
    """

    def __init__(
        self,
        namespace: str,
        output: TextIO = sys.stdout,
        timestamp_fn: Optional[Callable[[], int]] = None,
        dimension_keys: Optional[List[str]] = None,
        max_dimensions: int = 30,
        storage_resolution: int = 60,
    ):
        if not namespace or len(namespace) > 256:
            raise ValueError("namespace must be 1-256 characters")
        if storage_resolution not in (1, 60):
            raise ValueError("storage_resolution must be 1 or 60")
        if max_dimensions < 0 or max_dimensions > 30:
            raise ValueError("max_dimensions must be 0-30")

        # EMF works best with delta temporality for counters
        preferred_temporality: Dict[type, AggregationTemporality] = {
            Counter: AggregationTemporality.DELTA,
            UpDownCounter: AggregationTemporality.DELTA,
            HistogramInstrument: AggregationTemporality.DELTA,
            ObservableCounter: AggregationTemporality.DELTA,
            ObservableUpDownCounter: AggregationTemporality.CUMULATIVE,
            ObservableGauge: AggregationTemporality.CUMULATIVE,
        }
        super().__init__(preferred_temporality=preferred_temporality)

        self._namespace = namespace
        self._output = output
        self._timestamp_fn = timestamp_fn or (lambda: int(time.time() * 1000))
        self._dimension_keys = dimension_keys
        self._max_dimensions = max_dimensions
        self._storage_resolution = storage_resolution
        self._shutdown = False
        self._lock = threading.Lock()

    def export(
        self,
        metrics_data: MetricsData,
        timeout_millis: float = 10000,
        **kwargs: Any,
    ) -> MetricExportResult:
        """Export metrics as EMF JSON to stdout.

        Args:
            metrics_data: OpenTelemetry MetricsData containing metrics to export
            timeout_millis: Export timeout (unused, EMF export is synchronous)

        Returns:
            MetricExportResult.SUCCESS or MetricExportResult.FAILURE
        """
        with self._lock:
            if self._shutdown:
                logger.warning("Export called after shutdown")
                return MetricExportResult.FAILURE

        try:
            for resource_metrics in metrics_data.resource_metrics:
                resource_attrs = dict(resource_metrics.resource.attributes)

                for scope_metrics in resource_metrics.scope_metrics:
                    for metric in scope_metrics.metrics:
                        self._export_metric(metric, resource_attrs)

            return MetricExportResult.SUCCESS
        except Exception:
            logger.exception("Failed to export metrics")
            return MetricExportResult.FAILURE

    def _export_metric(
        self,
        metric: Metric,
        resource_attrs: Dict[str, Any],
    ) -> None:
        """Export a single metric as EMF JSON."""
        data = metric.data

        if isinstance(data, (Sum, Gauge)):
            self._export_number_metric(metric, data.data_points, resource_attrs)
        elif isinstance(data, Histogram):
            self._export_histogram_metric(metric, data.data_points, resource_attrs)

    def _export_number_metric(
        self,
        metric: Metric,
        data_points: Sequence[NumberDataPoint],
        resource_attrs: Dict[str, Any],
    ) -> None:
        """Export counter/gauge metrics."""
        for point in data_points:
            dimensions = self._build_dimensions(point.attributes, resource_attrs)
            value = point.value

            emf = self._build_emf_document(
                metric_name=metric.name,
                metric_value=value,
                metric_unit=metric.unit,
                dimensions=dimensions,
            )
            self._write_emf(emf)

    def _export_histogram_metric(
        self,
        metric: Metric,
        data_points: Sequence[HistogramDataPoint],
        resource_attrs: Dict[str, Any],
    ) -> None:
        """Export histogram metrics.

        For histograms, we emit multiple derived metrics in a single EMF document:
        - {name}_count: Number of observations
        - {name}_sum: Sum of all observations
        - {name}_min: Minimum value
        - {name}_max: Maximum value

        Note: OpenTelemetry histogram bucket boundaries are not preserved.
        CloudWatch EMF does not support native histogram bucket representation.
        """
        for point in data_points:
            dimensions = self._build_dimensions(point.attributes, resource_attrs)
            base_name = metric.name

            # Build a single EMF document with all histogram metrics
            metrics_list = []
            values: Dict[str, float] = {}

            if point.count is not None and point.count > 0:
                metrics_list.append({"Name": f"{base_name}_count", "Unit": "Count"})
                values[f"{base_name}_count"] = point.count

            if point.sum is not None:
                unit = map_unit(metric.unit)
                metrics_list.append({"Name": f"{base_name}_sum", "Unit": unit})
                values[f"{base_name}_sum"] = point.sum

            if point.min is not None:
                unit = map_unit(metric.unit)
                metrics_list.append({"Name": f"{base_name}_min", "Unit": unit})
                values[f"{base_name}_min"] = point.min

            if point.max is not None:
                unit = map_unit(metric.unit)
                metrics_list.append({"Name": f"{base_name}_max", "Unit": unit})
                values[f"{base_name}_max"] = point.max

            if metrics_list:
                emf = self._build_emf_document_multi(
                    metrics=metrics_list,
                    values=values,
                    dimensions=dimensions,
                )
                self._write_emf(emf)

    def _build_dimensions(
        self,
        point_attrs: Optional[Mapping[str, Any]],
        resource_attrs: Dict[str, Any],
    ) -> Dict[str, str]:
        """Build dimensions from point and resource attributes."""
        # Combine resource and point attributes
        all_attrs: Dict[str, Any] = {}
        all_attrs.update(resource_attrs)
        if point_attrs:
            all_attrs.update(dict(point_attrs))

        # Filter to dimension keys if specified
        if self._dimension_keys:
            filtered = {k: v for k, v in all_attrs.items() if k in self._dimension_keys}
        else:
            filtered = all_attrs

        # Convert to strings and limit count
        dimensions: Dict[str, str] = {}
        for key, value in list(filtered.items())[: self._max_dimensions]:
            # CloudWatch dimension values must be strings, max 1024 chars
            str_value = str(value)[:1024]
            # CloudWatch dimension names must be valid
            safe_key = self._sanitize_dimension_name(key)
            if safe_key and str_value:
                dimensions[safe_key] = str_value

        return dimensions

    def _sanitize_dimension_name(self, name: str) -> str:
        """Sanitize dimension name for CloudWatch compatibility."""
        # Replace dots and slashes with underscores (common in OTel attributes)
        sanitized = name.replace(".", "_").replace("/", "_")
        # Remove any remaining invalid characters
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in "_-")
        return sanitized[:250]  # CloudWatch limit

    def _build_emf_document(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: Optional[str],
        dimensions: Dict[str, str],
    ) -> Dict[str, Any]:
        """Build a single-metric EMF document."""
        cw_unit = map_unit(metric_unit)
        dimension_keys = list(dimensions.keys())

        emf: Dict[str, Any] = {
            "_aws": {
                "Timestamp": self._timestamp_fn(),
                "CloudWatchMetrics": [
                    {
                        "Namespace": self._namespace,
                        "Dimensions": [dimension_keys] if dimension_keys else [[]],
                        "Metrics": [
                            {
                                "Name": metric_name,
                                "Unit": cw_unit,
                                "StorageResolution": self._storage_resolution,
                            }
                        ],
                    }
                ],
            },
            metric_name: metric_value,
        }

        # Add dimensions as top-level keys
        emf.update(dimensions)

        return emf

    def _build_emf_document_multi(
        self,
        metrics: List[Dict[str, Any]],
        values: Dict[str, float],
        dimensions: Dict[str, str],
    ) -> Dict[str, Any]:
        """Build an EMF document with multiple metrics (for histograms)."""
        dimension_keys = list(dimensions.keys())

        # Add storage resolution to each metric
        for m in metrics:
            m["StorageResolution"] = self._storage_resolution

        emf: Dict[str, Any] = {
            "_aws": {
                "Timestamp": self._timestamp_fn(),
                "CloudWatchMetrics": [
                    {
                        "Namespace": self._namespace,
                        "Dimensions": [dimension_keys] if dimension_keys else [[]],
                        "Metrics": metrics,
                    }
                ],
            },
        }

        # Add metric values as top-level keys
        emf.update(values)
        # Add dimensions as top-level keys
        emf.update(dimensions)

        return emf

    def _write_emf(self, emf: Dict[str, Any]) -> None:
        """Write EMF document to output."""
        try:
            line = json.dumps(emf, separators=(",", ":"))
            self._output.write(line + "\n")
            self._output.flush()
        except Exception:
            logger.debug("Failed to write EMF document", exc_info=True)

    def force_flush(self, timeout_millis: float = 10000) -> bool:
        """Flush any buffered data.

        EMF export is synchronous, so this just flushes the output stream.
        """
        try:
            self._output.flush()
            return True
        except Exception:
            return False

    def shutdown(self, timeout_millis: float = 30000, **kwargs: Any) -> None:
        """Shutdown the exporter."""
        with self._lock:
            self._shutdown = True
        self.force_flush()
        logger.debug("CloudWatch EMF Exporter shut down")
