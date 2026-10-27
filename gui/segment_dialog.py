import os
import sys
import threading
import tkinter as tk
import customtkinter as ctk
from core.downloader import DownloadTask, format_size, format_time

def get_asset_path(filename: str) -> str:
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = os.path.join(base_dir, "assets", filename)
    if os.path.exists(p):
        return p
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", filename)

class SegmentDetailDialog(ctk.CTkToplevel):
    def __init__(self, parent, task: DownloadTask):
        super().__init__(parent)
        self.task = task
        self.title(f"Download Details & Speed Graph - {task.filename} - SRPCOM")
        self.geometry("660x680")
        self.transient(parent)

        icon_path = get_asset_path("logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self._init_ui()
        self._update_loop()

    def _init_ui(self):
        # Header
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(12, 6))

        title = ctk.CTkLabel(
            top_frame,
            text=f"Details: {self.task.filename}",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        title.pack(fill="x")

        # Info Box
        info_box = ctk.CTkFrame(self)
        info_box.pack(fill="x", padx=20, pady=4)

        self.status_lbl = ctk.CTkLabel(info_box, text="", anchor="w", font=ctk.CTkFont(size=12))
        self.status_lbl.pack(fill="x", padx=15, pady=1)

        self.size_lbl = ctk.CTkLabel(info_box, text="", anchor="w", font=ctk.CTkFont(size=12))
        self.size_lbl.pack(fill="x", padx=15, pady=1)

        self.speed_lbl = ctk.CTkLabel(info_box, text="", anchor="w", font=ctk.CTkFont(size=12))
        self.speed_lbl.pack(fill="x", padx=15, pady=1)

        self.eta_lbl = ctk.CTkLabel(info_box, text="", anchor="w", font=ctk.CTkFont(size=12))
        self.eta_lbl.pack(fill="x", padx=15, pady=1)

        self.resume_lbl = ctk.CTkLabel(info_box, text="", anchor="w", font=ctk.CTkFont(size=12))
        self.resume_lbl.pack(fill="x", padx=15, pady=1)

        self.threads_lbl = ctk.CTkLabel(
            info_box,
            text="",
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#06B6D4"
        )
        self.threads_lbl.pack(fill="x", padx=15, pady=(1, 3))

        self.error_lbl = ctk.CTkLabel(
            info_box,
            text="",
            anchor="w",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#EF4444",
            wraplength=600,
            justify="left"
        )

        # Overall Progress Bar
        self.overall_bar = ctk.CTkProgressBar(self, height=12)
        self.overall_bar.pack(fill="x", padx=20, pady=(8, 4))
        self.overall_bar.set(0)

        # --- Speed History Graph ---
        graph_box = ctk.CTkFrame(self)
        graph_box.pack(fill="x", padx=20, pady=(6, 4))

        graph_header = ctk.CTkFrame(graph_box, fg_color="transparent")
        graph_header.pack(fill="x", padx=10, pady=(6, 2))

        g_title = ctk.CTkLabel(
            graph_header,
            text="📈 Speed History Graph (Fluktuasi Kecepatan Real-Time):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        g_title.pack(side="left")

        self.graph_stat_lbl = ctk.CTkLabel(
            graph_header,
            text="Peak: 0 KB/s",
            font=ctk.CTkFont(size=11),
            text_color="#06B6D4"
        )
        self.graph_stat_lbl.pack(side="right")

        # Tkinter Canvas for Speed Graph
        self.canvas_h = 100
        self.canvas = tk.Canvas(
            graph_box,
            height=self.canvas_h,
            bg="#0f172a",
            highlightthickness=1,
            highlightbackground="#1e293b"
        )
        self.canvas.pack(fill="x", padx=10, pady=(2, 8))

        # --- Segments Section ---
        self.seg_title = ctk.CTkLabel(
            self,
            text="Connection Threads (Dynamic Chunk Splitting):",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.seg_title.pack(fill="x", padx=20, pady=(6, 2))

        # Scrollable Frame for Segment bars
        self.seg_scroll = ctk.CTkScrollableFrame(self, height=140)
        self.seg_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 6))

        self.seg_widgets = []
        for i in range(max(1, len(self.task.segments))):
            self._create_segment_row(i)

        # Close button
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(4, 12))

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            width=100,
            command=self.destroy
        )
        close_btn.pack(side="right")

    def _create_segment_row(self, index: int):
        row = ctk.CTkFrame(self.seg_scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)

        lbl = ctk.CTkLabel(row, text=f"Connection {index+1}:", width=140, anchor="w", font=ctk.CTkFont(size=11))
        lbl.pack(side="left", padx=(0, 5))

        pbar = ctk.CTkProgressBar(row, height=8)
        pbar.pack(side="left", fill="x", expand=True, padx=5)
        pbar.set(0)

        val_lbl = ctk.CTkLabel(row, text="0 / 0", width=130, anchor="e", font=ctk.CTkFont(size=11))
        val_lbl.pack(side="right", padx=(5, 0))

        self.seg_widgets.append((lbl, pbar, val_lbl))

    def _draw_speed_graph(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas_h
        if w < 10:
            w = 600

        history = list(self.task.speed_history)
        if not history:
            history = [self.task.speed]

        peak_speed = max(max(history), 1024)
        curr_speed = history[-1] if history else 0
        self.graph_stat_lbl.configure(text=f"Current: {format_size(int(curr_speed))}/s | Peak: {format_size(int(peak_speed))}/s")

        # Draw grid lines (0%, 50%, 100%)
        margin_y = 10
        margin_x = 10
        plot_w = w - (margin_x * 2)
        plot_h = h - (margin_y * 2)

        # Midline
        mid_y = margin_y + (plot_h / 2)
        self.canvas.create_line(margin_x, mid_y, w - margin_x, mid_y, fill="#1e293b", dash=(3, 3))
        self.canvas.create_text(w - margin_x - 5, mid_y - 6, text=f"{format_size(int(peak_speed/2))}/s", fill="#475569", font=("Segoe UI", 8), anchor="e")

        # Top line
        self.canvas.create_line(margin_x, margin_y, w - margin_x, margin_y, fill="#1e293b", dash=(3, 3))
        self.canvas.create_text(w - margin_x - 5, margin_y + 6, text=f"{format_size(int(peak_speed))}/s", fill="#475569", font=("Segoe UI", 8), anchor="e")

        # Points calculation
        max_points = 50
        data = history[-max_points:]
        n = len(data)
        if n < 2:
            pts = [(margin_x, h - margin_y), (w - margin_x, h - margin_y)]
        else:
            dx = plot_w / (n - 1)
            pts = []
            for i, val in enumerate(data):
                px = margin_x + (i * dx)
                ratio = min(1.0, max(0.0, val / peak_speed))
                py = h - margin_y - (ratio * plot_h)
                pts.append((px, py))

        # Fill under curve
        fill_poly = [(pts[0][0], h - margin_y)] + pts + [(pts[-1][0], h - margin_y)]
        flat_poly = [coord for pt in fill_poly for coord in pt]
        self.canvas.create_polygon(flat_poly, fill="#0c4a6e", outline="")

        # Neon Cyan Curve Line
        flat_line = [coord for pt in pts for coord in pt]
        self.canvas.create_line(flat_line, fill="#06B6D4", width=2, smooth=True)

        # Current point dot
        last_x, last_y = pts[-1]
        self.canvas.create_oval(last_x - 3, last_y - 3, last_x + 3, last_y + 3, fill="#38BDF8", outline="#ffffff", width=1)

    def _update_loop(self):
        if not self.winfo_exists():
            return

        pct = self.task.progress_percentage
        speed_str = format_size(int(self.task.speed)) + "/s"
        eta_str = format_time(self.task.eta)
        down_str = format_size(self.task.downloaded_size)
        total_str = format_size(self.task.total_size) if self.task.total_size > 0 else "Unknown"

        status_color = "#E53E3E" if self.task.status == "Error" else "#38A169" if self.task.status == "Completed" else "#3182CE"
        self.status_lbl.configure(text=f"Status: {self.task.status}", text_color=status_color)
        if getattr(self.task, "error_message", ""):
            self.error_lbl.configure(text=f"❌ Error Detail: {self.task.error_message}")
            if not self.error_lbl.winfo_ismapped():
                self.error_lbl.pack(fill="x", padx=15, pady=(1, 4))
        else:
            if self.error_lbl.winfo_ismapped():
                self.error_lbl.pack_forget()

        self.size_lbl.configure(text=f"Downloaded: {down_str} of {total_str} ({pct:.1f}%)")
        self.speed_lbl.configure(text=f"Transfer Rate: {speed_str}")
        self.eta_lbl.configure(text=f"Estimated Time Left: {eta_str}")
        if self.task.task_type == "video":
            self.resume_lbl.configure(text=f"Resume Capability: Yes (Segmented Stream - {self.task.connections} Concurrent Threads)")
        else:
            self.resume_lbl.configure(text=f"Resume Capability: {'Yes (HTTP Range Supported)' if self.task.supports_ranges else 'No (Single Stream)'}")

        self.overall_bar.set(pct / 100.0)

        # Draw real-time Speed Graph
        self._draw_speed_graph()

        # Update dynamic chunk splitting connection list
        with getattr(self.task, "segment_lock", threading.Lock()):
            segs = list(self.task.segments)

        if self.task.task_type == "video" and len(segs) == 0:
            self.threads_lbl.configure(
                text=f"Jumlah Thread: {self.task.connections} Concurrent Stream Threads (Akselerasi Fragmen Video)"
            )
            self.seg_title.configure(text=f"Connection Threads ({self.task.connections} Threads Concurrent - Multi-thread Stream):")
            if not hasattr(self, "_video_stream_box"):
                self._video_stream_box = ctk.CTkFrame(self.seg_scroll, fg_color=("gray85", "gray20"), corner_radius=6)
                self._video_stream_box.pack(fill="x", padx=4, pady=4)
                
                v_lbl = ctk.CTkLabel(
                    self._video_stream_box,
                    text=f"⚡ Video Stream Multi-threading: {self.task.connections} thread fragmen paralel berjalan simultan",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color="#38BDF8",
                    anchor="w"
                )
                v_lbl.pack(fill="x", padx=10, pady=(6, 2))
                
                self._video_stream_bar = ctk.CTkProgressBar(self._video_stream_box, height=8, progress_color="#06B6D4")
                self._video_stream_bar.pack(fill="x", padx=10, pady=(2, 8))
            
            if hasattr(self, "_video_stream_bar"):
                self._video_stream_bar.set(pct / 100.0)
            self.after(500, self._update_loop)
            return

        active_count = sum(1 for s in segs if getattr(s, "is_active", False))
        finished_count = sum(1 for s in segs if getattr(s, "is_finished", False))
        self.threads_lbl.configure(
            text=f"Jumlah Thread: {active_count} Aktif / {self.task.connections} Max Threads ({len(segs)} Segmen, {finished_count} Selesai - Dynamic Chunk Splitting)"
        )
        self.seg_title.configure(text=f"Connection Threads ({active_count} Aktif / {len(segs)} Segmen - Dynamic Chunk Splitting):")

        # Grow segment rows if new sub-segments were created dynamically
        if len(segs) > len(self.seg_widgets):
            for i in range(len(self.seg_widgets), len(segs)):
                self._create_segment_row(i)

        # Update progress and status icons for each segment
        for idx, seg in enumerate(segs):
            if idx < len(self.seg_widgets):
                lbl, pbar, val_lbl = self.seg_widgets[idx]
                seg_pct = (seg.downloaded / seg.total) if seg.total > 0 else 0
                pbar.set(min(1.0, seg_pct))
                
                status_icon = "🟢" if seg.is_finished else ("🔵" if getattr(seg, "is_active", False) else "⚪")
                lbl.configure(text=f"{status_icon} Part {idx+1}:")
                val_lbl.configure(text=f"{format_size(seg.downloaded)} / {format_size(seg.total)}")

        self.after(500, self._update_loop)
