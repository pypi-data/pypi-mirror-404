"""Local audit logging module.

This module provides append-only audit logging for compliance
and security tracking. Supports both full audit and GDPR-compliant
metadata-only modes.

Key features:
- Append-only log (immutable for compliance)
- GDPR metadata mode (no actual PII values stored)
- Configurable retention and rotation
- Query and export capabilities
"""

import gzip
import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterator, List, Optional, Dict, Any


@dataclass
class AuditEntry:
    """A single audit log entry."""

    timestamp: str
    event_type: str
    decision: str
    destination: str
    detected_types: List[str]
    detected_counts: Dict[str, int]
    bytes_processed: int
    duration_ms: float = 0.0
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Entry hash for integrity verification
    entry_hash: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "decision": self.decision,
            "destination": self.destination,
            "detected_types": self.detected_types,
            "detected_counts": self.detected_counts,
            "bytes_processed": self.bytes_processed,
            "duration_ms": self.duration_ms,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "metadata": self.metadata,
            "entry_hash": self.entry_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        """Create from dictionary."""
        return cls(
            timestamp=data["timestamp"],
            event_type=data["event_type"],
            decision=data["decision"],
            destination=data.get("destination", "AI_TOOL"),
            detected_types=data.get("detected_types", []),
            detected_counts=data.get("detected_counts", {}),
            bytes_processed=data.get("bytes_processed", 0),
            duration_ms=data.get("duration_ms", 0.0),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            metadata=data.get("metadata", {}),
            entry_hash=data.get("entry_hash"),
        )

    def compute_hash(self, previous_hash: Optional[str] = None) -> str:
        """Compute hash for this entry (blockchain-style chaining)."""
        content = json.dumps({
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "decision": self.decision,
            "detected_types": self.detected_types,
            "previous_hash": previous_hash or "",
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:32]


class AuditLog:
    """Append-only audit log for compliance tracking.

    This class provides immutable audit logging with optional
    GDPR-compliant metadata-only mode.

    Example:
        # Full audit mode
        audit = AuditLog("/var/log/aegis/audit.jsonl")
        audit.log_processing(
            decision="ALLOWED_WITH_MASKING",
            destination="AI_TOOL",
            detected=[{"type": "EMAIL", "count": 2}],
            bytes_processed=1024,
        )

        # GDPR metadata-only mode
        audit = AuditLog(
            "/var/log/aegis/audit.jsonl",
            metadata_only=True
        )
        # Only stores: {"type": "EMAIL", "count": 2}, never actual values
    """

    def __init__(
        self,
        log_path: Path,
        metadata_only: bool = True,
        rotation_days: int = 30,
        rotation_size_mb: int = 100,
        compress_rotated: bool = True,
        retention_days: Optional[int] = None,
        verify_chain: bool = False,
    ):
        """Initialize audit log.

        Args:
            log_path: Path to audit log file
            metadata_only: If True, never store actual PII samples (GDPR mode, default)
            rotation_days: Rotate log after this many days
            rotation_size_mb: Rotate log after this size in MB
            compress_rotated: Compress rotated log files
            retention_days: Delete logs older than this (None = keep forever)
            verify_chain: Verify hash chain on each write (slower)
        """
        self.log_path = Path(log_path)
        self.metadata_only = metadata_only
        self.rotation_days = rotation_days
        self.rotation_size_mb = rotation_size_mb
        self.compress_rotated = compress_rotated
        self.retention_days = retention_days
        self.verify_chain = verify_chain

        self._lock = threading.Lock()
        self._last_hash: Optional[str] = None

        # Ensure directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Load last hash if verifying chain
        if self.verify_chain:
            self._last_hash = self._get_last_hash()

    def log_processing(
        self,
        decision: str,
        destination: str,
        detected: List[Dict],
        bytes_processed: int,
        duration_ms: float = 0.0,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Log a processing event.

        Args:
            decision: Processing decision
            destination: Target destination
            detected: List of detection results
            bytes_processed: Number of bytes processed
            duration_ms: Processing duration
            user_id: Optional user identifier
            session_id: Optional session identifier
            request_id: Optional request identifier
            metadata: Optional additional metadata
        """
        # Extract types and counts (metadata only)
        detected_types = []
        detected_counts = {}

        for item in detected:
            # Handle both dict and object (DetectedItem) inputs
            if isinstance(item, dict):
                det_type = item.get("type", "UNKNOWN")
                det_count = item.get("count", 1)
            else:
                det_type = getattr(item, "type", "UNKNOWN")
                det_count = getattr(item, "count", 1)

            detected_types.append(det_type)
            detected_counts[det_type] = detected_counts.get(det_type, 0) + det_count

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="processing",
            decision=decision,
            destination=destination,
            detected_types=detected_types,
            detected_counts=detected_counts,
            bytes_processed=bytes_processed,
            duration_ms=duration_ms,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            metadata=metadata or {},
        )

        self._write_entry(entry)

    def log_blocked(
        self,
        reason: str,
        destination: str,
        detected: List[Dict],
        bytes_processed: int,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Log a blocked request.

        Args:
            reason: Reason for blocking
            destination: Target destination
            detected: List of detection results
            bytes_processed: Number of bytes
            user_id: Optional user identifier
            metadata: Optional additional metadata
        """
        detected_types = []
        for d in detected:
            if isinstance(d, dict):
                detected_types.append(d.get("type", "UNKNOWN"))
            else:
                detected_types.append(getattr(d, "type", "UNKNOWN"))
        detected_counts = {t: 1 for t in detected_types}

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="blocked",
            decision="BLOCKED",
            destination=destination,
            detected_types=detected_types,
            detected_counts=detected_counts,
            bytes_processed=bytes_processed,
            user_id=user_id,
            metadata={"reason": reason, **(metadata or {})},
        )

        self._write_entry(entry)

    def log_access(
        self,
        action: str,
        resource: str,
        user_id: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict] = None,
    ):
        """Log an access event.

        Args:
            action: Action performed (read, write, delete)
            resource: Resource accessed
            user_id: User performing action
            success: Whether action succeeded
            metadata: Additional metadata
        """
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="access",
            decision="SUCCESS" if success else "FAILURE",
            destination=resource,
            detected_types=[],
            detected_counts={},
            bytes_processed=0,
            user_id=user_id,
            metadata={"action": action, **(metadata or {})},
        )

        self._write_entry(entry)

    def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        decisions: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Iterator[AuditEntry]:
        """Query audit log entries.

        Args:
            start_time: Filter entries after this time
            end_time: Filter entries before this time
            event_types: Filter by event types
            decisions: Filter by decisions
            user_id: Filter by user ID
            limit: Maximum entries to return

        Yields:
            Matching AuditEntry objects
        """
        count = 0

        for entry in self._read_entries():
            # Apply filters
            if start_time:
                entry_time = datetime.fromisoformat(entry.timestamp)
                if entry_time < start_time:
                    continue

            if end_time:
                entry_time = datetime.fromisoformat(entry.timestamp)
                if entry_time > end_time:
                    continue

            if event_types and entry.event_type not in event_types:
                continue

            if decisions and entry.decision not in decisions:
                continue

            if user_id and entry.user_id != user_id:
                continue

            yield entry
            count += 1

            if limit and count >= limit:
                break

    def get_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict:
        """Get summary statistics.

        Args:
            start_time: Start of period
            end_time: End of period

        Returns:
            Summary dictionary
        """
        total_entries = 0
        total_bytes = 0
        decisions: Dict[str, int] = {}
        detections: Dict[str, int] = {}
        event_types: Dict[str, int] = {}

        for entry in self.query(start_time=start_time, end_time=end_time):
            total_entries += 1
            total_bytes += entry.bytes_processed

            decisions[entry.decision] = decisions.get(entry.decision, 0) + 1
            event_types[entry.event_type] = event_types.get(entry.event_type, 0) + 1

            for det_type, count in entry.detected_counts.items():
                detections[det_type] = detections.get(det_type, 0) + count

        return {
            "total_entries": total_entries,
            "total_bytes": total_bytes,
            "decisions": decisions,
            "detections": detections,
            "event_types": event_types,
        }

    def export(
        self,
        output_path: Path,
        format: str = "jsonl",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """Export audit log to file.

        Args:
            output_path: Output file path
            format: Output format (jsonl, csv)
            start_time: Start of export period
            end_time: End of export period

        Returns:
            Number of entries exported
        """
        count = 0

        with open(output_path, "w") as f:
            if format == "csv":
                # Write header
                f.write("timestamp,event_type,decision,destination,detected_types,bytes_processed,user_id\n")

            for entry in self.query(start_time=start_time, end_time=end_time):
                if format == "jsonl":
                    f.write(json.dumps(entry.to_dict()) + "\n")
                elif format == "csv":
                    f.write(
                        f"{entry.timestamp},{entry.event_type},{entry.decision},"
                        f"{entry.destination},{';'.join(entry.detected_types)},"
                        f"{entry.bytes_processed},{entry.user_id or ''}\n"
                    )
                count += 1

        return count

    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """Verify the integrity of the audit log.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.verify_chain:
            return True, None

        previous_hash = None

        for entry in self._read_entries():
            expected_hash = entry.compute_hash(previous_hash)

            if entry.entry_hash and entry.entry_hash != expected_hash:
                return False, f"Hash mismatch at {entry.timestamp}"

            previous_hash = entry.entry_hash or expected_hash

        return True, None

    def rotate(self, force: bool = False):
        """Rotate the audit log.

        Args:
            force: Force rotation regardless of size/age
        """
        if not self.log_path.exists():
            return

        should_rotate = force

        if not should_rotate:
            # Check size
            size_mb = self.log_path.stat().st_size / (1024 * 1024)
            if size_mb >= self.rotation_size_mb:
                should_rotate = True

        if not should_rotate:
            # Check age
            mtime = datetime.fromtimestamp(self.log_path.stat().st_mtime)
            age_days = (datetime.now() - mtime).days
            if age_days >= self.rotation_days:
                should_rotate = True

        if should_rotate:
            self._perform_rotation()

    def cleanup(self):
        """Clean up old rotated logs based on retention policy."""
        if not self.retention_days:
            return

        cutoff = datetime.now() - timedelta(days=self.retention_days)
        log_dir = self.log_path.parent

        for file in log_dir.glob(f"{self.log_path.stem}.*"):
            if file == self.log_path:
                continue

            try:
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime < cutoff:
                    file.unlink()
            except OSError:
                pass

    def _write_entry(self, entry: AuditEntry):
        """Write an entry to the log."""
        with self._lock:
            # Check rotation
            self._check_rotation()

            # Compute hash if verifying
            if self.verify_chain:
                entry.entry_hash = entry.compute_hash(self._last_hash)
                self._last_hash = entry.entry_hash

            # Append to log
            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")

    def _read_entries(self) -> Iterator[AuditEntry]:
        """Read all entries from log."""
        if not self.log_path.exists():
            return

        with open(self.log_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    yield AuditEntry.from_dict(data)
                except (json.JSONDecodeError, KeyError):
                    continue

    def _check_rotation(self):
        """Check if rotation is needed."""
        if not self.log_path.exists():
            return

        size_mb = self.log_path.stat().st_size / (1024 * 1024)
        if size_mb >= self.rotation_size_mb:
            self._perform_rotation()

    def _perform_rotation(self):
        """Perform log rotation."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        rotated_name = f"{self.log_path.stem}.{timestamp}{self.log_path.suffix}"
        rotated_path = self.log_path.parent / rotated_name

        self.log_path.rename(rotated_path)

        if self.compress_rotated:
            with open(rotated_path, "rb") as f_in:
                with gzip.open(f"{rotated_path}.gz", "wb") as f_out:
                    f_out.writelines(f_in)
            rotated_path.unlink()

    def _get_last_hash(self) -> Optional[str]:
        """Get hash of last entry for chain verification."""
        last_hash = None

        for entry in self._read_entries():
            if entry.entry_hash:
                last_hash = entry.entry_hash

        return last_hash


class GDPRAuditLog(AuditLog):
    """GDPR-compliant audit log that never stores PII.

    This is a convenience subclass that enforces metadata-only mode
    and provides additional GDPR compliance features.

    Example:
        audit = GDPRAuditLog("/var/log/aegis/gdpr_audit.jsonl")
        # Only stores: {"detected_types": ["EMAIL"], "detected_counts": {"EMAIL": 5}}
        # Never stores: actual email addresses
    """

    def __init__(
        self,
        log_path: Path,
        retention_days: int = 90,  # GDPR default
        **kwargs,
    ):
        """Initialize GDPR audit log.

        Args:
            log_path: Path to audit log
            retention_days: Retention period (default 90 days for GDPR)
            **kwargs: Additional AuditLog arguments
        """
        super().__init__(
            log_path=log_path,
            metadata_only=True,  # Force metadata only
            retention_days=retention_days,
            **kwargs,
        )

    def get_data_subject_report(self, user_id: str) -> dict:
        """Generate a GDPR Article 15 data subject access report.

        Args:
            user_id: The data subject's user ID

        Returns:
            Report dictionary
        """
        entries = list(self.query(user_id=user_id))

        return {
            "data_subject": user_id,
            "report_generated": datetime.now(timezone.utc).isoformat(),
            "total_processing_events": len(entries),
            "detection_summary": self._summarize_detections(entries),
            "processing_purposes": ["AI tool data protection"],
            "data_categories_detected": list(set(
                dt for e in entries for dt in e.detected_types
            )),
            "note": "No actual PII values are stored (GDPR Article 5 compliant)",
        }

    def _summarize_detections(self, entries: List[AuditEntry]) -> dict:
        """Summarize detections for a list of entries."""
        summary = {}
        for entry in entries:
            for det_type, count in entry.detected_counts.items():
                summary[det_type] = summary.get(det_type, 0) + count
        return summary
