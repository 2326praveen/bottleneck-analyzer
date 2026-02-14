"""Disk scheduling algorithms for the OS Performance Bottleneck Analyzer."""

from __future__ import annotations

from typing import Dict, List, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from workload import ProcessWorkload


DiskStats = Dict[str, float]


def fcfs_seek_time(requests: Sequence[int], initial_head: int = 100) -> int:
    if not requests:
        return 0

    total_seek = abs(initial_head - requests[0])
    for prev, curr in zip(requests[:-1], requests[1:]):
        total_seek += abs(curr - prev)
    return total_seek


def sstf_seek_time(requests: Sequence[int], initial_head: int = 100) -> int:
    remaining = list(requests)
    head = initial_head
    total_seek = 0

    while remaining:
        closest = min(remaining, key=lambda r: abs(r - head))
        total_seek += abs(closest - head)
        head = closest
        remaining.remove(closest)

    return total_seek


def simulate_disk(
    workload: Sequence["ProcessWorkload"],
    initial_head: int = 100,
) -> DiskStats:
    requests = [track for process in workload for track in process.disk_requests]
    if not requests:
        return {
            "FCFS": 0,
            "SSTF": 0,
            "request_count": 0,
            "average_seek": 0.0,
        }

    fcfs_total = fcfs_seek_time(requests, initial_head)
    sstf_total = sstf_seek_time(requests, initial_head)
    return {
        "FCFS": fcfs_total,
        "SSTF": sstf_total,
        "request_count": len(requests),
        "average_seek": fcfs_total / len(requests),
    }
