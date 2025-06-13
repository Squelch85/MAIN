from state_manager import load_state, save_state


def test_load_state_missing(tmp_path):
    missing = tmp_path / "state.json"
    assert load_state(str(missing)) == (None, [], {}, 1.0)


def test_save_and_load_state(tmp_path):
    state_file = tmp_path / "state.json"
    geometry = "800x600+100+100"
    files = ["a.ini", "b.ini"]
    file_states = {"a.ini": {"collapsed": {"Sec": True}}}
    zoom = 1.2
    save_state(str(state_file), geometry, files, file_states, zoom)
    loaded_geometry, loaded_files, loaded_states, loaded_zoom = load_state(str(state_file))
    assert loaded_geometry == geometry
    assert loaded_files == files
    assert loaded_states == file_states
    assert loaded_zoom == zoom
