import sys
import os
import customtkinter as ctk
from core.manager import DownloadManager
from core.browser_listener import start_browser_listener
from gui.main_window import MainWindow

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

    # Start Browser Integration listener
    start_browser_listener(
        on_download_received=app.open_add_dialog_with_url,
        on_video_download_received=app.open_video_download_dialog
    )

    # Clean shutdown handler
    def on_closing():
        manager.pause_all()
        manager.save_tasks()
        app.destroy()
        sys.exit(0)

    app.protocol("WM_DELETE_WINDOW", on_closing)

    # If launched on Windows boot (--autostart / --minimized), start minimized to taskbar
    if any(arg in sys.argv for arg in ["--autostart", "--minimized", "-minimized"]):
        app.after(150, app.iconify)

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
