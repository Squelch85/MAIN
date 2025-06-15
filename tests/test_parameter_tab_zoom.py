import types
import tkinter as tk
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
