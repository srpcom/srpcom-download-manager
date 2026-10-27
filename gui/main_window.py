import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image
from typing import Dict, Optional, List

from core.downloader import DownloadTask, format_size, format_time
from core.manager import DownloadManager, DEFAULT_DOWNLOAD_DIR
from .add_dialog import AddDownloadDialog
from .segment_dialog import SegmentDetailDialog
from .complete_dialog import DownloadCompleteDialog
from .extension_dialog import BrowserExtensionDialog
from .window_utils import bring_window_to_front

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

class TaskRow(ctk.CTkFrame):
    def __init__(self, master, task: DownloadTask, on_select, on_double_click, on_context_menu, on_action_click):
        super().__init__(master, height=52, fg_color=("gray90", "gray17"), corner_radius=6)
        self.task = task
        self.on_select = on_select
        self.on_double_click = on_double_click
        self.on_context_menu = on_context_menu
        self.on_action_click = on_action_click
        self.is_selected = False

        self.pack_propagate(False)
        self._init_ui()
        self._bind_events(self)

    def _init_ui(self):
        # Left side: File Name & Category Icon (Dynamically expands)
        left_box = ctk.CTkFrame(self, fg_color="transparent")
        left_box.pack(side="left", fill="both", expand=True, padx=(10, 5))

        icon = CATEGORY_ICONS.get(self.task.category, "📁")
        self.name_lbl = ctk.CTkLabel(
            left_box,
            text=f"{icon} {self.task.filename}",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.name_lbl.pack(side="left", fill="x", expand=True, pady=12)

        # Right side container: Fixed-width metrics to ensure pixel-perfect alignment
        right_box = ctk.CTkFrame(self, fg_color="transparent", width=520)
        right_box.pack(side="right", fill="y", padx=(0, 6))
        right_box.pack_propagate(False)

        # 1. Size (Width 75)
        self.size_lbl = ctk.CTkLabel(
            right_box,
            text=format_size(self.task.total_size) if self.task.total_size > 0 else "--",
            width=75,
            font=ctk.CTkFont(size=11),
            anchor="center"
        )
        self.size_lbl.pack(side="left", padx=2)

        # 2. Status Badge (Width 85)
        status_color = STATUS_COLORS.get(self.task.status, "gray")
        self.status_lbl = ctk.CTkLabel(
            right_box,
            text=self.task.status,
            width=85,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=status_color,
            anchor="center"
        )
        self.status_lbl.pack(side="left", padx=2)

        # 3. Progress Bar & % (Width 140)
        prog_box = ctk.CTkFrame(right_box, fg_color="transparent", width=140)
        prog_box.pack(side="left", fill="y", padx=3)
        prog_box.pack_propagate(False)

        self.pbar = ctk.CTkProgressBar(prog_box, height=8)
        self.pbar.pack(side="top", fill="x", pady=(15, 2))
        self.pbar.set(self.task.progress_percentage / 100.0)

        self.pct_lbl = ctk.CTkLabel(
            prog_box,
            text=f"{self.task.progress_percentage:.1f}%",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.pct_lbl.pack(side="top")

        # 4. Speed (Width 75)
        self.speed_lbl = ctk.CTkLabel(
            right_box,
            text=(format_size(int(self.task.speed)) + "/s") if self.task.status == "Downloading" else "-",
            width=75,
            font=ctk.CTkFont(size=11),
            anchor="center"
        )
        self.speed_lbl.pack(side="left", padx=2)

        # 5. Time Left (Width 75)
        self.eta_lbl = ctk.CTkLabel(
            right_box,
            text=format_time(self.task.eta) if self.task.status == "Downloading" else "-",
            width=75,
            font=ctk.CTkFont(size=11),
            anchor="center"
        )
        self.eta_lbl.pack(side="left", padx=2)

        # 6. Quick Action Button (Width 60)
        act_box = ctk.CTkFrame(right_box, fg_color="transparent", width=60)
        act_box.pack(side="left", fill="y", padx=(2, 4))
        act_box.pack_propagate(False)

        self.quick_btn = ctk.CTkButton(
            act_box,
            text="⏸" if self.task.status == "Downloading" else ("▶" if self.task.status == "Paused" else "📂"),
            width=32,
            height=28,
            fg_color="#3182CE" if self.task.status == "Downloading" else "#4A5568",
            hover_color="#2B6CB0",
            font=ctk.CTkFont(size=12),
            command=lambda: self.on_action_click(self.task.task_id)
        )
        self.quick_btn.pack(expand=True, pady=10)

    def _bind_events(self, widget):
        if widget is not self.quick_btn:
            widget.bind("<Button-1>", lambda e: self.on_select(self.task.task_id))
            widget.bind("<Double-Button-1>", lambda e: self.on_double_click(self.task.task_id))
            widget.bind("<Button-3>", lambda e: self.on_context_menu(e, self.task.task_id))
        for child in widget.winfo_children():
            if child is not self.quick_btn:
                self._bind_events(child)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        if selected:
            self.configure(border_width=2, border_color="#3182CE", fg_color=("gray85", "gray22"))
        else:
            self.configure(border_width=0, fg_color=("gray90", "gray17"))

    def update_values(self):
        icon = CATEGORY_ICONS.get(self.task.category, "📁")
        self.name_lbl.configure(text=f"{icon} {self.task.filename}")
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

        # Wire task completion callback
        self.manager.on_task_completed = self._on_download_complete

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

        # Right side of toolbar: Speed Limiter
        speed_box = ctk.CTkFrame(tb, fg_color="transparent")
        speed_box.pack(side="right", padx=(0, 15))

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
        header = ctk.CTkFrame(main_box, height=34, fg_color=("gray80", "gray22"), corner_radius=6)
        header.pack(fill="x", padx=10, pady=(2, 4))
        header.pack_propagate(False)

        # Left: File Name (expands)
        left_h = ctk.CTkLabel(header, text="File Name", font=ctk.CTkFont(size=11, weight="bold"), anchor="w")
        left_h.pack(side="left", fill="x", expand=True, padx=(10, 5))

        # Right: Fixed width container (520px matching row)
        right_h = ctk.CTkFrame(header, fg_color="transparent", width=520)
        right_h.pack(side="right", fill="y", padx=(0, 6))
        right_h.pack_propagate(False)

        ctk.CTkLabel(right_h, text="Size", width=75, anchor="center", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=2)
        ctk.CTkLabel(right_h, text="Status", width=85, anchor="center", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=2)
        ctk.CTkLabel(right_h, text="Progress", width=140, anchor="center", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=3)
        ctk.CTkLabel(right_h, text="Speed", width=75, anchor="center", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=2)
        ctk.CTkLabel(right_h, text="Time Left", width=75, anchor="center", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=2)
        ctk.CTkLabel(right_h, text="Action", width=60, anchor="center", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(2, 4))

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
            if os.path.exists(task.target_file_path):
                subprocess.Popen(f'explorer /select,"{task.target_file_path}"')
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

    def open_add_dialog_with_url(self, url: str, filename: str = ""):
        if is_video_streaming_url(url):
            self.open_video_download_dialog(url, "best", filename)
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
                on_batch_submit=self._create_batch_download
            )
            dlg.url_entry.delete(0, "end")
            dlg.url_entry.insert(0, url)
            if filename and filename != "sendMessage":
                dlg.fn_entry.delete(0, "end")
                dlg.fn_entry.insert(0, clean_filename(filename))
            bring_window_to_front(dlg)
            dlg._trigger_inspect()
        self.after(0, show)

    def open_video_download_dialog(self, url: str, quality: str = "best", title: str = ""):
        def show():
            bring_window_to_front(self)
            from core.settings import get_remembered_folder
            from core.downloader import clean_filename
            cat = "Music" if quality == "audio" else "Video"
            video_dir = get_remembered_folder(cat)

            dlg = AddDownloadDialog(
                parent=self,
                default_dir=video_dir,
                on_submit=self._create_download,
                on_batch_submit=self._create_batch_download,
                initial_quality=quality
            )
            dlg.url_entry.delete(0, "end")
            dlg.url_entry.insert(0, url)
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
        connections: int,
        start_now: bool,
        task_type: str = "file",
        video_quality: str = "best"
    ):
        task = self.manager.add_task(
            url=url,
            save_dir=save_dir,
            filename=filename,
            connections=connections,
            start_now=start_now,
            task_type=task_type,
            video_quality=video_quality
        )
        self._refresh_task_rows()
        self._select_task(task.task_id)

    def _create_batch_download(self, urls: List[str], save_dir: str):
        for url in urls:
            self.manager.add_task(
                url=url,
                save_dir=save_dir,
                filename="",
                connections=8,
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
        if task and os.path.exists(task.target_file_path):
            try:
                os.startfile(task.target_file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")
        else:
            messagebox.showwarning("File Missing", "The target file does not exist on disk or has not finished downloading.")

    def _open_selected_folder(self):
        if not self.selected_task_id:
            return
        task = self.manager.tasks.get(self.selected_task_id)
        if task and os.path.isdir(task.save_dir):
            if os.path.exists(task.target_file_path):
                subprocess.Popen(f'explorer /select,"{task.target_file_path}"')
            else:
                subprocess.Popen(f'explorer "{task.save_dir}"')

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

    def _on_download_complete(self, task: DownloadTask):
        def show_dialog():
            dlg = DownloadCompleteDialog(self, task)
            bring_window_to_front(dlg)
        self.after(0, show_dialog)

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
