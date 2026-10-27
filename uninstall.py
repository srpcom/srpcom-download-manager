import os
import sys
import subprocess
import winreg
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox

APP_NAME = "SRPCOM Download Manager"

def get_asset_path(filename: str) -> str:
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(base_dir, "assets", filename)
    if os.path.exists(p):
        return p
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", filename)

class UninstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title(f"Uninstall {APP_NAME}")
        self.geometry("480x280")
        self.resizable(False, False)

        icon_path = get_asset_path("logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self._init_ui()

    def _init_ui(self):
        # Header banner
        header = ctk.CTkFrame(self, fg_color="#C53030", height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        logo_path = get_asset_path("logo.png")
        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                self.ctk_logo = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(38, 38))
                lbl_logo = ctk.CTkLabel(header, image=self.ctk_logo, text="")
                lbl_logo.pack(side="left", padx=(15, 10))
            except Exception:
                pass

        h_title = ctk.CTkLabel(
            header,
            text=f"Uninstall {APP_NAME}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        h_title.pack(side="left", pady=12)

        # Buttons packed at the bottom first so they are never obscured
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=20, pady=(10, 18))

        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=90,
            height=34,
            fg_color="#718096",
            hover_color="#4A5568",
            command=self.destroy
        )
        self.cancel_btn.pack(side="right", padx=(8, 0))

        self.uninstall_btn = ctk.CTkButton(
            btn_frame,
            text="Uninstall",
            width=100,
            height=34,
            fg_color="#E53E3E",
            hover_color="#9B2C2C",
            font=ctk.CTkFont(weight="bold"),
            command=self._do_uninstall
        )
        self.uninstall_btn.pack(side="right")

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=15)

        q_lbl = ctk.CTkLabel(
            body,
            text=f"Are you sure you want to completely remove {APP_NAME}?",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        q_lbl.pack(fill="x", pady=(0, 6))

        d_lbl = ctk.CTkLabel(
            body,
            text="This will remove the application, shortcuts, and configuration files from your computer.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
            wraplength=440
        )
        d_lbl.pack(fill="x", pady=(0, 10))

        self.status_lbl = ctk.CTkLabel(body, text="", font=ctk.CTkFont(size=11), anchor="w")
        self.status_lbl.pack(fill="x")

    def _do_uninstall(self):
        self.uninstall_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")
        self.status_lbl.configure(text="Removing application and shortcuts...", text_color="#3182CE")

        # 1. Kill any running SRPCOM Download Manager process
        try:
            subprocess.run(["taskkill", "/f", "/im", f"{APP_NAME}.exe"], capture_output=True, creationflags=0x08000000)
        except Exception:
            pass

        # 2. Delete Shortcuts
        try:
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            desktop_lnk = os.path.join(desktop_dir, f"{APP_NAME}.lnk")
            if os.path.exists(desktop_lnk):
                os.remove(desktop_lnk)

            start_menu_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs")
            start_lnk = os.path.join(start_menu_dir, f"{APP_NAME}.lnk")
            if os.path.exists(start_lnk):
                os.remove(start_lnk)

            uninstall_lnk = os.path.join(start_menu_dir, f"Uninstall {APP_NAME}.lnk")
            if os.path.exists(uninstall_lnk):
                os.remove(uninstall_lnk)
        except Exception as e:
            print(f"Error removing shortcuts: {e}")

        # 3. Remove Windows Registry Uninstall Key
        try:
            key_path = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME.replace(' ', '')}"
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except Exception:
            pass

        # 4. Schedule self-deletion of installation directory
        # We can launch a detached cmd script that waits 1 sec then removes the folder
        install_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self_del_cmd = f'ping 127.0.0.1 -n 2 > nul & rmdir /s /q "{install_dir}"'
        try:
            subprocess.Popen(
                ["cmd.exe", "/c", self_del_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW | 0x00000008,
                close_fds=True
            )
        except Exception:
            pass

        messagebox.showinfo("Uninstalled", f"{APP_NAME} has been successfully removed from your computer.")
        self.destroy()

if __name__ == "__main__":
    app = UninstallerApp()
    app.mainloop()
