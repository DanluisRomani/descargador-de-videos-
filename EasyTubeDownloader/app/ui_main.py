# app/ui_main.py
import customtkinter as ctk
import threading
import os
from . import downloader, utils, settings
from tkinter import messagebox, filedialog

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MainWindow:
    def __init__(self):
        self.settings = settings.load_settings()
        self.root = ctk.CTk()
        self.root.title("Miko Downloader")
        self.root.geometry("520x320")
        self.root.resizable(False, False)

        # --- Widgets principales ---
        self.label_title = ctk.CTkLabel(
            self.root, text="Miko Downloader",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.label_title.pack(pady=(12,6))

        self.entry_url = ctk.CTkEntry(
            self.root, placeholder_text="Pega el enlace de YouTube aquí..."
        )
        self.entry_url.pack(fill="x", padx=24, pady=(6,6))

        # --- Selección de formato ---
        self.frame_options = ctk.CTkFrame(self.root)
        self.frame_options.pack(fill="x", padx=24, pady=(4,4))

        self.format_var = ctk.StringVar(
            value=self.settings.get("default_format", "mp3")
        )
        self.radio_mp3 = ctk.CTkRadioButton(
            self.frame_options, text="MP3 (Audio)",
            variable=self.format_var, value="mp3"
        )
        self.radio_mp4 = ctk.CTkRadioButton(
            self.frame_options, text="MP4 (Video)",
            variable=self.format_var, value="mp4"
        )
        self.radio_mp3.grid(row=0, column=0, padx=8, pady=8)
        self.radio_mp4.grid(row=0, column=1, padx=8, pady=8)

        # --- Carpeta de destino ---
        # Si hay una carpeta guardada, usarla; sino, la predeterminada (Descargas)
        self.download_path = self.settings.get("last_download_path", settings.get_download_path())

        self.label_path = ctk.CTkLabel(
            self.root, text=f"Destino: {self.download_path}", anchor="w"
        )
        self.label_path.pack(fill="x", padx=24, pady=(2,2))

        self.btn_change_folder = ctk.CTkButton(
            self.root, text="Cambiar carpeta", command=self.change_folder
        )
        self.btn_change_folder.pack(padx=24, pady=(4,6))

        # --- Botones principales ---
        self.frame_buttons = ctk.CTkFrame(self.root)
        self.frame_buttons.pack(fill="x", padx=24, pady=(6,6))

        self.btn_download = ctk.CTkButton(
            self.frame_buttons, text="Descargar", command=self.on_download_click
        )
        self.btn_download.grid(row=0, column=0, padx=6)

        self.btn_advanced = ctk.CTkButton(
            self.frame_buttons, text="Modo avanzado", command=self.open_advanced
        )
        self.btn_advanced.grid(row=0, column=1, padx=6)

        # --- Progreso y estado ---
        self.progress = ctk.CTkProgressBar(self.root)
        self.progress.set(0.0)
        self.progress.pack(fill="x", padx=24, pady=(8,4))

        self.label_status = ctk.CTkLabel(self.root, text="Listo")
        self.label_status.pack(pady=(2,12))

    # --- Métodos de funcionalidad ---

    def change_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = folder
            self.label_path.configure(text=f"Destino: {self.download_path}")
            # guardar la carpeta elegida para recordarla después
            self.settings["last_download_path"] = folder
            settings.save_settings(self.settings)

    def run(self):
        self.root.mainloop()

    def set_status(self, text: str):
        self.label_status.configure(text=text)

    def progress_hook(self, d):
        """Actualiza la UI según el progreso del downloader"""
        status = d.get('status')
        if status == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total:
                try:
                    fraction = downloaded / total
                except Exception:
                    fraction = 0.0
                self.progress.set(fraction)
                self.set_status(f"Descargando... {int(fraction*100)}%")
            else:
                self.set_status(f"Descargando... {utils.human_size(downloaded)}")
        elif status == 'finished':
            self.progress.set(1.0)
            self.set_status("Descarga completada")
        elif status == 'error':
            self.set_status("Error durante la descarga")

    def on_download_click(self):
        url = self.entry_url.get().strip()
        if not url:
            messagebox.showerror("Error", "Pega un enlace de YouTube válido.")
            return
        if not utils.is_youtube_url(url):
            messagebox.showerror("Error", "El enlace no parece ser de YouTube.")
            return

        mode = self.format_var.get()  # 'mp3' o 'mp4'
        self.btn_download.configure(state="disabled")
        self.set_status("Preparando descarga...")
        self.progress.set(0.0)

        # Descargar en hilo separado (no bloquea interfaz)
        def worker():
            success, error = downloader.download(
                url, mode, self.download_path,
                selected_format=None, progress_callback=self.progress_hook
            )
            if success:
                messagebox.showinfo(
                    "Completado",
                    f"Descarga finalizada.\nArchivo guardado en: {self.download_path}"
                )
            else:
                messagebox.showerror("Error", f"Ocurrió un error:\n{error}")
            self.btn_download.configure(state="normal")
            self.set_status("Listo")
            self.progress.set(0.0)

        threading.Thread(target=worker, daemon=True).start()

    def open_advanced(self):
        from .ui_advanced import AdvancedWindow
        AdvancedWindow(parent=self.root)
