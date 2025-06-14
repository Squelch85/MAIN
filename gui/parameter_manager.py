import os
import tkinter as tk
from tkinter import ttk, filedialog
from .parameter_tab import ParameterTab, DEFAULT_CELL_WIDTH
from state_manager import load_state, save_state

class ParameterManagerGUI:
    def __init__(self, root_window):
        self.root_window = root_window
        # store window state in a user writable location
        self.state_path = os.path.expanduser("~/.ini_editor/state.json")
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        self.open_files = []
        self.saved_geometry = None
        self.file_states = {}
        self.saved_geometry, self.open_files, self.file_states = load_state(self.state_path)

        self.cell_width = DEFAULT_CELL_WIDTH

        self.notebook = ttk.Notebook(self.root_window)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<Button-3>", self.show_tab_menu)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.tab_menu = tk.Menu(self.notebook, tearoff=0)
        self.tab_menu.add_command(label="Close", command=self.close_current_tab)

        self.tabs = {}
        self.current_tab = None
        self.initialize_menu()

        if self.saved_geometry:
            self.root_window.geometry(self.saved_geometry)
        for f in self.open_files:
            if os.path.exists(f):
                self._open_file(f)
        self.root_window.protocol("WM_DELETE_WINDOW", self.on_close)
        # Bind once to handle window resize events and delegate to the active tab
        self._resize_bind_id = self.root_window.bind("<Configure>", self.on_root_resize)
        # Ctrl + mouse wheel to adjust cell size globally
        self.root_window.bind_all("<Control-MouseWheel>", self._on_ctrl_wheel)
        self.root_window.bind_all("<Control-Button-4>", self._on_ctrl_wheel)
        self.root_window.bind_all("<Control-Button-5>", self._on_ctrl_wheel)

        self._update_zoom_title()

    def switch_active_tab(self, new_tab):
        """Manage global mouse wheel bindings when the active tab changes."""
        if self.current_tab is new_tab:
            return
        if self.current_tab and hasattr(self.current_tab, "unbind_mousewheel"):
            self.current_tab.unbind_mousewheel()
        self.current_tab = new_tab
        if self.current_tab and hasattr(self.current_tab, "bind_mousewheel"):
            self.current_tab.bind_mousewheel()

    def initialize_menu(self):
        menu_bar = tk.Menu(self.root_window)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open File(s)", command=self.open_files_dialog)
        file_menu.add_command(label="Exit", command=self.on_close)
        menu_bar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="Increase Cell Size", command=self.increase_cell_size)
        view_menu.add_command(label="Decrease Cell Size", command=self.decrease_cell_size)
        view_menu.add_command(label="Reset Cell Size", command=self.reset_cell_size)
        menu_bar.add_cascade(label="View", menu=view_menu)
        self.root_window.config(menu=menu_bar)


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
                break

        if tab == self.current_tab:
            self.switch_active_tab(None)
        self.notebook.forget(index)
        tab.destroy()

        if file_path:
            self.tabs.pop(file_path, None)
            if file_path in self.open_files:
                self.open_files.remove(file_path)

    def on_close(self):
        for path, tab in self.tabs.items():
            self.file_states[path] = tab.get_state()
        save_state(
            self.state_path,
            self.root_window.geometry(),
            list(self.tabs.keys()),
            self.file_states,
        )
        self.switch_active_tab(None)
        # remove resize binding before destroying the window
        if hasattr(self, "_resize_bind_id"):
            self.root_window.unbind("<Configure>", self._resize_bind_id)
        self.root_window.destroy()

    def _open_file(self, file_path):
        tab_state = self.file_states.get(file_path)
        tab = ParameterTab(
            self.notebook,
            file_path,
            initial_state=tab_state,
            cell_width=self.cell_width,
        )
        self.notebook.add(tab, text=os.path.basename(file_path))
        self.tabs[file_path] = tab
        self.notebook.select(tab)
        tab.update_layout_for_current_size()
        self.switch_active_tab(tab)
        if file_path not in self.open_files:
            self.open_files.append(file_path)

    def increase_cell_size(self):
        if self.cell_width < 240:
            self.cell_width += 10
            for tab in self.tabs.values():
                tab.set_cell_size(self.cell_width)
            self._update_zoom_title()

    def decrease_cell_size(self):
        if self.cell_width > 60:
            self.cell_width -= 10
            for tab in self.tabs.values():
                tab.set_cell_size(self.cell_width)
            self._update_zoom_title()

    def on_tab_changed(self, event):
        tab_id = self.notebook.select()
        tab = self.notebook.nametowidget(tab_id)
        self.switch_active_tab(tab)
        if hasattr(tab, "update_layout_for_current_size"):
            tab.update_layout_for_current_size()

    def on_root_resize(self, event):
        """Delegate root <Configure> events to the active tab."""
        if self.current_tab and hasattr(self.current_tab, "on_resize"):
            self.current_tab.on_resize(event)

    def _update_zoom_title(self):
        level = (self.cell_width - DEFAULT_CELL_WIDTH) // 10
        self.root_window.title(f"Parameter Manager (Level {level})")

    def reset_cell_size(self):
        self.cell_width = DEFAULT_CELL_WIDTH
        for tab in self.tabs.values():
            tab.set_cell_size(self.cell_width)
        self._update_zoom_title()

    def _on_ctrl_wheel(self, event):
        direction = 1
        if getattr(event, "delta", 0) < 0 or getattr(event, "num", None) == 5:
            direction = -1
        elif getattr(event, "num", None) == 4:
            direction = 1

        if direction > 0:
            self.increase_cell_size()
        else:
            self.decrease_cell_size()

