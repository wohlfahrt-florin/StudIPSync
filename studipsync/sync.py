"""Programmstart und Ablaufsteuerung für StudIPSync.

Die eigentliche Kommunikation ist in drei spezialisierte Module ausgelagert:

* ``studip_client.py`` liest Kurse und Dateien aus der Stud.IP-JSON-API.
* ``drive_client.py`` verwaltet Google-OAuth, Kursordner und Uploads.
* ``sync_state.py`` merkt sich erfolgreich synchronisierte Dateien.

Dieses Modul verbindet die drei Bausteine und legt die Synchronisationsrichtung
fest: ausschließlich von Stud.IP nach Google Drive.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from .app_paths import PROJECT_DIR
from .drive_client import DriveClient
from .studip_client import StudIPClient, TARGET_SEMESTER
from .sync_paths import temp_path_for
from .sync_state import SyncState


def download_to_temp(studip, file_ref, course_name, project_dir=PROJECT_DIR):
    """Speichert eine Stud.IP-Datei im lokalen, kursbezogenen Zwischenspeicher.

    Die File-Ref-ID wird dem lokalen Namen vorangestellt. So können zwei
    gleichnamige Dateien aus verschiedenen Stud.IP-Unterordnern gleichzeitig
    gespeichert werden, ohne sich gegenseitig zu überschreiben.
    """
    attributes = file_ref["attributes"]
    local_name = f"{file_ref['id']}_{attributes['name']}"
    local_path = Path(
        temp_path_for(
            course_name,
            local_name,
            temp_root=str(project_dir / "temp"),
        )
    )
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(studip.download_file(file_ref))
    return local_path


def synchronize(project_dir=PROJECT_DIR, log=print):
    """Führt eine vollständige, einseitige Synchronisationsrunde aus.

    Für jede neue Stud.IP-Datei gilt die Reihenfolge:

    1. Datei-Referenzen aus Stud.IP lesen.
    2. Datei nach ``temp/`` herunterladen.
    3. Datei in den passenden Google-Drive-Kursordner hochladen.
    4. Erst nach einem erfolgreichen Upload den Status speichern.

    Es gibt absichtlich keinen Zugriff, der Dateien im Drive löscht oder nach
    Stud.IP zurückschreibt.
    """
    project_dir = Path(project_dir)
    load_dotenv(project_dir / ".env", override=True)
    username = os.environ["STUDIP_USER"]
    password = os.environ["STUDIP_PASSWORD"]
    root_folder_id = os.environ["DRIVE_ROOT_FOLDER_ID"]

    studip = StudIPClient(username, password)
    user = studip.current_user()
    courses = studip.semester_courses(user["id"], TARGET_SEMESTER)
    log(f"{len(courses)} Kurse im {TARGET_SEMESTER} gefunden.")

    drive = DriveClient(project_dir, root_folder_id)
    state = SyncState(project_dir / "sync_state.json")

    for course_id, course_name in courses:
        log(f"Kurs: {course_name}")
        drive_folder_id = drive.ensure_course_folder(course_name)

        for file_ref in studip.file_refs(course_id):
            attributes = file_ref["attributes"]
            if not attributes.get("is-downloadable", True):
                continue

            # Die Kombination aus Kurs-ID und File-Ref-ID bleibt stabil, auch
            # wenn sich der sichtbare Dateiname in Stud.IP ändert.
            state_key = f"{course_id}:{file_ref['id']}"
            if state.contains(state_key):
                continue

            local_path = download_to_temp(studip, file_ref, course_name, project_dir)
            drive_file_id = drive.upload(
                str(local_path),
                attributes["name"],
                attributes.get("mime-type", "application/octet-stream"),
                drive_folder_id,
            )

            # Der Status wird erst hier gespeichert. Bei einem Fehler vorher
            # wird die Datei beim nächsten täglichen Lauf erneut versucht.
            state.remember(
                state_key,
                {
                    "course_id": course_id,
                    "course_name": course_name,
                    "file_ref_id": file_ref["id"],
                    "file_name": attributes["name"],
                    "drive_file_id": drive_file_id,
                    "studip_changed": attributes.get("chdate"),
                },
            )
            log(f"  Neu: {attributes['name']}")

    log("Synchronisation abgeschlossen. Richtung: Stud.IP -> Google Drive")


if __name__ == "__main__":
    synchronize()
