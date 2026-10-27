import os
import sys
import subprocess
import customtkinter as ctk
from core.downloader import DownloadTask, format_size, detect_category
from gui.window_utils import center_window, bring_window_to_front

def get_asset_path(filename: str) -> str:
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = os.path.join(base_dir, "assets", filename)
    if os.path.exists(p):
        return p
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", filename)

try:
    import winsound
except ImportError:
    winsound = None

CATEGORY_ICONS = {
    "Compressed": "📦",
    "Documents": "📄",
    "Video": "🎬",
    "Music": "🎵",
    "Programs": "💻",
    "Other": "📁"
}

class DownloadCompleteDialog(ctk.CTkToplevel):
    def __init__(self, parent, task: DownloadTask):
        super().__init__(parent)
        self.task = task
        self.title("Download Complete - SRPCOM")
        self.geometry("480x280")
        self.resizable(False, False)
        self.transient(parent)

        icon_path = get_asset_path("logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Play system sound
        if winsound:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

        self._init_ui()
        center_window(self, 480, 280)
        bring_window_to_front(self)

    def _init_ui(self):
        # Header banner
        header = ctk.CTkFrame(self, fg_color="#2F855A", height=50, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        icon = CATEGORY_ICONS.get(self.task.category, "📁")
        h_lbl = ctk.CTkLabel(
            header,
            text=f"✔ Download Finished Successfully!",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        )
        h_lbl.pack(side="left", padx=20, pady=10)

        # Body info
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=15)

        # File Name & Icon
        fn_lbl = ctk.CTkLabel(
            body,
            text=f"{icon} {self.task.filename}",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        fn_lbl.pack(fill="x", pady=(0, 4))

        # Size & Category
        size_str = format_size(self.task.total_size) if self.task.total_size > 0 else "Unknown"
        info_lbl = ctk.CTkLabel(
            body,
            text=f"Size: {size_str}  |  Category: {self.task.category}  |  Connections: {len(self.task.segments)}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        info_lbl.pack(fill="x", pady=(0, 8))

        # Folder location
        path_box = ctk.CTkFrame(body, fg_color=("gray85", "gray20"), corner_radius=6)
        path_box.pack(fill="x", pady=(0, 10))

        path_lbl = ctk.CTkLabel(
            path_box,
            text=f"Saved to: {self.task.target_file_path}",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        path_lbl.pack(fill="x", padx=10, pady=6)

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 18), side="bottom")

        close_btn = ctk.CTkButton(
            btn_row,
            text="Close",
            width=90,
            height=32,
            fg_color="#718096",
            hover_color="#4A5568",
            command=self.destroy
        )
        close_btn.pack(side="right", padx=(8, 0))

        folder_btn = ctk.CTkButton(
            btn_row,
            text="📂 Open Folder",
            width=115,
            height=32,
            fg_color="#4A5568",
            hover_color="#2D3748",
            command=self._open_folder
        )
        folder_btn.pack(side="right", padx=(8, 0))

        open_btn = ctk.CTkButton(
            btn_row,
            text="▶ Open File",
            width=105,
            height=32,
            fg_color="#2B6CB0",
            hover_color="#2C5282",
            font=ctk.CTkFont(weight="bold"),
            command=self._open_file
        )
        open_btn.pack(side="right")

    def _open_file(self):
        if os.path.exists(self.task.target_file_path):
            try:
                os.startfile(self.task.target_file_path)
            except Exception:
                pass
        self.destroy()

    def _open_folder(self):
        if os.path.exists(self.task.target_file_path):
            subprocess.Popen(f'explorer /select,"{self.task.target_file_path}"')
        elif os.path.isdir(self.task.save_dir):
            subprocess.Popen(f'explorer "{self.task.save_dir}"')
        self.destroy()
