"""Locations for application configuration and runtime data."""

import os
from pathlib import Path
import shutil
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]


def bundled_credentials_path():
    """Return the OAuth client file bundled into a packaged executable."""
    if not getattr(sys, "frozen", False):
        return None
    bundle_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    path = bundle_dir / "credentials.json"
    return path if path.is_file() else None


def data_dir():
    """Return a writable per-user folder for a packaged app, or the project folder."""
    if not getattr(sys, "frozen", False):
        return PROJECT_DIR

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA ist nicht gesetzt.")
    path = Path(local_app_data) / "StudIPSync"
    path.mkdir(parents=True, exist_ok=True)
    legacy_dir = Path(sys.executable).resolve().parent.parent
    if (legacy_dir / "studipsync.py").is_file():
        for filename in (
            ".env",
            "credentials.json",
            "token.json",
            "sync_state.json",
        ):
            source = legacy_dir / filename
            destination = path / filename
            if source.is_file() and not destination.exists():
                shutil.copy2(source, destination)
    return path


def clear_user_data(directory):
    """Remove saved account data, sync history, logs, and downloaded temp files."""
    directory = Path(directory)
    for filename in (".env", "token.json", "sync_state.json", "sync.log"):
        path = directory / filename
        if path.exists():
            path.unlink()

    temp_directory = directory / "temp"
    if temp_directory.exists():
        shutil.rmtree(temp_directory)
