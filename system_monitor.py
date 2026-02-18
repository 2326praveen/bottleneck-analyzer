"""Real-time system performance monitoring using psutil."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict

try:
    import psutil
except ImportError:
    psutil = None


@dataclass(frozen=True)
class SystemMetrics:
    """Real-time system performance metrics."""

    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    memory_used_mb: float
    memory_total_mb: float
    disk_read_mb: float
    disk_write_mb: float
    disk_read_count: int
    disk_write_count: int
    disk_percent: float
    process_count: int
    timestamp: float


class SystemMonitor:
    """Monitor real-time system performance."""

    def __init__(self):
        if psutil is None:
            raise ImportError(
                "psutil is required for real-time monitoring. "
                "Install it with: pip install psutil"
            )
        self._last_disk_io = None
        self._last_timestamp = None

    def get_current_metrics(self) -> SystemMetrics:
        """Capture current system performance metrics."""

        # CPU usage (1-second sample)
        cpu_percent = psutil.cpu_percent(interval=0.5)

        # Memory usage
        mem = psutil.virtual_memory()
        memory_percent = mem.percent
        memory_available_mb = mem.available / (1024 * 1024)
        memory_used_mb = mem.used / (1024 * 1024)
        memory_total_mb = mem.total / (1024 * 1024)

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_usage = psutil.disk_usage('/')

        # Calculate disk I/O rate
        current_time = time.time()
        if self._last_disk_io and self._last_timestamp:
            time_delta = current_time - self._last_timestamp
            disk_read_mb = (disk_io.read_bytes - self._last_disk_io.read_bytes) / (1024 * 1024 * time_delta)
            disk_write_mb = (disk_io.write_bytes - self._last_disk_io.write_bytes) / (1024 * 1024 * time_delta)
            disk_read_count = disk_io.read_count - self._last_disk_io.read_count
            disk_write_count = disk_io.write_count - self._last_disk_io.write_count
        else:
            disk_read_mb = 0.0
            disk_write_mb = 0.0
            disk_read_count = 0
            disk_write_count = 0

        self._last_disk_io = disk_io
        self._last_timestamp = current_time

        # Process count
        process_count = len(psutil.pids())

        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_mb=memory_available_mb,
            memory_used_mb=memory_used_mb,
            memory_total_mb=memory_total_mb,
            disk_read_mb=disk_read_mb,
            disk_write_mb=disk_write_mb,
            disk_read_count=disk_read_count,
            disk_write_count=disk_write_count,
            disk_percent=disk_usage.percent,
            process_count=process_count,
            timestamp=current_time,
        )

    def get_analysis_compatible_stats(self) -> tuple[Dict[str, float], Dict[str, float]]:
        """
        Get metrics in a format compatible with the existing analyzer.
        
        Returns:
            tuple: (memory_stats, disk_stats) dictionaries
        """
        metrics = self.get_current_metrics()

        # Convert real metrics to analyzer-compatible format
        memory_stats = {
            "page_fault_rate": metrics.memory_percent / 100.0,  # Normalize to 0-1
            "FIFO": metrics.memory_used_mb,
            "LRU": metrics.memory_used_mb * 0.95,  # Simulated improvement with LRU
            "Optimal": metrics.memory_used_mb * 0.90,  # Theoretical optimal
            "memory_percent": metrics.memory_percent,
            "available_mb": metrics.memory_available_mb,
            "used_mb": metrics.memory_used_mb,
        }

        # Disk I/O activity as "seek time" proxy
        # Higher I/O = higher effective seek time
        disk_activity = (metrics.disk_read_count + metrics.disk_write_count) * 10
        disk_stats = {
            "FCFS": disk_activity,
            "SSTF": disk_activity * 0.7,  # SSTF is typically 30% more efficient
            "request_count": metrics.disk_read_count + metrics.disk_write_count,
            "disk_percent": metrics.disk_percent,
            "read_mb_s": metrics.disk_read_mb,
            "write_mb_s": metrics.disk_write_mb,
        }

        return memory_stats, disk_stats


def is_psutil_available() -> bool:
    """Check if psutil is installed and available."""
    return psutil is not None
