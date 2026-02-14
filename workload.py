"""Generate synthetic workloads for the OS Performance Bottleneck Analyzer."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class ProcessWorkload:
    """Represents the simplified resource needs of a process."""

    pid: int
    memory_requirement: int
    page_references: Sequence[int]
    disk_requests: Sequence[int]


def generate_workload(
    num_processes: int = 5,
    memory_range: tuple[int, int] = (128, 512),
    reference_length: int = 30,
    num_pages: int = 32,
    disk_requests: int = 15,
    disk_track_range: tuple[int, int] = (0, 499),
    seed: int | None = None,
) -> List[ProcessWorkload]:
    """Create a randomized workload for the simulator."""

    if num_processes <= 0:
        raise ValueError("num_processes must be a positive integer")

    if reference_length <= 0 or num_pages <= 0 or disk_requests <= 0:
        raise ValueError("reference_length, num_pages, and disk_requests must be positive")

    rng = random.Random(seed)
    processes: List[ProcessWorkload] = []
    for pid in range(1, num_processes + 1):
        memory_requirement = rng.randint(*memory_range)
        page_refs = [rng.randint(0, num_pages - 1) for _ in range(reference_length)]
        disk_refs = [rng.randint(*disk_track_range) for _ in range(disk_requests)]
        processes.append(
            ProcessWorkload(
                pid=pid,
                memory_requirement=memory_requirement,
                page_references=page_refs,
                disk_requests=disk_refs,
            )
        )

    return processes
