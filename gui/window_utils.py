import sys
import customtkinter as ctk

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
