# StudIPSync

Synchronisiert Dateien aus meinen Stud.IP-Kursen (MLU Halle) automatisch in einen Google-Drive-Ordner – ein Unterordner pro Kurs.

> Status: **in Entwicklung** – Login & API werden noch getestet.
> Ausführliche Doku, Debugging-Logs und Tests liegen in Obsidian (`StudIPSync/`).

## Dateien

| Datei | Zweck |
|---|---|
| `studipsync.py` | Hauptskript: Login → Kurse finden → Dateien laden → Drive-Upload |
| `test.py` | Debug-Skript für den Cookie-/Formular-Login |
| `StudIP_API_Test.py` | Test der Stud.IP JSON:API (`/jsonapi.php/v1`) |
| `.env.example` | Vorlage für Zugangsdaten (wird zu `.env`) |
| `credentials.json` / `token.json` | Google-OAuth – **nicht im Repo** (siehe `.gitignore`) |

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # danach .env ausfüllen
```

`credentials.json` aus der Google Cloud Console (OAuth-Client „Desktop-App“, Drive API aktiviert) in diesen Ordner legen. Beim ersten Start öffnet sich der Browser, danach wird `token.json` wiederverwendet.

## Nutzung

```powershell
python StudIP_API_Test.py   # 1. API-Zugang prüfen
python test.py              # 2. Formular-Login prüfen
python studipsync.py        # 3. Synchronisation
```

## Sicherheit

Zugangsdaten stehen ausschließlich in `.env`. `.env`, `credentials.json`, `token.json` und `temp/` sind per `.gitignore` ausgeschlossen.
