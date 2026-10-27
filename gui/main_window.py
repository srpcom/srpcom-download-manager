import os
import sys
import subprocess
import re
import tkinter as tk
from tkinter import messagebox, font as tkfont
import customtkinter as ctk
from PIL import Image
from typing import Dict, Optional, List

from core.downloader import (
    DownloadTask, format_size, format_time, is_video_streaming_url,
    sanitize_media_url, fetch_fast_video_title, clean_filename
)
from core.manager import DownloadManager, DEFAULT_DOWNLOAD_DIR
from core.settings import get_default_connections, set_default_connections, get_column_widths, set_column_widths
from .add_dialog import AddDownloadDialog
from .segment_dialog import SegmentDetailDialog
from .complete_dialog import DownloadCompleteDialog
from .extension_dialog import BrowserExtensionDialog
from .help_dialog import HelpAboutDialog
from .window_utils import bring_window_to_front, open_folder_and_select

def get_asset_path(filename: str) -> str:
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = os.path.join(base_dir, "assets", filename)
    if os.path.exists(p):
        return p
    fallback = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", filename)
    return fallback

# Status Colors
STATUS_COLORS = {
    "Completed": "#38A169",   # Green
    "Downloading": "#3182CE", # Blue
    "Paused": "#DD6B20",      # Orange
    "Queued": "#805AD5",      # Purple
    "Error": "#E53E3E"        # Red
}

CATEGORY_ICONS = {
    "Compressed": "📦",
    "Documents": "📄",
    "Video": "🎬",
    "Music": "🎵",
    "Programs": "💻",
    "Other": "📁"
}

SPEED_LIMIT_MAP = {
    "Unlimited": 0,
    "256 KB/s": 256 * 1024,
    "512 KB/s": 512 * 1024,
    "1 MB/s": 1024 * 1024,
    "2 MB/s": 2 * 1024 * 1024,
    "5 MB/s": 5 * 1024 * 1024,
    "10 MB/s": 10 * 1024 * 1024
}

COLUMN_CONFIG = [
    ("name", "File Name", 140, "w"),
    ("size", "Size", 60, "center"),
    ("status", "Status", 70, "center"),
    ("progress", "Progress", 90, "center"),
    ("speed", "Speed", 60, "center"),
    ("eta", "Time Left", 60, "center"),
    ("action", "Action", 50, "center"),
]

class ToolTip:
    def __init__(self, widget, text_func):
        self.widget = widget
        self.text_func = text_func
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        text = self.text_func()
        if not text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        lbl = tk.Label(
            tw,
            text=text,
            justify="left",
            background="#1A202C",
            foreground="#F7FAFC",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=8,
            pady=4
        )
        lbl.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None

class TaskRow(ctk.CTkFrame):
    def __init__(
        self,
        master,
        task: DownloadTask,
        column_widths: dict,
        on_select,
        on_double_click,
        on_context_menu,
        on_action_click
    ):
        super().__init__(master, height=52, fg_color=("gray90", "gray17"), corner_radius=6)
        self.task = task
        self.column_widths = column_widths
        self.on_select = on_select
        self.on_double_click = on_double_click
        self.on_context_menu = on_context_menu
        self.on_action_click = on_action_click
        self.is_selected = False
        self.cells: Dict[str, ctk.CTkFrame] = {}

        self.pack_propagate(False)
        self._init_ui()
        self._bind_events(self)

    def _init_ui(self):
        for idx, (col_key, _, _, _) in enumerate(COLUMN_CONFIG):
            w = self.column_widths.get(col_key, 100)
            cell = ctk.CTkFrame(self, fg_color="transparent", width=w, height=52)
            cell.pack(side="left", fill="y")
            cell.pack_propagate(False)
            self.cells[col_key] = cell

            if col_key == "name":
                icon = CATEGORY_ICONS.get(self.task.category, "📁")
                self.name_lbl = ctk.CTkLabel(
                    cell,
                    text=self._get_truncated_name(w),
                    font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="w"
                )
                self.name_lbl.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=12)
                ToolTip(self.name_lbl, lambda: f"{self.task.filename}\n{self.task.url}")

            elif col_key == "size":
                self.size_lbl = ctk.CTkLabel(
                    cell,
                    text=format_size(self.task.total_size) if self.task.total_size > 0 else "--",
                    font=ctk.CTkFont(size=11),
                    anchor="center"
                )
                self.size_lbl.pack(expand=True, fill="both")

            elif col_key == "status":
                status_color = STATUS_COLORS.get(self.task.status, "gray")
                self.status_lbl = ctk.CTkLabel(
                    cell,
                    text=self.task.status,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=status_color,
                    anchor="center"
                )
                self.status_lbl.pack(expand=True, fill="both")
                ToolTip(self.status_lbl, lambda: f"Status: {self.task.status}" + (f"\nPesan Error: {self.task.error_message}" if getattr(self.task, "error_message", "") else ""))

            elif col_key == "progress":
                self.pbar = ctk.CTkProgressBar(cell, height=8)
                self.pbar.pack(side="top", fill="x", padx=6, pady=(15, 2))
                self.pbar.set(self.task.progress_percentage / 100.0)

                self.pct_lbl = ctk.CTkLabel(
                    cell,
                    text=f"{self.task.progress_percentage:.1f}%",
                    font=ctk.CTkFont(size=10),
                    text_color="gray"
                )
                self.pct_lbl.pack(side="top")

            elif col_key == "speed":
                self.speed_lbl = ctk.CTkLabel(
                    cell,
                    text=(format_size(int(self.task.speed)) + "/s") if self.task.status == "Downloading" else "-",
                    font=ctk.CTkFont(size=11),
                    anchor="center"
                )
                self.speed_lbl.pack(expand=True, fill="both")

            elif col_key == "eta":
                self.eta_lbl = ctk.CTkLabel(
                    cell,
                    text=format_time(self.task.eta) if self.task.status == "Downloading" else "-",
                    font=ctk.CTkFont(size=11),
                    anchor="center"
                )
                self.eta_lbl.pack(expand=True, fill="both")

            elif col_key == "action":
                btn_txt = "⏸" if self.task.status == "Downloading" else ("📂" if self.task.status == "Completed" else ("🔄" if self.task.status == "Error" else "▶"))
                btn_clr = "#3182CE" if self.task.status == "Downloading" else ("#4A5568" if self.task.status == "Completed" else ("#E53E3E" if self.task.status == "Error" else "#38A169"))
                self.quick_btn = ctk.CTkButton(
                    cell,
                    text=btn_txt,
                    width=32,
                    height=28,
                    fg_color=btn_clr,
                    hover_color="#2B6CB0",
                    font=ctk.CTkFont(size=12),
                    command=lambda: self.on_action_click(self.task.task_id)
                )
                self.quick_btn.pack(expand=True, pady=10)

            # Match 4px separator spacing from header
            if idx < len(COLUMN_CONFIG) - 1:
                spacer = ctk.CTkFrame(self, width=4, fg_color="transparent")
                spacer.pack(side="left", fill="y")

        # Trailing fill
        self.trailing_filler = ctk.CTkFrame(self, fg_color="transparent")
        self.trailing_filler.pack(side="left", fill="both", expand=True)

    def _get_truncated_name(self, width: int) -> str:
        icon = CATEGORY_ICONS.get(self.task.category, "📁")
        full_text = f"{icon} {self.task.filename}"
        try:
            f = tkfont.Font(family="Segoe UI", size=10, weight="bold")
            max_w = max(30, width - 26)
            if f.measure(full_text) <= max_w:
                return full_text
            dots = "..."
            dots_w = f.measure(dots)
            low, high = 0, len(full_text)
            best = ""
            while low <= high:
                mid = (low + high) // 2
                sub = full_text[:mid]
                if f.measure(sub) + dots_w <= max_w:
                    best = sub + dots
                    low = mid + 1
                else:
                    high = mid - 1
            return best if best else full_text[:5] + dots
        except Exception:
            max_chars = max(8, (width - 26) // 8)
            if len(full_text) > max_chars:
                return full_text[:max_chars - 3] + "..."
            return full_text

    def update_column_width(self, col_key: str, width: int):
        self.column_widths[col_key] = width
        if col_key in self.cells:
            self.cells[col_key].configure(width=width)
            if col_key == "name":
                self.name_lbl.configure(text=self._get_truncated_name(width))

    def _bind_events(self, widget):
        if widget is not getattr(self, "quick_btn", None):
            widget.bind("<Button-1>", lambda e: self.on_select(self.task.task_id))
            widget.bind("<Double-Button-1>", lambda e: self.on_double_click(self.task.task_id))
            widget.bind("<Button-3>", lambda e: self.on_context_menu(e, self.task.task_id))
        for child in widget.winfo_children():
            if child is not getattr(self, "quick_btn", None):
                self._bind_events(child)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        if selected:
            self.configure(border_width=2, border_color="#3182CE", fg_color=("gray85", "gray22"))
        else:
            self.configure(border_width=0, fg_color=("gray90", "gray17"))

    def update_values(self):
        w = self.cells["name"].winfo_width()
        if w <= 1:
            w = self.column_widths.get("name", 300)
        self.name_lbl.configure(text=self._get_truncated_name(w))
        self.size_lbl.configure(text=format_size(self.task.total_size) if self.task.total_size > 0 else "--")
        
        status_color = STATUS_COLORS.get(self.task.status, "gray")
        self.status_lbl.configure(text=self.task.status, text_color=status_color)
        
        pct = self.task.progress_percentage
        self.pbar.set(pct / 100.0)
        self.pct_lbl.configure(text=f"{pct:.1f}%")

        if self.task.status == "Completed":
            self.pbar.configure(progress_color="#38A169")
            self.speed_lbl.configure(text="-")
            self.eta_lbl.configure(text="-")
            self.quick_btn.configure(text="📂", fg_color="#4A5568")
        elif self.task.status == "Downloading":
            self.pbar.configure(progress_color="#3182CE")
            self.speed_lbl.configure(text=format_size(int(self.task.speed)) + "/s")
            self.eta_lbl.configure(text=format_time(self.task.eta))
            self.quick_btn.configure(text="⏸", fg_color="#DD6B20")
        elif self.task.status == "Error":
            self.pbar.configure(progress_color="#E53E3E")
            self.speed_lbl.configure(text="-")
            self.eta_lbl.configure(text="-")
            self.quick_btn.configure(text="🔄", fg_color="#E53E3E")
        else:
            self.pbar.configure(progress_color="#3182CE")
            self.speed_lbl.configure(text="-")
            self.eta_lbl.configure(text="-")
            self.quick_btn.configure(text="▶", fg_color="#38A169")


class MainWindow(ctk.CTk):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.manager = manager
        self.selected_task_id: Optional[str] = None
        self.current_filter = "All"
        self.search_query = ""
        self.row_widgets: Dict[str, TaskRow] = {}
        self.column_widths = get_column_widths()
        self.header_cells: Dict[str, ctk.CTkFrame] = {}

        self.title("SRPCOM Download Manager")
        self.geometry("1080x660")
        self.minsize(880, 520)

        # Set Window Icon
        icon_path = get_asset_path("logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Wire task completion & update callbacks
        self.manager.on_task_completed = self._on_download_complete
        self.manager.on_task_updated = lambda t: self.after(0, lambda: self._on_task_updated(t))

        # Context menu
        self.context_menu = tk.Menu(self, tearoff=0)

        self._init_layout()
        self._build_context_menu()
        self._refresh_task_rows()
        self._periodic_ui_update()
        self._start_clipboard_monitor()

    def _init_layout(self):
        # Top Toolbar
        self._init_toolbar()

        # Center Body (Sidebar + Content)
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Left Sidebar
        self._init_sidebar(body)

        # Main Table Area
        self._init_main_content(body)

    def _init_toolbar(self):
        tb = ctk.CTkFrame(self, height=52, corner_radius=0, fg_color=("gray85", "gray14"))
        tb.pack(fill="x", padx=0, pady=(0, 8))

        # Brand with Logo
        brand_box = ctk.CTkFrame(tb, fg_color="transparent")
        brand_box.pack(side="left", padx=(12, 14))

        logo_img_path = get_asset_path("logo.png")
        if os.path.exists(logo_img_path):
            try:
                pil_img = Image.open(logo_img_path)
                self.logo_ctk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(32, 32))
                logo_lbl = ctk.CTkLabel(brand_box, image=self.logo_ctk, text="")
                logo_lbl.pack(side="left", padx=(0, 8))
            except Exception:
                pass

        brand = ctk.CTkLabel(
            brand_box,
            text="SRPCOM Manager",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#E53E3E"
        )
        brand.pack(side="left")

        # Buttons
        add_btn = ctk.CTkButton(
            tb,
            text="+ Add URL",
            width=95,
            height=34,
            fg_color="#2B6CB0",
            hover_color="#2C5282",
            font=ctk.CTkFont(weight="bold"),
            command=self._open_add_dialog
        )
        add_btn.pack(side="left", padx=3)

        self.resume_btn = ctk.CTkButton(
            tb,
            text="▶ Resume",
            width=80,
            height=34,
            fg_color="#38A169",
            hover_color="#2F855A",
            command=self._resume_selected
        )
        self.resume_btn.pack(side="left", padx=3)

        self.pause_btn = ctk.CTkButton(
            tb,
            text="⏸ Pause",
            width=75,
            height=34,
            fg_color="#DD6B20",
            hover_color="#C05621",
            command=self._pause_selected
        )
        self.pause_btn.pack(side="left", padx=3)

        stop_all_btn = ctk.CTkButton(
            tb,
            text="⏹ Stop All",
            width=80,
            height=34,
            fg_color="#718096",
            hover_color="#4A5568",
            command=self.manager.pause_all
        )
        stop_all_btn.pack(side="left", padx=3)

        self.del_btn = ctk.CTkButton(
            tb,
            text="🗑 Delete",
            width=75,
            height=34,
            fg_color="#E53E3E",
            hover_color="#9B2C2C",
            command=self._delete_selected
        )
        self.del_btn.pack(side="left", padx=3)

        open_fld_btn = ctk.CTkButton(
            tb,
            text="📂 Folder",
            width=75,
            height=34,
            fg_color="#4A5568",
            hover_color="#2D3748",
            command=self._open_selected_folder
        )
        open_fld_btn.pack(side="left", padx=3)

        details_btn = ctk.CTkButton(
            tb,
            text="👁 Details",
            width=75,
            height=34,
            fg_color="#4A5568",
            hover_color="#2D3748",
            command=self._open_selected_details
        )
        details_btn.pack(side="left", padx=3)

        ext_btn = ctk.CTkButton(
            tb,
            text="🌐 Chrome Ext",
            width=100,
            height=34,
            fg_color="#805AD5",
            hover_color="#6B46C1",
            font=ctk.CTkFont(weight="bold"),
            command=self._open_extension_dialog
        )
        ext_btn.pack(side="left", padx=3)

        help_btn = ctk.CTkButton(
            tb,
            text="❓ Bantuan",
            width=90,
            height=34,
            fg_color="#4A5568",
            hover_color="#2D3748",
            font=ctk.CTkFont(weight="bold"),
            command=self._open_help_dialog
        )
        help_btn.pack(side="left", padx=3)

        # Right side of toolbar: Speed Limiter & Threads Limiter
        # 1. Threads / Segments Selector
        threads_box = ctk.CTkFrame(tb, fg_color="transparent")
        threads_box.pack(side="right", padx=(0, 10))

        threads_lbl = ctk.CTkLabel(threads_box, text="🚀 Threads:", font=ctk.CTkFont(size=11, weight="bold"))
        threads_lbl.pack(side="left", padx=(0, 4))

        def_conns = get_default_connections()
        self.threads_combo = ctk.CTkComboBox(
            threads_box,
            values=["32 (Optimal)", "24 Threads", "16 Threads", "8 Threads", "4 Threads", "1 Thread"],
            width=125,
            height=30,
            command=self._on_toolbar_threads_change
        )
        matched = False
        for v in self.threads_combo._values:
            if v.startswith(str(def_conns)):
                self.threads_combo.set(v)
                matched = True
                break
        if not matched:
            self.threads_combo.set("32 (Optimal)")
        self.threads_combo.pack(side="left")

        # 2. Speed Limiter
        speed_box = ctk.CTkFrame(tb, fg_color="transparent")
        speed_box.pack(side="right", padx=(0, 8))

        speed_lbl = ctk.CTkLabel(speed_box, text="⚡ Speed Limit:", font=ctk.CTkFont(size=11, weight="bold"))
        speed_lbl.pack(side="left", padx=(0, 5))

        self.speed_combo = ctk.CTkComboBox(
            speed_box,
            values=["Unlimited", "256 KB/s", "512 KB/s", "1 MB/s", "2 MB/s", "5 MB/s", "10 MB/s"],
            width=110,
            height=30,
            command=self._on_speed_limit_change
        )
        self.speed_combo.set("Unlimited")
        self.speed_combo.pack(side="left")

    def _init_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, width=190, corner_radius=8)
        sidebar.pack(side="left", fill="y", padx=(0, 8), pady=0)
        sidebar.pack_propagate(False)

        cat_title = ctk.CTkLabel(
            sidebar,
            text="CATEGORIES",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray"
        )
        cat_title.pack(anchor="w", padx=15, pady=(15, 8))

        filters = [
            ("📁 All Downloads", "All"),
            ("⬇ Downloading", "Downloading"),
            ("✔ Completed", "Completed"),
            ("⏸ Paused", "Paused"),
            ("📦 Compressed", "Compressed"),
            ("📄 Documents", "Documents"),
            ("🎬 Video", "Video"),
            ("🎵 Music", "Music"),
            ("💻 Programs", "Programs"),
        ]

        self.filter_buttons = {}
        for label, filt in filters:
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                height=32,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray80", "gray25"),
                command=lambda f=filt: self._set_filter(f)
            )
            btn.pack(fill="x", padx=8, pady=2)
            self.filter_buttons[filt] = btn

        self._highlight_filter_button("All")

        # Theme Selector at bottom of sidebar
        theme_box = ctk.CTkFrame(sidebar, fg_color="transparent")
        theme_box.pack(side="bottom", fill="x", padx=12, pady=12)

        theme_lbl = ctk.CTkLabel(theme_box, text="Appearance:", font=ctk.CTkFont(size=11), text_color="gray")
        theme_lbl.pack(anchor="w", pady=(0, 4))

        self.theme_menu = ctk.CTkOptionMenu(
            theme_box,
            values=["System", "Dark", "Light"],
            command=self._change_appearance_mode,
            height=28
        )
        self.theme_menu.set("Dark")
        self.theme_menu.pack(fill="x")

    def _init_main_content(self, parent):
        main_box = ctk.CTkFrame(parent, corner_radius=8)
        main_box.pack(side="right", fill="both", expand=True)

        # Search Bar Row
        search_row = ctk.CTkFrame(main_box, fg_color="transparent")
        search_row.pack(fill="x", padx=10, pady=(8, 4))

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="🔍 Search downloads by name or URL...",
            height=30
        )
        self.search_entry.pack(side="right", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self._on_search_change)

        # Header Row
        self.header = ctk.CTkFrame(main_box, height=34, fg_color=("gray80", "gray22"), corner_radius=6)
        self.header.pack(fill="x", padx=10, pady=(2, 4))
        self.header.pack_propagate(False)

        self.header_cells.clear()
        for idx, (col_key, title, min_w, align) in enumerate(COLUMN_CONFIG):
            w = self.column_widths.get(col_key, 100)
            h_cell = ctk.CTkFrame(self.header, fg_color="transparent", width=w, height=34)
            h_cell.pack(side="left", fill="y")
            h_cell.pack_propagate(False)
            self.header_cells[col_key] = h_cell

            lbl = ctk.CTkLabel(
                h_cell,
                text=title,
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor=align
            )
            lbl.pack(fill="both", expand=True, padx=4)

            # Draggable column separator
            if idx < len(COLUMN_CONFIG) - 1:
                sep = ctk.CTkFrame(self.header, width=4, fg_color=("gray70", "gray35"), cursor="sb_h_double_arrow")
                sep.pack(side="left", fill="y")

                sep.bind("<Enter>", lambda e, s=sep: s.configure(fg_color="#3182CE"))
                sep.bind("<Leave>", lambda e, s=sep: s.configure(fg_color=("gray70", "gray35")))
                sep.bind("<Button-1>", lambda e, k=col_key: self._start_column_resize(e, k))
                sep.bind("<B1-Motion>", lambda e, k=col_key: self._on_column_resize(e, k))
                sep.bind("<ButtonRelease-1>", lambda e, k=col_key: self._end_column_resize(e, k))

        # Trailing fill
        self.header_filler = ctk.CTkFrame(self.header, fg_color="transparent")
        self.header_filler.pack(side="left", fill="both", expand=True)

        # Scrollable Task List
        self.scroll_list = ctk.CTkScrollableFrame(main_box, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_context_menu(self):
        self.context_menu.add_command(label="▶ Resume", command=self._resume_selected)
        self.context_menu.add_command(label="⏸ Pause", command=self._pause_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="👁 Details & Segments", command=self._open_selected_details)
        self.context_menu.add_command(label="📄 Open File", command=self._open_selected_file)
        self.context_menu.add_command(label="📂 Open Containing Folder", command=self._open_selected_folder)
        self.context_menu.add_command(label="🔗 Copy Download URL", command=self._copy_selected_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑 Delete from List", command=lambda: self._delete_task(delete_file=False))
        self.context_menu.add_command(label="🔥 Delete File from Disk", command=lambda: self._delete_task(delete_file=True))

    def _start_column_resize(self, event, col_key: str):
        self._resize_col = col_key
        self._resize_start_x = event.x_root
        self._resize_start_w = self.column_widths.get(col_key, 100)

    def _on_column_resize(self, event, col_key: str):
        if not hasattr(self, "_resize_col") or self._resize_col != col_key:
            return
        delta = event.x_root - self._resize_start_x
        min_w = 60
        for k, _, mw, _ in COLUMN_CONFIG:
            if k == col_key:
                min_w = mw
                break
        new_w = max(min_w, self._resize_start_w + delta)
        self.column_widths[col_key] = new_w

        if col_key in self.header_cells:
            self.header_cells[col_key].configure(width=new_w)

        for row in self.row_widgets.values():
            row.update_column_width(col_key, new_w)

    def _end_column_resize(self, event, col_key: str):
        set_column_widths(self.column_widths)
        if hasattr(self, "_resize_col"):
            del self._resize_col

    def _on_toolbar_threads_change(self, choice: str):
        m = re.search(r'\d+', choice)
        val = int(m.group()) if m else 32
        set_default_connections(val)
        if self.selected_task_id:
            task = self.manager.tasks.get(self.selected_task_id)
            if task and task.status != "Completed":
                task.connections = val

    def _on_speed_limit_change(self, choice: str):
        limit_bps = SPEED_LIMIT_MAP.get(choice, 0)
        self.manager.set_global_speed_limit(limit_bps)

    def _on_search_change(self, event=None):
        self.search_query = self.search_entry.get().strip().lower()
        self._refresh_task_rows()

    def _set_filter(self, filt: str):
        self.current_filter = filt
        self._highlight_filter_button(filt)
        self._refresh_task_rows()

    def _highlight_filter_button(self, active_filt: str):
        for f, btn in self.filter_buttons.items():
            if f == active_filt:
                btn.configure(fg_color="#3182CE", text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"))

    def _refresh_task_rows(self):
        # Clear existing rows
        for row in self.row_widgets.values():
            row.destroy()
        self.row_widgets.clear()

        # Filter tasks
        tasks = list(self.manager.tasks.values())
        for task in reversed(tasks):
            if not self._task_matches_filter(task):
                continue
            if self.search_query:
                if self.search_query not in task.filename.lower() and self.search_query not in task.url.lower():
                    continue

            row = TaskRow(
                self.scroll_list,
                task=task,
                column_widths=self.column_widths,
                on_select=self._select_task,
                on_double_click=self._handle_double_click,
                on_context_menu=self._show_context_menu,
                on_action_click=self._handle_row_action
            )
            row.pack(fill="x", pady=2)
            self.row_widgets[task.task_id] = row

            if task.task_id == self.selected_task_id:
                row.set_selected(True)

    def _task_matches_filter(self, task: DownloadTask) -> bool:
        if self.current_filter == "All":
            return True
        if self.current_filter in ("Downloading", "Completed", "Paused"):
            return task.status == self.current_filter
        return task.category == self.current_filter

    def _select_task(self, task_id: str):
        self.selected_task_id = task_id
        for tid, row in self.row_widgets.items():
            row.set_selected(tid == task_id)

    def _handle_double_click(self, task_id: str):
        task = self.manager.tasks.get(task_id)
        if not task:
            return
        if task.status == "Completed":
            self._open_selected_file()
        else:
            self._open_selected_details()

    def _handle_row_action(self, task_id: str):
        task = self.manager.tasks.get(task_id)
        if not task:
            return
        if task.status == "Downloading":
            self.manager.pause_task(task_id)
        elif task.status == "Completed":
            open_folder_and_select(task.target_file_path, task.save_dir)
        else:
            self.manager.resume_task(task_id)

    def _show_context_menu(self, event, task_id: str):
        self._select_task(task_id)
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _open_add_dialog(self):
        dlg = AddDownloadDialog(
            parent=self,
            default_dir=DEFAULT_DOWNLOAD_DIR,
            on_submit=self._create_download,
            on_batch_submit=self._create_batch_download
        )
        bring_window_to_front(dlg)

    def open_add_dialog_with_url(
        self,
        url: str,
        filename: str = "",
        cookies: str = "",
        referer: str = "",
        user_agent: str = ""
    ):
        if is_video_streaming_url(url):
            self.open_video_download_dialog(url, "best", filename, cookies=cookies, referer=referer, user_agent=user_agent)
            return

        def show():
            bring_window_to_front(self)
            from core.settings import get_remembered_folder
            from core.downloader import clean_filename, detect_category
            cat = detect_category(filename) if filename else "Other"
            save_dir = get_remembered_folder(cat)

            dlg = AddDownloadDialog(
                parent=self,
                default_dir=save_dir,
                on_submit=self._create_download,
                on_batch_submit=self._create_batch_download,
                cookies=cookies,
                referer=referer,
                user_agent=user_agent
            )
            dlg.url_entry.delete(0, "end")
            dlg.url_entry.insert(0, url)
            if filename and filename != "sendMessage":
                dlg.fn_entry.delete(0, "end")
                dlg.fn_entry.insert(0, clean_filename(filename))
            bring_window_to_front(dlg)
            dlg._trigger_inspect()
        self.after(0, show)

    def open_video_download_dialog(
        self,
        url: str,
        quality: str = "best",
        title: str = "",
        cookies: str = "",
        referer: str = "",
        user_agent: str = ""
    ):
        def show():
            bring_window_to_front(self)
            from core.settings import get_remembered_folder
            from core.downloader import clean_filename, sanitize_media_url
            cat = "Music" if quality == "audio" else "Video"
            video_dir = get_remembered_folder(cat)

            clean_url = sanitize_media_url(url)
            dlg = AddDownloadDialog(
                parent=self,
                default_dir=video_dir,
                on_submit=self._create_download,
                on_batch_submit=self._create_batch_download,
                initial_quality=quality,
                cookies=cookies,
                referer=referer,
                user_agent=user_agent
            )
            dlg.url_entry.delete(0, "end")
            dlg.url_entry.insert(0, clean_url)
            if title and title != "sendMessage":
                ext = "mp3" if quality == "audio" else "mp4"
                clean_title = clean_filename(title, ext)
                dlg.fn_entry.delete(0, "end")
                dlg.fn_entry.insert(0, clean_title)
            bring_window_to_front(dlg)
            dlg._trigger_inspect()
        self.after(0, show)

    def _create_download(
        self,
        url: str,
        save_dir: str,
        filename: str,
        connections: Optional[int] = None,
        start_now: bool = True,
        task_type: str = "file",
        video_quality: str = "best",
        cookies: str = "",
        referer: str = "",
        user_agent: str = ""
    ):
        if connections is None or connections <= 0:
            connections = get_default_connections()
        task = self.manager.add_task(
            url=url,
            save_dir=save_dir,
            filename=filename,
            connections=connections,
            start_now=start_now,
            task_type=task_type,
            video_quality=video_quality,
            cookies=cookies,
            referer=referer,
            user_agent=user_agent
        )
        self._refresh_task_rows()
        self._select_task(task.task_id)

    def _create_batch_download(self, urls: List[str], save_dir: str):
        def_conn = get_default_connections()
        for url in urls:
            self.manager.add_task(
                url=url,
                save_dir=save_dir,
                filename="",
                connections=def_conn,
                start_now=True
            )
        self._refresh_task_rows()

    def _resume_selected(self):
        if self.selected_task_id:
            self.manager.resume_task(self.selected_task_id)

    def _pause_selected(self):
        if self.selected_task_id:
            self.manager.pause_task(self.selected_task_id)

    def _delete_selected(self):
        if not self.selected_task_id:
            return
        task = self.manager.tasks.get(self.selected_task_id)
        if not task:
            return

        confirm = messagebox.askyesno(
            "Delete Download",
            f"Are you sure you want to remove '{task.filename}' from the list?\n\n(Choose No to cancel)"
        )
        if confirm:
            self.manager.delete_task(self.selected_task_id, delete_file=False)
            self.selected_task_id = None
            self._refresh_task_rows()

    def _delete_task(self, delete_file: bool):
        if not self.selected_task_id:
            return
        task = self.manager.tasks.get(self.selected_task_id)
        if not task:
            return

        msg = f"Delete '{task.filename}' and all downloaded files permanently from disk?" if delete_file else f"Remove '{task.filename}' from download list?"
        confirm = messagebox.askyesno("Confirm Delete", msg)
        if confirm:
            self.manager.delete_task(self.selected_task_id, delete_file=delete_file)
            self.selected_task_id = None
            self._refresh_task_rows()

    def _open_selected_file(self):
        if not self.selected_task_id:
            return
        task = self.manager.tasks.get(self.selected_task_id)
        if not task:
            return
        norm_file = os.path.normpath(task.target_file_path)
        if os.path.exists(norm_file):
            try:
                os.startfile(norm_file)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")
        else:
            messagebox.showwarning("File Missing", "The target file does not exist on disk or has not finished downloading.")

    def _open_selected_folder(self):
        if not self.selected_task_id:
            return
        task = self.manager.tasks.get(self.selected_task_id)
        if task:
            open_folder_and_select(task.target_file_path, task.save_dir)

    def _copy_selected_url(self):
        if not self.selected_task_id:
            return
        task = self.manager.tasks.get(self.selected_task_id)
        if task:
            self.clipboard_clear()
            self.clipboard_append(task.url)

    def _open_selected_details(self):
        if not self.selected_task_id:
            return
        task = self.manager.tasks.get(self.selected_task_id)
        if task:
            SegmentDetailDialog(self, task)

    def _open_extension_dialog(self):
        BrowserExtensionDialog(self)

    def _open_help_dialog(self):
        HelpAboutDialog(self)

    def _on_download_complete(self, task: DownloadTask):
        def show_dialog():
            self._refresh_task_rows()
            dlg = DownloadCompleteDialog(self, task)
            bring_window_to_front(dlg)
        self.after(0, show_dialog)

    def _on_task_updated(self, task: DownloadTask):
        if task.task_id in self.row_widgets:
            self.row_widgets[task.task_id].update_values()

    def _change_appearance_mode(self, mode: str):
        ctk.set_appearance_mode(mode.lower())

    def _periodic_ui_update(self):
        # Update progress and text for active downloads
        for tid, row in list(self.row_widgets.items()):
            task = self.manager.tasks.get(tid)
            if task:
                row.update_values()

        self.after(500, self._periodic_ui_update)

    def _start_clipboard_monitor(self):
        self.last_clipboard_url = ""
        self._check_clipboard_tick()

    def _check_clipboard_tick(self):
        try:
            cb = self.clipboard_get().strip()
            if cb and cb != self.last_clipboard_url:
                if cb.startswith("http://") or cb.startswith("https://"):
                    # Check YouTube / Video URLs directly
                    if any(v in cb.lower() for v in (
                        "youtube.com/watch", "youtu.be/", "youtube.com/shorts",
                        "vimeo.com/", "tiktok.com/@", "dailymotion.com/video"
                    )):
                        self.last_clipboard_url = cb
                        self.open_video_download_dialog(cb)
                        self.after(800, self._check_clipboard_tick)
                        return

                    clean = cb.split("?")[0].split("#")[0].lower()
                    if any(clean.endswith(ext) for ext in (
                        ".zip", ".rar", ".7z", ".tar", ".gz", ".iso",
                        ".exe", ".msi", ".apk", ".bin",
                        ".mp4", ".mkv", ".avi", ".mov",
                        ".mp3", ".wav", ".flac",
                        ".pdf", ".docx", ".xlsx", ".pptx"
                    )):
                        self.last_clipboard_url = cb
                        self.open_add_dialog_with_url(cb)
        except Exception:
            pass
        self.after(800, self._check_clipboard_tick)
