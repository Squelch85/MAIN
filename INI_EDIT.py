import tkinter as tk
from tkinter import ttk, filedialog
import os
import hashlib
from collections import OrderedDict

class ParameterManagerGUI:
    def __init__(self, root_window):
        self.root_window = root_window
        self.selected_file_path = None
        self.parameters = OrderedDict()
        self.last_file_hash = None
        self.grid_columns = 6
        self.widget_registry = {}
        self.file_check_interval_ms = 1000

        self.main_frame = ttk.Frame(self.root_window)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_content = ttk.Frame(self.canvas)

        self.scrollable_content.bind(
            "<Configure>",
            lambda e: self.adjust_window_size()
        )

        self.canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.initialize_menu()

    def initialize_menu(self):
        menu_bar = tk.Menu(self.root_window)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open File", command=self.open_file)
        file_menu.add_command(label="Exit", command=self.root_window.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.root_window.config(menu=menu_bar)

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=(
                ("INI Files", "*.ini"),
                ("All Files", "*.*")
            )
        )
        if not file_path:
            return

        self.selected_file_path = file_path
        self.load_parameters()  # 별도의 스레드 대신 바로 메인 스레드에서 실행

    def load_parameters(self):
        self.last_file_hash = self.compute_file_hash()
        self.load_parameters_from_file()
        self.refresh_ui(full_refresh=True)
        self.adjust_window_size()  # 새로 계산된 크기로 조정
        self.root_window.update_idletasks()  # 변경된 UI 강제 반영
        self.root_window.geometry(f"{self.canvas.winfo_width()}x{self.canvas.winfo_height()}")  # 창 크기 강제 조정
        self.root_window.title(f"Parameter Manager - {os.path.basename(self.selected_file_path)}")
        self.monitor_file_changes()

    def compute_file_hash(self):
        if not self.selected_file_path:
            return None
        try:
            with open(self.selected_file_path, "rb") as file:
                return hashlib.md5(file.read()).hexdigest()
        except FileNotFoundError:
            return None

    def load_parameters_from_file(self):
        if not self.selected_file_path:
            return
        self.parameters.clear()
        with open(self.selected_file_path, "r", encoding="utf-8") as file:
            for line in file:
                if "=" in line:
                    key, value = map(str.strip, line.split("=", 1))
                    self.parameters[key] = value

    def refresh_ui(self, full_refresh=False):
        if full_refresh:
            for widget in self.scrollable_content.winfo_children():
                widget.destroy()
            self.widget_registry.clear()

        for index, (param_name, param_value) in enumerate(self.parameters.items()):
            if param_name not in self.widget_registry:
                self.create_parameter_widget(index, param_name, param_value)
            else:
                current_value = self.parameters[param_name]
                widget_frame, toggle_button, value_entry = self.widget_registry[param_name]
                if value_entry.get() != current_value:
                    self.update_parameter_widget(param_name, current_value)

        for index, (param_name, param_value) in enumerate(self.parameters.items()):
            if param_name not in self.widget_registry:
                self.create_parameter_widget(index, param_name, param_value)
            elif not full_refresh:
                # 변경된 항목만 업데이트
                current_value = self.parameters[param_name]
                widget_frame, toggle_button, value_entry = self.widget_registry[param_name]
                if value_entry.get() != current_value:
                    self.update_parameter_widget(param_name, current_value)

    def create_parameter_widget(self, index, param_name, param_value):
        row, column = divmod(index, self.grid_columns)
        parameter_frame = ttk.Frame(self.scrollable_content, borderwidth=1, relief="solid")
        parameter_frame.grid(row=row, column=column, padx=4, pady=4, sticky="nsew")

        ttk.Label(parameter_frame, text=param_name, font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, sticky=tk.W)

        toggle_button = tk.Button(
            parameter_frame, text="ON" if param_value == "1" else "OFF",
            bg="green" if param_value == "1" else "red",
            fg="white", font=('Arial', 10, 'bold'),
            width=6, command=lambda: self.toggle_parameter_value(param_name)
        )
        toggle_button.grid(row=1, column=0)

        value_entry = ttk.Entry(parameter_frame, width=10)
        value_entry.insert(0, param_value)
        value_entry.bind("<Return>", lambda e: self.update_parameter_value(param_name, value_entry.get()))
        value_entry.grid(row=1, column=1)

        self.widget_registry[param_name] = (parameter_frame, toggle_button, value_entry)

    def update_parameter_widget(self, param_name, param_value):
        parameter_frame, toggle_button, value_entry = self.widget_registry[param_name]
        toggle_button.config(
            text="ON" if param_value == "1" else "OFF",
            bg="green" if param_value == "1" else "red",
            fg="white", font=('Arial', 10, 'bold')
        )
        value_entry.delete(0, tk.END)
        value_entry.insert(0, param_value)

    def toggle_parameter_value(self, param_name):
        self.parameters[param_name] = "0" if self.parameters[param_name] == "1" else "1"
        self.update_parameter_widget(param_name, self.parameters[param_name])
        self.save_parameters_to_file()

    def update_parameter_value(self, param_name, param_value):
        self.parameters[param_name] = param_value
        self.update_parameter_widget(param_name, param_value)
        self.save_parameters_to_file()

    def save_parameters_to_file(self):
        if not self.selected_file_path:
            return
        with open(self.selected_file_path, "w", encoding="utf-8") as file:
            for key, value in self.parameters.items():
                file.write(f"{key}={value}\n")

    def monitor_file_changes(self):
        if not self.selected_file_path:
            return

        file_size = os.path.getsize(self.selected_file_path)
        interval = 1000 if file_size < 1024 * 10 else 2000  # 파일 크기에 따라 주기 조정

        if self.compute_file_hash() != self.last_file_hash:
            self.load_parameters_from_file()
            for param_name, param_value in self.parameters.items():
                self.update_parameter_widget(param_name, param_value)
            self.last_file_hash = self.compute_file_hash()

        self.root_window.after(interval, self.monitor_file_changes)

    def adjust_window_size(self):
        self.root_window.update_idletasks()
        bbox = self.canvas.bbox("all")  # scrollable_content의 실제 크기 계산
        if bbox:
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            self.canvas.config(scrollregion=bbox, width=width, height=height)


if __name__ == "__main__":
    app_root = tk.Tk()
    app_root.title("Parameter Manager")
    gui = ParameterManagerGUI(app_root)
    app_root.mainloop()
