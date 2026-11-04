"""Client für die Stud.IP-JSON-API.

Dieses Modul kennt nur Stud.IP. Es kümmert sich um Authentifizierung, Kurse,
Semester und Dateien, aber nicht um Google Drive oder den lokalen Status.
Dadurch kann der Stud.IP-Zugriff unabhängig getestet und erklärt werden.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import time

import requests

from sync_paths import absolute_studip_url


BASE_URL = "https://studip.uni-halle.de"
API_URL = f"{BASE_URL}/jsonapi.php/v1"
TARGET_SEMESTER = "WiSe 2026/27"


class StudIPClient:
    """Stellt authentifizierte Lesezugriffe auf die Stud.IP-JSON-API bereit."""

    def __init__(self, username, password):
        """Erzeugt eine API-Sitzung mit HTTP Basic Auth."""
        self.session = requests.Session()
        self.session.auth = (username, password)
        # Dieser Header fordert die JSON:API-Repräsentation an. Ohne ihn kann
        # Stud.IP mit HTTP 406 (Not Acceptable) antworten.
        self.session.headers.update({"Accept": "application/vnd.api+json"})

    @staticmethod
    def _get_response(session, url, params=None, timeout=30):
        """Wiederholt vorübergehende Serverfehler begrenzt."""
        for attempt in range(3):
            response = session.get(url, params=params, timeout=timeout)
            if response.status_code < 500 or attempt == 2:
                response.raise_for_status()
                return response
            time.sleep(0.5 * (2**attempt))

    def get_json(self, url, params=None):
        """Sendet einen GET-Request und gibt die JSON-Nutzdaten zurück."""
        return self._get_response(self.session, url, params=params).json()

    def current_user(self):
        """Liefert die Daten des aktuell angemeldeten Stud.IP-Benutzers."""
        return self.get_json(f"{API_URL}/users/me")["data"]

    def semester_courses(self, user_id, semester_title=TARGET_SEMESTER):
        """Liefert die eigenen Kurse, die ein bestimmtes Semester berühren.

        Die Kursmitgliedschaft liefert zunächst nur IDs. Für jede ID werden
        Start- und Endsemester geladen. Ein Kurs wird aufgenommen, wenn sein
        Zeitraum den Zeitraum des Zielsemesters überschneidet.
        """
        semester_data = self.get_json(
            f"{API_URL}/semesters",
            params={"page[limit]": 100},
        )["data"]
        semesters = {item["id"]: item["attributes"] for item in semester_data}
        target = next(
            item["attributes"]
            for item in semester_data
            if item["attributes"]["title"] == semester_title
        )
        target_start = datetime.fromisoformat(target["start"])
        target_end = datetime.fromisoformat(target["end"])

        memberships = self.get_json(
            f"{API_URL}/users/{user_id}/course-memberships",
            params={"page[limit]": 100},
        )["data"]
        course_ids = [
            membership["relationships"]["course"]["data"]["id"]
            for membership in memberships
        ]

        def inspect_course(course_id):
            # requests.Session ist nicht für parallele Nutzung vorgesehen.
            # Jeder Thread erhält deshalb eine eigene Sitzung.
            course_session = requests.Session()
            course_session.auth = self.session.auth
            course_session.headers.update({"Accept": "application/vnd.api+json"})
            data = self._get_response(
                course_session,
                f"{API_URL}/courses/{course_id}",
                timeout=30,
            )
            course = data.json()["data"]

            relationships = course["relationships"]
            start_data = relationships.get("start-semester", {}).get("data")
            end_data = relationships.get("end-semester", {}).get("data")
            if not start_data or not end_data:
                return None

            start_attributes = semesters.get(start_data["id"])
            end_attributes = semesters.get(end_data["id"])
            if not start_attributes or not end_attributes:
                return None

            course_start = datetime.fromisoformat(start_attributes["start"])
            course_end = datetime.fromisoformat(end_attributes["end"])
            if course_start <= target_end and course_end >= target_start:
                title = course["attributes"].get("title") or "(ohne Titel)"
                return course_id, title
            return None

        # Die Kursdetails können unabhängig voneinander gelesen werden.
        with ThreadPoolExecutor(max_workers=10) as executor:
            return [
                course
                for course in executor.map(inspect_course, course_ids)
                if course is not None
            ]

    def file_refs(self, course_id):
        """Lädt alle Datei-Referenzen eines Kurses, inklusive Pagination."""
        file_refs = []
        offset = 0
        while True:
            payload = self.get_json(
                f"{API_URL}/courses/{course_id}/file-refs",
                params={"page[limit]": 100, "page[offset]": offset},
            )
            page = payload.get("data", [])
            file_refs.extend(page)
            total = payload.get("meta", {}).get("page", {}).get("total")
            if not page or (total is not None and len(file_refs) >= total):
                return file_refs
            offset += len(page)

    def course_events(self, course_id):
        """Lädt alle Termine eines Kurses, inklusive Pagination."""
        events = []
        offset = 0
        while True:
            payload = self.get_json(
                f"{API_URL}/courses/{course_id}/events",
                params={"page[limit]": 100, "page[offset]": offset},
            )
            page = payload.get("data", [])
            events.extend(page)
            total = payload.get("meta", {}).get("page", {}).get("total")
            if not page or (total is not None and len(events) >= total):
                return events
            offset += len(page)

    def download_file(self, file_ref):
        """Lädt den Inhalt einer Stud.IP-Datei als Bytes herunter."""
        download_url = absolute_studip_url(
            file_ref["meta"]["download-url"],
            BASE_URL,
        )
        response = self.session.get(download_url, timeout=60)
        response.raise_for_status()
        return response.content
