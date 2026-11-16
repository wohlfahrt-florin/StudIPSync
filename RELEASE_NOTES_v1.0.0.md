# Stud.IPSync v1.0.0

Stud.IPSync synchronisiert neue Dateien aus Stud.IP-Kursen automatisch in einen ausgewählten Google-Drive-Ordner.

## Highlights

- Einseitige Synchronisierung von Stud.IP nach Google Drive
- Automatische Erkennung und Übertragung neuer Kursdateien
- Auswahl des Google-Drive-Zielordners über den Google-Drive-Picker
- Persönliche Google-Anmeldung mit lokal gespeichertem OAuth-Token
- Tägliche Synchronisierung über die Windows-Aufgabenplanung
- Bestehende Windows-Aufgaben werden beim erneuten Aktivieren ersetzt, statt doppelt angelegt zu werden
- Kompakte Windows-Oberfläche mit zentral positionierten Fenstern
- Einheitliches `Stud.IPSync`-Branding in der Anwendung und auf der Website
- Neue Dateien werden im Log nach Datum sortiert angezeigt

## Windows-Start

Die Anwendung kann direkt aus dem Quellcode gestartet werden:

```powershell
.\.venv\Scripts\python.exe .\run_app.py
```

Für eine portable Windows-Version steht der Build unter `packaging/windows/build_windows.ps1` zur Verfügung.

## Hinweise

- Beim ersten Start werden Stud.IP-Zugangsdaten und ein Google-Drive-Zielordner benötigt.
- Der aktuelle Google-Desktop-Picker erlaubt die Auswahl vorhandener Ordner, aber keine Ordnererstellung innerhalb des Pickers.
- Die Synchronisierung löscht keine bestehenden Dateien in Google Drive.
- Zugangsdaten, OAuth-Token und lokale Statusdateien bleiben auf dem Computer des Benutzers.
