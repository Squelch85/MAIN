import hashlib

from config_io import compute_file_hash, load_parameters, save_parameters


def test_compute_file_hash(tmp_path):
    ini = tmp_path / "sample.ini"
    ini.write_text("key=1\n")
    expected = hashlib.md5(ini.read_bytes()).hexdigest()
    assert compute_file_hash(str(ini)) == expected


def test_compute_file_hash_missing():
    assert compute_file_hash(None) is None
    assert compute_file_hash("nonexistent.ini") is None


def test_load_parameters(tmp_path):
    ini = tmp_path / "sample.ini"
    ini.write_text("key=1\n[Section]\nvalue=2\n# comment\n; semi\n")
    sections = load_parameters(str(ini))
    assert list(sections.keys()) == ["DEFAULT", "Section"]
    assert sections["DEFAULT"]["key"] == "1"
    assert sections["Section"]["value"] == "2"


def test_save_parameters_roundtrip(tmp_path):
    sections = {
        "DEFAULT": {"key": "1"},
        "Section": {"value": "2"},
    }
    output = tmp_path / "out.ini"
    save_parameters(str(output), sections)
    reloaded = load_parameters(str(output))
    assert reloaded == sections
