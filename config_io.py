import hashlib
from collections import OrderedDict


def compute_file_hash(filepath):
    """Return md5 hash of file content or None if file does not exist."""
    if not filepath:
        return None
    try:
        with open(filepath, "rb") as file:
            return hashlib.md5(file.read()).hexdigest()
    except FileNotFoundError:
        return None


def load_parameters(filepath):
    """Load parameters from INI-like file into an OrderedDict sections structure."""
    sections = OrderedDict()
    if not filepath:
        return sections
    current_section = "DEFAULT"
    sections[current_section] = OrderedDict()
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith(("#", ";")):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1].strip()
                sections[current_section] = OrderedDict()
            elif "=" in line:
                key, value = map(str.strip, line.split("=", 1))
                sections.setdefault(current_section, OrderedDict())[key] = value
    return sections


def save_parameters(filepath, sections):
    """Save parameters sections structure back to an INI-like file."""
    if not filepath:
        return
    with open(filepath, "w", encoding="utf-8") as file:
        for section, params in sections.items():
            if section != "DEFAULT":
                file.write(f"[{section}]\n")
            for key, value in params.items():
                file.write(f"{key}={value}\n")
            file.write("\n")
