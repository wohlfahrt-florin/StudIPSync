"""Einfacher Funktionstest der Stud.IP-JSON-API.

Das Skript testet ausschließlich Stud.IP und Google Drive nicht. Es zeigt, ob
die Zugangsdaten funktionieren und welche eigenen Kurse das WiSe 2026/27
berühren. Die wiederverwendbare API-Logik liegt in ``studip_client.py``.
"""

import os
from pathlib import Path
import sys

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
from studipsync.studip_client import StudIPClient, TARGET_SEMESTER


def main():
    """Meldet sich an und gibt die gefilterten Stud.IP-Kurse aus."""
    # Der Pfad ist unabhängig vom aktuellen Terminalordner. Dadurch kann der
    # Test auch über einen absoluten Dateipfad gestartet werden.
    load_dotenv(PROJECT_DIR / ".env")

    # Die Zugangsdaten bleiben im Quelltext und in der Terminalausgabe geheim.
    username = os.environ["STUDIP_USER"]
    password = os.environ["STUDIP_PASSWORD"]
    studip = StudIPClient(username, password)

    # ``users/me`` prüft gleichzeitig die Verbindung und die Authentifizierung.
    user = studip.current_user()
    print("users/me: 200")
    print("User-ID:", user["id"])

    # Die Kursfilterung erfolgt über den wiederverwendbaren Stud.IP-Client.
    courses = studip.semester_courses(user["id"], TARGET_SEMESTER)
    print(f"Kurse im {TARGET_SEMESTER}: {len(courses)}")
    for course_id, course_name in courses:
        print(f" - {course_name} (Kurs-ID: {course_id})")


if __name__ == "__main__":
    main()
