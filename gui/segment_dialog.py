import os
import sys
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
        self.title(f"Download Status - {task.filename} - SRPCOM")
        self.geometry("620x520")
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
        top_frame.pack(fill="x", padx=20, pady=(15, 10))

        title = ctk.CTkLabel(
            top_frame,
            text=f"Details: {self.task.filename}",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        title.pack(fill="x")

        # Info Box
        info_box = ctk.CTkFrame(self)
        info_box.pack(fill="x", padx=20, pady=5)

        self.status_lbl = ctk.CTkLabel(info_box, text="", anchor="w")
        self.status_lbl.pack(fill="x", padx=15, pady=2)

        self.size_lbl = ctk.CTkLabel(info_box, text="", anchor="w")
        self.size_lbl.pack(fill="x", padx=15, pady=2)

        self.speed_lbl = ctk.CTkLabel(info_box, text="", anchor="w")
        self.speed_lbl.pack(fill="x", padx=15, pady=2)

        self.eta_lbl = ctk.CTkLabel(info_box, text="", anchor="w")
        self.eta_lbl.pack(fill="x", padx=15, pady=2)

        self.resume_lbl = ctk.CTkLabel(info_box, text="", anchor="w")
        self.resume_lbl.pack(fill="x", padx=15, pady=2)

        # Overall Progress Bar
        self.overall_bar = ctk.CTkProgressBar(self, height=14)
        self.overall_bar.pack(fill="x", padx=20, pady=(10, 5))
        self.overall_bar.set(0)

        # Segments Label
        seg_title = ctk.CTkLabel(
            self,
            text="Connection Threads (Multi-segmented download):",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        seg_title.pack(fill="x", padx=20, pady=(10, 5))

        # Scrollable Frame for Segment bars
        self.seg_scroll = ctk.CTkScrollableFrame(self, height=180)
        self.seg_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.seg_widgets = []
        for i in range(max(1, len(self.task.segments))):
            row = ctk.CTkFrame(self.seg_scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)

            lbl = ctk.CTkLabel(row, text=f"Connection {i+1}:", width=110, anchor="w", font=ctk.CTkFont(size=11))
            lbl.pack(side="left", padx=(0, 5))

            pbar = ctk.CTkProgressBar(row, height=10)
            pbar.pack(side="left", fill="x", expand=True, padx=5)
            pbar.set(0)

            val_lbl = ctk.CTkLabel(row, text="0 / 0", width=120, anchor="e", font=ctk.CTkFont(size=11))
            val_lbl.pack(side="right", padx=(5, 0))

            self.seg_widgets.append((lbl, pbar, val_lbl))

        # Close button
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 15))

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            width=100,
            command=self.destroy
        )
        close_btn.pack(side="right")

    def _update_loop(self):
        if not self.winfo_exists():
            return

        pct = self.task.progress_percentage
        speed_str = format_size(int(self.task.speed)) + "/s"
        eta_str = format_time(self.task.eta)
        down_str = format_size(self.task.downloaded_size)
        total_str = format_size(self.task.total_size) if self.task.total_size > 0 else "Unknown"

        self.status_lbl.configure(text=f"Status: {self.task.status}")
        self.size_lbl.configure(text=f"Downloaded: {down_str} of {total_str} ({pct:.1f}%)")
        self.speed_lbl.configure(text=f"Transfer Rate: {speed_str}")
        self.eta_lbl.configure(text=f"Estimated Time Left: {eta_str}")
        self.resume_lbl.configure(text=f"Resume Capability: {'Yes (HTTP Range Supported)' if self.task.supports_ranges else 'No (Single Stream)'}")

        self.overall_bar.set(pct / 100.0)

        # Re-populate segment widgets if segment count changed
        if len(self.task.segments) > len(self.seg_widgets):
            for i in range(len(self.seg_widgets), len(self.task.segments)):
                row = ctk.CTkFrame(self.seg_scroll, fg_color="transparent")
                row.pack(fill="x", pady=3)

                lbl = ctk.CTkLabel(row, text=f"Connection {i+1}:", width=110, anchor="w", font=ctk.CTkFont(size=11))
                lbl.pack(side="left", padx=(0, 5))

                pbar = ctk.CTkProgressBar(row, height=10)
                pbar.pack(side="left", fill="x", expand=True, padx=5)
                pbar.set(0)

                val_lbl = ctk.CTkLabel(row, text="0 / 0", width=120, anchor="e", font=ctk.CTkFont(size=11))
                val_lbl.pack(side="right", padx=(5, 0))

                self.seg_widgets.append((lbl, pbar, val_lbl))

        # Update segment bars
        for idx, seg in enumerate(self.task.segments):
            if idx < len(self.seg_widgets):
                _, pbar, val_lbl = self.seg_widgets[idx]
                seg_pct = (seg.downloaded / seg.total) if seg.total > 0 else 0
                pbar.set(min(1.0, seg_pct))
                val_lbl.configure(text=f"{format_size(seg.downloaded)} / {format_size(seg.total)}")

        self.after(500, self._update_loop)
