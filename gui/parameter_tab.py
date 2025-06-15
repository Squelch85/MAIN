import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
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
        # 줌 배율과 기본 폰트/셀 크기 설정
        self.zoom = 1.0
        self.base_cell_width = int(120 * 0.85)
        self.cell_width = self.base_cell_width
        self.base_header_font_size = 9
        self.base_param_font_size = 10
        self.header_font = tkfont.Font(
            family="Arial", size=self.base_header_font_size, weight="bold"
        )
        self.param_font = tkfont.Font(
            family="Arial", size=self.base_param_font_size, weight="bold"
        )
        self.button_font = tkfont.Font(
            family="Arial", size=self.base_param_font_size, weight="bold"
        )
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

        # 탭 내부에서 마우스 휠 스크롤을 처리
        # 각 탭이 활성화될 때 bind_mousewheel()을 호출해 전역 스크롤을 설정한다.

        # 창 크기 변화를 감지해 레이아웃을 재계산
        # ParameterManagerGUI will delegate resize events to the active tab,
        # so no direct binding is done here.
        self._padding = 0
        self._padding_initialized = False
        self._resize_bind_id = None

        self.load_parameters()

    def update_layout_for_current_size(self):
        """Recalculate grid layout using the current toplevel size."""
        if not self.winfo_exists():
            return
        toplevel = self.winfo_toplevel()
        self.update_idletasks()
        self._padding = toplevel.winfo_width() - self.winfo_width()
        self._padding_initialized = True
        width = toplevel.winfo_width()
        new_cols = max(1, (width - self._padding) // self.cell_width)
        self.canvas.itemconfigure(self.canvas_window, width=width - self._padding)
        if new_cols != self.grid_columns:
            self.grid_columns = new_cols
            self.layout_parameters()
        self.adjust_window_size()

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
            outer.grid(row=sec_index, column=0, sticky="nsew", padx=1, pady=1)
            header = ttk.Frame(outer)
            header.grid(row=0, column=0, sticky="ew")
            outer.columnconfigure(0, weight=1)

            collapsed = self.section_states.get(section, False)
            toggle_btn = ttk.Button(
                header,
                text="+" if collapsed else "-",
                width=2,
                command=lambda s=section: self.toggle_section(s),
            )
            toggle_btn.pack(side="left")

            up_btn = ttk.Button(
                header, text="\u2191", width=2, command=lambda s=section: self.move_section_up(s)
            )
            up_btn.pack(side="left")

            down_btn = ttk.Button(
                header, text="\u2193", width=2, command=lambda s=section: self.move_section_down(s)
            )
            down_btn.pack(side="left")

            ttk.Label(header, text=section, font=self.header_font).pack(
                side="left", padx=(4, 0), fill="x", expand=True
            )


            grid_frame = ttk.Frame(outer)
            grid_frame.grid(row=1, column=0, sticky="nsew")

            self.widget_registry[section] = {
                "frame": outer,
                "grid_frame": grid_frame,
                "params": {},
                "toggle": toggle_btn,
            }

            if collapsed:
                grid_frame.grid_remove()

            for index, (param_name, param_value) in enumerate(params.items()):
                self.create_parameter_widget(section, index, param_name, param_value)
        self.layout_parameters()

    def create_parameter_widget(self, section, index, param_name, param_value):
        section_info = self.widget_registry[section]
        row, column = divmod(index, self.grid_columns)
        row += 1
        container = section_info["grid_frame"]
        parameter_frame = ttk.Frame(
            container, borderwidth=1, relief="solid", width=self.cell_width
        )
        # 셀 간 간격을 좁히기 위해 padding 값을 조정
        parameter_frame.grid(row=row, column=column, padx=1, pady=1, sticky="nsew")

        # 파라미터 텍스트 크기를 키워 가독성을 높임
        ttk.Label(
            parameter_frame,
            text=param_name,
            font=self.param_font,
            anchor=tk.W,
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W)

        toggle_button = tk.Button(
            parameter_frame,
            text="ON" if param_value == "1" else "OFF",
            bg="green" if param_value == "1" else "red",
            fg="white",
            font=self.button_font,
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
            font=self.button_font,
            width=4,
        )
        value_entry.delete(0, tk.END)
        value_entry.insert(0, param_value)

    def toggle_parameter_value(self, section, param_name):
        current = self.sections[section][param_name]
        self.sections[section][param_name] = "0" if current == "1" else "1"
        self.update_parameter_widget(section, param_name, self.sections[section][param_name])
        save_parameters(self.file_path, self.sections)
        self.last_file_hash = compute_file_hash(self.file_path)

    def update_parameter_value(self, section, param_name, param_value):
        self.sections[section][param_name] = param_value
        self.update_parameter_widget(section, param_name, param_value)
        save_parameters(self.file_path, self.sections)
        self.last_file_hash = compute_file_hash(self.file_path)

    def monitor_file_changes(self):
        if not self.file_path:
            return
        file_size = os.path.getsize(self.file_path)
        interval = 1000 if file_size < 1024 * 10 else 2000
        current_hash = compute_file_hash(self.file_path)
        if current_hash != self.last_file_hash:
            new_sections = load_parameters(self.file_path)

            structure_changed = (
                list(new_sections.keys()) != list(self.sections.keys())
            )
            if not structure_changed:
                for sec in new_sections:
                    if list(new_sections[sec].keys()) != list(
                        self.sections.get(sec, {}).keys()
                    ):
                        structure_changed = True
                        break

            if structure_changed:
                self.sections = new_sections
                self.refresh_ui()
            else:
                for sec, params in new_sections.items():
                    for param, value in params.items():
                        if self.sections[sec][param] != value:
                            self.sections[sec][param] = value
                            self.update_parameter_widget(sec, param, value)
                self.adjust_window_size()

            self.last_file_hash = current_hash
        self.after(interval, self.monitor_file_changes)

    def adjust_window_size(self):
        self.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.config(scrollregion=bbox)

    def _apply_zoom(self):
        """Update fonts and layout according to the current zoom level."""
        self.cell_width = int(self.base_cell_width * self.zoom)
        self.header_font.config(size=int(self.base_header_font_size * self.zoom))
        self.param_font.config(size=int(self.base_param_font_size * self.zoom))
        self.button_font.config(size=int(self.base_param_font_size * self.zoom))
        self.update_layout_for_current_size()

    def _on_mousewheel(self, event):
        ctrl_pressed = bool(event.state & 0x4)
        if ctrl_pressed:
            if hasattr(event, "delta") and event.delta:
                delta = event.delta
            elif event.num == 4:
                delta = 120
            elif event.num == 5:
                delta = -120
            else:
                delta = 0
            if delta:
                step = 0.1 if delta > 0 else -0.1
                self.zoom = max(0.5, min(3.0, self.zoom + step))
                self._apply_zoom()
            return "break"
        if hasattr(event, "delta") and event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def bind_mousewheel(self):
        """Enable scrolling with the mouse wheel for this tab."""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.canvas.bind_all("<Button-4>", self._on_mousewheel, add="+")
        self.canvas.bind_all("<Button-5>", self._on_mousewheel, add="+")

    def unbind_mousewheel(self):
        """Disable global mouse wheel bindings for this tab."""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def on_resize(self, event):
        if not self.winfo_exists():
            return
        toplevel = self.winfo_toplevel()

        if event.widget is not toplevel:
            return

        if not self._padding_initialized:
            self._padding = event.width - self.winfo_width()
            self._padding_initialized = True

        new_cols = max(1, (event.width - self._padding) // self.cell_width)

        # 창 크기에 맞춰 내부 프레임 폭을 바로 반영
        self.canvas.itemconfigure(self.canvas_window, width=event.width - self._padding)

        if new_cols != self.grid_columns:
            self.grid_columns = new_cols
            self.layout_parameters()

        self.adjust_window_size()

    def layout_parameters(self):
        for section, info in self.widget_registry.items():
            container = info["grid_frame"]
            for i in range(self.grid_columns):
                container.columnconfigure(i, minsize=self.cell_width)
            for index, param_name in enumerate(self.sections[section].keys()):
                frame = info["params"][param_name][0]
                row, column = divmod(index, self.grid_columns)
                row += 1
                frame.grid_configure(row=row, column=column, sticky="nw")

    def toggle_section(self, section):
        info = self.widget_registry.get(section)
        if not info:
            return
        collapsed = self.section_states.get(section, False)
        if collapsed:
            info["grid_frame"].grid()
            info["toggle"].config(text="-")
        else:
            info["grid_frame"].grid_remove()
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

    def destroy(self):
        """Remove event bindings and destroy the tab."""
        # Resize events are managed by ParameterManagerGUI, so no unbinding
        # of <Configure> is necessary here.
        self.unbind_mousewheel()
        super().destroy()


