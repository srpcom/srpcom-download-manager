import os
import sys
import re
import urllib.parse
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
import requests
from core.downloader import format_size, detect_category, is_video_streaming_url, clean_filename
from core.settings import get_remembered_folder, set_remembered_folder, get_default_connections
from gui.window_utils import center_window, bring_window_to_front

def get_asset_path(filename: str) -> str:
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = os.path.join(base_dir, "assets", filename)
    if os.path.exists(p):
        return p
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", filename)

class AddDownloadDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        default_dir: str,
        on_submit,
        on_batch_submit=None,
        initial_quality: str = "best",
        cookies: str = "",
        referer: str = "",
        user_agent: str = ""
    ):
        super().__init__(parent)
        self.title("Add Download - SRPCOM")
        self.geometry("580x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_submit = on_submit
        self.on_batch_submit = on_batch_submit
        self.cookies = cookies
        self.referer = referer
        self.user_agent = user_agent

        icon_path = get_asset_path("logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.initial_quality = initial_quality
        self.current_category = "Music" if initial_quality == "audio" else ("Video" if initial_quality in ("best", "1080", "720", "480", "360") else "Other")
        
        # Load remembered directory for category if available
        rem_dir = get_remembered_folder(self.current_category)
        downloads_std = os.path.join(os.path.expanduser("~"), "Downloads")
        if default_dir and default_dir != downloads_std and os.path.isdir(default_dir):
            self.default_dir = default_dir
        else:
            self.default_dir = rem_dir or default_dir

        self.fetched_size = 0
        self.is_inspecting = False

        self._init_ui()
        self._check_clipboard()

        # Keyboard shortcuts
        self.bind("<Return>", lambda e: self._submit(start_now=True))
        self.bind("<Escape>", lambda e: self.destroy())

        # Center on screen and pop up immediately to front (like IDM)
        center_window(self, 580, 520)
        bring_window_to_front(self)

    def _init_ui(self):
        # Tabview: Single vs Batch
        self.tabview = ctk.CTkTabview(self, height=390)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(5, 5))

        tab_single = self.tabview.add("Single Download")
        tab_batch = self.tabview.add("Batch (Multiple URLs)")

        # --- Tab 1: Single Download ---
        self._build_single_tab(tab_single)

        # --- Tab 2: Batch Download ---
        self._build_batch_tab(tab_batch)

    def _build_single_tab(self, frame):
        # 1. URL Entry
        url_label = ctk.CTkLabel(frame, text="URL / Address:", font=ctk.CTkFont(size=12, weight="bold"))
        url_label.pack(anchor="w", pady=(5, 2))

        url_row = ctk.CTkFrame(frame, fg_color="transparent")
        url_row.pack(fill="x", pady=(0, 8))

        self.url_entry = ctk.CTkEntry(url_row, placeholder_text="https://example.com/file.zip", height=32)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.url_entry.bind("<KeyRelease>", self._on_url_change)

        self.fetch_btn = ctk.CTkButton(
            url_row,
            text="Inspect",
            width=75,
            height=32,
            command=self._trigger_inspect
        )
        self.fetch_btn.pack(side="right")

        # 2. File Name
        fn_label = ctk.CTkLabel(frame, text="File Name:", font=ctk.CTkFont(size=12, weight="bold"))
        fn_label.pack(anchor="w", pady=(3, 2))

        self.fn_entry = ctk.CTkEntry(frame, placeholder_text="filename.ext", height=32)
        self.fn_entry.pack(fill="x", pady=(0, 8))

        # 3. Save Directory
        dir_label = ctk.CTkLabel(frame, text="Save To Folder:", font=ctk.CTkFont(size=12, weight="bold"))
        dir_label.pack(anchor="w", pady=(3, 2))

        dir_row = ctk.CTkFrame(frame, fg_color="transparent")
        dir_row.pack(fill="x", pady=(0, 8))

        self.dir_entry = ctk.CTkEntry(dir_row, height=32)
        self.dir_entry.insert(0, self.default_dir)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(
            dir_row,
            text="Browse...",
            width=75,
            height=32,
            fg_color="#4A5568",
            hover_color="#2D3748",
            command=self._browse_folder
        )
        browse_btn.pack(side="right")

        # Remember Folder Checkbox (Per-Category Memory)
        self.remember_cb_var = ctk.BooleanVar(value=True)
        self.remember_cb = ctk.CTkCheckBox(
            frame,
            text=f"Ingat folder ini untuk kategori {self.current_category}",
            variable=self.remember_cb_var,
            font=ctk.CTkFont(size=11),
            checkbox_width=18,
            checkbox_height=18
        )
        self.remember_cb.pack(anchor="w", pady=(0, 6))

        # 4. Quality & Format (Video / Stream / Audio)
        self.quality_row = ctk.CTkFrame(frame, fg_color="transparent")
        self.quality_row.pack(fill="x", pady=(2, 6))

        q_label = ctk.CTkLabel(self.quality_row, text="Quality / Format:", font=ctk.CTkFont(size=11, weight="bold"))
        q_label.pack(side="left", padx=(0, 8))

        self.quality_combo = ctk.CTkComboBox(
            self.quality_row,
            values=[
                "Best Quality (1080p/720p HD MP4)",
                "720p HD (MP4)",
                "480p SD (MP4)",
                "360p Hemat (MP4)",
                "Audio Saja (MP3)"
            ],
            width=260,
            height=28,
            command=self._on_quality_change
        )
        if self.initial_quality == "audio":
            self.quality_combo.set("Audio Saja (MP3)")
        elif self.initial_quality == "720":
            self.quality_combo.set("720p HD (MP4)")
        elif self.initial_quality == "480":
            self.quality_combo.set("480p SD (MP4)")
        elif self.initial_quality == "360":
            self.quality_combo.set("360p Hemat (MP4)")
        else:
            self.quality_combo.set("Best Quality (1080p/720p HD MP4)")
        self.quality_combo.pack(side="left")

        # 5. Connections & Info
        info_row = ctk.CTkFrame(frame, fg_color="transparent")
        info_row.pack(fill="x", pady=(4, 6))

        conn_label = ctk.CTkLabel(info_row, text="Threads / Segmen:", font=ctk.CTkFont(size=11, weight="bold"))
        conn_label.pack(side="left", padx=(0, 6))

        def_conn = get_default_connections()
        self.conn_combo = ctk.CTkComboBox(
            info_row,
            values=[
                "32 (Optimal - Max Speed)",
                "24 (Sangat Cepat)",
                "16 (Cepat)",
                "8 (Standar)",
                "4 (Hemat)",
                "1 (Single Stream)"
            ],
            width=180,
            height=28
        )
        matched = False
        for val in self.conn_combo._values:
            if val.startswith(str(def_conn)):
                self.conn_combo.set(val)
                matched = True
                break
        if not matched:
            self.conn_combo.set("32 (Optimal - Max Speed)")
        self.conn_combo.pack(side="left", padx=(0, 6))

        opt_btn = ctk.CTkButton(
            info_row,
            text="⚡ Optimal (Max)",
            width=110,
            height=28,
            fg_color="#38A169",
            hover_color="#2F855A",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.conn_combo.set("32 (Optimal - Max Speed)")
        )
        opt_btn.pack(side="left")

        self.size_info_label = ctk.CTkLabel(
            info_row,
            text="Size: Unknown",
            text_color="gray",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.size_info_label.pack(side="right")

        # Status note
        self.status_label = ctk.CTkLabel(
            frame,
            text="",
            text_color="#38A169",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(anchor="w", pady=(0, 5))

        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0), side="bottom")

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=85,
            height=32,
            fg_color="#718096",
            hover_color="#4A5568",
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        later_btn = ctk.CTkButton(
            btn_frame,
            text="Download Later",
            width=110,
            height=32,
            fg_color="#3182CE",
            hover_color="#2B6CB0",
            command=lambda: self._submit(start_now=False)
        )
        later_btn.pack(side="right", padx=(8, 0))

        download_now_btn = ctk.CTkButton(
            btn_frame,
            text="Download Now",
            width=120,
            height=32,
            fg_color="#2B6CB0",
            hover_color="#2C5282",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self._submit(start_now=True)
        )
        download_now_btn.pack(side="right")

    def _build_batch_tab(self, frame):
        batch_lbl = ctk.CTkLabel(
            frame,
            text="Enter download links (one URL per line):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        batch_lbl.pack(anchor="w", pady=(5, 3))

        self.batch_text = ctk.CTkTextbox(frame, height=130)
        self.batch_text.pack(fill="x", pady=(0, 8))

        # Folder row for batch
        b_dir_row = ctk.CTkFrame(frame, fg_color="transparent")
        b_dir_row.pack(fill="x", pady=(0, 8))

        b_dir_lbl = ctk.CTkLabel(b_dir_row, text="Save To:", font=ctk.CTkFont(size=11, weight="bold"))
        b_dir_lbl.pack(side="left", padx=(0, 5))

        self.b_dir_entry = ctk.CTkEntry(b_dir_row, height=30)
        self.b_dir_entry.insert(0, self.default_dir)
        self.b_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        b_browse = ctk.CTkButton(
            b_dir_row,
            text="Browse...",
            width=70,
            height=30,
            fg_color="#4A5568",
            command=lambda: self._browse_folder_target(self.b_dir_entry)
        )
        b_browse.pack(side="right")

        # Bottom batch buttons
        b_btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        b_btn_frame.pack(fill="x", pady=(10, 0), side="bottom")

        b_cancel = ctk.CTkButton(
            b_btn_frame,
            text="Cancel",
            width=85,
            height=32,
            fg_color="#718096",
            command=self.destroy
        )
        b_cancel.pack(side="right", padx=(8, 0))

        b_start = ctk.CTkButton(
            b_btn_frame,
            text="Add All to Queue",
            width=130,
            height=32,
            fg_color="#2B6CB0",
            hover_color="#2C5282",
            font=ctk.CTkFont(weight="bold"),
            command=self._submit_batch
        )
        b_start.pack(side="right")

    def _check_clipboard(self):
        try:
            cb = self.clipboard_get().strip()
            if cb.startswith("http://") or cb.startswith("https://"):
                if "\n" in cb:
                    # Multiple URLs
                    self.tabview.set("Batch (Multiple URLs)")
                    self.batch_text.insert("1.0", cb)
                else:
                    self.url_entry.delete(0, "end")
                    self.url_entry.insert(0, cb)
                    self._trigger_inspect()
        except Exception:
            pass

    def _browse_folder(self):
        path = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if path:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, path)

    def _browse_folder_target(self, entry_widget):
        path = filedialog.askdirectory(initialdir=entry_widget.get())
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)

    def _update_category(self, cat: str):
        self.current_category = cat
        if hasattr(self, "remember_cb"):
            self.remember_cb.configure(text=f"Ingat folder ini untuk kategori {cat}")

    def _on_quality_change(self, choice):
        if "Audio" in choice or "MP3" in choice:
            self._update_category("Music")
        else:
            self._update_category("Video")

        curr_fn = self.fn_entry.get().strip()
        if curr_fn:
            stem = os.path.splitext(curr_fn)[0]
            ext = ".mp3" if self.current_category == "Music" else ".mp4"
            self.fn_entry.delete(0, "end")
            self.fn_entry.insert(0, stem + ext)

    def _on_url_change(self, event=None):
        url = self.url_entry.get().strip()
        if is_video_streaming_url(url):
            self._update_category("Video")
        elif not self.fn_entry.get():
            try:
                base = os.path.basename(urllib.parse.urlparse(url).path)
                if base:
                    clean = urllib.parse.unquote(base)
                    self.fn_entry.insert(0, clean_filename(clean))
                    cat = detect_category(clean)
                    self._update_category(cat)
            except Exception:
                pass

    def _trigger_inspect(self):
        url = self.url_entry.get().strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            return

        if self.is_inspecting:
            return

        self.is_inspecting = True
        self.fetch_btn.configure(state="disabled", text="Checking...")

        if is_video_streaming_url(url):
            is_audio = "Audio" in self.quality_combo.get() or "MP3" in self.quality_combo.get()
            self._update_category("Music" if is_audio else "Video")

            # Apply remembered category folder
            rem_dir = get_remembered_folder(self.current_category)
            if rem_dir and os.path.isdir(rem_dir):
                self.dir_entry.delete(0, "end")
                self.dir_entry.insert(0, rem_dir)

            self.status_label.configure(text="Mengambil info video YouTube...", text_color="#3182CE")
            def yt_inspect_worker():
                try:
                    import yt_dlp
                    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        if info:
                            raw_title = info.get('title') or "video"
                            q = self.quality_combo.get()
                            ext = "mp3" if ("Audio" in q or "MP3" in q) else "mp4"
                            clean_fn = clean_filename(raw_title, ext)
                            dur = info.get('duration') or 0
                            dur_str = f"{dur//60}m {dur%60}s" if dur else ""

                            def update_yt_ui():
                                # ALWAYS set detected video filename
                                self.fn_entry.delete(0, "end")
                                self.fn_entry.insert(0, clean_fn)
                                self.size_info_label.configure(
                                    text=f"Stream Video ({dur_str})" if dur_str else "Stream Video (HD/MP4)",
                                    text_color="#38A169"
                                )
                                self.status_label.configure(text="Judul video berhasil dideteksi!", text_color="#38A169")
                                self.fetch_btn.configure(state="normal", text="Inspect")
                                self.is_inspecting = False
                            self.after(0, update_yt_ui)
                            return
                except Exception as e:
                    print(f"Error inspecting video: {e}")
                def fallback_err():
                    self.status_label.configure(text="Video stream siap diunduh", text_color="#38A169")
                    self.fetch_btn.configure(state="normal", text="Inspect")
                    self.is_inspecting = False
                self.after(0, fallback_err)
            threading.Thread(target=yt_inspect_worker, daemon=True).start()
            return

        self.status_label.configure(text="Querying server info...", text_color="gray")

        def inspect_worker():
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.head(url, headers=headers, allow_redirects=True, timeout=8)
                if resp.status_code >= 400 or resp.status_code == 405:
                    headers["Range"] = "bytes=0-0"
                    resp = requests.get(url, headers=headers, stream=True, timeout=8)

                filename = ""
                cd = resp.headers.get("Content-Disposition", "")
                if cd and "filename=" in cd:
                    match = re.findall(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)["\']?', cd, flags=re.IGNORECASE)
                    if match:
                        filename = urllib.parse.unquote(match[0].strip())

                if not filename:
                    base = os.path.basename(urllib.parse.urlparse(resp.url).path)
                    filename = urllib.parse.unquote(base) if base else "download"

                content_len = resp.headers.get("Content-Length")
                content_range = resp.headers.get("Content-Range", "")
                size = 0
                if content_len and content_len.isdigit():
                    size = int(content_len)
                elif content_range:
                    m = re.search(r"/(\d+)", content_range)
                    if m:
                        size = int(m.group(1))

                accepts_range = (resp.headers.get("Accept-Ranges", "").lower() == "bytes") or bool(content_range)

                def update_ui():
                    if filename and not self.fn_entry.get():
                        self.fn_entry.delete(0, "end")
                        self.fn_entry.insert(0, filename)
                    
                    self.fetched_size = size
                    if size > 0:
                        range_str = "Supports Resume" if accepts_range else "No Resume"
                        self.size_info_label.configure(
                            text=f"Size: {format_size(size)} ({range_str})",
                            text_color="#38A169" if accepts_range else "#DD6B20"
                        )
                    self.status_label.configure(text="Ready to download", text_color="#38A169")
                    self.fetch_btn.configure(state="normal", text="Inspect")
                    self.is_inspecting = False

                self.after(0, update_ui)
            except Exception as e:
                def update_err():
                    self.status_label.configure(text="Could not reach server automatically", text_color="#E53E3E")
                    self.fetch_btn.configure(state="normal", text="Inspect")
                    self.is_inspecting = False
                self.after(0, update_err)

        threading.Thread(target=inspect_worker, daemon=True).start()

    def _submit(self, start_now: bool):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL.")
            return

        filename = self.fn_entry.get().strip()
        if filename:
            filename = clean_filename(filename)

        save_dir = self.dir_entry.get().strip()
        try:
            conn_match = re.search(r'\d+', self.conn_combo.get())
            connections = int(conn_match.group()) if conn_match else 32
        except Exception:
            connections = 32

        if not os.path.isdir(save_dir):
            try:
                os.makedirs(save_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Invalid save directory: {e}")
                return

        # Map quality option
        q_text = self.quality_combo.get()
        if "Audio" in q_text or "MP3" in q_text:
            quality = "audio"
        elif "720p" in q_text:
            quality = "720"
        elif "480p" in q_text:
            quality = "480"
        elif "360p" in q_text:
            quality = "360"
        elif "1080p" in q_text:
            quality = "1080"
        else:
            quality = "best"

        task_type = "video" if is_video_streaming_url(url) else "file"

        # Remember folder for this category if checked
        if hasattr(self, "remember_cb_var") and self.remember_cb_var.get() and os.path.isdir(save_dir):
            set_remembered_folder(self.current_category, save_dir)

        if self.on_submit:
            try:
                self.on_submit(
                    url, save_dir, filename, connections, start_now, task_type, quality,
                    self.cookies, self.referer, self.user_agent
                )
            except TypeError:
                try:
                    self.on_submit(url, save_dir, filename, connections, start_now, task_type, quality)
                except TypeError:
                    self.on_submit(url, save_dir, filename, connections, start_now)
            except Exception as e:
                print(f"Error starting download: {e}")
                messagebox.showerror("Error", f"Failed to start download: {e}")
                return

        self.destroy()

    def _submit_batch(self):
        raw_text = self.batch_text.get("1.0", "end").strip()
        if not raw_text:
            messagebox.showerror("Error", "Please enter at least one URL.")
            return

        urls = [line.strip() for line in raw_text.splitlines() if line.strip().startswith("http")]
        if not urls:
            messagebox.showerror("Error", "No valid HTTP/HTTPS URLs found.")
            return

        save_dir = self.b_dir_entry.get().strip()
        os.makedirs(save_dir, exist_ok=True)

        if self.on_batch_submit:
            self.on_batch_submit(urls, save_dir)
        elif self.on_submit:
            for url in urls:
                try:
                    self.on_submit(url, save_dir, "", 8, True)
                except Exception:
                    pass

        self.destroy()
