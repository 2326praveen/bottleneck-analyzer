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
from system_monitor import SystemMonitor, is_psutil_available


class AnalyzerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OS Performance Bottleneck Analyzer - Real-Time Monitor")
        self.root.geometry("1024x750")

        self.frame_var = tk.IntVar(value=12)
        self.result_var = tk.StringVar(value="Click Analyze to begin.")
        self.suggestion_var = tk.StringVar(value="")
        self.mode_var = tk.StringVar(value="simulation")
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.refresh_interval = 2000  # milliseconds
        self.auto_refresh_id = None

        # Simulation custom input variables
        self.num_processes_var = tk.IntVar(value=5)
        self.memory_usage_var = tk.DoubleVar(value=50.0)  # percentage
        self.disk_activity_var = tk.IntVar(value=300)  # seek time approximation
        self.use_custom_var = tk.BooleanVar(value=False)

        # Initialize system monitor if available
        self.system_monitor = None
        if is_psutil_available():
            try:
                self.system_monitor = SystemMonitor()
            except ImportError:
                pass

        self._canvas = None
        self._setup_layout()

    def _setup_layout(self) -> None:
        # Top control panel
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        # Mode selection
        ttk.Label(top_frame, text="Mode:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 5))
        mode_frame = ttk.Frame(top_frame)
        mode_frame.grid(row=0, column=1, sticky="w", padx=(0, 20))
        
        real_radio = ttk.Radiobutton(mode_frame, text="Real-Time", variable=self.mode_var, value="real", command=self._on_mode_change)
        real_radio.pack(side="left", padx=(0, 10))
        if not self.system_monitor:
            real_radio.config(state="disabled")
        
        sim_radio = ttk.Radiobutton(mode_frame, text="Simulation", variable=self.mode_var, value="simulation", command=self._on_mode_change)
        sim_radio.pack(side="left")

        # Analyze button
        analyze_button = ttk.Button(top_frame, text="Analyze Now", command=self.run_analysis)
        analyze_button.grid(row=0, column=2, padx=(0, 10))

        # Auto-refresh toggle (only for real-time)
        self.auto_check = ttk.Checkbutton(top_frame, text="Auto-Refresh (2s)", variable=self.auto_refresh_var, 
                                      command=self.toggle_auto_refresh)
        self.auto_check.grid(row=0, column=3)

        # Status indicator
        self.status_label = ttk.Label(top_frame, text="● Idle", foreground="gray")
        self.status_label.grid(row=0, column=4, padx=(20, 0))

        # Show warning if psutil is not available
        if not self.system_monitor:
            warning_text = "⚠️ Real-time monitoring unavailable. Install psutil: pip install psutil"
            warning_label = ttk.Label(top_frame, text=warning_text, foreground="orange")
            warning_label.grid(row=1, column=0, columnspan=5, sticky="w", pady=(5, 0))

        # Simulation custom input panel
        self.sim_input_frame = ttk.LabelFrame(self.root, text="Simulation Parameters (Custom Input)", padding=10)
        self.sim_input_frame.pack(fill="x", padx=10, pady=5)

        # Custom input toggle
        custom_check = ttk.Checkbutton(self.sim_input_frame, text="Use Custom Values", 
                                       variable=self.use_custom_var, command=self._toggle_custom_inputs)
        custom_check.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        # Input fields
        ttk.Label(self.sim_input_frame, text="Processes:").grid(row=1, column=0, sticky="w", padx=(0, 5))
        self.proc_spin = ttk.Spinbox(self.sim_input_frame, from_=1, to=20, textvariable=self.num_processes_var, width=8, state="disabled")
        self.proc_spin.grid(row=1, column=1, padx=(0, 20), sticky="w")

        ttk.Label(self.sim_input_frame, text="Physical Frames:").grid(row=1, column=2, sticky="w", padx=(0, 5))
        self.frame_spin = ttk.Spinbox(self.sim_input_frame, from_=3, to=64, textvariable=self.frame_var, width=8, state="disabled")
        self.frame_spin.grid(row=1, column=3, padx=(0, 20), sticky="w")

        ttk.Label(self.sim_input_frame, text="Memory Load (%):").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=(10, 0))
        self.mem_scale = ttk.Scale(self.sim_input_frame, from_=0, to=100, variable=self.memory_usage_var, 
                                   orient="horizontal", length=150, state="disabled")
        self.mem_scale.grid(row=2, column=1, padx=(0, 5), sticky="w", pady=(10, 0))
        self.mem_label = ttk.Label(self.sim_input_frame, text="50%")
        self.mem_label.grid(row=2, column=1, sticky="e", padx=(0, 20), pady=(10, 0))

        ttk.Label(self.sim_input_frame, text="Disk I/O Load:").grid(row=2, column=2, sticky="w", padx=(0, 5), pady=(10, 0))
        self.disk_scale = ttk.Scale(self.sim_input_frame, from_=50, to=1000, variable=self.disk_activity_var, 
                                    orient="horizontal", length=150, state="disabled")
        self.disk_scale.grid(row=2, column=3, padx=(0, 5), sticky="w", pady=(10, 0))
        self.disk_label = ttk.Label(self.sim_input_frame, text="300")
        self.disk_label.grid(row=2, column=3, sticky="e", padx=(0, 20), pady=(10, 0))

        # Info labels
        ttk.Label(self.sim_input_frame, text="💡 Set Memory > 85% to trigger RAM bottleneck", 
                 foreground="blue", font=("Segoe UI", 8, "italic")).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Label(self.sim_input_frame, text="💡 Set Disk I/O > 500 to trigger Disk bottleneck", 
                 foreground="blue", font=("Segoe UI", 8, "italic")).grid(row=3, column=2, columnspan=2, sticky="w", pady=(10, 0))

        # Bind scale changes to update labels
        self.memory_usage_var.trace_add("write", self._update_mem_label)
        self.disk_activity_var.trace_add("write", self._update_disk_label)

        # Results panel
        result_frame = ttk.LabelFrame(self.root, text="Analysis Results", padding=10)
        result_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(result_frame, textvariable=self.result_var, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(result_frame, textvariable=self.suggestion_var, wraplength=950).pack(anchor="w", pady=(5, 0))

        # Metrics panel
        metrics_frame = ttk.LabelFrame(self.root, text="System Metrics", padding=10)
        metrics_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.metrics_text = tk.Text(metrics_frame, height=8, wrap="word", font=("Consolas", 10))
        self.metrics_text.pack(fill="both", expand=True)
        self.metrics_text.insert("1.0", "Metrics will appear here after analysis.")
        self.metrics_text.configure(state="disabled")

        # Graph panel
        graph_frame = ttk.LabelFrame(self.root, text="Performance Visualization", padding=10)
        graph_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.graph_container = graph_frame

        # Initial state
        self._on_mode_change()

        # Initial state
        self._on_mode_change()

    def _on_mode_change(self) -> None:
        """Handle mode switching between real-time and simulation."""
        is_simulation = self.mode_var.get() == "simulation"
        
        # Show/hide simulation input panel
        if is_simulation:
            self.sim_input_frame.pack(fill="x", padx=10, pady=5, after=self.sim_input_frame.master.winfo_children()[0])
        else:
            self.sim_input_frame.pack_forget()
        
        # Enable/disable auto-refresh (only for real-time)
        if is_simulation:
            self.auto_refresh_var.set(False)
            self.auto_check.config(state="disabled")
        else:
            self.auto_check.config(state="normal")

    def _toggle_custom_inputs(self) -> None:
        """Enable or disable custom input fields."""
        state = "normal" if self.use_custom_var.get() else "disabled"
        self.proc_spin.config(state=state)
        self.frame_spin.config(state=state)
        self.mem_scale.config(state=state)
        self.disk_scale.config(state=state)

    def _update_mem_label(self, *args) -> None:
        """Update memory percentage label."""
        self.mem_label.config(text=f"{self.memory_usage_var.get():.0f}%")

    def _update_disk_label(self, *args) -> None:
        """Update disk activity label."""
        self.disk_label.config(text=f"{self.disk_activity_var.get():.0f}")

    def toggle_auto_refresh(self) -> None:
        """Enable or disable automatic refresh."""
        if self.auto_refresh_var.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()

    def start_auto_refresh(self) -> None:
        """Start automatic refresh cycle."""
        if self.auto_refresh_id is None:
            self.run_analysis()
            self.auto_refresh_id = self.root.after(self.refresh_interval, self.auto_refresh_callback)

    def auto_refresh_callback(self) -> None:
        """Callback for auto-refresh timer."""
        if self.auto_refresh_var.get():
            self.run_analysis()
            self.auto_refresh_id = self.root.after(self.refresh_interval, self.auto_refresh_callback)

    def stop_auto_refresh(self) -> None:
        """Stop automatic refresh cycle."""
        if self.auto_refresh_id is not None:
            self.root.after_cancel(self.auto_refresh_id)
            self.auto_refresh_id = None

    def run_analysis(self) -> None:
        try:
            self.status_label.config(text="● Analyzing...", foreground="blue")
            self.root.update_idletasks()

            mode = self.mode_var.get()
            
            if mode == "real" and self.system_monitor:
                # Real-time monitoring mode
                memory_stats, disk_stats = self.system_monitor.get_analysis_compatible_stats()
                analysis = analyze_performance(memory_stats, disk_stats)
                suggestion = get_suggestion(analysis.bottleneck)
                
                # Get additional real-time metrics
                current_metrics = self.system_monitor.get_current_metrics()
                
            else:
                # Simulation mode
                if self.use_custom_var.get():
                    # Use custom user-defined values
                    num_processes = self.num_processes_var.get()
                    memory_usage_pct = self.memory_usage_var.get()
                    disk_activity = self.disk_activity_var.get()
                    
                    # Generate workload based on custom parameters
                    workload = generate_workload(
                        num_processes=num_processes,
                        reference_length=30,
                        num_pages=int(self.frame_var.get() * 3),  # Scale pages with frames
                        disk_requests=15
                    )
                    
                    # Calculate memory stats based on custom input
                    memory_stats = simulate_memory(workload, frame_count=self.frame_var.get())
                    
                    # Override page fault rate with user's custom value (as percentage)
                    memory_stats["page_fault_rate"] = memory_usage_pct / 100.0
                    memory_stats["memory_percent"] = memory_usage_pct
                    
                    # Calculate disk stats with custom activity level
                    disk_stats = simulate_disk(workload)
                    disk_stats["FCFS"] = disk_activity
                    disk_stats["SSTF"] = disk_activity * 0.7  # SSTF typically 30% better
                    
                else:
                    # Use random generation
                    workload = generate_workload()
                    memory_stats = simulate_memory(workload, frame_count=self.frame_var.get())
                    disk_stats = simulate_disk(workload)
                
                analysis = analyze_performance(memory_stats, disk_stats)
                suggestion = get_suggestion(analysis.bottleneck)
                current_metrics = None

        except Exception as exc:  # pragma: no cover - GUI feedback path
            messagebox.showerror("Analysis Failed", str(exc))
            self.status_label.config(text="● Error", foreground="red")
            return

        self._update_textual_feedback(analysis, suggestion, memory_stats, disk_stats, current_metrics)
        self._render_graph(memory_stats, disk_stats)
        
        # Only speak on manual analysis, not during auto-refresh
        if not self.auto_refresh_var.get():
            self._speak_async(analysis.bottleneck, suggestion)
        
        self.status_label.config(text="● Ready", foreground="green")

    def _update_textual_feedback(self, analysis, suggestion, memory_stats, disk_stats, current_metrics=None) -> None:
        self.result_var.set(f"Detected: {analysis.bottleneck}")
        self.suggestion_var.set(f"Recommendation: {suggestion}")

        if current_metrics:
            # Real-time mode - show actual system metrics
            metrics_lines = [
                "=== REAL-TIME SYSTEM METRICS ===",
                f"CPU Usage: {current_metrics.cpu_percent:.1f}%",
                f"Memory Usage: {current_metrics.memory_percent:.1f}% ({current_metrics.memory_used_mb:.0f} MB / {current_metrics.memory_total_mb:.0f} MB)",
                f"Memory Available: {current_metrics.memory_available_mb:.0f} MB",
                f"Disk Usage: {current_metrics.disk_percent:.1f}%",
                f"Disk Read: {current_metrics.disk_read_mb:.2f} MB/s",
                f"Disk Write: {current_metrics.disk_write_mb:.2f} MB/s",
                f"Disk I/O Operations: {current_metrics.disk_read_count + current_metrics.disk_write_count} ops/s",
                f"Active Processes: {current_metrics.process_count}",
            ]
        else:
            # Simulation mode - show simulated metrics
            mode_text = "CUSTOM INPUT" if self.use_custom_var.get() else "RANDOM GENERATION"
            metrics_lines = [
                f"=== SIMULATION METRICS ({mode_text}) ===",
            ]
            
            if self.use_custom_var.get():
                # Show custom input values
                metrics_lines.extend([
                    f"Input - Processes: {self.num_processes_var.get()}",
                    f"Input - Physical Frames: {self.frame_var.get()}",
                    f"Input - Memory Load: {self.memory_usage_var.get():.0f}%",
                    f"Input - Disk I/O Load: {self.disk_activity_var.get():.0f}",
                    "",
                    "Analysis Results:",
                ])
            
            # Show computed metrics
            metrics_lines.extend([
                f"Page Fault Rate: {analysis.page_fault_rate:.2%}",
                f"FIFO Page Faults: {memory_stats.get('FIFO', 0):.0f}",
                f"LRU Page Faults: {memory_stats.get('LRU', 0):.0f}",
                f"Optimal Page Faults: {memory_stats.get('Optimal', 0):.0f}",
                f"Disk Seek Time (FCFS): {analysis.disk_seek_time:.0f}",
                f"Disk Seek Time (SSTF): {disk_stats.get('SSTF', 0):.0f}",
                f"Total Disk Requests: {disk_stats.get('request_count', 0):.0f}",
            ])

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
    app = AnalyzerGUI(root)
    
    # Ensure cleanup on window close
    def on_closing():
        app.stop_auto_refresh()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
