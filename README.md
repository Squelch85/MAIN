# MAIN

This project provides a Tkinter-based GUI for editing INI configuration files.
It allows multiple INI files to be opened in separate tabs and tracks the window
state between sessions.

## Requirements
- Python 3.8 or higher
- Tkinter (bundled with the standard Python distribution)

No additional third‑party packages are required.

## Project Structure
- `gui/parameter_tab.py` – dynamic section/parameter UI with toggle buttons
  and editable fields.
- `gui/parameter_manager.py` – manages tabs for multiple files and persists
  window geometry and open files to `state.json` using `state_manager.py`.
- `state_manager.py` – load/save helpers for the JSON state file.
- `config_io.py` – utilities for reading and writing INI-style files.
- `INI_EDIT.py` – entry point that launches the GUI.

## Usage
Run the application from the repository root:

```bash
python INI_EDIT.py
```

Any INI files opened will be listed in a tabbed interface. When closing the
program, the set of open files, window size and per-file UI state (collapsed
sections and custom ordering) are stored in `gui/state.json` and reloaded on the
next start so the interface appears exactly as you left it.

n30yli-codex/modify-window-resizing-to-snap-to-columns
When you manually resize the main window, its width snaps to the nearest
120‑pixel increment to keep parameter columns aligned.
 main

## Contributing
- Follow [PEP 8](https://peps.python.org/pep-0008/) for code style.
- Submit pull requests with clear descriptions of changes.
- If adding new modules or features, include docstrings and update this README
  accordingly.
