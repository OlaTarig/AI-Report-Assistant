import re
import uuid
from pathlib import Path

from app.config import get_settings

settings = get_settings()

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_filename(original_filename: str) -> str:
    """Strip path components and anything that isn't a safe filename
    character, then prefix with a UUID so two uploads can never collide
    even if the original names match."""
    name = Path(original_filename).name  # drops any directory traversal, e.g. "../../x" -> "x"
    name = _UNSAFE_CHARS.sub("_", name)
    return f"{uuid.uuid4().hex}_{name}"


def get_upload_dir() -> Path:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


async def save_upload(original_filename: str, content: bytes) -> tuple[str, Path]:
    """Writes the file to disk, returns (stored_filename, full_path)."""
    stored_filename = sanitize_filename(original_filename)
    full_path = get_upload_dir() / stored_filename
    full_path.write_bytes(content)
    return stored_filename, full_path
