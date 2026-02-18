"""Analyze collected metrics to identify likely performance bottlenecks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AnalysisResult:
    bottleneck: str
    page_fault_rate: float
    disk_seek_time: float
    context: Dict[str, float]


def analyze_performance(
    memory_stats: Dict[str, float],
    disk_stats: Dict[str, float],
    disk_threshold: float = 500.0,
    memory_threshold: float = 0.85,  # 85% memory usage
) -> AnalysisResult:
    """
    Analyze system performance metrics to identify bottlenecks.
    
    Works with both simulated and real system metrics.
    For real metrics, page_fault_rate represents memory usage percentage.
    """
    page_fault_rate = memory_stats.get("page_fault_rate", 0.0)
    fifo_faults = memory_stats.get("FIFO", 0.0)
    lru_faults = memory_stats.get("LRU", 0.0)
    disk_seek_time = disk_stats.get("FCFS", 0.0)
    
    # Check for real-time metrics indicators
    memory_percent = memory_stats.get("memory_percent", page_fault_rate * 100)
    disk_io_count = disk_stats.get("request_count", 0.0)

    # Analyze bottlenecks with priority order
    if memory_percent > memory_threshold * 100 or page_fault_rate > memory_threshold:
        bottleneck = "RAM Bottleneck"
    elif disk_seek_time > disk_threshold or disk_io_count > 100:
        bottleneck = "Disk I/O Bottleneck"
    elif lru_faults and fifo_faults > lru_faults * 1.25:
        bottleneck = "Inefficient Page Replacement"
    else:
        bottleneck = "Balanced System"

    return AnalysisResult(
        bottleneck=bottleneck,
        page_fault_rate=page_fault_rate,
        disk_seek_time=disk_seek_time,
        context={
            "fifo_faults": fifo_faults,
            "lru_faults": lru_faults,
            "optimal_faults": memory_stats.get("Optimal", 0.0),
            "disk_sstf": disk_stats.get("SSTF", 0.0),
            "request_count": disk_stats.get("request_count", 0.0),
            "memory_percent": memory_percent,
        },
    )
