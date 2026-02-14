"""Tkinter interface tying every component together."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from analyzer import analyze_performance
from audio_report import narrate_result
from disk_scheduler import simulate_disk
from graphs import create_performance_figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from memory_manager import simulate_memory
from suggestion import get_suggestion
from workload import generate_workload


class AnalyzerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OS Performance Bottleneck Analyzer")
        self.root.geometry("960x640")

        self.frame_var = tk.IntVar(value=12)
        self.result_var = tk.StringVar(value="Click Analyze to begin.")
        self.suggestion_var = tk.StringVar(value="")

        self._canvas = None
        self._setup_layout()

    def _setup_layout(self) -> None:
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        ttk.Label(top_frame, text="Physical Frames").grid(row=0, column=0, sticky="w")
        frame_spin = ttk.Spinbox(top_frame, from_=3, to=64, textvariable=self.frame_var, width=5)
        frame_spin.grid(row=0, column=1, padx=(5, 20))

        analyze_button = ttk.Button(top_frame, text="Analyze", command=self.run_analysis)
        analyze_button.grid(row=0, column=2)

        result_frame = ttk.LabelFrame(self.root, text="Insights", padding=10)
        result_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(result_frame, textvariable=self.result_var, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(result_frame, textvariable=self.suggestion_var, wraplength=900).pack(anchor="w", pady=(5, 0))

        metrics_frame = ttk.LabelFrame(self.root, text="Metrics", padding=10)
        metrics_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.metrics_text = tk.Text(metrics_frame, height=8, wrap="word")
        self.metrics_text.pack(fill="both", expand=True)
        self.metrics_text.insert("1.0", "Metrics will appear here after analysis.")
        self.metrics_text.configure(state="disabled")

        graph_frame = ttk.LabelFrame(self.root, text="Performance Graph", padding=10)
        graph_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.graph_container = graph_frame

    def run_analysis(self) -> None:
        try:
            workload = generate_workload()
            memory_stats = simulate_memory(workload, frame_count=self.frame_var.get())
            disk_stats = simulate_disk(workload)
            analysis = analyze_performance(memory_stats, disk_stats)
            suggestion = get_suggestion(analysis.bottleneck)
        except Exception as exc:  # pragma: no cover - GUI feedback path
            messagebox.showerror("Analysis Failed", str(exc))
            return

        self._update_textual_feedback(analysis, suggestion, memory_stats, disk_stats)
        self._render_graph(memory_stats, disk_stats)
        self._speak_async(analysis.bottleneck, suggestion)

    def _update_textual_feedback(self, analysis, suggestion, memory_stats, disk_stats) -> None:
        self.result_var.set(f"Detected: {analysis.bottleneck}")
        self.suggestion_var.set(f"Recommendation: {suggestion}")

        metrics_lines = [
            f"Page Fault Rate (LRU): {analysis.page_fault_rate:.2f}",
            f"FIFO Faults: {memory_stats.get('FIFO', 0):.0f}",
            f"LRU Faults: {memory_stats.get('LRU', 0):.0f}",
            f"Optimal Faults: {memory_stats.get('Optimal', 0):.0f}",
            f"Disk Seek Time (FCFS): {analysis.disk_seek_time:.0f}",
            f"Disk Seek Time (SSTF): {disk_stats.get('SSTF', 0):.0f}",
            f"Disk Requests: {disk_stats.get('request_count', 0):.0f}",
        ]

        self.metrics_text.configure(state="normal")
        self.metrics_text.delete("1.0", tk.END)
        self.metrics_text.insert("1.0", "\n".join(metrics_lines))
        self.metrics_text.configure(state="disabled")

    def _render_graph(self, memory_stats, disk_stats) -> None:
        fig = create_performance_figure(memory_stats, disk_stats)
        if self._canvas:
            self._canvas.get_tk_widget().destroy()
        self._canvas = FigureCanvasTkAgg(fig, master=self.graph_container)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    def _speak_async(self, bottleneck: str, suggestion: str) -> None:
        threading.Thread(
            target=narrate_result,
            args=(bottleneck, suggestion),
            daemon=True,
        ).start()


def launch_gui() -> None:
    root = tk.Tk()
    AnalyzerGUI(root)
    root.mainloop()
