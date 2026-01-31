"""Performance metrics collection and reporting for cwms.

This module provides:
- Operation timing (swap, search, embedding generation)
- Performance statistics (min, max, avg, count)
- Metrics persistence for debugging
- Recent operations history
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OperationMetric:
    """A single operation's timing and metadata."""

    operation: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    success: bool
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "operation": self.operation,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "success": self.success,
            "details": self.details,
            "error": self.error,
        }


@dataclass
class OperationStats:
    """Aggregate statistics for an operation type."""

    operation: str
    count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    last_operation: datetime | None = None

    @property
    def avg_duration_ms(self) -> float:
        """Calculate average duration in milliseconds."""
        if self.count == 0:
            return 0.0
        return self.total_duration_ms / self.count

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        if self.count == 0:
            return 0.0
        return (self.success_count / self.count) * 100

    def record(self, metric: OperationMetric) -> None:
        """Record a new operation metric.

        Args:
            metric: The operation metric to record
        """
        self.count += 1
        if metric.success:
            self.success_count += 1
        else:
            self.failure_count += 1

        self.total_duration_ms += metric.duration_ms
        self.min_duration_ms = min(self.min_duration_ms, metric.duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, metric.duration_ms)
        self.last_operation = metric.end_time

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "operation": self.operation,
            "count": self.count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": f"{self.success_rate:.1f}%",
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "min_duration_ms": round(self.min_duration_ms, 2) if self.count > 0 else 0,
            "max_duration_ms": round(self.max_duration_ms, 2),
            "last_operation": self.last_operation.isoformat() if self.last_operation else None,
        }


class MetricsCollector:
    """Collects and aggregates performance metrics.

    Thread-safe metrics collection with support for:
    - Operation timing via context manager
    - Aggregate statistics per operation type
    - Recent operations history
    - Persistence to disk
    """

    # Operation type constants
    SWAP = "swap"
    SEARCH = "search"
    RETRIEVE = "retrieve"
    EMBED = "embed"
    EMBED_BATCH = "embed_batch"
    STORAGE_READ = "storage_read"
    STORAGE_WRITE = "storage_write"
    BM25_INDEX = "bm25_index"
    BM25_SEARCH = "bm25_search"

    def __init__(
        self,
        history_size: int = 100,
        persist_path: Path | None = None,
    ) -> None:
        """Initialize the metrics collector.

        Args:
            history_size: Maximum number of recent operations to keep
            persist_path: Optional path to persist metrics (JSON file)
        """
        self._lock = RLock()
        self._stats: dict[str, OperationStats] = defaultdict(
            lambda: OperationStats(operation="unknown")
        )
        self._history: list[OperationMetric] = []
        self._history_size = history_size
        self._persist_path = persist_path
        self._start_time = datetime.now()

        # Load persisted metrics if available
        if persist_path and persist_path.exists():
            self._load_persisted()

    def _load_persisted(self) -> None:
        """Load metrics from persisted file."""
        if not self._persist_path or not self._persist_path.exists():
            return

        try:
            with open(self._persist_path, encoding="utf-8") as f:
                data = json.load(f)

            # Restore stats
            for op_name, stats_data in data.get("stats", {}).items():
                stats = OperationStats(operation=op_name)
                stats.count = stats_data.get("count", 0)
                stats.success_count = stats_data.get("success_count", 0)
                stats.failure_count = stats_data.get("failure_count", 0)
                stats.total_duration_ms = stats_data.get("total_duration_ms", 0.0)
                min_dur = stats_data.get("min_duration_ms", float("inf"))
                stats.min_duration_ms = min_dur if min_dur != 0 else float("inf")
                stats.max_duration_ms = stats_data.get("max_duration_ms", 0.0)
                if stats_data.get("last_operation"):
                    stats.last_operation = datetime.fromisoformat(stats_data["last_operation"])
                self._stats[op_name] = stats

            logger.debug("Loaded persisted metrics from %s", self._persist_path)
        except Exception as e:
            logger.warning("Failed to load persisted metrics: %s", e)

    def _persist(self) -> None:
        """Persist current metrics to disk."""
        if not self._persist_path:
            return

        try:
            stats_data: dict[str, Any] = {}

            for op_name, stats in self._stats.items():
                stats_data[op_name] = {
                    "count": stats.count,
                    "success_count": stats.success_count,
                    "failure_count": stats.failure_count,
                    "total_duration_ms": stats.total_duration_ms,
                    "min_duration_ms": stats.min_duration_ms if stats.count > 0 else 0,
                    "max_duration_ms": stats.max_duration_ms,
                    "last_operation": (
                        stats.last_operation.isoformat() if stats.last_operation else None
                    ),
                }

            data = {
                "stats": stats_data,
                "last_updated": datetime.now().isoformat(),
            }

            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._persist_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            logger.warning("Failed to persist metrics: %s", e)

    @contextmanager
    def measure(
        self,
        operation: str,
        **details: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """Context manager to measure operation duration.

        Args:
            operation: Name of the operation (use class constants)
            **details: Additional details to record

        Yields:
            A dictionary that can be updated with additional details

        Example:
            with metrics.measure(MetricsCollector.SWAP, project="my-project") as ctx:
                # Do the swap operation
                ctx["chunks"] = 5
            # Metrics are automatically recorded
        """
        context: dict[str, Any] = dict(details)
        start_time = time.perf_counter()
        start_dt = datetime.now()
        error: str | None = None
        success = True

        try:
            yield context
        except Exception as e:
            error = str(e)
            success = False
            raise
        finally:
            end_time = time.perf_counter()
            end_dt = datetime.now()
            duration_ms = (end_time - start_time) * 1000

            metric = OperationMetric(
                operation=operation,
                start_time=start_dt,
                end_time=end_dt,
                duration_ms=duration_ms,
                success=success,
                details=context,
                error=error,
            )

            self.record(metric)

    def record(self, metric: OperationMetric) -> None:
        """Record an operation metric.

        Args:
            metric: The operation metric to record
        """
        with self._lock:
            # Update stats
            if metric.operation not in self._stats:
                self._stats[metric.operation] = OperationStats(operation=metric.operation)
            self._stats[metric.operation].record(metric)

            # Add to history
            self._history.append(metric)
            if len(self._history) > self._history_size:
                self._history.pop(0)

            # Persist periodically (every 10 operations)
            total_ops = sum(s.count for s in self._stats.values())
            if self._persist_path and total_ops % 10 == 0:
                self._persist()

        # Log the operation
        level = logging.DEBUG if metric.success else logging.WARNING
        logger.log(
            level,
            "%s %s: %.2fms%s",
            metric.operation,
            "succeeded" if metric.success else "failed",
            metric.duration_ms,
            f" - {metric.error}" if metric.error else "",
        )

    def get_stats(self, operation: str | None = None) -> dict[str, Any]:
        """Get statistics for operations.

        Args:
            operation: Specific operation to get stats for, or None for all

        Returns:
            Dictionary of statistics
        """
        with self._lock:
            if operation:
                if operation in self._stats:
                    return self._stats[operation].to_dict()
                return {"operation": operation, "count": 0, "message": "No data"}

            return {
                op_name: stats.to_dict()
                for op_name, stats in self._stats.items()
                if stats.count > 0
            }

    def get_recent_operations(
        self,
        count: int = 10,
        operation: str | None = None,
        failures_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Get recent operations from history.

        Args:
            count: Maximum number of operations to return
            operation: Filter by operation type
            failures_only: Only return failed operations

        Returns:
            List of recent operation metrics
        """
        with self._lock:
            results = []
            for metric in reversed(self._history):
                if operation and metric.operation != operation:
                    continue
                if failures_only and metric.success:
                    continue
                results.append(metric.to_dict())
                if len(results) >= count:
                    break
            return results

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all metrics.

        Returns:
            Dictionary with overall metrics summary
        """
        with self._lock:
            total_ops = sum(s.count for s in self._stats.values())
            total_failures = sum(s.failure_count for s in self._stats.values())
            total_duration = sum(s.total_duration_ms for s in self._stats.values())

            return {
                "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
                "total_operations": total_ops,
                "total_failures": total_failures,
                "total_duration_ms": round(total_duration, 2),
                "operations": self.get_stats(),
                "recent_failures": self.get_recent_operations(count=5, failures_only=True),
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._stats.clear()
            self._history.clear()
            self._start_time = datetime.now()

            if self._persist_path and self._persist_path.exists():
                self._persist_path.unlink()

    def save(self) -> None:
        """Force save metrics to disk."""
        with self._lock:
            self._persist()


# Global metrics instance
_global_metrics: MetricsCollector | None = None


def get_metrics(
    persist_path: Path | None = None,
) -> MetricsCollector:
    """Get the global metrics collector instance.

    Creates a new instance if one doesn't exist.

    Args:
        persist_path: Optional path for metrics persistence

    Returns:
        The global MetricsCollector instance
    """
    global _global_metrics

    if _global_metrics is None:
        # Default persist path in user's cache directory
        if persist_path is None:
            cache_dir = Path.home() / ".claude" / "cwms"
            persist_path = cache_dir / "metrics.json"

        _global_metrics = MetricsCollector(persist_path=persist_path)

    return _global_metrics


def reset_metrics() -> None:
    """Reset the global metrics collector."""
    global _global_metrics
    if _global_metrics:
        _global_metrics.reset()
    _global_metrics = None


@contextmanager
def timed_operation(
    operation: str,
    **details: Any,
) -> Generator[dict[str, Any], None, None]:
    """Convenience context manager for timing operations.

    Uses the global metrics collector.

    Args:
        operation: Name of the operation
        **details: Additional details to record

    Yields:
        A dictionary for additional details

    Example:
        with timed_operation("swap", project="my-project") as ctx:
            # Do work
            ctx["chunks_swapped"] = 5
    """
    metrics = get_metrics()
    with metrics.measure(operation, **details) as ctx:
        yield ctx
