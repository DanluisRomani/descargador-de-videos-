import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import threading
from . import downloader, settings, utils

class AdvancedWindow(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Modo Avanzado - EasyTube")
        self.geometry("950x650")
        self.minsize(1000, 800)
        self.resizable(True, True)

        # Variables
        self.url_var = ctk.StringVar()
        self.download_folder = settings.load_settings().get("last_download_path", settings.get_download_path())
        self.formats_video = []
        self.formats_audio = []
        self.filtered_video = []
        self.filtered_audio = []
        self.selected_format_id = None

        # --- Entrada de enlace ---
        ctk.CTkLabel(self, text="Enlace de YouTube:").pack(anchor="w", padx=12, pady=(12, 4))
        entry = ctk.CTkEntry(self, textvariable=self.url_var, width=640)
        entry.pack(padx=12, pady=(0, 8))

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkButton(btn_frame, text="Detectar formatos", command=self.on_detect).grid(row=0, column=0, padx=6, pady=6)
        ctk.CTkButton(btn_frame, text="Cambiar carpeta destino", command=self.change_folder).grid(row=0, column=1, padx=6, pady=6)

        self.label_folder = ctk.CTkLabel(self, text=f"Destino: {self.download_folder}", anchor="w")
        self.label_folder.pack(fill="x", padx=12, pady=(0, 6))

        # --- Tabs (Video / Audio) ---
        self.tabview = ctk.CTkTabview(self, width=880, height=460)
        self.tabview.pack(padx=12, pady=10, fill="both", expand=True)

        self.tab_video = self.tabview.add("Formatos de Video")
        self.tab_audio = self.tabview.add("Formatos de Audio")

        # TAB VIDEO
        self.filter_var_video = ctk.StringVar(value="Todos")
        self._create_filter_section(self.tab_video, self.filter_var_video, self.apply_filter_video)

        self.tree_video = self._create_tree(self.tab_video)
        self.tree_video.bind("<<TreeviewSelect>>", self.on_select_format_video)

        # TAB AUDIO
        self.filter_var_audio = ctk.StringVar(value="Todos")
        self._create_filter_section(self.tab_audio, self.filter_var_audio, self.apply_filter_audio)

        self.tree_audio = self._create_tree(self.tab_audio)
        self.tree_audio.bind("<<TreeviewSelect>>", self.on_select_format_audio)

        # --- Parte inferior ---  
        frame_bottom = ctk.CTkFrame(self)
        frame_bottom.pack(fill="x", padx=12, pady=(6, 12))

        self.btn_download = ctk.CTkButton(
            frame_bottom,
            text="⬇ Descargar formato seleccionado",
            fg_color="#0078D7",
            hover_color="#005A9E",
            command=self.on_download
        )
        self.btn_download.pack(side="left", padx=6, pady=4)

        # Etiqueta de estado
        self.label_status = ctk.CTkLabel(frame_bottom, text="Listo", width=200)
        self.label_status.pack(side="right", padx=6, pady=4)

        # --- BARRA DE PROGRESO ---
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 12))

        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Progreso: 0%", anchor="w")
        self.progress_label.pack(anchor="w", padx=6)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=6, pady=(4, 0))

    # ---------------------------
    # Construcción de interfaz
    # ---------------------------

    def _create_filter_section(self, parent, var, command):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=12, pady=(4, 0))
        ctk.CTkLabel(frame, text="Filtrar por calidad:").pack(side="left", padx=(6, 4))
        ctk.CTkOptionMenu(frame, values=["Todos", "Alta", "Media", "Baja"], variable=var, command=command).pack(side="left", padx=(0, 6))

    def _create_tree(self, parent):
        container = ctk.CTkFrame(parent)
        container.pack(fill="both", expand=True, padx=6, pady=6)

        tree = ttk.Treeview(
            container,
            columns=("ID", "Tipo", "Resolución", "Códecs", "Tamaño", "Recomendado"),
            show="headings"
        )
        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        for col in ("ID", "Tipo", "Resolución", "Códecs", "Tamaño", "Recomendado"):
            tree.heading(col, text=col, command=lambda c=col, t=tree: self.sort_by(t, c, False))
            tree.column(col, width=130, anchor="center")

        return tree

    # ---------------------------
    # Funciones principales
    # ---------------------------

    def change_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_folder)
        if folder:
            self.download_folder = folder
            self.label_folder.configure(text=f"Destino: {self.download_folder}")
            s = settings.load_settings()
            s["last_download_path"] = folder
            settings.save_settings(s)

    def get_recommendation(self, res, size):
        try:
            if "x" in res:
                w, h = map(int, res.split("x"))
            else:
                h = 0
            mb = utils.size_to_mb(size)
            if h >= 1080 and mb <= 150:
                return "Alta"
            elif h >= 720 and mb <= 100:
                return "Media"
            else:
                return "Baja"
        except:
            return "Baja"

    def on_detect(self):
        url = self.url_var.get().strip()
        if not url or not utils.is_youtube_url(url):
            messagebox.showerror("Error", "Pega un enlace de YouTube válido.")
            return

        self.label_status.configure(text="Obteniendo formatos...")

        for tree in (self.tree_video, self.tree_audio):
            for item in tree.get_children():
                tree.delete(item)

        def worker():
            try:
                all_formats = downloader.get_formats(url)
                self.formats_video = [f for f in all_formats if f["vcodec"] != "none"]
                self.formats_audio = [f for f in all_formats if f["vcodec"] == "none"]
                self.filtered_video = self.formats_video.copy()
                self.filtered_audio = self.formats_audio.copy()
                self.refresh_trees()
                total = len(self.formats_video) + len(self.formats_audio)
                self.label_status.configure(text=f"Formatos detectados: {total}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo obtener formatos:\n{e}")
                self.label_status.configure(text="Error")

        threading.Thread(target=worker, daemon=True).start()

    def refresh_trees(self):
        for tree, formats in ((self.tree_video, self.filtered_video), (self.tree_audio, self.filtered_audio)):
            for item in tree.get_children():
                tree.delete(item)

            for f in formats:
                tipo = "Video" if f in self.formats_video else "Audio"
                resol = f.get("resolution") or "-"
                codecs = f"{f.get('vcodec', '-')}/{f.get('acodec', '-')}" if tipo == "Video" else f.get('acodec', '-')
                size = utils.human_size(f["filesize"]) if f.get("filesize") else "Desconocido"
                recom = self.get_recommendation(resol, size) if tipo == "Video" else ("Alta" if "m4a" in f["ext"] or "opus" in codecs else "Media")
                tree.insert("", "end", values=(f["format_id"], tipo, resol, codecs, size, recom))

    def apply_filter_video(self, selection):
        if selection == "Todos":
            self.filtered_video = self.formats_video.copy()
        else:
            self.filtered_video = [f for f in self.formats_video if self.get_recommendation(f.get("resolution","-"), utils.human_size(f.get("filesize",0))) == selection]
        self.refresh_trees()

    def apply_filter_audio(self, selection):
        if selection == "Todos":
            self.filtered_audio = self.formats_audio.copy()
        else:
            self.filtered_audio = [f for f in self.formats_audio if ("m4a" in f["ext"] or "opus" in f.get("acodec","")) and selection=="Alta"]
        self.refresh_trees()

    def sort_by(self, tree, col, descending):
        data = [(tree.set(child, col), child) for child in tree.get_children('')]
        if col in ("Resolución", "Tamaño"):
            def key_func(v):
                try:
                    if col == "Resolución":
                        parts = v[0].split('x')
                        return int(parts[1]) if len(parts) > 1 else 0
                    elif col == "Tamaño":
                        return utils.size_to_mb(v[0])
                except:
                    return 0
            data.sort(key=key_func, reverse=descending)
        else:
            data.sort(reverse=descending)

        for idx, item in enumerate(data):
            tree.move(item[1], '', idx)
        tree.heading(col, command=lambda: self.sort_by(tree, col, not descending))

    # ---------------------------
    # Selección y descarga
    # ---------------------------

    def on_select_format_video(self, event):
        selected = self.tree_video.focus()
        if selected:
            values = self.tree_video.item(selected, "values")
            if values:
                self.selected_format_id = values[0]
                self.selected_type = "video"
                self.label_status.configure(text=f"Seleccionado formato VIDEO ID: {self.selected_format_id}")

    def on_select_format_audio(self, event):
        selected = self.tree_audio.focus()
        if selected:
            values = self.tree_audio.item(selected, "values")
            if values:
                self.selected_format_id = values[0]
                self.selected_type = "audio"
                self.label_status.configure(text=f"Seleccionado formato AUDIO ID: {self.selected_format_id}")

    # ---------------------------
    # DESCARGA CON PROGRESO
    # ---------------------------

    def on_download(self):
        if not hasattr(self, "selected_type") or not self.selected_format_id:
            messagebox.showerror("Error", "Selecciona un formato antes de descargar.")
            return

        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Pega un enlace de YouTube válido.")
            return

        self.btn_download.configure(state="disabled")
        self.label_status.configure(text="Descargando...")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Progreso: 0%")

        def progress_hook(d):
            if d.get("status") == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes", 0)
                percent = (downloaded / total) if total > 0 else 0

                speed = d.get("speed", 0)
                eta = d.get("eta", 0)

                self.progress_bar.set(percent)
                percent_text = f"{percent * 100:.1f}%"
                speed_text = utils.human_size(speed) + "/s" if speed else "-"
                eta_text = f"{eta:.0f}s restantes" if eta else "calculando..."
                self.progress_label.configure(
                    text=f"Progreso: {percent_text} | Vel: {speed_text} | ETA: {eta_text}"
                )

            elif d.get("status") == "finished":
                self.progress_bar.set(1.0)
                self.progress_label.configure(text="Progreso: 100% - Completado ✅")
                self.label_status.configure(text="Descarga terminada")

        def worker():
            formats = self.formats_video if self.selected_type == "video" else self.formats_audio
            tipo = next((f for f in formats if f["format_id"] == self.selected_format_id), None)
            mode = "mp3" if self.selected_type == "audio" else "mp4"

            success, error = downloader.download(
                url, mode, self.download_folder,
                selected_format=self.selected_format_id,
                progress_callback=progress_hook
            )

            if success:
                messagebox.showinfo("Completado", f"Descarga finalizada.\nArchivos en:\n{self.download_folder}")
            else:
                messagebox.showerror("Error", error)

            self.btn_download.configure(state="normal")
            self.label_status.configure(text="Listo")
            self.progress_label.configure(text="Progreso: 0%")
            self.progress_bar.set(0)

        threading.Thread(target=worker, daemon=True).start()
