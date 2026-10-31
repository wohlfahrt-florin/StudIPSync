import os
import re
from urllib.parse import urljoin

WINDOWS_FORBIDDEN_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')


def sanitize_filename(name):
    """Make a Stud.IP title safe to use as a Windows file or folder name."""
    cleaned = WINDOWS_FORBIDDEN_FILENAME_CHARS.sub("_", (name or "").strip())
    cleaned = cleaned.rstrip(" .")
    return cleaned or "unnamed"


def temp_path_for(course_name, filename, temp_root="temp"):
    """Keep each course's downloads in its own folder so names cannot collide."""
    course_dir = os.path.join(temp_root, sanitize_filename(course_name))
    return os.path.join(course_dir, sanitize_filename(filename))


def absolute_studip_url(href, base_url):
    return urljoin(base_url.rstrip("/") + "/", href)
