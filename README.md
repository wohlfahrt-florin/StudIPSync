# StudIPSync

Synchronisiert neue Dateien aus den Stud.IP-Kursen der MLU Halle in einen
Google-Drive-Ordner – ein Unterordner pro Kurs.

> Richtung: **Stud.IP → Google Drive**. Änderungen im Google Drive werden nicht
> nach Stud.IP zurückgeschrieben.

## Dateien

| Datei | Zweck |
|---|---|
| `studipsync.py` | Einstiegspunkt und Ablaufsteuerung der Synchronisation |
| `studip_client.py` | Authentifizierter Zugriff auf die Stud.IP-JSON-API |
| `drive_client.py` | Google-OAuth, Kursordner und Uploads |
| `sync_state.py` | Status bereits hochgeladener Stud.IP-Dateien |
| `StudIP_API_Test.py` | Test der Stud.IP-JSON-API und Ausgabe der Kurse |
| `sync_paths.py` | Sichere lokale Pfade für Kurse und Dateien |
| `test_studipsync.py` | Tests für die Pfadfunktionen |
| `.env.example` | Vorlage für Zugangsdaten und Drive-Zielordner |
| `credentials.json` / `token.json` | Google-OAuth – nicht ins Repository legen |
| `sync_state.json` | Lokaler Status bereits hochgeladener Stud.IP-Dateien |

## Setup

```powershell
\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Danach `.env` ausfüllen und `credentials.json` aus der Google Cloud Console
(OAuth-Client „Desktop-App“, Drive API aktiviert) in den Projektordner legen.
Beim ersten Start öffnet sich der Browser für die Google-Anmeldung; danach wird
`token.json` wiederverwendet.

## Nutzung

```powershell
\.venv\Scripts\python.exe .\StudIP_API_Test.py
\.venv\Scripts\python.exe .\studipsync.py
```

Die Synchronisation berücksichtigt die 22 Kurse, die das WiSe 2026/27
überschneiden. Bereits hochgeladene Dateien werden über `sync_state.json`
erkannt. Dateien im Drive werden weder gelöscht noch zurück nach Stud.IP
übertragen.

Für eine automatische Ausführung muss `studipsync.py` regelmäßig gestartet
werden, zum Beispiel über die Windows-Aufgabenplanung.

## Sicherheit

Zugangsdaten stehen ausschließlich in `.env`. `.env`, `credentials.json`,
`token.json`, `sync_state.json` und `temp/` sind per `.gitignore` ausgeschlossen.
