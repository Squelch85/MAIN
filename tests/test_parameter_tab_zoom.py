import types
import tkinter as tk
from tkinter import font as tkfont
import pytest
from gui.parameter_tab import ParameterTab


def _event(delta=120, state=0x4, num=None):
    return types.SimpleNamespace(delta=delta, state=state, num=num)


def test_zoom_in_out(tmp_path):
    ini = tmp_path / "sample.ini"
    ini.write_text("[Section]\nkey=1\n")
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk unavailable: {e}")
    root.withdraw()
    tab = ParameterTab(root, str(ini))
    root.update_idletasks()
    original_width = tab.cell_width
    original_size = tab.param_font.cget("size")

    tab._on_mousewheel(_event(delta=120))
    assert tab.cell_width > original_width
    assert tab.param_font.cget("size") > original_size

    tab._on_mousewheel(_event(delta=-120))
    assert tab.cell_width == original_width
    assert tab.param_font.cget("size") == original_size
    root.destroy()


def test_entry_font_scales(tmp_path):
    ini = tmp_path / "sample.ini"
    ini.write_text("[Section]\nkey=1\n")
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk unavailable: {e}")
    root.withdraw()
    tab = ParameterTab(root, str(ini))
    root.update_idletasks()

    entry = tab.widget_registry["Section"]["params"]["key"][2]
    f = tkfont.nametofont(entry.cget("font"))
    original_size = f.cget("size")

    tab._on_mousewheel(_event(delta=120))
    assert f.cget("size") > original_size

    tab._on_mousewheel(_event(delta=-120))
    assert f.cget("size") == original_size
    root.destroy()
