"""Provide optimization suggestions based on detected bottlenecks."""

from __future__ import annotations

from typing import Dict

SUGGESTIONS: Dict[str, str] = {
    "RAM Bottleneck": "Increase available RAM or switch to an LRU-based paging strategy.",
    "Disk I/O Bottleneck": "Adopt SSTF scheduling or move intensive workloads to SSD storage.",
    "Inefficient Page Replacement": "Replace FIFO with LRU or Optimal where possible.",
}


def get_suggestion(bottleneck: str) -> str:
    return SUGGESTIONS.get(
        bottleneck,
        "System is balanced. Continue monitoring workload trends for emerging bottlenecks.",
    )
