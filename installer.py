import os
import sys
import time
import shutil
import subprocess
import winreg
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox

APP_NAME = "SRPCOM Download Manager"
APP_PUBLISHER = "SRPCOM"
APP_VERSION = "1.2.1"

EXTENSION_IDS = [
    "jnfbdfkbbpmoanbkgablmbmklfpgacl",
    "keoeiohodnbgednmclmnconnkihjlail"
]

def get_asset_path(filename: str) -> str:
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(base_dir, "assets", filename)
    if os.path.exists(p):
        return p
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", filename)

def get_bundled_file_path(filename: str) -> str:
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    p1 = os.path.join(base_dir, "payload", filename)
    if os.path.exists(p1):
        return p1
    p2 = os.path.join(base_dir, "dist", filename)
    if os.path.exists(p2):
        return p2
    p3 = os.path.join(base_dir, filename)
    if os.path.exists(p3):
        return p3
    return ""

def create_windows_shortcut(target_exe: str, shortcut_path: str, icon_path: str = "", args: str = "", description: str = ""):
    icon_line = f'$s.IconLocation = "{icon_path}"' if icon_path else ""
    args_line = f'$s.Arguments = "{args}"' if args else ""
    work_dir = os.path.dirname(target_exe)
    ps_cmd = f'''
    $ws = New-Object -ComObject WScript.Shell;
    $s = $ws.CreateShortcut("{shortcut_path}");
    $s.TargetPath = "{target_exe}";
    $s.WorkingDirectory = "{work_dir}";
    $s.Description = "{description}";
    {args_line};
    {icon_line};
    $s.Save();
    '''
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
    except Exception as e:
        print(f"Error creating shortcut {shortcut_path}: {e}")

def register_browser_extensions(install_dir: str):
    ext_dir = os.path.join(install_dir, "browser_extension")
    for ext_id in EXTENSION_IDS:
        for reg_path in [
            rf"Software\Google\Chrome\Extensions\{ext_id}",
            rf"Software\Microsoft\Edge\Extensions\{ext_id}"
        ]:
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                    winreg.SetValueEx(key, "path", 0, winreg.REG_SZ, ext_dir)
                    winreg.SetValueEx(key, "version", 0, winreg.REG_SZ, APP_VERSION)
            except Exception as e:
                print(f"Registry error for {reg_path}: {e}")

def unregister_browser_extensions():
    for ext_id in EXTENSION_IDS:
        for reg_path in [
            rf"Software\Google\Chrome\Extensions\{ext_id}",
            rf"Software\Microsoft\Edge\Extensions\{ext_id}"
        ]:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
            except Exception:
                pass

def register_in_control_panel(install_dir: str, main_exe: str, icon_path: str, uninstaller_exe: str):
    try:
        key_path = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME.replace(' ', '')}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, APP_PUBLISHER)
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_path)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller_exe}" --uninstall')
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception as e:
        print(f"Registry registration error: {e}")

def unregister_control_panel():
    try:
        key_path = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME.replace(' ', '')}"
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
    except Exception:
        pass


class UnifiedSetupApp(ctk.CTk):
    def __init__(self, mode: str):
        super().__init__()
        self.mode = mode  # "install", "maintenance", "uninstall"
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        self.default_install_dir = os.path.join(local_app_data, "Programs", APP_NAME)

        self.geometry("580x520")
        self.resizable(False, False)

        icon_path = get_asset_path("logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self._init_ui()
        self._apply_mode_ui()

    def _init_ui(self):
        # 1. Header Banner
        self.header_frame = ctk.CTkFrame(self, fg_color="#8B0000", height=80, corner_radius=0)
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False)

        logo_path = get_asset_path("logo.png")
        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                self.ctk_logo = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(50, 50))
                lbl_logo = ctk.CTkLabel(self.header_frame, image=self.ctk_logo, text="")
                lbl_logo.pack(side="left", padx=(20, 15))
            except Exception:
                pass

        self.h_title = ctk.CTkLabel(
            self.header_frame,
            text=f"{APP_NAME} Setup",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        self.h_title.pack(side="left", pady=15)

        # 2. Bottom Buttons Container
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=25, pady=(10, 20), side="bottom")

        # 3. Middle Body Frame
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=25, pady=15)

    def _apply_mode_ui(self):
        # Clear body and button frames
        for w in self.body.winfo_children():
            w.destroy()
        for w in self.btn_frame.winfo_children():
            w.destroy()

        if self.mode == "uninstall":
            self.title(f"Uninstall {APP_NAME}")
            self.header_frame.configure(fg_color="#C53030")
            self.h_title.configure(text=f"Uninstall {APP_NAME}")
            self._build_uninstall_body()
            self._build_uninstall_buttons()
        elif self.mode == "maintenance":
            self.title(f"{APP_NAME} Setup & Maintenance")
            self.header_frame.configure(fg_color="#2B6CB0")
            self.h_title.configure(text=f"{APP_NAME} Setup & Maintenance")
            self._build_maintenance_body()
            self._build_maintenance_buttons()
        else:
            self.title(f"{APP_NAME} Setup")
            self.header_frame.configure(fg_color="#8B0000")
            self.h_title.configure(text=f"Wizard Instalasi {APP_NAME}")
            self._build_install_body()
            self._build_install_buttons()

    def _build_install_body(self):
        welcome_lbl = ctk.CTkLabel(
            self.body,
            text=f"Selamat datang di Wizard Instalasi {APP_NAME}.",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        welcome_lbl.pack(fill="x", pady=(0, 4))

        desc_lbl = ctk.CTkLabel(
            self.body,
            text=f"Wizard ini akan memasang aplikasi {APP_NAME} v{APP_VERSION} di komputer Anda.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        desc_lbl.pack(fill="x", pady=(0, 15))

        dest_lbl = ctk.CTkLabel(self.body, text="Folder Instalasi:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
        dest_lbl.pack(fill="x", pady=(0, 4))

        self.dest_entry = ctk.CTkEntry(self.body, height=34)
        self.dest_entry.insert(0, self.default_install_dir)
        self.dest_entry.pack(fill="x", pady=(0, 15))

        self.chk_desktop = ctk.CTkCheckBox(self.body, text="Buat Shortcut di Desktop", font=ctk.CTkFont(size=12))
        self.chk_desktop.select()
        self.chk_desktop.pack(anchor="w", pady=4)

        self.chk_start_menu = ctk.CTkCheckBox(self.body, text="Buat Shortcut di Start Menu", font=ctk.CTkFont(size=12))
        self.chk_start_menu.select()
        self.chk_start_menu.pack(anchor="w", pady=4)

        self.chk_launch = ctk.CTkCheckBox(self.body, text=f"Jalankan {APP_NAME} setelah selesai", font=ctk.CTkFont(size=12))
        self.chk_launch.select()
        self.chk_launch.pack(anchor="w", pady=4)

        self.pbar = ctk.CTkProgressBar(self.body, height=8)
        self.pbar.pack(fill="x", pady=(15, 6))
        self.pbar.set(0)

        self.status_lbl = ctk.CTkLabel(self.body, text="Siap memasang aplikasi", text_color="gray", font=ctk.CTkFont(size=11), anchor="w")
        self.status_lbl.pack(fill="x")

    def _build_install_buttons(self):
        self.cancel_btn = ctk.CTkButton(
            self.btn_frame,
            text="Batal",
            width=95,
            height=36,
            fg_color="#718096",
            hover_color="#4A5568",
            command=self.destroy
        )
        self.cancel_btn.pack(side="right", padx=(10, 0))

        self.action_btn = ctk.CTkButton(
            self.btn_frame,
            text="📥 Pasang (Install)",
            width=160,
            height=36,
            fg_color="#C53030",
            hover_color="#9B2C2C",
            font=ctk.CTkFont(weight="bold"),
            command=self._do_install
        )
        self.action_btn.pack(side="right")

    def _build_maintenance_body(self):
        status_box = ctk.CTkFrame(self.body, fg_color=("gray85", "gray20"), corner_radius=8)
        status_box.pack(fill="x", pady=(0, 15))

        info_lbl = ctk.CTkLabel(
            status_box,
            text=f"✔ {APP_NAME} saat ini terpasang di komputer Anda.",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38A169",
            anchor="w"
        )
        info_lbl.pack(fill="x", padx=15, pady=(12, 4))

        loc_lbl = ctk.CTkLabel(
            status_box,
            text=f"Lokasi: {self.default_install_dir}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        loc_lbl.pack(fill="x", padx=15, pady=(0, 12))

        q_lbl = ctk.CTkLabel(
            self.body,
            text="Pilih tindakan yang ingin Anda lakukan:",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        q_lbl.pack(fill="x", pady=(0, 6))

        d_lbl = ctk.CTkLabel(
            self.body,
            text="Anda dapat memperbarui/memasang ulang aplikasi ke versi terbaru ini atau menghapus instalan secara bersih dari sistem.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
            justify="left",
            wraplength=520
        )
        d_lbl.pack(fill="x", pady=(0, 15))

        self.pbar = ctk.CTkProgressBar(self.body, height=8)
        self.pbar.pack(fill="x", pady=(10, 6))
        self.pbar.set(0)

        self.status_lbl = ctk.CTkLabel(self.body, text="Siap memperbarui atau mencopot aplikasi", text_color="gray", font=ctk.CTkFont(size=11), anchor="w")
        self.status_lbl.pack(fill="x")

    def _build_maintenance_buttons(self):
        close_btn = ctk.CTkButton(
            self.btn_frame,
            text="Tutup",
            width=95,
            height=36,
            fg_color="#718096",
            hover_color="#4A5568",
            command=self.destroy
        )
        close_btn.pack(side="right", padx=(10, 0))

        reinstall_btn = ctk.CTkButton(
            self.btn_frame,
            text="🔄 Perbarui / Pasang Ulang",
            width=180,
            height=36,
            fg_color="#2B6CB0",
            hover_color="#2C5282",
            font=ctk.CTkFont(weight="bold"),
            command=self._switch_to_install
        )
        reinstall_btn.pack(side="right", padx=(10, 0))

        uninstall_btn = ctk.CTkButton(
            self.btn_frame,
            text="🗑️ Hapus (Uninstall)",
            width=150,
            height=36,
            fg_color="#E53E3E",
            hover_color="#9B2C2C",
            command=self._switch_to_uninstall
        )
        uninstall_btn.pack(side="right")

    def _build_uninstall_body(self):
        status_box = ctk.CTkFrame(self.body, fg_color=("gray85", "gray20"), corner_radius=8)
        status_box.pack(fill="x", pady=(0, 15))

        info_lbl = ctk.CTkLabel(
            status_box,
            text=f"Konfirmasi Pencopotan {APP_NAME}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#E53E3E",
            anchor="w"
        )
        info_lbl.pack(fill="x", padx=15, pady=(12, 4))

        loc_lbl = ctk.CTkLabel(
            status_box,
            text=f"Lokasi program: {self.default_install_dir}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        loc_lbl.pack(fill="x", padx=15, pady=(0, 12))

        q_lbl = ctk.CTkLabel(
            self.body,
            text="Apakah Anda yakin ingin menghapus SRPCOM Download Manager?",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        q_lbl.pack(fill="x", pady=(0, 4))

        d_lbl = ctk.CTkLabel(
            self.body,
            text="Tindakan ini akan menghapus aplikasi, shortcut Desktop, Start Menu, dan pendaftaran sistem secara bersih dari komputer Anda.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
            justify="left",
            wraplength=520
        )
        d_lbl.pack(fill="x", pady=(0, 15))

        self.pbar = ctk.CTkProgressBar(self.body, height=8)
        self.pbar.pack(fill="x", pady=(10, 6))
        self.pbar.set(0)

        self.status_lbl = ctk.CTkLabel(self.body, text="Siap mencopot aplikasi", text_color="gray", font=ctk.CTkFont(size=11), anchor="w")
        self.status_lbl.pack(fill="x")

    def _build_uninstall_buttons(self):
        self.cancel_btn = ctk.CTkButton(
            self.btn_frame,
            text="Batal",
            width=95,
            height=36,
            fg_color="#718096",
            hover_color="#4A5568",
            command=self.destroy
        )
        self.cancel_btn.pack(side="right", padx=(10, 0))

        self.action_btn = ctk.CTkButton(
            self.btn_frame,
            text="🗑️ Hapus (Uninstall)",
            width=160,
            height=36,
            fg_color="#E53E3E",
            hover_color="#9B2C2C",
            font=ctk.CTkFont(weight="bold"),
            command=self._do_uninstall
        )
        self.action_btn.pack(side="right")

    def _switch_to_install(self):
        self.mode = "install"
        self._apply_mode_ui()

    def _switch_to_uninstall(self):
        self.mode = "uninstall"
        self._apply_mode_ui()

    def _do_install(self):
        self.action_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")
        self.status_lbl.configure(text="Menyiapkan instalasi...", text_color="#3182CE")
        self.pbar.set(0.1)

        try:
            # Terminate running app instance ONLY (do NOT kill the installer/setup itself!)
            try:
                subprocess.run(["taskkill", "/F", "/T", "/IM", f"{APP_NAME}.exe"], capture_output=True, creationflags=0x08000000)
                subprocess.run(["powershell", "-NoProfile", "-Command", f"Get-Process -Name '{APP_NAME}' -ErrorAction SilentlyContinue | Where-Object {{ $_.ProcessName -notlike '*Setup*' }} | Stop-Process -Force"], creationflags=0x08000000)
                time.sleep(0.3)
            except Exception:
                pass

            install_dir = getattr(self, "dest_entry", None)
            install_dir = install_dir.get().strip() if install_dir else self.default_install_dir
            os.makedirs(install_dir, exist_ok=True)

            self.status_lbl.configure(text="Menyalin file executable aplikasi...")
            self.pbar.set(0.3)

            # 1. Copy Main Executable
            src_exe = get_bundled_file_path(f"{APP_NAME}.exe")
            if not src_exe or not os.path.exists(src_exe):
                messagebox.showerror("Error", "Gagal menemukan executable aplikasi!")
                self.action_btn.configure(state="normal")
                self.cancel_btn.configure(state="normal")
                return

            target_exe = os.path.join(install_dir, f"{APP_NAME}.exe")
            if os.path.exists(target_exe):
                try:
                    os.chmod(target_exe, 0o777)
                except Exception:
                    pass
            try:
                shutil.copy2(src_exe, target_exe)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menyalin executable aplikasi: {e}")
                self.action_btn.configure(state="normal")
                self.cancel_btn.configure(state="normal")
                return

            self.pbar.set(0.5)
            self.status_lbl.configure(text="Menyalin aset dan ekstensi...")

            # 2. Copy Assets
            target_assets = os.path.join(install_dir, "assets")
            os.makedirs(target_assets, exist_ok=True)
            src_ico = get_asset_path("logo.ico")
            src_png = get_asset_path("logo.png")
            if os.path.exists(src_ico):
                shutil.copy2(src_ico, os.path.join(target_assets, "logo.ico"))
            if os.path.exists(src_png):
                shutil.copy2(src_png, os.path.join(target_assets, "logo.png"))

            # 3. Copy Browser Extension
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            src_ext = os.path.join(base_dir, "browser_extension")
            if not os.path.exists(src_ext):
                src_ext = os.path.join(base_dir, "payload", "browser_extension")
            target_ext = os.path.join(install_dir, "browser_extension")
            if os.path.exists(src_ext):
                shutil.copytree(src_ext, target_ext, dirs_exist_ok=True)

            # 4. Copy this setup executable itself into install_dir for self-uninstaller!
            current_setup = sys.argv[0]
            target_setup = os.path.join(install_dir, "SRPCOM_Setup.exe")
            if os.path.exists(current_setup) and os.path.abspath(current_setup).lower() != os.path.abspath(target_setup).lower():
                try:
                    shutil.copy2(current_setup, target_setup)
                except Exception:
                    pass

            self.pbar.set(0.7)
            self.status_lbl.configure(text="Mendaftarkan shortcut dan integrasi sistem...")

            # 5. Create Shortcuts
            ico_file = os.path.join(target_assets, "logo.ico")
            chk_desk = getattr(self, "chk_desktop", None)
            if chk_desk is None or chk_desk.get():
                desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                desktop_lnk = os.path.join(desktop_dir, f"{APP_NAME}.lnk")
                try:
                    create_windows_shortcut(target_exe, desktop_lnk, ico_file, description=f"Download manager by {APP_PUBLISHER}")
                except Exception as e:
                    print(f"Error desktop shortcut: {e}")

            start_menu_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs")
            chk_start = getattr(self, "chk_start_menu", None)
            if chk_start is None or chk_start.get():
                start_lnk = os.path.join(start_menu_dir, f"{APP_NAME}.lnk")
                try:
                    create_windows_shortcut(target_exe, start_lnk, ico_file, description=f"Download manager by {APP_PUBLISHER}")
                except Exception as e:
                    print(f"Error start menu shortcut: {e}")

            # Start menu uninstaller shortcut pointing to this dual-mode setup with --uninstall
            if os.path.exists(target_setup):
                uninst_lnk = os.path.join(start_menu_dir, f"Uninstall {APP_NAME}.lnk")
                try:
                    create_windows_shortcut(target_setup, uninst_lnk, ico_file, args="--uninstall", description=f"Uninstall {APP_NAME}")
                except Exception:
                    pass

            # 6. Register in Windows Control Panel (Settings -> Installed Apps)
            uninstaller_exe = target_setup if os.path.exists(target_setup) else target_exe
            register_in_control_panel(install_dir, target_exe, ico_file, uninstaller_exe)

            # 7. Register Browser Extensions in Chrome and Edge Registry
            register_browser_extensions(install_dir)

            self.pbar.set(1.0)
            self.status_lbl.configure(text="Instalasi berhasil selesai!", text_color="#38A169")

            # Launch if checked
            chk_launch = getattr(self, "chk_launch", None)
            if chk_launch is not None and chk_launch.get():
                try:
                    subprocess.Popen([target_exe])
                except Exception:
                    pass

            messagebox.showinfo("Instalasi Selesai", f"{APP_NAME} v{APP_VERSION} berhasil dipasang!")
            self.destroy()

        except Exception as e:
            import traceback
            err_details = traceback.format_exc()
            messagebox.showerror("Error Instalasi", f"Terjadi kesalahan saat memasang aplikasi:\n{e}\n\nDetail:\n{err_details}")
            self.action_btn.configure(state="normal")
            self.cancel_btn.configure(state="normal")

    def _do_uninstall(self):
        confirm = messagebox.askyesno(
            "Konfirmasi Uninstall",
            f"Apakah Anda benar-benar ingin menghapus {APP_NAME} dari komputer Anda secara bersih?"
        )
        if not confirm:
            return

        self.action_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")

        self.status_lbl.configure(text="Menutup proses aplikasi...", text_color="#3182CE")
        self.pbar.set(0.2)

        try:
            # 1. Kill running instances
            for proc in [f"{APP_NAME}.exe", "Uninstall.exe"]:
                try:
                    subprocess.run(["taskkill", "/F", "/T", "/IM", proc], capture_output=True, creationflags=0x08000000)
                except Exception:
                    pass
            try:
                subprocess.run(["powershell", "-NoProfile", "-Command", f"Get-Process -Name '{APP_NAME}' -ErrorAction SilentlyContinue | Where-Object {{ $_.ProcessName -notlike '*Setup*' -and $_.ProcessName -notlike '*Uninstall*' }} | Stop-Process -Force"], creationflags=0x08000000)
            except Exception:
                pass
            time.sleep(0.4)

            # 2. Remove Shortcuts
            self.status_lbl.configure(text="Menghapus shortcut...")
            self.pbar.set(0.4)
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            desktop_lnk = os.path.join(desktop_dir, f"{APP_NAME}.lnk")
            if os.path.exists(desktop_lnk):
                try:
                    os.remove(desktop_lnk)
                except Exception:
                    pass

            start_menu_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs")
            for lnk_name in [f"{APP_NAME}.lnk", f"Uninstall {APP_NAME}.lnk"]:
                s_lnk = os.path.join(start_menu_dir, lnk_name)
                if os.path.exists(s_lnk):
                    try:
                        os.remove(s_lnk)
                    except Exception:
                        pass

            # 3. Unregister from Windows Settings / Control Panel and Browser Registries
            self.status_lbl.configure(text="Membersihkan pendaftaran sistem dan ekstensi...")
            self.pbar.set(0.6)
            unregister_control_panel()
            unregister_browser_extensions()

            # 4. Remove all files from installation directory directly in Python
            self.status_lbl.configure(text="Menghapus file program...")
            self.pbar.set(0.8)
            install_dir = self.default_install_dir

            current_exe = os.path.abspath(sys.argv[0]).lower()

            if os.path.exists(install_dir):
                # First explicitly remove main executable so is_installed is NEVER true
                main_exe = os.path.join(install_dir, f"{APP_NAME}.exe")
                if os.path.exists(main_exe):
                    try:
                        os.chmod(main_exe, 0o777)
                        os.remove(main_exe)
                    except Exception as e:
                        print(f"Error removing main exe: {e}")

                for root, dirs, files in os.walk(install_dir, topdown=False):
                    for f in files:
                        fp = os.path.join(root, f)
                        if fp.lower() == current_exe:
                            continue
                        try:
                            os.chmod(fp, 0o777)
                            os.remove(fp)
                        except Exception:
                            pass
                    for d in dirs:
                        dp = os.path.join(root, d)
                        try:
                            shutil.rmtree(dp, ignore_errors=True)
                        except Exception:
                            pass

                # Try to remove the installation directory itself
                try:
                    shutil.rmtree(install_dir, ignore_errors=True)
                except Exception:
                    pass

            # 5. In case self-uninstaller is running or delayed cleanup is needed:
            if os.path.exists(install_dir):
                cmd_clean = f'ping 127.0.0.1 -n 3 > nul & rmdir /s /q "{install_dir}"'
                try:
                    subprocess.Popen(
                        ["cmd.exe", "/c", cmd_clean],
                        creationflags=subprocess.CREATE_NO_WINDOW | 0x00000008,
                        close_fds=True
                    )
                except Exception:
                    pass

            self.pbar.set(1.0)
            self.status_lbl.configure(text="Uninstall berhasil selesai!", text_color="#38A169")
            messagebox.showinfo("Uninstall Berhasil", f"{APP_NAME} telah berhasil dihapus secara bersih dari komputer Anda.")
            self.destroy()

        except Exception as e:
            import traceback
            err = traceback.format_exc()
            messagebox.showerror("Error Uninstall", f"Terjadi kesalahan saat menghapus aplikasi:\n{e}\n\nDetail:\n{err}")
            self.action_btn.configure(state="normal")
            self.cancel_btn.configure(state="normal")

def main():
    local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    install_dir = os.path.join(local_app_data, "Programs", APP_NAME)
    is_installed = os.path.exists(os.path.join(install_dir, f"{APP_NAME}.exe"))
    current_exe = os.path.abspath(sys.argv[0])

    # If launched with --from-pid, wait briefly for parent process to release handles
    for arg in sys.argv:
        if arg.startswith("--from-pid="):
            time.sleep(0.8)
            break

    # If --uninstall is requested:
    if "--uninstall" in sys.argv:
        # If the uninstaller is currently running from inside install_dir, copy to %TEMP% to prevent directory lock!
        if install_dir.lower() in current_exe.lower():
            temp_dir = os.environ.get("TEMP", os.path.expanduser("~\\AppData\\Local\\Temp"))
            temp_uninstaller = os.path.join(temp_dir, "SRPCOM_Uninstaller.exe")
            try:
                shutil.copy2(current_exe, temp_uninstaller)
                subprocess.Popen([temp_uninstaller, "--uninstall", f"--from-pid={os.getpid()}"], close_fds=True)
                sys.exit(0)
            except Exception as e:
                print(f"Error relocating uninstaller to temp: {e}")

        mode = "uninstall"
    elif is_installed:
        mode = "maintenance"
    else:
        mode = "install"

    app = UnifiedSetupApp(mode=mode)
    app.mainloop()

if __name__ == "__main__":
    main()
