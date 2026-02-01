"""Async metrics reporting module.

This module provides non-blocking metrics collection and reporting
to Aegis Cloud. Metrics are batched and sent asynchronously to
minimize impact on processing latency.

Key features:
- Non-blocking metric recording
- Batched uploads (by count or time)
- Thread-safe operation
- Graceful degradation on network issues
- No customer data in metrics (only counts and types)
"""

import json
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional, Dict, List
from pathlib import Path

from aegis_sdk import __version__

# Default configuration
DEFAULT_BATCH_SIZE = 100
DEFAULT_FLUSH_INTERVAL = 300  # 5 minutes
DEFAULT_API_ENDPOINT = "https://api.aegispreflight.com/v1"


@dataclass
class MetricEvent:
    """A single metric event."""

    timestamp: str
    decision: str
    bytes_processed: int
    detected_types: List[str]
    detected_counts: Dict[str, int]
    destination: str = "AI_TOOL"
    duration_ms: float = 0.0
    source: str = "sdk"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "decision": self.decision,
            "bytes": self.bytes_processed,
            "detected_types": self.detected_types,
            "detected_counts": self.detected_counts,
            "destination": self.destination,
            "duration_ms": self.duration_ms,
            "source": self.source,
        }


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for a batch."""

    period_start: str
    period_end: str
    total_checks: int = 0
    bytes_scanned: int = 0
    decisions: Dict[str, int] = field(default_factory=dict)
    detections: Dict[str, int] = field(default_factory=dict)
    avg_duration_ms: float = 0.0
    destinations: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for API."""
        return {
            "period": f"{self.period_start}/{self.period_end}",
            "aggregated": {
                "total_checks": self.total_checks,
                "bytes_scanned": self.bytes_scanned,
                "decisions": self.decisions,
                "detections": self.detections,
                "avg_duration_ms": round(self.avg_duration_ms, 2),
                "destinations": self.destinations,
            },
        }


class MetricsReporter:
    """Async metrics reporter for Aegis Cloud.

    This class collects processing metrics and sends them to
    Aegis Cloud in batches. All operations are non-blocking
    and thread-safe.

    IMPORTANT: No customer data is ever sent. Only:
    - Counts (checks, bytes, detections)
    - Types (EMAIL, PHONE, etc.)
    - Decisions (ALLOWED, MASKED, BLOCKED)

    Example:
        reporter = MetricsReporter("aegis_lic_xxxxx")

        # Record a processing result
        reporter.record(
            decision="ALLOWED_WITH_MASKING",
            bytes_processed=1024,
            detected_types=["EMAIL", "PHONE"],
            detected_counts={"EMAIL": 2, "PHONE": 1},
        )

        # Metrics are automatically flushed in background
        # Or force flush before shutdown
        reporter.flush()
    """

    def __init__(
        self,
        license_key: str,
        api_endpoint: str = DEFAULT_API_ENDPOINT,
        batch_size: int = DEFAULT_BATCH_SIZE,
        flush_interval: int = DEFAULT_FLUSH_INTERVAL,
        enabled: bool = True,
        on_error: Optional[Callable[[Exception], None]] = None,
        fallback_path: Optional[Path] = None,
        sdk_version: Optional[str] = None,
        policy_group: Optional[str] = None,
    ):
        """Initialize metrics reporter.

        Args:
            license_key: Aegis license key for authentication
            api_endpoint: Aegis API endpoint
            batch_size: Number of events before auto-flush
            flush_interval: Seconds between auto-flushes
            enabled: Whether metrics reporting is enabled
            on_error: Callback for error handling
            fallback_path: Path for fallback storage on network failure
        """
        self.license_key = license_key
        self.api_endpoint = api_endpoint
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.enabled = enabled
        self.on_error = on_error
        self.fallback_path = fallback_path

        # Get SDK version if not provided
        if sdk_version is None:
            try:
                from aegis_sdk import __version__
                sdk_version = __version__
            except ImportError:
                sdk_version = "unknown"
        self.sdk_version = sdk_version
        self.policy_group = policy_group

        self._queue: queue.Queue = queue.Queue()
        self._buffer: List[MetricEvent] = []
        self._buffer_lock = threading.Lock()
        self._last_flush = time.time()
        self._flush_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Start background flush thread
        if self.enabled:
            self._start_flush_thread()

    def record(
        self,
        decision: str,
        bytes_processed: int,
        detected_types: List[str],
        detected_counts: Dict[str, int],
        destination: str = "AI_TOOL",
        duration_ms: float = 0.0,
    ):
        """Record a processing event (non-blocking).

        Args:
            decision: Processing decision
            bytes_processed: Number of bytes processed
            detected_types: List of detection types found
            detected_counts: Count of each detection type
            destination: Target destination
            duration_ms: Processing duration in milliseconds
        """
        if not self.enabled:
            return

        event = MetricEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision=decision,
            bytes_processed=bytes_processed,
            detected_types=detected_types,
            detected_counts=detected_counts,
            destination=destination,
            duration_ms=duration_ms,
        )

        with self._buffer_lock:
            self._buffer.append(event)

            # Auto-flush if buffer is full
            if len(self._buffer) >= self.batch_size:
                self._trigger_flush()

    def record_from_result(self, result, destination: str = "AI_TOOL", duration_ms: float = 0.0):
        """Record from a ProcessingResult object.

        Args:
            result: ProcessingResult from Aegis processing
            destination: Target destination
            duration_ms: Processing duration
        """
        # Get decision as string
        decision = result.decision
        if hasattr(decision, 'value'):
            decision = decision.value
        else:
            decision = str(decision)

        # Get detection types and counts
        detected_types = []
        detected_counts = {}
        for d in result.detected:
            dtype = d.type.value if hasattr(d.type, 'value') else str(d.type)
            detected_types.append(dtype)
            detected_counts[dtype] = detected_counts.get(dtype, 0) + d.count

        self.record(
            decision=decision,
            bytes_processed=result.bytes_processed,
            detected_types=detected_types,
            detected_counts=detected_counts,
            destination=destination,
            duration_ms=duration_ms,
        )

    def flush(self, blocking: bool = True):
        """Flush buffered metrics to API.

        Args:
            blocking: If True, wait for flush to complete
        """
        if not self.enabled:
            return

        if blocking:
            self._do_flush()
        else:
            self._trigger_flush()

    def stop(self):
        """Stop the reporter and flush remaining metrics."""
        self._stop_event.set()

        # Final flush
        self._do_flush()

        if self._flush_thread and self._flush_thread.is_alive():
            self._flush_thread.join(timeout=5)

    def get_pending_count(self) -> int:
        """Get number of pending metrics in buffer."""
        with self._buffer_lock:
            return len(self._buffer)

    def _start_flush_thread(self):
        """Start background flush thread."""
        def flush_loop():
            while not self._stop_event.is_set():
                # Check if we should flush
                time_since_flush = time.time() - self._last_flush
                if time_since_flush >= self.flush_interval:
                    self._do_flush()

                # Sleep for a bit
                self._stop_event.wait(timeout=10)

        self._flush_thread = threading.Thread(target=flush_loop, daemon=True)
        self._flush_thread.start()

    def _trigger_flush(self):
        """Trigger a non-blocking flush."""
        threading.Thread(target=self._do_flush, daemon=True).start()

    def _do_flush(self):
        """Perform the actual flush."""
        with self._buffer_lock:
            if not self._buffer:
                return

            events = self._buffer.copy()
            self._buffer.clear()
            self._last_flush = time.time()

        # Aggregate events
        aggregated = self._aggregate_events(events)

        # Send to API
        try:
            self._send_metrics(aggregated)
        except Exception as e:
            # Try fallback storage
            if self.fallback_path:
                self._save_to_fallback(events)

            if self.on_error:
                self.on_error(e)

    def _aggregate_events(self, events: List[MetricEvent]) -> AggregatedMetrics:
        """Aggregate events into summary metrics."""
        if not events:
            now = datetime.now(timezone.utc).isoformat()
            return AggregatedMetrics(period_start=now, period_end=now)

        total_bytes = 0
        total_duration = 0.0
        decisions: Dict[str, int] = {}
        detections: Dict[str, int] = {}
        destinations: Dict[str, int] = {}

        for event in events:
            total_bytes += event.bytes_processed
            total_duration += event.duration_ms

            # Count decisions
            decisions[event.decision] = decisions.get(event.decision, 0) + 1

            # Sum detection counts
            for det_type, count in event.detected_counts.items():
                detections[det_type] = detections.get(det_type, 0) + count

            # Count destinations
            destinations[event.destination] = destinations.get(event.destination, 0) + 1

        return AggregatedMetrics(
            period_start=events[0].timestamp,
            period_end=events[-1].timestamp,
            total_checks=len(events),
            bytes_scanned=total_bytes,
            decisions=decisions,
            detections=detections,
            avg_duration_ms=total_duration / len(events) if events else 0,
            destinations=destinations,
        )

    def _send_metrics(self, metrics: AggregatedMetrics):
        """Send metrics to Aegis Cloud API."""
        try:
            import urllib.request
            import urllib.error

            url = f"{self.api_endpoint}/v1/metrics/batch"
            headers = {
                "Authorization": f"Bearer {self.license_key}",
                "Content-Type": "application/json",
                "User-Agent": f"aegis-sdk/{__version__}",
            }

            payload = {
                "license_key": self.license_key,
                "sdk_version": self.sdk_version,
                "policy_group": self.policy_group,
                **metrics.to_dict(),
            }

            data = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                url, data=data, headers=headers, method="POST"
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status not in (200, 201, 202):
                    raise Exception(f"API returned status {response.status}")

        except ImportError:
            # No urllib available
            pass
        except Exception as e:
            raise e

    def _save_to_fallback(self, events: List[MetricEvent]):
        """Save events to fallback file for later retry."""
        if not self.fallback_path:
            return

        try:
            self.fallback_path.parent.mkdir(parents=True, exist_ok=True)

            # Append to file
            with open(self.fallback_path, "a") as f:
                for event in events:
                    f.write(json.dumps(event.to_dict()) + "\n")
        except OSError:
            pass


class LocalMetricsCollector:
    """Local-only metrics collector for offline/air-gapped environments.

    This collector stores metrics locally without sending to cloud.
    Useful for compliance reporting and internal analytics.

    Example:
        collector = LocalMetricsCollector("/var/log/aegis/metrics.jsonl")
        collector.record(...)

        # Get summary
        summary = collector.get_summary()
    """

    def __init__(
        self,
        output_path: Path,
        rotation_size_mb: int = 100,
    ):
        """Initialize local collector.

        Args:
            output_path: Path for metrics file
            rotation_size_mb: Rotate file after this size
        """
        self.output_path = Path(output_path)
        self.rotation_size_mb = rotation_size_mb
        self._lock = threading.Lock()

        # Ensure directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        decision: str,
        bytes_processed: int,
        detected_types: List[str],
        detected_counts: Dict[str, int],
        destination: str = "AI_TOOL",
        duration_ms: float = 0.0,
    ):
        """Record a metric event locally."""
        event = MetricEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision=decision,
            bytes_processed=bytes_processed,
            detected_types=detected_types,
            detected_counts=detected_counts,
            destination=destination,
            duration_ms=duration_ms,
            source="sdk-local",
        )

        with self._lock:
            self._check_rotation()

            with open(self.output_path, "a") as f:
                f.write(json.dumps(event.to_dict()) + "\n")

    def get_summary(self, since: Optional[datetime] = None) -> dict:
        """Get summary of recorded metrics.

        Args:
            since: Only include events after this time

        Returns:
            Summary dictionary
        """
        events = []

        try:
            with open(self.output_path, "r") as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if since:
                            event_time = datetime.fromisoformat(event["timestamp"])
                            if event_time < since:
                                continue
                        events.append(event)
                    except (json.JSONDecodeError, KeyError):
                        continue
        except FileNotFoundError:
            pass

        if not events:
            return {"total_checks": 0, "bytes_scanned": 0}

        total_bytes = sum(e.get("bytes", 0) for e in events)
        decisions = {}
        detections = {}

        for event in events:
            decision = event.get("decision", "UNKNOWN")
            decisions[decision] = decisions.get(decision, 0) + 1

            for det_type, count in event.get("detected_counts", {}).items():
                detections[det_type] = detections.get(det_type, 0) + count

        return {
            "total_checks": len(events),
            "bytes_scanned": total_bytes,
            "decisions": decisions,
            "detections": detections,
            "period_start": events[0].get("timestamp") if events else None,
            "period_end": events[-1].get("timestamp") if events else None,
        }

    def _check_rotation(self):
        """Check if file should be rotated."""
        try:
            if not self.output_path.exists():
                return

            size_mb = self.output_path.stat().st_size / (1024 * 1024)
            if size_mb >= self.rotation_size_mb:
                # Rotate file
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                rotated_path = self.output_path.with_suffix(f".{timestamp}.jsonl")
                self.output_path.rename(rotated_path)
        except OSError:
            pass
