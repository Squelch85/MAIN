import json
import os


def load_state(state_path):
    """JSON 파일에서 GUI 상태를 읽어옵니다.

    반환 값은 ``(geometry, files, file_states)`` 튜플이며,
    ``file_states``에는 각 파일별 UI 정보가 저장됩니다.
    상태 파일이 없거나 해당 키가 없으면 ``file_states`` 는 빈 딕셔너리를 돌려줍니다.
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
    """GUI 상태를 JSON 파일로 저장합니다."""
    state = {"geometry": geometry, "files": files, "file_states": file_states}
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass
