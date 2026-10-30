import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# === KONFIGURATION ===
BASE_URL = "https://studip.uni-halle.de"
LOGIN_URL = f"{BASE_URL}/dispatch.php/login?again=yes"
# Zugangsdaten kommen aus .env (siehe .env.example) – NIE im Code speichern
USERNAME = os.environ["STUDIP_USER"]
PASSWORD = os.environ["STUDIP_PASSWORD"]

# === GOOGLE DRIVE AUTHENTIFIZIERUNG ===
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

from google.auth.transport.requests import Request

def get_drive_credentials():
    """Nutzt token.json wieder, statt bei jedem Start neu im Browser zu fragen."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
    with open("token.json", "w", encoding="utf-8") as token:
        token.write(creds.to_json())
    return creds

creds = get_drive_credentials()

drive = build("drive", "v3", credentials=creds)

# === FUNKTIONEN ===
def ensure_drive_folder(name, parent_id):
    """Erstellt einen Ordner auf Google Drive, falls er nicht existiert."""
    query = f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder'"
    res = drive.files().list(q=query).execute().get("files", [])
    if res:
        return res[0]["id"]
    folder = drive.files().create(
        body={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
    ).execute()
    return folder["id"]

def upload_to_drive(local_path, filename, parent_id):
    """Lädt eine Datei in den angegebenen Drive-Ordner hoch."""
    drive.files().create(
        body={"name": filename, "parents": [parent_id]},
        media_body=local_path
    ).execute()

# === LOGIN BEI STUD.IP ===
session = requests.Session()
login_soup = BeautifulSoup(session.get(LOGIN_URL).text, "html.parser")

def hidden(name):
    field = login_soup.find("input", {"name": name})
    return field["value"] if field else ""

resp = session.post(LOGIN_URL, data={
    "loginname": USERNAME,
    "password": PASSWORD,
    "login_ticket": hidden("login_ticket"),
    "security_token": hidden("security_token"),
    "resolution": "",
})
if 'name="loginname"' in resp.text:
    raise SystemExit("Login fehlgeschlagen – siehe Obsidian: StudIPSync/Login-Debugging")

# === KURSE AUTOMATISCH ERKENNEN ===
r = session.get(f"{BASE_URL}/dispatch.php/start")
soup = BeautifulSoup(r.text, "html.parser")
courses = {a.text.strip(): a["href"].split("to=")[1] for a in soup.select("a[href*='course/go?to=']")}

# === HAUPTORDNER AUF GOOGLE DRIVE FINDEN ===
root_folder_id = os.environ["DRIVE_ROOT_FOLDER_ID"]

# === DATEIEN SYNCHRONISIEREN ===
os.makedirs("temp", exist_ok=True)

for course_name, cid in courses.items():
    print(f"🔍 Kurs: {course_name}")
    course_folder_id = ensure_drive_folder(course_name, root_folder_id)
    files_url = f"{BASE_URL}/plugins.php/courseware/courseware?cid={cid}"
    r = session.get(files_url)
    soup = BeautifulSoup(r.text, "html.parser")

    for link in soup.select("a[href*='sendfile.php']"):
        file_url = BASE_URL + link["href"]
        filename = link.text.strip()
        local_path = os.path.join("temp", filename)

        if not os.path.exists(local_path):
            print(f"📥 Lade {filename} herunter …")
            with open(local_path, "wb") as f:
                f.write(session.get(file_url).content)
            upload_to_drive(local_path, filename, course_folder_id)
            print(f"📤 {filename} → {course_name}")
            time.sleep(1)

print("✅ Synchronisation abgeschlossen.")
