"""Google-Drive-Zugriff für die einseitige StudIPSync-Synchronisation.

Dieses Modul erstellt Kursordner und lädt Dateien hoch. Es enthält bewusst
keine Funktion zum Löschen oder Herunterladen aus Google Drive: Drive ist in
diesem Projekt ausschließlich das Zielsystem.
"""

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class DriveClient:
    """Kapselt OAuth, Ordnerverwaltung und Uploads in Google Drive."""

    def __init__(self, project_dir, root_folder_id):
        """Initialisiert den Client für den konfigurierten Zielordner."""
        self.project_dir = Path(project_dir)
        self.root_folder_id = root_folder_id
        self.drive = build("drive", "v3", credentials=self._credentials())

    def _credentials(self):
        """Lädt `token.json` oder führt einmalig den Google-OAuth-Flow aus."""
        token_path = self.project_dir / "token.json"
        credentials_path = self.project_dir / "credentials.json"
        credentials = None

        if token_path.exists():
            credentials = Credentials.from_authorized_user_file(token_path, SCOPES)
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        if not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            credentials = flow.run_local_server(port=0)

        # Das Token verhindert, dass bei jedem täglichen Lauf ein Browser-Login
        # erforderlich ist.
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        return credentials

    def ensure_course_folder(self, course_name):
        """Gibt den Kursordner zurück und erstellt ihn bei Bedarf."""
        safe_name = course_name.replace("'", "\\'")
        query = (
            f"name='{safe_name}' and '{self.root_folder_id}' in parents "
            "and mimeType='application/vnd.google-apps.folder' and trashed=false"
        )
        result = self.drive.files().list(
            q=query,
            fields="files(id,name)",
        ).execute()
        folders = result.get("files", [])
        if folders:
            return folders[0]["id"]

        folder = self.drive.files().create(
            body={
                "name": course_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [self.root_folder_id],
            },
            fields="id",
        ).execute()
        return folder["id"]

    def upload(self, local_path, filename, mime_type, parent_id):
        """Lädt eine lokale Datei als neue Datei in einen Drive-Ordner hoch."""
        media = MediaFileUpload(local_path, mimetype=mime_type, resumable=False)
        result = self.drive.files().create(
            body={"name": filename, "parents": [parent_id]},
            media_body=media,
            fields="id,name",
        ).execute()
        return result["id"]
