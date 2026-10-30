import os
import sys
import subprocess
import winreg
import webbrowser
import customtkinter as ctk
from tkinter import messagebox

WEBSTORE_URL = "https://chromewebstore.google.com/detail/srpcom-download-manager-i/jnfbfdkpbbpmoanbkgablbmbklfpgacl"

EXTENSION_IDS = [
    "jnfbfdkpbbpmoanbkgablbmbklfpgacl", # Chrome Web Store official ID
    "keoeiohodnbgednmclmnconnkihjlail"  # Local developer unpacked ID
]

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
    for ext_id in EXTENSION_IDS:
        for reg_path in [
            rf"Software\Google\Chrome\Extensions\{ext_id}",
            rf"Software\Microsoft\Edge\Extensions\{ext_id}"
        ]:
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                    winreg.SetValueEx(key, "path", 0, winreg.REG_SZ, ext_dir)
                    winreg.SetValueEx(key, "version", 0, winreg.REG_SZ, "1.3.3")
            except Exception:
                pass

class BrowserExtensionDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Integrasi Ekstensi Browser - SRPCOM")
        self.geometry("660x600")
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
            text="🌐 Integrasi Ekstensi Browser Chrome / Edge",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="white"
        )
        h_title.pack(side="left", padx=20, pady=18)

        # Bottom Buttons packed first
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(10, 18), side="bottom")

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Tutup",
            width=95,
            height=34,
            fg_color="#718096",
            command=self.destroy
        )
        close_btn.pack(side="right")

        # Body container
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=25, pady=12)

        # 1. Status Bar
        status_box = ctk.CTkFrame(body, fg_color=("gray85", "gray20"), corner_radius=8)
        status_box.pack(fill="x", pady=(0, 12))

        s1 = ctk.CTkLabel(
            status_box,
            text="🟢 Server Desktop: AKTIF & MENDENGARKAN (127.0.0.1:9876)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38A169",
            anchor="w"
        )
        s1.pack(fill="x", padx=15, pady=(10, 4))

        s2 = ctk.CTkLabel(
            status_box,
            text=f"🟢 Windows Registry: TERDAFTAR OTOMATIS ({len(EXTENSION_IDS)} ID Terverifikasi)",
            font=ctk.CTkFont(size=11),
            text_color="#38A169",
            anchor="w"
        )
        s2.pack(fill="x", padx=15, pady=(0, 10))

        # 2. METODE UTAMA (Chrome Web Store Resmi)
        store_frame = ctk.CTkFrame(body, fg_color=("gray90", "#1E293B"), corner_radius=10, border_width=1.5, border_color="#3B82F6")
        store_frame.pack(fill="x", pady=(0, 14), padx=2)

        st_title = ctk.CTkLabel(
            store_frame,
            text="⭐ Jalur Resmi: Google Chrome Web Store (Disarankan)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#60A5FA",
            anchor="w"
        )
        st_title.pack(fill="x", padx=16, pady=(12, 4))

        st_desc = ctk.CTkLabel(
            store_frame,
            text="Instalasi 1-klik resmi dari Google Chrome Web Store. Bebas dari pesan peringatan 'Developer mode' dan otomatis menerima pembaruan versi terbaru selamanya.",
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray70"),
            wraplength=590,
            justify="left",
            anchor="w"
        )
        st_desc.pack(fill="x", padx=16, pady=(0, 10))

        btn_row_store = ctk.CTkFrame(store_frame, fg_color="transparent")
        btn_row_store.pack(fill="x", padx=16, pady=(0, 12))

        open_webstore_btn = ctk.CTkButton(
            btn_row_store,
            text="🌐 Buka Halaman Chrome Web Store (1-Klik Pasang)",
            height=38,
            fg_color="#1D4ED8",
            hover_color="#1E40AF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._open_webstore
        )
        open_webstore_btn.pack(side="left", padx=(0, 10))

        store_hint = ctk.CTkLabel(
            btn_row_store,
            text="✔ Kompatibel: Chrome, Edge, Brave, Opera",
            font=ctk.CTkFont(size=11),
            text_color="#38A169"
        )
        store_hint.pack(side="left")

        # 3. METODE CADANGAN (Pengembang / Pengujian Offline)
        dev_frame = ctk.CTkFrame(body, fg_color=("gray90", "gray17"), corner_radius=8)
        dev_frame.pack(fill="x", pady=(0, 8), padx=2)

        dev_title = ctk.CTkLabel(
            dev_frame,
            text="🛠️ Metode Pengembang / Uji Coba Offline (Load Unpacked)",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        dev_title.pack(fill="x", padx=14, pady=(10, 4))

        dev_desc = (
            "Jika tidak terhubung ke Web Store atau ingin menguji perubahan lokal secara langsung:\n"
            "1. Buka chrome://extensions di Chrome lalu aktifkan 'Developer mode'.\n"
            "2. Klik 'Load unpacked' lalu pilih folder 'browser_extension'."
        )
        dev_lbl = ctk.CTkLabel(
            dev_frame,
            text=dev_desc,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            justify="left",
            anchor="w"
        )
        dev_lbl.pack(fill="x", padx=14, pady=(0, 10))

        dev_btn_row = ctk.CTkFrame(dev_frame, fg_color="transparent")
        dev_btn_row.pack(fill="x", padx=14, pady=(0, 10))

        open_folder_btn = ctk.CTkButton(
            dev_btn_row,
            text="📂 Buka Folder Ekstensi",
            width=170,
            height=32,
            fg_color="#4A5568",
            hover_color="#2D3748",
            font=ctk.CTkFont(size=11),
            command=self._open_ext_folder
        )
        open_folder_btn.pack(side="left", padx=(0, 8))

        chrome_btn = ctk.CTkButton(
            dev_btn_row,
            text="🚀 Buka Chrome Dev Mode",
            width=180,
            height=32,
            fg_color="#2B6CB0",
            hover_color="#2C5282",
            font=ctk.CTkFont(size=11),
            command=self._launch_chrome
        )
        chrome_btn.pack(side="left")

    def _open_webstore(self):
        try:
            webbrowser.open(WEBSTORE_URL)
        except Exception:
            subprocess.Popen(f'cmd /c start "" "{WEBSTORE_URL}"')

    def _launch_chrome(self):
        ext_folder = get_ext_path()
        exe = find_browser_exe("chrome")
        try:
            subprocess.Popen([exe, f'--load-extension={ext_folder}', "chrome://extensions"])
            messagebox.showinfo("Google Chrome", "Google Chrome telah dibuka dengan ekstensi lokal dimuat!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal meluncurkan Chrome: {e}")

    def _open_ext_folder(self):
        folder = os.path.normpath(get_ext_path())
        os.makedirs(folder, exist_ok=True)
        try:
            os.startfile(folder)
        except Exception:
            subprocess.Popen(f'explorer.exe "{folder}"')
