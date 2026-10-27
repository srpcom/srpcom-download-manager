import os
import sys
import subprocess
import customtkinter as ctk

def open_folder_and_select(file_path: str, save_dir: str = ""):
    """
    Open Windows File Explorer with the downloaded file selected/highlighted,
    or open its containing folder if the file is not yet assembled or missing.
    Normalizes Windows backslashes so Explorer never misinterprets forward slashes
    as command switches and falls back to Desktop.
    """
    norm_file = os.path.normpath(file_path) if file_path else ""
    norm_dir = os.path.normpath(save_dir) if save_dir else ""

    # Priority 1: If target file exists on disk, open Explorer and select it
    if norm_file and os.path.exists(norm_file):
        try:
            subprocess.Popen(f'explorer.exe /select,"{norm_file}"')
            return
        except Exception:
            pass

    # Priority 2: If folder exists, open folder directly
    folder = norm_dir if (norm_dir and os.path.isdir(norm_dir)) else (os.path.dirname(norm_file) if norm_file else "")
    if folder and os.path.isdir(folder):
        try:
            os.startfile(folder)
            return
        except Exception:
            try:
                subprocess.Popen(f'explorer.exe "{folder}"')
                return
            except Exception:
                pass

    # Priority 3: Fallback to standard Downloads folder
    user_downloads = os.path.normpath(os.path.expanduser("~/Downloads"))
    if os.path.isdir(user_downloads):
        try:
            os.startfile(user_downloads)
        except Exception:
            subprocess.Popen(f'explorer.exe "{user_downloads}"')

def center_window(window, width: int = 580, height: int = 520):
    """Center a window on the current screen."""
    try:
        window.update_idletasks()
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    except Exception:
        pass

def bring_window_to_front(window, keep_topmost_ms: int = 1200):
    """
    Force a Tkinter/CustomTkinter window to the foreground on Windows,
    bypassing Windows foreground lock (LockSetForegroundWindow), just like IDM.
    """
    try:
        window.deiconify()
        window.attributes("-topmost", True)
        window.lift()
        window.focus_force()

        if keep_topmost_ms > 0:
            window.after(keep_topmost_ms, lambda: _release_topmost(window))

        if sys.platform == "win32":
            import ctypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            hwnd = window.winfo_id()
            root_hwnd = user32.GetAncestor(hwnd, 2) or hwnd

            fore_hwnd = user32.GetForegroundWindow()
            fore_thread = user32.GetWindowThreadProcessId(fore_hwnd, None)
            app_thread = kernel32.GetCurrentThreadId()

            if fore_thread != app_thread:
                user32.AttachThreadInput(fore_thread, app_thread, True)
                user32.ShowWindow(root_hwnd, 9)  # 9 = SW_RESTORE
                user32.SetWindowPos(root_hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)  # HWND_TOPMOST, SWP_NOMOVE | SWP_NOSIZE
                user32.SetWindowPos(root_hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002)  # HWND_NOTOPMOST
                user32.SetForegroundWindow(root_hwnd)
                user32.BringWindowToTop(root_hwnd)
                user32.AttachThreadInput(fore_thread, app_thread, False)
            else:
                user32.ShowWindow(root_hwnd, 9)
                user32.SetForegroundWindow(root_hwnd)
                user32.BringWindowToTop(root_hwnd)
    except Exception as e:
        print(f"bring_window_to_front error: {e}")

def _release_topmost(window):
    try:
        if window.winfo_exists():
            window.attributes("-topmost", False)
    except Exception:
        pass
