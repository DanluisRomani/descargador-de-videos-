# app/utils.py
import re
import os
from pathlib import Path

# --- Expresión regular para validar enlaces de YouTube ---
YOUTUBE_REGEX = re.compile(
    r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
)

def is_youtube_url(url: str) -> bool:
    """Verifica si una URL es válida de YouTube."""
    return bool(url and YOUTUBE_REGEX.match(url.strip()))

def ensure_folder(path: str):
    """Crea una carpeta si no existe."""
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"[ERROR] No se pudo crear la carpeta: {e}")

def human_size(bytesize: int) -> str:
    """Convierte bytes a un formato legible (KB, MB, GB...)."""
    if bytesize is None:
        return "Desconocido"
    try:
        b = float(bytesize)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if b < 1024.0:
                return f"{b:3.1f}{unit}"
            b /= 1024.0
        return f"{b:.1f}PB"
    except Exception:
        return "Desconocido"

def size_to_mb(size_str: str) -> float:
    """
    Convierte una cadena de tamaño (ej: '24.3MB', '512KB', '1.2GB')
    a un valor numérico en MB para poder ordenar correctamente.
    """
    if not size_str or not isinstance(size_str, str):
        return 0.0

    try:
        size_str = size_str.strip().upper()

        if "MB" in size_str:
            return float(size_str.replace("MB", "").strip())
        elif "KB" in size_str:
            return float(size_str.replace("KB", "").strip()) / 1024
        elif "GB" in size_str:
            return float(size_str.replace("GB", "").strip()) * 1024
        elif "B" in size_str:
            return float(size_str.replace("B", "").strip()) / (1024 * 1024)
        else:
            return float(size_str)  # Si no hay unidad, intenta parsear directo
    except ValueError:
        return 0.0
