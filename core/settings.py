import os
import json

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")

DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
DEFAULT_VIDEOS_DIR = os.path.join(os.path.expanduser("~"), "Videos") if os.path.exists(os.path.join(os.path.expanduser("~"), "Videos")) else DEFAULT_DOWNLOAD_DIR
DEFAULT_MUSIC_DIR = os.path.join(os.path.expanduser("~"), "Music") if os.path.exists(os.path.join(os.path.expanduser("~"), "Music")) else DEFAULT_DOWNLOAD_DIR
DEFAULT_DOCS_DIR = os.path.join(os.path.expanduser("~"), "Documents") if os.path.exists(os.path.join(os.path.expanduser("~"), "Documents")) else DEFAULT_DOWNLOAD_DIR

DEFAULT_SETTINGS = {
    "remembered_dirs": {
        "Video": DEFAULT_VIDEOS_DIR,
        "Music": DEFAULT_MUSIC_DIR,
        "Compressed": DEFAULT_DOWNLOAD_DIR,
        "Documents": DEFAULT_DOCS_DIR,
        "Programs": DEFAULT_DOWNLOAD_DIR,
        "Other": DEFAULT_DOWNLOAD_DIR
    },
    "default_dir": DEFAULT_DOWNLOAD_DIR,
    "default_connections": 32,
    "column_widths": {
        "name": 300,
        "size": 80,
        "status": 90,
        "progress": 140,
        "speed": 85,
        "eta": 80,
        "action": 60
    }
}

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                res = DEFAULT_SETTINGS.copy()
                if "remembered_dirs" in saved:
                    res["remembered_dirs"].update(saved["remembered_dirs"])
                if "default_dir" in saved:
                    res["default_dir"] = saved["default_dir"]
                if "default_connections" in saved:
                    res["default_connections"] = saved["default_connections"]
                if "column_widths" in saved:
                    col_w = DEFAULT_SETTINGS["column_widths"].copy()
                    col_w.update(saved["column_widths"])
                    res["column_widths"] = col_w
                return res
        except Exception as e:
            print(f"Error loading settings: {e}")
    return DEFAULT_SETTINGS.copy()

def save_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving settings: {e}")

def get_remembered_folder(category: str = "Other") -> str:
    s = load_settings()
    dirs = s.get("remembered_dirs", {})
    folder = dirs.get(category)
    if folder and os.path.isdir(folder):
        return folder
    return s.get("default_dir", DEFAULT_DOWNLOAD_DIR)

def set_remembered_folder(category: str, folder_path: str):
    if not folder_path or not os.path.isdir(folder_path):
        return
    s = load_settings()
    if "remembered_dirs" not in s:
        s["remembered_dirs"] = {}
    s["remembered_dirs"][category] = os.path.abspath(folder_path)
    if category in ("Other", "General"):
        s["default_dir"] = os.path.abspath(folder_path)
    save_settings(s)

def get_default_connections() -> int:
    s = load_settings()
    return int(s.get("default_connections", 32))

def set_default_connections(conns: int):
    s = load_settings()
    s["default_connections"] = int(conns)
    save_settings(s)

def get_column_widths() -> dict:
    s = load_settings()
    return s.get("column_widths", DEFAULT_SETTINGS["column_widths"].copy())

def set_column_widths(widths: dict):
    s = load_settings()
    s["column_widths"] = widths
    save_settings(s)
