import hashlib

def compute_file_hash(filepath):
    """파일이 존재하면 md5 해시를 반환하고 없으면 ``None``을 반환합니다."""
    if not filepath:
        return None
    try:
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as file:
            for chunk in iter(lambda: file.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        return None


def load_parameters(filepath):
    """INI 형식 파일을 읽어 딕셔너리 구조로 파라미터를 불러옵니다."""
    sections = {}
    if not filepath:
        return sections
    current_section = "DEFAULT"
    sections[current_section] = {}
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith(("#", ";")):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1].strip()
                sections[current_section] = {}
            elif "=" in line:
                key, value = map(str.strip, line.split("=", 1))
                sections.setdefault(current_section, {})[key] = value
    return sections


def save_parameters(filepath, sections):
    """파라미터 섹션 구조를 INI 형식 파일로 저장합니다."""
    if not filepath:
        return
    with open(filepath, "w", encoding="utf-8") as file:
        for section, params in sections.items():
            if section != "DEFAULT":
                file.write(f"[{section}]\n")
            for key, value in params.items():
                file.write(f"{key}={value}\n")
            file.write("\n")
