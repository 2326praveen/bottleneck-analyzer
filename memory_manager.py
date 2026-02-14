"""Simulate page replacement algorithms and collect statistics."""

from __future__ import annotations

from typing import Dict, List, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from workload import ProcessWorkload


AlgorithmStats = Dict[str, float]


def fifo_page_faults(reference_string: Sequence[int], frame_count: int) -> int:
    if frame_count <= 0:
        raise ValueError("frame_count must be positive")

    frames: List[int] = []
    pointer = 0
    faults = 0

    for page in reference_string:
        if page in frames:
            continue
        faults += 1
        if len(frames) < frame_count:
            frames.append(page)
        else:
            frames[pointer] = page
            pointer = (pointer + 1) % frame_count

    return faults


def lru_page_faults(reference_string: Sequence[int], frame_count: int) -> int:
    if frame_count <= 0:
        raise ValueError("frame_count must be positive")

    frames: List[int] = []
    last_used: Dict[int, int] = {}
    faults = 0

    for idx, page in enumerate(reference_string):
        if page in frames:
            last_used[page] = idx
            continue

        faults += 1
        if len(frames) < frame_count:
            frames.append(page)
        else:
            lru_page = min(frames, key=lambda p: last_used.get(p, -1))
            replace_index = frames.index(lru_page)
            frames[replace_index] = page
        last_used[page] = idx

    return faults


def optimal_page_faults(reference_string: Sequence[int], frame_count: int) -> int:
    if frame_count <= 0:
        raise ValueError("frame_count must be positive")

    frames: List[int] = []
    faults = 0

    for idx, page in enumerate(reference_string):
        if page in frames:
            continue

        faults += 1
        if len(frames) < frame_count:
            frames.append(page)
            continue

        future_refs = reference_string[idx + 1 :]
        next_use = {}
        for frame_page in frames:
            try:
                next_use[frame_page] = future_refs.index(frame_page)
            except ValueError:
                next_use[frame_page] = float("inf")

        page_to_replace = max(next_use, key=next_use.get)
        replace_index = frames.index(page_to_replace)
        frames[replace_index] = page

    return faults


def simulate_memory(
    workload: Sequence["ProcessWorkload"],
    frame_count: int = 12,
) -> AlgorithmStats:
    """Aggregate page faults for every process in the workload."""

    references = [page for process in workload for page in process.page_references]
    total_refs = len(references)
    if total_refs == 0:
        return {
            "FIFO": 0,
            "LRU": 0,
            "Optimal": 0,
            "total_references": 0,
            "page_fault_rate": 0.0,
        }

    fifo_faults = fifo_page_faults(references, frame_count)
    lru_faults = lru_page_faults(references, frame_count)
    optimal_faults = optimal_page_faults(references, frame_count)

    return {
        "FIFO": fifo_faults,
        "LRU": lru_faults,
        "Optimal": optimal_faults,
        "total_references": total_refs,
        "page_fault_rate": lru_faults / total_refs,
    }
