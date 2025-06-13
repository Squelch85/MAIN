import json
import os


def load_state(state_path):
    """Load GUI state from JSON file."""
    saved_geometry = None
    open_files = []
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                saved_geometry = data.get("geometry")
                open_files = data.get("files", [])
        except Exception:
            pass
    return saved_geometry, open_files


def save_state(state_path, geometry, files):
    """Save GUI state to JSON file."""
    state = {"geometry": geometry, "files": files}
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass
