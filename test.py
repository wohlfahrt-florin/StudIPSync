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
LOGIN_URL = f"{BASE_URL}/dispatch.php/login?again=yes"  # echtes Formular-Ziel (Stand 10/2026)
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

# === TEST: Login-Mechanismus prüfen ===
login_page = session.get(LOGIN_URL)
soup = BeautifulSoup(login_page.text, "html.parser")

# Versteckte Formularfelder extrahieren (heißen login_ticket + security_token, NICHT login_token)
def hidden(name):
    field = soup.find("input", {"name": name})
    return field["value"] if field else None

login_ticket = hidden("login_ticket")
security_token = hidden("security_token")
print("login_ticket:", login_ticket, "| security_token:", security_token)

# Login absenden
payload = {
    "loginname": USERNAME,
    "password": PASSWORD,
    "login_ticket": login_ticket,
    "security_token": security_token,
    "resolution": "",
}
response = session.post(LOGIN_URL, data=payload)

print("Login-Statuscode:", response.status_code)
print("Redirect-URL:", response.url)
print("Erste 300 Zeichen nach Login:")
print(response.text[:300])
exit()


# === KURSE AUTOMATISCH ERKENNEN ===
r = session.get(f"{BASE_URL}/dispatch.php/start")

# === TEST: Stud.IP-Download prüfen ===
test_url = f"{BASE_URL}/dispatch.php/start"
test_response = session.get(test_url)
print("Statuscode:", test_response.status_code)
print("Erste 500 Zeichen der Seite:")
print(test_response.text[:500])
exit()

# soup = BeautifulSoup(r.text, "html.parser")
# courses = {a.text.strip(): a["href"].split("to=")[1] for a in soup.select("a[href*='course/go?to=']")}

# # === HAUPTORDNER AUF GOOGLE DRIVE FINDEN ===
# root_folder_id = os.environ["DRIVE_ROOT_FOLDER_ID"]

# # === DATEIEN SYNCHRONISIEREN ===
# os.makedirs("temp", exist_ok=True)

# for course_name, cid in courses.items():
#     print(f"🔍 Kurs: {course_name}")
#     course_folder_id = ensure_drive_folder(course_name, root_folder_id)
#     files_url = f"{BASE_URL}/plugins.php/courseware/courseware?cid={cid}"
#     r = session.get(files_url)
#     soup = BeautifulSoup(r.text, "html.parser")

#     for link in soup.select("a[href*='sendfile.php']"):
#         file_url = BASE_URL + link["href"]
#         filename = link.text.strip()
#         local_path = os.path.join("temp", filename)

#         if not os.path.exists(local_path):
#             print(f"📥 Lade {filename} herunter …")
#             with open(local_path, "wb") as f:
#                 f.write(session.get(file_url).content)
#             upload_to_drive(local_path, filename, course_folder_id)
#             print(f"📤 {filename} → {course_name}")
#             time.sleep(1)

# print("✅ Synchronisation abgeschlossen.")
