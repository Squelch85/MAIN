import tkinter as tk
from tkinter import ttk, filedialog
import os
import hashlib
import json
from collections import OrderedDict


class ParameterTab(ttk.Frame):
    def __init__(self, master, file_path):
        super().__init__(master)
        self.file_path = file_path
        self.sections = OrderedDict()
        self.last_file_hash = None
        self.widget_registry = {}
        # initial column count; will adjust on resize
        self.grid_columns = 4

        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_content = ttk.Frame(self.canvas)

        self.scrollable_content.bind(
            "<Configure>",
            lambda e: self.adjust_window_size()
        )

        self.canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")
        self.scrollable_content.columnconfigure(0, weight=1)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # track size changes to recompute layout
        self.bind("<Configure>", self.on_resize)

        self.load_parameters()

    def compute_file_hash(self):
        if not self.file_path:
            return None
        try:
            with open(self.file_path, "rb") as file:
                return hashlib.md5(file.read()).hexdigest()
        except FileNotFoundError:
            return None

    def load_parameters(self):
        self.last_file_hash = self.compute_file_hash()
        self.load_parameters_from_file()
        self.refresh_ui()
        self.adjust_window_size()
        self.after(100, self.monitor_file_changes)

    def load_parameters_from_file(self):
        if not self.file_path:
            return
        self.sections.clear()
        current_section = "DEFAULT"
        self.sections[current_section] = OrderedDict()
        with open(self.file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith(("#", ";")):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1].strip()
                    self.sections[current_section] = OrderedDict()
                elif "=" in line:
                    key, value = map(str.strip, line.split("=", 1))
                    self.sections.setdefault(current_section, OrderedDict())[key] = value

    def refresh_ui(self):
        for widget in self.scrollable_content.winfo_children():
            widget.destroy()
        self.widget_registry.clear()

        for sec_index, (section, params) in enumerate(self.sections.items()):
            section_frame = ttk.LabelFrame(self.scrollable_content, text=section)
            section_frame.grid(row=sec_index, column=0, sticky="nsew", padx=5, pady=5)
            self.widget_registry[section] = {"frame": section_frame, "params": {}}

            for index, (param_name, param_value) in enumerate(params.items()):
                self.create_parameter_widget(section, index, param_name, param_value)
        self.layout_parameters()

    def create_parameter_widget(self, section, index, param_name, param_value):
        section_info = self.widget_registry[section]
        row, column = divmod(index, self.grid_columns)
        parameter_frame = ttk.Frame(section_info["frame"], borderwidth=1, relief="solid")
        parameter_frame.grid(row=row, column=column, padx=4, pady=4, sticky="nsew")

        ttk.Label(parameter_frame, text=param_name, font=("Arial", 8, "bold")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W
        )

        toggle_button = tk.Button(
            parameter_frame,
            text="ON" if param_value == "1" else "OFF",
            bg="green" if param_value == "1" else "red",
            fg="white",
            font=("Arial", 8, "bold"),
            width=4,
            command=lambda: self.toggle_parameter_value(section, param_name),
        )
        toggle_button.grid(row=1, column=0)

        value_entry = ttk.Entry(parameter_frame, width=8)
        value_entry.insert(0, param_value)
        value_entry.bind(
            "<Return>",
            lambda e: self.update_parameter_value(section, param_name, value_entry.get()),
        )
        value_entry.grid(row=1, column=1)

        section_info["params"][param_name] = (parameter_frame, toggle_button, value_entry)

    def update_parameter_widget(self, section, param_name, param_value):
        parameter_frame, toggle_button, value_entry = self.widget_registry[section]["params"][param_name]
        toggle_button.config(
            text="ON" if param_value == "1" else "OFF",
            bg="green" if param_value == "1" else "red",
            fg="white",
            font=("Arial", 8, "bold"),
            width=4,
        )
        value_entry.delete(0, tk.END)
        value_entry.insert(0, param_value)

    def toggle_parameter_value(self, section, param_name):
        current = self.sections[section][param_name]
        self.sections[section][param_name] = "0" if current == "1" else "1"
        self.update_parameter_widget(section, param_name, self.sections[section][param_name])
        self.save_parameters_to_file()

    def update_parameter_value(self, section, param_name, param_value):
        self.sections[section][param_name] = param_value
        self.update_parameter_widget(section, param_name, param_value)
        self.save_parameters_to_file()

    def save_parameters_to_file(self):
        if not self.file_path:
            return
        with open(self.file_path, "w", encoding="utf-8") as file:
            for section, params in self.sections.items():
                if section != "DEFAULT":
                    file.write(f"[{section}]\n")
                for key, value in params.items():
                    file.write(f"{key}={value}\n")
                file.write("\n")

    def monitor_file_changes(self):
        if not self.file_path:
            return
        file_size = os.path.getsize(self.file_path)
        interval = 1000 if file_size < 1024 * 10 else 2000
        current_hash = self.compute_file_hash()
        if current_hash != self.last_file_hash:
            self.load_parameters_from_file()
            self.refresh_ui()
            self.last_file_hash = current_hash
        self.after(interval, self.monitor_file_changes)

    def adjust_window_size(self):
        self.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            self.canvas.config(scrollregion=bbox, width=width, height=height)

    def on_resize(self, event):
        new_cols = max(1, event.width // 120)
        if new_cols != self.grid_columns:
            self.grid_columns = new_cols
            self.layout_parameters()
            self.adjust_window_size()

    def layout_parameters(self):
        for section, info in self.widget_registry.items():
            section_frame = info["frame"]
            for i in range(self.grid_columns):
                section_frame.columnconfigure(i, weight=1)
            for index, param_name in enumerate(self.sections[section].keys()):
                frame = info["params"][param_name][0]
                row, column = divmod(index, self.grid_columns)
                frame.grid_configure(row=row, column=column, sticky="nsew")


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


if __name__ == "__main__":
    app_root = tk.Tk()
    app_root.title("Parameter Manager")
    gui = ParameterManagerGUI(app_root)
    app_root.mainloop()