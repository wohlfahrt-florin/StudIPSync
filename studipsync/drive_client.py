"""Google-Drive-Zugriff für die einseitige StudIPSync-Synchronisation.

Dieses Modul erstellt Kursordner und lädt Dateien hoch. Es enthält bewusst
keine Funktion zum Löschen oder Herunterladen aus Google Drive: Drive ist in
diesem Projekt ausschließlich das Zielsystem.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import webbrowser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def parse_picker_callback(callback_url, expected_state):
    """Return the authorization code and single selected Drive folder ID."""
    parameters = parse_qs(urlparse(callback_url).query)
    returned_state = parameters.get("state", [None])[0]
    if returned_state != expected_state:
        raise ValueError("Die Google-Anmeldung konnte nicht sicher zugeordnet werden.")

    error = parameters.get("error", [None])[0]
    if error:
        raise ValueError(f"Google-Ordnerauswahl abgebrochen: {error}")

    authorization_code = parameters.get("code", [None])[0]
    selected_ids = parameters.get("picked_file_ids", [None])[0]
    if not authorization_code or not selected_ids:
        raise ValueError("Google hat keinen Ordner zur Auswahl zurueckgegeben.")

    folder_ids = selected_ids.split(",")
    if len(folder_ids) != 1 or not folder_ids[0]:
        raise ValueError("Bitte genau einen Google-Drive-Ordner auswaehlen.")
    return authorization_code, folder_ids[0]


class _PickerCallbackHandler(BaseHTTPRequestHandler):
    """Capture the OAuth redirect from the desktop Google Picker."""

    def do_GET(self):
        self.server.callback_url = f"http://{self.headers['Host']}{self.path}"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h2>Ordnerauswahl abgeschlossen</h2>"
            b"<p>Du kannst dieses Browserfenster schliessen.</p></body></html>"
        )

    def log_message(self, _format, *_args):
        pass


def pick_drive_folder(project_dir):
    """Open Google's desktop Picker and return the selected folder ID/name."""
    project_dir = Path(project_dir)
    credentials_path = project_dir / "credentials.json"
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    server = HTTPServer(("localhost", 0), _PickerCallbackHandler)
    server.timeout = 300
    flow.redirect_uri = f"http://localhost:{server.server_port}/"

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        trigger_onepick="true",
        allow_folder_selection="true",
        mimetypes="application/vnd.google-apps.folder",
    )
    try:
        if not webbrowser.open(authorization_url, new=1, autoraise=True):
            raise RuntimeError("Der Browser fuer die Google-Ordnerauswahl konnte nicht geoeffnet werden.")
        server.handle_request()
    finally:
        server.server_close()

    callback_url = getattr(server, "callback_url", None)
    if not callback_url:
        raise TimeoutError("Google hat die Ordnerauswahl nicht rechtzeitig abgeschlossen.")

    authorization_code, folder_id = parse_picker_callback(callback_url, state)
    flow.fetch_token(code=authorization_code)
    credentials = flow.credentials
    (project_dir / "token.json").write_text(credentials.to_json(), encoding="utf-8")

    drive = build("drive", "v3", credentials=credentials)
    folder = drive.files().get(fileId=folder_id, fields="id,name,mimeType").execute()
    if folder.get("mimeType") != "application/vnd.google-apps.folder":
        raise ValueError("Das ausgewaehlte Element ist kein Google-Drive-Ordner.")
    return folder["id"], folder["name"]


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
