# Stud.IPSync

Synchronisiert neue Dateien aus deinen Stud.IP-Kursen automatisch nach Google Drive.

## Download für Windows

**[Stud.IPSync v1.0.0 herunterladen](https://github.com/wohlfahrt-florin/StudIPSync/releases/tag/v1.0.0)**

Auf der Release-Seite die Datei **`StudIPSync.exe`** unter „Assets“ herunterladen und starten. Du brauchst weder Python noch den Quellcode.

> Hinweis: Das Release ist derzeit als Vorabversion gekennzeichnet. Die EXE muss noch als Release-Asset hochgeladen werden; bis dahin wird sie auf der Release-Seite nicht zum Download angezeigt.

## Schnellstart

1. `StudIPSync.exe` starten.
2. Deine Stud.IP-Zugangsdaten eingeben.
3. Im Browser mit deinem Google-Konto anmelden und den Zielordner in Google Drive auswählen.
4. Auf **Speichern** klicken. Neue Kursdateien werden automatisch synchronisiert.

Über **Jetzt synchronisieren** kannst du die Übertragung jederzeit manuell starten. Die tägliche automatische Synchronisierung lässt sich im Hauptfenster aktivieren.

## Datenschutz und Verhalten

- Die Synchronisierung läuft nur von Stud.IP nach Google Drive.
- Bereits vorhandene Dateien in Google Drive werden nicht gelöscht.
- Google-Anmeldedaten und Synchronisierungsstatus werden lokal auf deinem Computer gespeichert.
- Die mitgelieferte OAuth-Konfiguration ist für die Anmeldung der App bestimmt. Du brauchst keine eigene `credentials.json`.

## Für Entwickler

### Aus dem Quellcode starten

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe .\run_app.py
```

Für einen Start aus dem Quellcode wird `credentials.json` mit der OAuth-Desktop-App-Konfiguration im Projektordner benötigt.

### Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

### Windows-Build erstellen

```powershell
.\packaging\windows\build_windows.ps1
```

Technische Details: [docs/ablauf-und-objekte.md](docs/ablauf-und-objekte.md)
