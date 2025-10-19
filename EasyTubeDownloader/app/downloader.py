# app/downloader.py
import yt_dlp
import os
from typing import Tuple, Optional, List, Dict


def get_video_info(url: str) -> dict:
    """Extrae información del video intentando usar cookies (firefox) y fallback a cookiefile."""
    base_opts = {
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        }
    }

    cookiefile_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')

    # 1) Intentar con cookies desde Firefox
    opts = base_opts.copy()
    opts['cookies_from_browser'] = 'firefox'
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception:
        pass

    # 2) Fallback: usar cookiefile si existe
    if os.path.exists(cookiefile_path):
        opts = base_opts.copy()
        opts['cookiefile'] = cookiefile_path
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception:
            pass

    # 3) Último intento sin cookies (puede fallar si YouTube exige login)
    opts = base_opts.copy()
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        raise Exception(
            "No se pudo obtener info del video. YouTube solicita autenticación.\n"
            "Soluciones:\n"
            " • Exporta cookies desde Firefox a app/cookies.txt y vuelve a intentarlo.\n"
            " • O asegúrate de estar logueado en Firefox y que yt-dlp pueda leer cookies (--cookies-from-browser firefox).\n"
            f"Detalles: {e}"
        )


def get_formats(url: str) -> List[Dict]:
    """Retorna una lista de formatos disponibles con información relevante."""
    info = get_video_info(url)
    formats = info.get('formats', [])
    result = []
    for f in formats:
        result.append({
            'format_id': f.get('format_id'),
            'ext': f.get('ext'),
            'resolution': (
                f.get('resolution')
                or (f"{f.get('width')}x{f.get('height')}" if f.get('width') else 'audio only')
            ),
            'fps': f.get('fps'),
            'acodec': f.get('acodec'),
            'vcodec': f.get('vcodec'),
            'filesize': f.get('filesize') or f.get('filesize_approx'),
            'tbr': f.get('tbr'),
            'format_note': f.get('format_note'),
        })
    return result


def select_best_audio_format(info: dict) -> str:
    """
    Selecciona el mejor formato de audio con prioridad por compatibilidad.
    Retorna el 'format_id' más adecuado.
    """
    preferred_exts = ['mp3', 'm4a', 'aac', 'ogg', 'opus', 'webm']
    audio_formats = [
        f for f in info.get('formats', [])
        if f.get('vcodec') == 'none' and f.get('acodec') != 'none'
    ]

    # Filtrar por preferencia de extensión
    for ext in preferred_exts:
        best = next((f for f in sorted(audio_formats, key=lambda x: x.get('abr', 0), reverse=True)
                     if f.get('ext') == ext), None)
        if best:
            return best.get('format_id')

    # Fallback al mejor audio general
    if audio_formats:
        return max(audio_formats, key=lambda f: f.get('abr', 0) or 0).get('format_id')

    return None


def download(url: str, mode: str, target_folder: str, selected_format: str = None, progress_callback=None):
    """Descarga el video/audio."""
    os.makedirs(target_folder, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best' if mode == 'mp3' else 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(target_folder, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_callback] if progress_callback else None,
        'cookies_from_browser': 'firefox',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        }
    }

    # Agregar postprocessors según el modo
    if mode == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True, None
    except Exception as e:
        return False, str(e)
