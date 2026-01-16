from pathlib import Path

from .config import DEFAULT_ROOT_WINDOWS


def detect_root(start: Path) -> Path:
    current = start.resolve()
    for _ in range(6):
        try:
            if any(p.is_dir() and p.name.startswith("BLF_") for p in current.iterdir()):
                return current
        except PermissionError:
            pass
        if current.parent == current:
            break
        current = current.parent
    return start.resolve()


def normalize_root(path_str: str) -> Path:
    return Path(path_str).expanduser().resolve()


def default_root() -> Path:
    if DEFAULT_ROOT_WINDOWS.is_dir():
        return DEFAULT_ROOT_WINDOWS.resolve()
    return detect_root(Path.cwd())