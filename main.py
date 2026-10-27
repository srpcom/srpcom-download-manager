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
    data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads_data.json")
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
    app.mainloop()

if __name__ == "__main__":
    main()
