import tkinter as tk
from tkinter import ttk
import os
from collections import OrderedDict
from config_io import compute_file_hash, load_parameters, save_parameters

class ParameterTab(ttk.Frame):
    def __init__(self, master, file_path, initial_state=None):
        super().__init__(master)
        self.file_path = file_path
        self.sections = OrderedDict()
        self.last_file_hash = None
        self.widget_registry = {}
        self.section_states = (initial_state or {}).get("collapsed", {})
        self._saved_order = (initial_state or {}).get("order")
        # 초기 열 개수, 창 크기에 맞춰 조정됩니다
        self.grid_columns = 4

        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_content = ttk.Frame(self.canvas)

        self.scrollable_content.bind(
            "<Configure>",
            lambda e: self.adjust_window_size()
        )

        # canvas에 올려질 프레임의 ID를 저장해 이후 사이즈 조정에 사용
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_content, anchor="nw"
        )
        # 캔버스 크기가 변하면 내부 프레임의 너비도 함께 조정
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self.canvas_window, width=e.width),
        )
        self.scrollable_content.columnconfigure(0, weight=1)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 탭 내부 어디서나 마우스 휠 스크롤을 허용
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)

        # 창 크기 변화를 감지해 레이아웃을 재계산
        self._padding = 0
        self._padding_initialized = False
        self.winfo_toplevel().bind("<Configure>", self.on_resize)

        self.load_parameters()

    def load_parameters(self):
        self.last_file_hash = compute_file_hash(self.file_path)
        self.sections = load_parameters(self.file_path)
        if self._saved_order:
            ordered = OrderedDict()
            for sec in self._saved_order:
                if sec in self.sections:
                    ordered[sec] = self.sections[sec]
            for sec in self.sections:
                if sec not in ordered:
                    ordered[sec] = self.sections[sec]
            self.sections = ordered
        self.max_label_len = max(
            (len(key) for params in self.sections.values() for key in params),
            default=0,
        )
        self.refresh_ui()
        self.adjust_window_size()
        self.after(100, self.monitor_file_changes)

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
        save_parameters(self.file_path, self.sections)

    def update_parameter_value(self, section, param_name, param_value):
        self.sections[section][param_name] = param_value
        self.update_parameter_widget(section, param_name, param_value)
        save_parameters(self.file_path, self.sections)

    def monitor_file_changes(self):
        if not self.file_path:
            return
        file_size = os.path.getsize(self.file_path)
        interval = 1000 if file_size < 1024 * 10 else 2000
        current_hash = compute_file_hash(self.file_path)
        if current_hash != self.last_file_hash:
            self.sections = load_parameters(self.file_path)
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
        toplevel = self.winfo_toplevel()

        if event.widget is not toplevel:
            return

        if not self._padding_initialized:
            self._padding = event.width - self.winfo_width()
            self._padding_initialized = True

        new_cols = max(1, (event.width - self._padding) // 120)

        # 캔버스의 윈도우 폭을 현재 캔버스 폭에 맞춤
        self.canvas.itemconfigure(self.canvas_window, width=self.canvas.winfo_width())

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
            save_parameters(self.file_path, self.sections)

    def move_section_down(self, section):
        keys = list(self.sections.keys())
        idx = keys.index(section)
        if idx < len(keys) - 1:
            keys[idx + 1], keys[idx] = keys[idx], keys[idx + 1]
            self.sections = OrderedDict((k, self.sections[k]) for k in keys)
            self.refresh_ui()
            self.adjust_window_size()
            save_parameters(self.file_path, self.sections)

    def get_state(self):
        """섹션 접힘 상태와 순서를 저장하기 위한 딕셔너리를 반환합니다."""
        return {
            "collapsed": self.section_states,
            "order": list(self.sections.keys()),
        }


