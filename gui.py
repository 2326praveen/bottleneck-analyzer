"""Modern dashboard-style Tkinter interface for OS Bottleneck Analyzer."""

from __future__ import annotations

import threading
import time
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

# ── Color Palette ──────────────────────────────────────────────────────────
BG_DARK       = "#0d1117"
BG_CARD       = "#161b22"
BG_INPUT      = "#21262d"
BG_HOVER      = "#30363d"
ACCENT        = "#58a6ff"
ACCENT_GLOW   = "#1f6feb"
ACCENT_DIM    = "#1a3a5c"
TEXT_PRIMARY   = "#f0f6fc"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED     = "#484f58"
GREEN         = "#3fb950"
GREEN_DIM     = "#1b3a2a"
RED           = "#f85149"
RED_DIM       = "#3d1a1e"
ORANGE        = "#d29922"
ORANGE_DIM    = "#3d2e00"
CYAN          = "#39d2c0"
PURPLE        = "#bc8cff"
BORDER        = "#30363d"
SEPARATOR     = "#21262d"


class AudioButton(tk.Canvas):
    """Circular audio play button with icon."""

    def __init__(self, parent, command=None, size=36, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=parent["bg"], highlightthickness=0, bd=0, **kw)
        self._command = command
        self._size = size
        self._enabled = False
        self._paint(GREEN_DIM, GREEN)
        self.bind("<Enter>", lambda e: self._on_hover() if self._enabled else None)
        self.bind("<Leave>", lambda e: self._on_leave() if self._enabled else None)
        self.bind("<ButtonRelease-1>", lambda e: self._on_click() if self._enabled else None)

    def _paint(self, bg_color, fg_color):
        self.delete("all")
        r = self._size / 2
        # Circle background
        self.create_oval(2, 2, self._size - 2, self._size - 2,
                         fill=bg_color, outline="", tags="circle")
        # Play icon (triangle)
        cx, cy = r, r
        pts = [
            cx - 5, cy - 6,
            cx - 5, cy + 6,
            cx + 6, cy
        ]
        self.create_polygon(pts, fill=fg_color, outline="", tags="icon")

    def _on_hover(self):
        if self._enabled:
            self._paint(GREEN, TEXT_PRIMARY)

    def _on_leave(self):
        if self._enabled:
            self._paint(GREEN_DIM, GREEN)

    def _on_click(self):
        if self._enabled and self._command:
            self._command()

    def enable(self):
        self._enabled = True
        self._paint(GREEN_DIM, GREEN)

    def disable(self):
        self._enabled = False
        self._paint(BG_INPUT, TEXT_MUTED)


class PillButton(tk.Canvas):
    """Pill-shaped button with glow hover effect."""

    def __init__(self, parent, text="", command=None, btn_width=140, btn_height=36,
                 bg_color=ACCENT_GLOW, fg_color="#ffffff", hover_color=ACCENT,
                 font_spec=("Segoe UI", 10, "bold"), **kw):
        super().__init__(parent, width=btn_width, height=btn_height,
                         bg=parent["bg"], highlightthickness=0, bd=0, **kw)
        self._command = command
        self._bg_color = bg_color
        self._hover_color = hover_color
        self._fg_color = fg_color
        self._btn_w = btn_width
        self._btn_h = btn_height
        self._font = font_spec
        self._label = text
        self._paint(bg_color)
        self.bind("<Enter>", lambda e: self._paint(self._hover_color))
        self.bind("<Leave>", lambda e: self._paint(self._bg_color))
        self.bind("<ButtonRelease-1>", lambda e: self._command() if self._command else None)

    def _paint(self, fill):
        self.delete("all")
        r = self._btn_h // 2
        w, h = self._btn_w, self._btn_h
        self.create_arc(0, 0, r * 2, h, start=90, extent=180, fill=fill, outline="")
        self.create_arc(w - r * 2, 0, w, h, start=-90, extent=180, fill=fill, outline="")
        self.create_rectangle(r, 0, w - r, h, fill=fill, outline="")
        self.create_text(w // 2, h // 2, text=self._label,
                         fill=self._fg_color, font=self._font)


class MetricTile(tk.Frame):
    """A small dashboard tile showing a single metric with label, value, and color bar."""

    def __init__(self, parent, label="Metric", value="--", bar_color=ACCENT, **kw):
        super().__init__(parent, bg=BG_CARD, **kw)

        # Left color accent bar
        tk.Frame(self, bg=bar_color, width=4).pack(side="left", fill="y")

        inner = tk.Frame(self, bg=BG_CARD)
        inner.pack(side="left", fill="both", expand=True, padx=(10, 12), pady=8)

        self._label = tk.Label(inner, text=label.upper(), fg=TEXT_MUTED, bg=BG_CARD,
                               font=("Segoe UI", 7, "bold"))
        self._label.pack(anchor="w")

        self._value = tk.Label(inner, text=value, fg=TEXT_PRIMARY, bg=BG_CARD,
                               font=("Segoe UI", 16, "bold"))
        self._value.pack(anchor="w")

    def set_value(self, text, color=TEXT_PRIMARY):
        self._value.config(text=text, fg=color)


class AnalyzerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OS Bottleneck Analyzer")
        self.root.geometry("1200x860")
        self.root.configure(bg=BG_DARK)
        self.root.minsize(960, 720)

        self._apply_theme()

        self.frame_var = tk.IntVar(value=12)
        self.result_var = tk.StringVar(value="Run an analysis to see results")
        self.suggestion_var = tk.StringVar(value="")
        self.mode_var = tk.StringVar(value="simulation")
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.refresh_interval = 2000
        self.auto_refresh_id = None

        self.num_processes_var = tk.IntVar(value=5)
        self.memory_usage_var = tk.DoubleVar(value=50.0)
        self.disk_activity_var = tk.IntVar(value=300)
        self.use_custom_var = tk.BooleanVar(value=False)

        self.system_monitor = None
        if is_psutil_available():
            try:
                self.system_monitor = SystemMonitor()
            except ImportError:
                pass

        self._canvas = None
        self._audio_data = None  # Store last analysis results for audio playback
        self._setup_layout()

    # ── Theme ──────────────────────────────────────────────────────────────
    def _apply_theme(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(".", background=BG_DARK, foreground=TEXT_PRIMARY,
                    fieldbackground=BG_INPUT, borderwidth=0, font=("Segoe UI", 10))
        s.configure("TFrame", background=BG_DARK)
        s.configure("TLabel", background=BG_DARK, foreground=TEXT_PRIMARY)
        s.configure("TRadiobutton", background=BG_DARK, foreground=TEXT_PRIMARY,
                    font=("Segoe UI", 10), indicatorcolor=ACCENT)
        s.map("TRadiobutton", background=[("active", BG_DARK)],
              foreground=[("disabled", TEXT_MUTED)])
        s.configure("TCheckbutton", background=BG_CARD, foreground=TEXT_PRIMARY,
                    font=("Segoe UI", 10), indicatorcolor=ACCENT)
        s.map("TCheckbutton", background=[("active", BG_CARD)],
              foreground=[("disabled", TEXT_MUTED)])
        s.configure("Dark.TCheckbutton", background=BG_DARK, foreground=TEXT_PRIMARY,
                    font=("Segoe UI", 10), indicatorcolor=ACCENT)
        s.map("Dark.TCheckbutton", background=[("active", BG_DARK)])
        s.configure("TSpinbox", fieldbackground=BG_INPUT, foreground=TEXT_PRIMARY,
                    arrowcolor=ACCENT, borderwidth=1, relief="flat")
        s.configure("Horizontal.TScale", background=BG_CARD, troughcolor=BG_INPUT,
                    sliderrelief="flat")
        s.map("Horizontal.TScale", background=[("active", ACCENT)])

    # ── Layout ─────────────────────────────────────────────────────────────
    def _setup_layout(self) -> None:
        # ── Sidebar ────────────────────────────────────────────────────────
        sidebar = tk.Frame(self.root, bg=BG_CARD, width=260)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo / Title
        brand = tk.Frame(sidebar, bg=BG_CARD)
        brand.pack(fill="x", padx=20, pady=(22, 4))
        tk.Label(brand, text="OS", fg=ACCENT, bg=BG_CARD,
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(brand, text=" Analyzer", fg=TEXT_PRIMARY, bg=BG_CARD,
                 font=("Segoe UI", 22)).pack(side="left")

        tk.Label(sidebar, text="Bottleneck diagnostics", fg=TEXT_MUTED, bg=BG_CARD,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 18))

        # Divider
        tk.Frame(sidebar, bg=SEPARATOR, height=1).pack(fill="x", padx=16, pady=(0, 14))

        # Mode selector
        tk.Label(sidebar, text="MODE", fg=TEXT_MUTED, bg=BG_CARD,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=20, pady=(0, 6))

        self.real_radio = ttk.Radiobutton(sidebar, text="  Real-Time Monitor",
                                          variable=self.mode_var, value="real",
                                          command=self._on_mode_change)
        self.real_radio.pack(anchor="w", padx=20, pady=2)
        if not self.system_monitor:
            self.real_radio.config(state="disabled")

        ttk.Radiobutton(sidebar, text="  Simulation", variable=self.mode_var,
                        value="simulation", command=self._on_mode_change
                        ).pack(anchor="w", padx=20, pady=2)

        # psutil note
        if not self.system_monitor:
            tk.Label(sidebar, text="psutil not installed", fg=ORANGE, bg=BG_CARD,
                     font=("Segoe UI", 7, "italic")).pack(anchor="w", padx=24, pady=(2, 0))

        tk.Frame(sidebar, bg=SEPARATOR, height=1).pack(fill="x", padx=16, pady=14)

        # ── Simulation parameters (in sidebar) ────────────────────────────
        self.sim_frame = tk.Frame(sidebar, bg=BG_CARD)
        self.sim_frame.pack(fill="x")

        tk.Label(self.sim_frame, text="SIMULATION PARAMETERS", fg=TEXT_MUTED, bg=BG_CARD,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=20, pady=(0, 8))

        custom_check = ttk.Checkbutton(self.sim_frame, text="Use Custom Values",
                                       variable=self.use_custom_var,
                                       command=self._toggle_custom_inputs)
        custom_check.pack(anchor="w", padx=20, pady=(0, 8))

        params = tk.Frame(self.sim_frame, bg=BG_CARD)
        params.pack(fill="x", padx=20)

        # Processes
        self._sidebar_label(params, "Processes", 0)
        self.proc_spin = ttk.Spinbox(params, from_=1, to=20, textvariable=self.num_processes_var,
                                     width=6, state="disabled")
        self.proc_spin.grid(row=0, column=1, sticky="e", pady=3)

        # Frames
        self._sidebar_label(params, "Phys. Frames", 1)
        self.frame_spin = ttk.Spinbox(params, from_=3, to=64, textvariable=self.frame_var,
                                      width=6, state="disabled")
        self.frame_spin.grid(row=1, column=1, sticky="e", pady=3)

        params.columnconfigure(0, weight=1)

        # Memory slider
        mem_row = tk.Frame(self.sim_frame, bg=BG_CARD)
        mem_row.pack(fill="x", padx=20, pady=(8, 0))
        tk.Label(mem_row, text="Memory Load", fg=TEXT_SECONDARY, bg=BG_CARD,
                 font=("Segoe UI", 9)).pack(side="left")
        self.mem_label = tk.Label(mem_row, text="50 %", fg=CYAN, bg=BG_CARD,
                                  font=("Segoe UI", 9, "bold"))
        self.mem_label.pack(side="right")
        self.mem_scale = ttk.Scale(self.sim_frame, from_=0, to=100,
                                   variable=self.memory_usage_var,
                                   orient="horizontal", length=200, state="disabled")
        self.mem_scale.pack(padx=20, anchor="w", pady=(2, 0))

        # Disk slider
        disk_row = tk.Frame(self.sim_frame, bg=BG_CARD)
        disk_row.pack(fill="x", padx=20, pady=(8, 0))
        tk.Label(disk_row, text="Disk I/O Load", fg=TEXT_SECONDARY, bg=BG_CARD,
                 font=("Segoe UI", 9)).pack(side="left")
        self.disk_label = tk.Label(disk_row, text="300", fg=CYAN, bg=BG_CARD,
                                   font=("Segoe UI", 9, "bold"))
        self.disk_label.pack(side="right")
        self.disk_scale = ttk.Scale(self.sim_frame, from_=50, to=1000,
                                    variable=self.disk_activity_var,
                                    orient="horizontal", length=200, state="disabled")
        self.disk_scale.pack(padx=20, anchor="w", pady=(2, 0))

        # Tips
        tk.Label(self.sim_frame, text="Mem > 85% = RAM bottleneck", fg=TEXT_MUTED, bg=BG_CARD,
                 font=("Segoe UI", 7, "italic")).pack(anchor="w", padx=20, pady=(10, 0))
        tk.Label(self.sim_frame, text="Disk > 500  = Disk bottleneck", fg=TEXT_MUTED, bg=BG_CARD,
                 font=("Segoe UI", 7, "italic")).pack(anchor="w", padx=20, pady=(1, 0))

        self.memory_usage_var.trace_add("write", self._update_mem_label)
        self.disk_activity_var.trace_add("write", self._update_disk_label)

        # Spacer
        tk.Frame(sidebar, bg=BG_CARD).pack(fill="both", expand=True)

        # Bottom buttons
        btn_area = tk.Frame(sidebar, bg=BG_CARD)
        btn_area.pack(fill="x", padx=16, pady=(0, 14))

        tk.Frame(btn_area, bg=SEPARATOR, height=1).pack(fill="x", pady=(0, 14))

        self.auto_check = ttk.Checkbutton(btn_area, text="Auto-Refresh (2 s)",
                                          variable=self.auto_refresh_var,
                                          command=self.toggle_auto_refresh)
        self.auto_check.pack(anchor="w", padx=4, pady=(0, 10))
        PillButton(btn_area, text="▶  Analyze Now", command=self.run_analysis,
                   btn_width=220, btn_height=42,
                   font_spec=("Segoe UI", 11, "bold")).pack(fill="x")

        # ── Main Content ──────────────────────────────────────────────────
        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(side="right", fill="both", expand=True)

        # Top bar
        topbar = tk.Frame(main, bg=BG_DARK)
        topbar.pack(fill="x", padx=24, pady=(18, 0))

        tk.Label(topbar, text="Dashboard", fg=TEXT_PRIMARY, bg=BG_DARK,
                 font=("Segoe UI", 17, "bold")).pack(side="left")
        self.status_badge = tk.Label(topbar, text="  IDLE  ", fg=TEXT_MUTED,
                                     bg=BG_INPUT, font=("Segoe UI", 8, "bold"),
                                     padx=10, pady=3)
        self.status_badge.pack(side="right")
        self.timestamp_lbl = tk.Label(topbar, text="", fg=TEXT_MUTED, bg=BG_DARK,
                                      font=("Segoe UI", 8))
        self.timestamp_lbl.pack(side="right", padx=(0, 12))

        # ── Metric Tiles Row ──────────────────────────────────────────────
        tiles_frame = tk.Frame(main, bg=BG_DARK)
        tiles_frame.pack(fill="x", padx=24, pady=(14, 0))

        self.tile_fault = MetricTile(tiles_frame, label="Page Fault Rate", value="--", bar_color=RED)
        self.tile_fault.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.tile_fifo = MetricTile(tiles_frame, label="FIFO Faults", value="--", bar_color=ORANGE)
        self.tile_fifo.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.tile_lru = MetricTile(tiles_frame, label="LRU Faults", value="--", bar_color=PURPLE)
        self.tile_lru.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.tile_disk = MetricTile(tiles_frame, label="Disk Seek (FCFS)", value="--", bar_color=CYAN)
        self.tile_disk.pack(side="left", fill="both", expand=True)

        # ── Result Banner ─────────────────────────────────────────────────
        self.result_card = tk.Frame(main, bg=BG_CARD, highlightthickness=1,
                                    highlightbackground=BORDER)
        self.result_card.pack(fill="x", padx=24, pady=(12, 0))

        # Left accent bar inside result card
        self.result_accent = tk.Frame(self.result_card, bg=ACCENT, width=5)
        self.result_accent.pack(side="left", fill="y")

        result_inner = tk.Frame(self.result_card, bg=BG_CARD)
        result_inner.pack(side="left", fill="both", expand=True, padx=16, pady=14)

        res_top = tk.Frame(result_inner, bg=BG_CARD)
        res_top.pack(fill="x")

        self.result_label = tk.Label(res_top, textvariable=self.result_var,
                                     fg=TEXT_SECONDARY, bg=BG_CARD,
                                     font=("Segoe UI", 14, "bold"), anchor="w")
        self.result_label.pack(side="left", fill="x", expand=True)

        # Audio button
        audio_frame = tk.Frame(res_top, bg=BG_CARD)
        audio_frame.pack(side="right", padx=(10, 0))
        
        tk.Label(audio_frame, text="🔊", fg=TEXT_MUTED, bg=BG_CARD,
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
        
        self.audio_btn = AudioButton(audio_frame, command=self._play_audio, size=38)
        self.audio_btn.pack(side="left")
        self.audio_btn.disable()

        self.suggestion_label = tk.Label(result_inner, textvariable=self.suggestion_var,
                                         fg=TEXT_MUTED, bg=BG_CARD,
                                         font=("Segoe UI", 9), anchor="w",
                                         wraplength=750, justify="left")
        self.suggestion_label.pack(fill="x", pady=(6, 0))

        # ── Bottom Row: Metrics + Graph side by side ──────────────────────
        bottom = tk.Frame(main, bg=BG_DARK)
        bottom.pack(fill="both", expand=True, padx=24, pady=(12, 18))

        # Metrics panel (left side)
        met_card = tk.Frame(bottom, bg=BG_CARD, highlightthickness=1,
                            highlightbackground=BORDER, width=320)
        met_card.pack(side="left", fill="y", padx=(0, 10))
        met_card.pack_propagate(False)

        met_header = tk.Frame(met_card, bg=BG_CARD)
        met_header.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(met_header, text="Detailed Metrics", fg=ACCENT, bg=BG_CARD,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")

        self.metrics_text = tk.Text(met_card, wrap="word",
                                    font=("Cascadia Code", 9),
                                    bg=BG_INPUT, fg=TEXT_PRIMARY,
                                    insertbackground=TEXT_PRIMARY,
                                    selectbackground=ACCENT_DIM,
                                    relief="flat", bd=0, padx=10, pady=10)
        self.metrics_text.pack(fill="both", expand=True, padx=14, pady=(8, 14))
        self.metrics_text.insert("1.0", " Waiting for analysis...")
        self.metrics_text.configure(state="disabled")

        # Graph panel (right side)
        graph_card = tk.Frame(bottom, bg=BG_CARD, highlightthickness=1,
                              highlightbackground=BORDER)
        graph_card.pack(side="right", fill="both", expand=True)

        graph_header = tk.Frame(graph_card, bg=BG_CARD)
        graph_header.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(graph_header, text="Visualization", fg=ACCENT, bg=BG_CARD,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")

        self.graph_container = tk.Frame(graph_card, bg=BG_CARD)
        self.graph_container.pack(fill="both", expand=True, padx=8, pady=(4, 10))

        # Init
        self._on_mode_change()

    # ── Sidebar helpers ────────────────────────────────────────────────────
    @staticmethod
    def _sidebar_label(parent, text, row):
        tk.Label(parent, text=text, fg=TEXT_SECONDARY, bg=BG_CARD,
                 font=("Segoe UI", 9)).grid(row=row, column=0, sticky="w", pady=3)

    # ── Mode / input helpers ───────────────────────────────────────────────
    def _on_mode_change(self) -> None:
        is_sim = self.mode_var.get() == "simulation"
        if is_sim:
            self.sim_frame.pack(fill="x")
        else:
            self.sim_frame.pack_forget()

        if is_sim:
            self.auto_refresh_var.set(False)
            self.auto_check.config(state="disabled")
        else:
            self.auto_check.config(state="normal")

    def _toggle_custom_inputs(self) -> None:
        state = "normal" if self.use_custom_var.get() else "disabled"
        self.proc_spin.config(state=state)
        self.frame_spin.config(state=state)
        self.mem_scale.config(state=state)
        self.disk_scale.config(state=state)

    def _update_mem_label(self, *args) -> None:
        self.mem_label.config(text=f"{self.memory_usage_var.get():.0f} %")

    def _update_disk_label(self, *args) -> None:
        self.disk_label.config(text=f"{self.disk_activity_var.get():.0f}")

    # ── Auto-refresh ───────────────────────────────────────────────────────
    def toggle_auto_refresh(self) -> None:
        if self.auto_refresh_var.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()

    def start_auto_refresh(self) -> None:
        if self.auto_refresh_id is None:
            self.run_analysis()
            self.auto_refresh_id = self.root.after(self.refresh_interval, self.auto_refresh_callback)

    def auto_refresh_callback(self) -> None:
        if self.auto_refresh_var.get():
            self.run_analysis()
            self.auto_refresh_id = self.root.after(self.refresh_interval, self.auto_refresh_callback)

    def stop_auto_refresh(self) -> None:
        if self.auto_refresh_id is not None:
            self.root.after_cancel(self.auto_refresh_id)
            self.auto_refresh_id = None

    # ── Core analysis ──────────────────────────────────────────────────────
    def run_analysis(self) -> None:
        try:
            self.status_badge.config(text="  ANALYZING  ", bg=ACCENT_DIM, fg=ACCENT)
            self.root.update_idletasks()

            mode = self.mode_var.get()

            if mode == "real" and self.system_monitor:
                memory_stats, disk_stats = self.system_monitor.get_analysis_compatible_stats()
                analysis = analyze_performance(memory_stats, disk_stats)
                suggestion = get_suggestion(analysis.bottleneck)
                current_metrics = self.system_monitor.get_current_metrics()
            else:
                if self.use_custom_var.get():
                    num_processes = self.num_processes_var.get()
                    memory_usage_pct = self.memory_usage_var.get()
                    disk_activity = self.disk_activity_var.get()
                    workload = generate_workload(
                        num_processes=num_processes, reference_length=30,
                        num_pages=int(self.frame_var.get() * 3), disk_requests=15)
                    memory_stats = simulate_memory(workload, frame_count=self.frame_var.get())
                    memory_stats["page_fault_rate"] = memory_usage_pct / 100.0
                    memory_stats["memory_percent"] = memory_usage_pct
                    disk_stats = simulate_disk(workload)
                    disk_stats["FCFS"] = disk_activity
                    disk_stats["SSTF"] = disk_activity * 0.7
                else:
                    workload = generate_workload()
                    memory_stats = simulate_memory(workload, frame_count=self.frame_var.get())
                    disk_stats = simulate_disk(workload)

                analysis = analyze_performance(memory_stats, disk_stats)
                suggestion = get_suggestion(analysis.bottleneck)
                current_metrics = None

        except Exception as exc:
            messagebox.showerror("Analysis Failed", str(exc))
            self.status_badge.config(text="  ERROR  ", bg=RED_DIM, fg=RED)
            return

        # Store for audio playback
        self._audio_data = (analysis.bottleneck, suggestion)
        
        self._update_feedback(analysis, suggestion, memory_stats, disk_stats, current_metrics)
        self._render_graph(memory_stats, disk_stats)

        # Enable audio button
        self.audio_btn.enable()

        self.status_badge.config(text="  READY  ", bg=GREEN_DIM, fg=GREEN)
        self.timestamp_lbl.config(text=time.strftime("Last run  %H:%M:%S"))

    # ── Feedback ───────────────────────────────────────────────────────────
    def _update_feedback(self, analysis, suggestion, memory_stats, disk_stats, current_metrics=None) -> None:
        bn = analysis.bottleneck.lower()
        if "none" in bn or "no" in bn:
            color, accent = GREEN, GREEN
        elif "disk" in bn:
            color, accent = ORANGE, ORANGE
        else:
            color, accent = RED, RED
        self.result_label.config(fg=color)
        self.result_accent.config(bg=accent)
        self.result_var.set(f"Detected:  {analysis.bottleneck}")
        self.suggestion_var.set(f"{suggestion}")

        # Update tiles
        pf_rate = analysis.page_fault_rate
        pf_color = GREEN if pf_rate < 0.5 else (ORANGE if pf_rate < 0.85 else RED)
        self.tile_fault.set_value(f"{pf_rate:.1%}", pf_color)

        fifo = memory_stats.get("FIFO", 0)
        self.tile_fifo.set_value(f"{fifo:.0f}", ORANGE if fifo > 15 else TEXT_PRIMARY)

        lru = memory_stats.get("LRU", 0)
        self.tile_lru.set_value(f"{lru:.0f}", PURPLE)

        fcfs = disk_stats.get("FCFS", 0)
        self.tile_disk.set_value(f"{fcfs:.0f}", CYAN)

        # Detailed metrics text
        if current_metrics:
            lines = [
                f" CPU          {current_metrics.cpu_percent:>6.1f} %",
                f" Memory       {current_metrics.memory_percent:>6.1f} %",
                f"   Used       {current_metrics.memory_used_mb:>6.0f} MB",
                f"   Total      {current_metrics.memory_total_mb:>6.0f} MB",
                f"   Avail      {current_metrics.memory_available_mb:>6.0f} MB",
                f" Disk %       {current_metrics.disk_percent:>6.1f} %",
                f"   Read       {current_metrics.disk_read_mb:>6.2f} MB/s",
                f"   Write      {current_metrics.disk_write_mb:>6.2f} MB/s",
                f"   I/O Ops    {current_metrics.disk_read_count + current_metrics.disk_write_count:>6}",
                f" Processes    {current_metrics.process_count:>6}",
            ]
        else:
            tag = "CUSTOM" if self.use_custom_var.get() else "RANDOM"
            lines = [f" Mode: {tag}", ""]
            if self.use_custom_var.get():
                lines += [
                    f" Processes    {self.num_processes_var.get():>6}",
                    f" Frames       {self.frame_var.get():>6}",
                    f" Mem Load     {self.memory_usage_var.get():>5.0f} %",
                    f" Disk Load    {self.disk_activity_var.get():>6.0f}",
                    "",
                ]
            lines += [
                f" Fault Rate   {analysis.page_fault_rate:>6.2%}",
                f" FIFO         {memory_stats.get('FIFO', 0):>6.0f}",
                f" LRU          {memory_stats.get('LRU', 0):>6.0f}",
                f" Optimal      {memory_stats.get('Optimal', 0):>6.0f}",
                f" FCFS Seek    {analysis.disk_seek_time:>6.0f}",
                f" SSTF Seek    {disk_stats.get('SSTF', 0):>6.0f}",
                f" Disk Reqs    {disk_stats.get('request_count', 0):>6.0f}",
            ]

        self.metrics_text.configure(state="normal")
        self.metrics_text.delete("1.0", tk.END)
        self.metrics_text.insert("1.0", "\n".join(lines))
        self.metrics_text.configure(state="disabled")

    def _render_graph(self, memory_stats, disk_stats) -> None:
        fig = create_performance_figure(memory_stats, disk_stats)
        if self._canvas:
            self._canvas.get_tk_widget().destroy()
        self._canvas = FigureCanvasTkAgg(fig, master=self.graph_container)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    def _play_audio(self) -> None:
        """Play audio narration from stored analysis results."""
        if self._audio_data:
            bottleneck, suggestion = self._audio_data
            threading.Thread(target=narrate_result, args=(bottleneck, suggestion), daemon=True).start()


def launch_gui() -> None:
    root = tk.Tk()
    app = AnalyzerGUI(root)

    def on_closing():
        app.stop_auto_refresh()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
