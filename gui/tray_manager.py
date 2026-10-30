import os
import sys
import threading
from PIL import Image
import pystray
from pystray import MenuItem as item, Menu

def get_asset_path(filename: str) -> str:
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = os.path.join(base_dir, "assets", filename)
    if os.path.exists(p):
        return p
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", filename)

class SystemTrayManager:
    """
    Manages the Windows System Tray (Notification Area / Hidden Icons) icon
    for SRPCOM Download Manager, matching IDM's behavior.
    """
    def __init__(self, app, manager):
        self.app = app
        self.manager = manager
        self.icon = None
        self._thread = None
        self._notified_first_close = False

        self._init_tray()

    def _get_icon_image(self) -> Image.Image:
        icon_path = get_asset_path("logo.png")
        if not os.path.exists(icon_path):
            icon_path = get_asset_path("logo.ico")

        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                return img.resize((64, 64), Image.Resampling.LANCZOS)
            except Exception:
                pass
        # Fallback 64x64 colored square if asset missing
        return Image.new("RGBA", (64, 64), color=(197, 48, 48, 255))

    def _init_tray(self):
        img = self._get_icon_image()

        def on_show_window(icon, item=None):
            self.show_window()

        def on_add_download(icon, item=None):
            self.show_window()
            self.app.after(100, self.app._open_add_dialog)

        def on_pause_all(icon, item=None):
            self.app.after(0, self.manager.pause_all)

        def on_resume_all(icon, item=None):
            self.app.after(0, self.manager.resume_all)

        def on_exit(icon, item=None):
            self.quit_app()

        menu = Menu(
            item("📂 Buka SRPCOM Download Manager", on_show_window, default=True),
            item("➕ Tambah URL Unduhan...", on_add_download),
            Menu.SEPARATOR,
            item("⏸ Jeda Semua Unduhan", on_pause_all),
            item("▶ Lanjutkan Semua Unduhan", on_resume_all),
            Menu.SEPARATOR,
            item("🚪 Keluar Sepenuhnya (Exit)", on_exit)
        )

        self.icon = pystray.Icon(
            name="SRPCOM Download Manager",
            icon=img,
            title="SRPCOM Download Manager",
            menu=menu
        )

    def start(self):
        """Start the system tray icon in a dedicated daemon thread."""
        if self.icon and not self._thread:
            self._thread = threading.Thread(target=self.icon.run, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop the system tray icon cleanly."""
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass

    def show_window(self):
        """Restore and bring the main window to foreground."""
        def _do_show():
            from gui.window_utils import bring_window_to_front
            bring_window_to_front(self.app)
        self.app.after(0, _do_show)

    def hide_to_tray(self, notify: bool = True):
        """Hide main window to system tray without stopping downloads or services."""
        self.app.withdraw()
        if notify and not self._notified_first_close:
            self._notified_first_close = True
            self.notify(
                "Aplikasi tetap berjalan di latar belakang (System Tray) untuk menangkap unduhan.",
                "SRPCOM Download Manager"
            )

    def notify(self, message: str, title: str = "SRPCOM Download Manager"):
        """Show balloon/toast notification from the tray icon."""
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception:
                pass

    def quit_app(self):
        """Completely shut down the application."""
        def _do_quit():
            self.stop()
            try:
                self.manager.pause_all()
                self.manager.save_tasks()
            except Exception:
                pass
            try:
                self.app.destroy()
            except Exception:
                pass
            sys.exit(0)
        self.app.after(0, _do_quit)
