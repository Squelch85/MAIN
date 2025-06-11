import os
import tkinter as tk
from tkinter import ttk, filedialog
import json
from parameter_tab import ParameterTab

class ParameterManagerGUI:
    def __init__(self, root_window):
        self.root_window = root_window
        self.state_path = os.path.join(os.path.dirname(__file__), "state.json")
        self.open_files = []
        self.saved_geometry = None
        self.load_state()

        self.notebook = ttk.Notebook(self.root_window)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<Button-3>", self.show_tab_menu)

        self.tab_menu = tk.Menu(self.notebook, tearoff=0)
        self.tab_menu.add_command(label="Close", command=self.close_current_tab)

        self.tabs = {}
        self.initialize_menu()

        if self.saved_geometry:
            self.root_window.geometry(self.saved_geometry)
        for f in self.open_files:
            if os.path.exists(f):
                self._open_file(f)
        self.root_window.protocol("WM_DELETE_WINDOW", self.on_close)

    def initialize_menu(self):
        menu_bar = tk.Menu(self.root_window)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open File(s)", command=self.open_files_dialog)
        file_menu.add_command(label="Exit", command=self.on_close)
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.root_window.config(menu=menu_bar)

    def load_state(self):
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.saved_geometry = data.get("geometry")
                    self.open_files = data.get("files", [])
            except Exception:
                self.saved_geometry = None
                self.open_files = []

    def save_state(self):
        state = {
            "geometry": self.root_window.geometry(),
            "files": list(self.tabs.keys()),
        }
        try:
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(state, f)
        except Exception:
            pass

    def open_files_dialog(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Data Files",
            filetypes=(("INI Files", "*.ini"), ("All Files", "*.*")),
        )
        for file_path in file_paths:
            if file_path and file_path not in self.tabs:
                self._open_file(file_path)

    def show_tab_menu(self, event):
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
            self.notebook.select(index)
            self._tab_index_for_menu = index
            self.tab_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.tab_menu.grab_release()

    def close_current_tab(self):
        index = getattr(self, "_tab_index_for_menu", None)
        if index is None:
            return
        tab_id = self.notebook.tabs()[index]
        tab = self.notebook.nametowidget(tab_id)
        file_path = None
        for path, t in list(self.tabs.items()):
            if t == tab:
                file_path = path
                del self.tabs[path]
                break
        self.notebook.forget(index)
        if file_path in self.open_files:
            self.open_files.remove(file_path)

    def on_close(self):
        self.save_state()
        self.root_window.destroy()

    def _open_file(self, file_path):
        tab = ParameterTab(self.notebook, file_path)
        self.notebook.add(tab, text=os.path.basename(file_path))
        self.tabs[file_path] = tab
        tab.adjust_window_size()
        if file_path not in self.open_files:
            self.open_files.append(file_path)

