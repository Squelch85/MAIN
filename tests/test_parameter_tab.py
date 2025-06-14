import types
from gui.parameter_tab import ParameterTab

class DummyTab(ParameterTab):
    def __init__(self, width):
        # don't call super().__init__
        self.cell_width = width
        self.widget_registry = {}
        self.sections = {}
        self.layout_called = False
        self.adjust_called = False

    def layout_parameters(self):
        self.layout_called = True

    def adjust_window_size(self):
        self.adjust_called = True


def test_resize_methods():
    tab = DummyTab(100)
    tab.increase_cell_size()
    assert tab.cell_width == 110
    assert tab.layout_called
    # adjust_window_size won't be called without a Tk context
    assert tab.adjust_called is False

    tab.layout_called = False
    tab.adjust_called = False
    tab.decrease_cell_size()
    assert tab.cell_width == 100
    assert tab.layout_called
    assert tab.adjust_called is False

    tab.cell_width = 240
    tab.layout_called = False
    tab.increase_cell_size()
    assert tab.cell_width == 240
    assert tab.layout_called is False

