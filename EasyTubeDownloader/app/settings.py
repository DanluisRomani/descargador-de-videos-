# app/settings.py
import json
import os
from pathlib import Path

DEFAULTS = {
    "download_path": "",        # si está vacío usamos la carpeta Descargas del sistema
    "default_format": "mp3",    # 'mp3' o 'mp4'
    "last_mode": "basic"        # 'basic' o 'advanced'
}

CONFIG_FILE = Path.home() / ".easytube_settings.json"

def load_settings():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # merge defaults with saved
            conf = DEFAULTS.copy()
            conf.update(data)
            return conf
        except Exception:
            return DEFAULTS.copy()
    else:
        return DEFAULTS.copy()

def save_settings(settings: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Error saving settings:", e)

def get_download_path():
    settings = load_settings()
    path = settings.get("download_path") or ""
    if path:
        return os.path.abspath(path)
    # fallback to system Downloads
    from os.path import expanduser, join
    home = expanduser("~")
    # cross-platform common download folder
    possible = [
        join(home, "Downloads"),
        join(home, "Descargas"),
        join(home, "downloads"),
    ]
    for p in possible:
        if os.path.isdir(p):
            return p
    # otherwise home folder
    return home
