# StudIPSync

Synchronisiert neue Dateien aus Stud.IP-Kursen nach Google Drive.

## Einrichtung

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Für einen Start aus dem Quellcode benötigt der Projektordner `credentials.json`
mit der OAuth-Desktop-App-Konfiguration des Projekts. In der veröffentlichten
EXE ist diese App-Konfiguration bereits enthalten; Nutzer müssen keine eigene
`credentials.json` besorgen. Beim ersten Start werden Stud.IP-Zugangsdaten
abgefragt. Anschließend meldet sich jeder im Browser mit dem eigenen
Google-Konto an und wählt den Zielordner im Drive-Picker aus. Das persönliche
Google-Anmeldungstoken wird lokal gespeichert.

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
