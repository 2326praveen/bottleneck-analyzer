"""Matplotlib helpers for visualizing analyzer metrics (dark dashboard theme)."""

from __future__ import annotations

from typing import Dict

import matplotlib.pyplot as plt
import numpy as np


# ── Palette (matches gui.py) ──────────────────────────────────────────────
_BG      = "#161b22"
_TEXT    = "#f0f6fc"
_MUTED   = "#484f58"
_GRID    = "#21262d"
_ACCENT  = "#58a6ff"
_GREEN   = "#3fb950"
_RED     = "#f85149"
_ORANGE  = "#d29922"
_PURPLE  = "#bc8cff"
_CYAN    = "#39d2c0"


def _style_ax(ax):
    """Apply dark theme to an axes."""
    ax.set_facecolor(_BG)
    ax.tick_params(colors=_TEXT, labelsize=8, length=3, pad=4)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("bottom", "left"):
        ax.spines[sp].set_color(_GRID)
        ax.spines[sp].set_linewidth(0.8)
    ax.yaxis.label.set_color(_TEXT)
    ax.xaxis.label.set_color(_TEXT)
    ax.title.set_color(_TEXT)


def create_performance_figure(memory_stats: Dict[str, float], disk_stats: Dict[str, float]):
    """Create enhanced 3-panel visualization with gauge and detailed comparison charts."""
    
    fig = plt.figure(figsize=(11, 3.8), facecolor=_BG)
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 0.05], width_ratios=[1.2, 1, 1],
                          hspace=0.05, wspace=0.35)
    
    ax_gauge = fig.add_subplot(gs[0, 0])
    ax_mem = fig.add_subplot(gs[0, 1])
    ax_disk = fig.add_subplot(gs[0, 2])
    
    # Apply styling
    for ax in [ax_mem, ax_disk]:
        _style_ax(ax)
    
    ax_gauge.set_facecolor(_BG)
    ax_gauge.axis("off")

    # ══════════════════════════════════════════════════════════════════════
    # PANEL 1: Enhanced Page Fault Rate Gauge
    # ══════════════════════════════════════════════════════════════════════
    pf_rate = memory_stats.get("page_fault_rate", 0.0)
    if pf_rate > 1:
        pf_rate = pf_rate / 100.0

    # Background arc
    theta = np.linspace(np.pi, 0, 180)
    ax_gauge.plot(np.cos(theta), np.sin(theta), color=_GRID, lw=16,
                  solid_capstyle="round", zorder=1)

    # Color zones
    gauge_color = _GREEN if pf_rate < 0.5 else (_ORANGE if pf_rate < 0.85 else _RED)
    
    # Filled arc representing current value
    end_idx = int(pf_rate * 180)
    if end_idx > 1:
        theta_fill = theta[:end_idx]
        ax_gauge.plot(np.cos(theta_fill), np.sin(theta_fill),
                      color=gauge_color, lw=16, solid_capstyle="round", zorder=2)

    # Threshold markers
    for thresh, label in [(0.5, "50%"), (0.85, "85%")]:
        angle = np.pi - thresh * np.pi
        x, y = 1.15 * np.cos(angle), 1.15 * np.sin(angle)
        ax_gauge.plot([0.9 * np.cos(angle), 1.05 * np.cos(angle)],
                      [0.9 * np.sin(angle), 1.05 * np.sin(angle)],
                      color=_MUTED, lw=1.5, zorder=0)
        ax_gauge.text(x, y, label, ha="center", va="center",
                      color=_MUTED, fontsize=7)

    # Needle
    angle = np.pi - pf_rate * np.pi
    needle_len = 0.72
    ax_gauge.annotate("", xy=(needle_len * np.cos(angle), needle_len * np.sin(angle)),
                      xytext=(0, 0),
                      arrowprops=dict(arrowstyle="-|>", color=_TEXT, lw=2, shrinkA=0, shrinkB=0))

    # Center value display
    ax_gauge.text(0, -0.12, f"{pf_rate:.0%}", ha="center", va="center",
                  color=gauge_color, fontsize=26, fontweight="bold")
    ax_gauge.text(0, -0.38, "Page Fault Rate", ha="center", va="center",
                  color=_MUTED, fontsize=9, style="italic")
    
    # Status labels
    status_text = "OPTIMAL" if pf_rate < 0.5 else ("WARNING" if pf_rate < 0.85 else "CRITICAL")
    status_color = _GREEN if pf_rate < 0.5 else (_ORANGE if pf_rate < 0.85 else _RED)
    ax_gauge.text(0, -0.55, status_text, ha="center", va="center",
                  color=status_color, fontsize=8, fontweight="bold")

    ax_gauge.set_xlim(-1.35, 1.35)
    ax_gauge.set_ylim(-0.65, 1.2)
    ax_gauge.set_aspect("equal")

    # ══════════════════════════════════════════════════════════════════════
    # PANEL 2: Memory Replacement Algorithms Comparison
    # ══════════════════════════════════════════════════════════════════════
    mem_cats = ["FIFO", "LRU", "Optimal"]
    mem_vals = [memory_stats.get(k, 0.0) for k in mem_cats]
    colors_mem = [_ORANGE, _PURPLE, _GREEN]
    
    y_pos = np.arange(len(mem_cats))
    bars_mem = ax_mem.barh(y_pos, mem_vals, height=0.6,
                           color=colors_mem, edgecolor=_BG, linewidth=1.5, zorder=3)
    
    ax_mem.set_yticks(y_pos)
    ax_mem.set_yticklabels(mem_cats, fontsize=9)
    ax_mem.set_xlabel("Page Faults", fontsize=9, labelpad=6)
    ax_mem.set_title("Memory Replacement", fontsize=11, fontweight="bold", pad=10)
    ax_mem.grid(axis="x", color=_GRID, linestyle="--", alpha=0.5, linewidth=0.7, zorder=0)
    ax_mem.invert_yaxis()
    
    # Value labels
    max_val = max(mem_vals) if mem_vals else 1
    for i, (bar, val) in enumerate(zip(bars_mem, mem_vals)):
        offset = max_val * 0.02
        ax_mem.text(bar.get_width() + offset, bar.get_y() + bar.get_height() / 2,
                    f"{val:.0f}", va="center", ha="left",
                    color=_TEXT, fontsize=10, fontweight="bold")
    
    # Add efficiency indicator
    if mem_vals[2] > 0:  # Optimal exists
        optimal = mem_vals[2]
        for i, val in enumerate(mem_vals[:2]):
            if val > 0:
                efficiency = (1 - (val - optimal) / val) * 100 if val > optimal else 100
                eff_color = _GREEN if efficiency > 80 else (_ORANGE if efficiency > 60 else _RED)
                ax_mem.text(0.02, y_pos[i], f"{efficiency:.0f}%",
                           va="center", ha="left", color=eff_color,
                           fontsize=7, fontweight="bold",
                           bbox=dict(boxstyle="round,pad=0.3", facecolor=_BG,
                                   edgecolor=eff_color, linewidth=0.8))

    # ══════════════════════════════════════════════════════════════════════
    # PANEL 3: Disk Scheduling Algorithms Comparison
    # ══════════════════════════════════════════════════════════════════════
    disk_cats = ["FCFS", "SSTF"]
    disk_vals = [disk_stats.get(k, 0.0) for k in disk_cats]
    colors_disk = [_CYAN, _ACCENT]
    
    y_pos_disk = np.arange(len(disk_cats))
    bars_disk = ax_disk.barh(y_pos_disk, disk_vals, height=0.5,
                             color=colors_disk, edgecolor=_BG, linewidth=1.5, zorder=3)
    
    ax_disk.set_yticks(y_pos_disk)
    ax_disk.set_yticklabels(disk_cats, fontsize=9)
    ax_disk.set_xlabel("Seek Distance", fontsize=9, labelpad=6)
    ax_disk.set_title("Disk Scheduling", fontsize=11, fontweight="bold", pad=10)
    ax_disk.grid(axis="x", color=_GRID, linestyle="--", alpha=0.5, linewidth=0.7, zorder=0)
    ax_disk.invert_yaxis()
    
    # Value labels
    max_disk = max(disk_vals) if disk_vals else 1
    for bar, val in zip(bars_disk, disk_vals):
        offset = max_disk * 0.02
        ax_disk.text(bar.get_width() + offset, bar.get_y() + bar.get_height() / 2,
                     f"{val:.0f}", va="center", ha="left",
                     color=_TEXT, fontsize=10, fontweight="bold")
    
    # Improvement indicator
    if disk_vals[0] > 0 and disk_vals[1] > 0:
        improvement = ((disk_vals[0] - disk_vals[1]) / disk_vals[0]) * 100
        imp_color = _GREEN if improvement > 0 else _RED
        ax_disk.text(0.98, 0.05, f"SSTF improves by {improvement:.1f}%",
                    transform=ax_disk.transAxes, ha="right", va="bottom",
                    color=imp_color, fontsize=7, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.4", facecolor=_BG,
                            edgecolor=imp_color, linewidth=0.8, alpha=0.9))

    # Footer info bar (spans all columns)
    info_ax = fig.add_subplot(gs[1, :])
    info_ax.set_facecolor(_BG)
    info_ax.axis("off")
    
    req_count = disk_stats.get("request_count", 0)
    info_text = f"Total Disk Requests: {req_count:.0f}  |  "
    info_text += f"FIFO: {mem_vals[0]:.0f} faults  |  LRU: {mem_vals[1]:.0f} faults  |  "
    info_text += f"Optimal: {mem_vals[2]:.0f} faults"
    
    info_ax.text(0.5, 0.5, info_text, ha="center", va="center",
                color=_MUTED, fontsize=7, transform=info_ax.transAxes)

    return fig
