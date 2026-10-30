import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Die alte REST-API (api.php) liefert an der MLU 404.
# Aktuell ist die JSON:API unter /jsonapi.php/v1 (Stand 10/2026).
BASE_URL = "https://studip.uni-halle.de"
API = f"{BASE_URL}/jsonapi.php/v1"
USERNAME = os.environ["STUDIP_USER"]
PASSWORD = os.environ["STUDIP_PASSWORD"]

session = requests.Session()
session.auth = (USERNAME, PASSWORD)  # HTTP Basic Auth

# 1) Wer bin ich? (ohne Login: 401)
r = session.get(f"{API}/users/me")
print("users/me:", r.status_code)
if r.status_code != 200:
    print(r.text[:500])
    raise SystemExit("Basic Auth abgelehnt – siehe Obsidian: StudIPSync/API-Tests")

user_id = r.json()["data"]["id"]
print("User-ID:", user_id)

# 2) Eigene Kurse
r = session.get(f"{API}/users/{user_id}/course-memberships", params={"page[limit]": 100})
print("course-memberships:", r.status_code)
for m in r.json().get("data", []):
    course = m["relationships"]["course"]["data"]["id"]
    print(" - Kurs-ID:", course)
