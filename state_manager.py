import json
import os


def load_state(state_path):
    """Load GUI state from JSON file.

    Returns a tuple ``(geometry, files, file_states)`` where ``file_states``
    holds any per-file UI information saved by the GUI. ``file_states`` will be
    an empty dictionary if no state file exists or it does not contain that key.
    """
    saved_geometry = None
    open_files = []
    file_states = {}
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                saved_geometry = data.get("geometry")
                open_files = data.get("files", [])
                file_states = data.get("file_states", {})
        except Exception:
            pass
    return saved_geometry, open_files, file_states


def save_state(state_path, geometry, files, file_states):
    """Save GUI state to JSON file."""
    state = {"geometry": geometry, "files": files, "file_states": file_states}
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass
