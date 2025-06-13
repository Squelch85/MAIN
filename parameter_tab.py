import tkinter as tk
from tkinter import ttk
import os
import hashlib
from collections import OrderedDict

class ParameterTab(ttk.Frame):
    def __init__(self, master, file_path):
        super().__init__(master)
        self.file_path = file_path
        self.sections = OrderedDict()
        self.last_file_hash = None
        self.widget_registry = {}
        self.section_states = {}
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

        # enable mouse wheel scrolling anywhere inside the tab
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)

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

        # placeholder for potential width calculations
        self.max_label_len = max(
            (len(key) for params in self.sections.values() for key in params),
            default=0,
        )

    def refresh_ui(self):
        for widget in self.scrollable_content.winfo_children():
            widget.destroy()
        self.widget_registry.clear()

        for sec_index, (section, params) in enumerate(self.sections.items()):
            outer = ttk.Frame(self.scrollable_content, borderwidth=2, relief="groove")
            outer.grid(row=sec_index, column=0, sticky="nsew", padx=5, pady=5)
            header = ttk.Frame(outer)
            header.grid(row=0, column=0, sticky="ew")
            outer.columnconfigure(0, weight=1)
            header.columnconfigure(1, weight=1)

            collapsed = self.section_states.get(section, False)
            toggle_btn = ttk.Button(
                header,
                text="+" if collapsed else "-",
                width=2,
                command=lambda s=section: self.toggle_section(s),
            )
            toggle_btn.grid(row=0, column=0)

            ttk.Label(header, text=section, font=("Arial", 9, "bold")).grid(
                row=0, column=1, sticky="w", padx=(4, 0)
            )

            up_btn = ttk.Button(
                header, text="\u2191", width=2, command=lambda s=section: self.move_section_up(s)
            )
            up_btn.grid(row=0, column=2, padx=(4, 0))

            down_btn = ttk.Button(
                header, text="\u2193", width=2, command=lambda s=section: self.move_section_down(s)
            )
            down_btn.grid(row=0, column=3, padx=(2, 0))

            params_frame = ttk.Frame(outer)
            params_frame.grid(row=1, column=0, sticky="nsew")

            self.widget_registry[section] = {
                "frame": outer,
                "params_frame": params_frame,
                "params": {},
                "toggle": toggle_btn,
            }

            if collapsed:
                params_frame.grid_remove()

            for index, (param_name, param_value) in enumerate(params.items()):
                self.create_parameter_widget(section, index, param_name, param_value)
        self.layout_parameters()

    def create_parameter_widget(self, section, index, param_name, param_value):
        section_info = self.widget_registry[section]
        row, column = divmod(index, self.grid_columns)
        container = section_info["params_frame"]
        parameter_frame = ttk.Frame(container, borderwidth=1, relief="solid")
        parameter_frame.grid(row=row, column=column, padx=4, pady=4, sticky="nsew")

        ttk.Label(
            parameter_frame,
            text=param_name,
            font=("Arial", 8, "bold"),
            anchor=tk.W,
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W)

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
            self.canvas.config(scrollregion=bbox)

    def _on_mousewheel(self, event):
        if hasattr(event, 'delta') and event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def on_resize(self, event):
        new_cols = max(1, event.width // 120)
        if new_cols != self.grid_columns:
            self.grid_columns = new_cols
            self.layout_parameters()
            self.adjust_window_size()

    def layout_parameters(self):
        for section, info in self.widget_registry.items():
            container = info["params_frame"]
            for i in range(self.grid_columns):
                container.columnconfigure(i, weight=1, uniform="param_cols")
            for index, param_name in enumerate(self.sections[section].keys()):
                frame = info["params"][param_name][0]
                row, column = divmod(index, self.grid_columns)
                frame.grid_configure(row=row, column=column, sticky="nsew")

    def toggle_section(self, section):
        info = self.widget_registry.get(section)
        if not info:
            return
        collapsed = self.section_states.get(section, False)
        if collapsed:
            info["params_frame"].grid()
            info["toggle"].config(text="-")
        else:
            info["params_frame"].grid_remove()
            info["toggle"].config(text="+")
        self.section_states[section] = not collapsed
        self.adjust_window_size()

    def move_section_up(self, section):
        keys = list(self.sections.keys())
        idx = keys.index(section)
        if idx > 0:
            keys[idx - 1], keys[idx] = keys[idx], keys[idx - 1]
            self.sections = OrderedDict((k, self.sections[k]) for k in keys)
            self.refresh_ui()
            self.adjust_window_size()

    def move_section_down(self, section):
        keys = list(self.sections.keys())
        idx = keys.index(section)
        if idx < len(keys) - 1:
            keys[idx + 1], keys[idx] = keys[idx], keys[idx + 1]
            self.sections = OrderedDict((k, self.sections[k]) for k in keys)
            self.refresh_ui()
            self.adjust_window_size()


