from pathlib import Path

AUTH_FILE = Path.home() / ".brokenxapi"

def save_key(key: str):
    AUTH_FILE.write_text(key.strip())

def get_key() -> str | None:
    if AUTH_FILE.exists():
        return AUTH_FILE.read_text().strip()
    return None
