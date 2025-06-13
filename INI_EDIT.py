import tkinter as tk
from gui.parameter_manager import ParameterManagerGUI

if __name__ == "__main__":
    app_root = tk.Tk()
    app_root.title("Parameter Manager")
    gui = ParameterManagerGUI(app_root)
    app_root.mainloop()
