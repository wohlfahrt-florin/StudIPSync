# StudIPSync

Synchronisiert neue Dateien aus Stud.IP-Kursen nach Google Drive.

## Einrichtung

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Lege `credentials.json` (Google-OAuth-Desktop-App mit aktivierter Drive API) ins Projektverzeichnis. Beim ersten Start werden Stud.IP-Zugang und Zielordner abgefragt.

## Start

```powershell
.\.venv\Scripts\python.exe .\run_app.py
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

## Windows-Build

```powershell
.\packaging\windows\build_windows.ps1
```

## Sicherheit

`.env`, `credentials.json`, Token, Statusdateien und temporäre Daten niemals committen. Die Synchronisierung läuft nur von Stud.IP nach Google Drive; bestehende Drive-Dateien werden nicht gelöscht.

Technische Details: [docs/ablauf-und-objekte.md](docs/ablauf-und-objekte.md)
