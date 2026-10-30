import sys
import os
import customtkinter as ctk
from core.manager import DownloadManager
from core.browser_listener import start_browser_listener
from gui.main_window import MainWindow
from gui.tray_manager import SystemTrayManager

def main():
    # Set default appearance
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    # Initialize manager & load tasks
    app_data_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "SRPCOM Download Manager")
    try:
        os.makedirs(app_data_dir, exist_ok=True)
    except Exception:
        pass
    data_file = os.path.join(app_data_dir, "downloads_data.json")

    # Migrate old data_file if exists in executable directory
    old_data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads_data.json")
    if os.path.exists(old_data_file) and not os.path.exists(data_file):
        try:
            import shutil
            shutil.copy2(old_data_file, data_file)
        except Exception:
            pass

    manager = DownloadManager(data_file=data_file)
    manager.load_tasks()

    app = MainWindow(manager=manager)

    # Initialize System Tray (Hidden Icons / Notification Area)
    tray = SystemTrayManager(app=app, manager=manager)
    app.tray_manager = tray
    tray.start()

    # Start Browser Integration listener
    start_browser_listener(
        on_download_received=app.open_add_dialog_with_url,
        on_video_download_received=app.open_video_download_dialog
    )

    # Intercept 'X' window close: minimize to system tray instead of killing app (IDM-style)
    app.protocol("WM_DELETE_WINDOW", app.hide_to_tray)

    # If launched on Windows boot (--autostart / --minimized), start directly hidden in tray
    if any(arg in sys.argv for arg in ["--autostart", "--minimized", "-minimized"]):
        app.after(50, lambda: tray.hide_to_tray(notify=False))

    app.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        log_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "SRPCOM Download Manager")
        try:
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "crash.log"), "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
        except Exception:
            pass
        raise
