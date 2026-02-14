"""Matplotlib helpers for visualizing analyzer metrics."""

from __future__ import annotations

from typing import Dict

import matplotlib.pyplot as plt


def create_performance_figure(memory_stats: Dict[str, float], disk_stats: Dict[str, float]):
    fig, ax = plt.subplots(figsize=(5, 4))

    categories = ["FIFO Faults", "LRU Faults", "Disk Seek Time"]
    values = [
        memory_stats.get("FIFO", 0.0),
        memory_stats.get("LRU", 0.0),
        disk_stats.get("FCFS", 0.0),
    ]

    bars = ax.bar(categories, values, color=["#f4a261", "#2a9d8f", "#264653"])
    ax.set_ylabel("Counts / Time")
    ax.set_title("Memory vs Disk Pressure")
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.0f}", ha="center", va="bottom")

    fig.tight_layout()
    return fig
