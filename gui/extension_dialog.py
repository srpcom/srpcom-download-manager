import os
import sys
import subprocess
import winreg
import customtkinter as ctk
from tkinter import messagebox

EXT_ID = "keoeiohodnbgednmclmnconnkihjlail"

def get_ext_path() -> str:
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = os.path.join(base_dir, "browser_extension")
    if os.path.exists(p):
        return p
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "browser_extension")

def find_browser_exe(browser_name: str) -> str:
    paths = []
    if browser_name == "chrome":
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
    elif browser_name == "edge":
        paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
        ]
    for p in paths:
        if os.path.exists(p):
            return p
    return browser_name

def register_registry_now():
    ext_dir = get_ext_path()
    for reg_path in [
        rf"Software\Google\Chrome\Extensions\{EXT_ID}",
        rf"Software\Microsoft\Edge\Extensions\{EXT_ID}"
    ]:
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                winreg.SetValueEx(key, "path", 0, winreg.REG_SZ, ext_dir)
                winreg.SetValueEx(key, "version", 0, winreg.REG_SZ, "1.0.0")
        except Exception:
            pass

class BrowserExtensionDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Integrasi Browser Chrome / Edge - SRPCOM")
        self.geometry("640x540")
        self.resizable(False, False)
        self.transient(parent)

        # Make sure registry is registered
        register_registry_now()

        self._init_ui()

    def _init_ui(self):
        # Header banner
        header = ctk.CTkFrame(self, fg_color="#C53030", height=65, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        h_title = ctk.CTkLabel(
            header,
            text="🌐 Integrasi Otomatis Browser Chrome / Edge (Khas IDM)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="white"
        )
        h_title.pack(side="left", padx=20, pady=18)

        # Bottom Buttons packed first
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(10, 20), side="bottom")

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Tutup",
            width=90,
            height=34,
            fg_color="#718096",
            command=self.destroy
        )
        close_btn.pack(side="right", padx=(10, 0))

        open_folder_btn = ctk.CTkButton(
            btn_frame,
            text="📂 Buka Folder Ekstensi",
            width=170,
            height=34,
            fg_color="#4A5568",
            hover_color="#2D3748",
            command=self._open_ext_folder
        )
        open_folder_btn.pack(side="right")

        # Body container
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=25, pady=15)

        # Status Box
        status_box = ctk.CTkFrame(body, fg_color=("gray85", "gray20"), corner_radius=8)
        status_box.pack(fill="x", pady=(0, 15))

        s1 = ctk.CTkLabel(
            status_box,
            text="🟢 Server Desktop: AKTIF & MENDENGARKAN (127.0.0.1:9876)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38A169",
            anchor="w"
        )
        s1.pack(fill="x", padx=15, pady=(10, 3))

        s2 = ctk.CTkLabel(
            status_box,
            text=f"🟢 Windows Registry: TERDAFTAR OTOMATIS (ID: {EXT_ID[:8]}...)",
            font=ctk.CTkFont(size=11),
            text_color="#38A169",
            anchor="w"
        )
        s2.pack(fill="x", padx=15, pady=(0, 10))

        # 1-Click Action Frame
        action_frame = ctk.CTkFrame(body, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 15))

        act_lbl = ctk.CTkLabel(
            action_frame,
            text="⚡ Luncurkan Browser dengan Ekstensi Langsung Aktif (1-Click):",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        act_lbl.pack(fill="x", pady=(0, 8))

        btn_row = ctk.CTkFrame(action_frame, fg_color="transparent")
        btn_row.pack(fill="x")

        chrome_btn = ctk.CTkButton(
            btn_row,
            text="🚀 Buka Google Chrome",
            width=180,
            height=36,
            fg_color="#2B6CB0",
            hover_color="#2C5282",
            font=ctk.CTkFont(weight="bold"),
            command=self._launch_chrome
        )
        chrome_btn.pack(side="left", padx=(0, 10))

        edge_btn = ctk.CTkButton(
            btn_row,
            text="🚀 Buka Microsoft Edge",
            width=180,
            height=36,
            fg_color="#319795",
            hover_color="#285E61",
            font=ctk.CTkFont(weight="bold"),
            command=self._launch_edge
        )
        edge_btn.pack(side="left")

        # Separator / Manual Step Info
        manual_lbl = ctk.CTkLabel(
            body,
            text="Atau cara manual satu kali via menu Chrome (chrome://extensions):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray",
            anchor="w"
        )
        manual_lbl.pack(fill="x", pady=(10, 4))

        steps_frame = ctk.CTkFrame(body, fg_color=("gray90", "gray17"), corner_radius=6)
        steps_frame.pack(fill="x", pady=(0, 5))

        st_text = (
            "1. Buka chrome://extensions di address bar Chrome.\n"
            "2. Aktifkan 'Developer mode' di pojok kanan atas.\n"
            "3. Klik 'Load unpacked' lalu pilih folder 'browser_extension'."
        )
        st_lbl = ctk.CTkLabel(
            steps_frame,
            text=st_text,
            font=ctk.CTkFont(size=11),
            justify="left",
            anchor="w"
        )
        st_lbl.pack(fill="x", padx=12, pady=8)

        success_tip = ctk.CTkLabel(
            body,
            text="✔ Begitu terpasang, setiap kali Anda mengklik download file (.apk, .zip, .mp4, dll) di website mana pun, Chrome akan langsung meneruskannya ke SRPCOM Download Manager!",
            font=ctk.CTkFont(size=11),
            text_color="#38A169",
            wraplength=580,
            justify="left",
            anchor="w"
        )
        success_tip.pack(fill="x", pady=(8, 0))

    def _launch_chrome(self):
        ext_folder = get_ext_path()
        exe = find_browser_exe("chrome")
        try:
            subprocess.Popen([exe, f'--load-extension={ext_folder}', "chrome://extensions"])
            messagebox.showinfo("Google Chrome", "Google Chrome telah dibuka dengan ekstensi SRPCOM langsung aktif!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal meluncurkan Chrome: {e}")

    def _launch_edge(self):
        ext_folder = get_ext_path()
        exe = find_browser_exe("edge")
        try:
            subprocess.Popen([exe, f'--load-extension={ext_folder}', "edge://extensions"])
            messagebox.showinfo("Microsoft Edge", "Microsoft Edge telah dibuka dengan ekstensi SRPCOM langsung aktif!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal meluncurkan Edge: {e}")

    def _open_ext_folder(self):
        folder = os.path.normpath(get_ext_path())
        os.makedirs(folder, exist_ok=True)
        try:
            os.startfile(folder)
        except Exception:
            subprocess.Popen(f'explorer.exe "{folder}"')
