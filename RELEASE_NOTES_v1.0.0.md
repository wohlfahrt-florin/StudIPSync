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

## Download und Start

1. [Release v1.0.0 öffnen](https://github.com/wohlfahrt-florin/StudIPSync/releases/tag/v1.0.0).
2. Unter **Assets** die Datei `StudIPSync.exe` herunterladen und starten.
3. Bei Stud.IP anmelden, danach mit Google anmelden und den Drive-Zielordner auswählen.

Hinweis: Die EXE muss noch als Release-Asset hochgeladen werden. Bis dahin wird sie unter **Assets** nicht angezeigt.

## Hinweise

- Beim ersten Start werden Stud.IP-Zugangsdaten und ein Google-Drive-Zielordner benötigt.
- Der aktuelle Google-Desktop-Picker erlaubt die Auswahl vorhandener Ordner, aber keine Ordnererstellung innerhalb des Pickers.
- Die Synchronisierung löscht keine bestehenden Dateien in Google Drive.
- Zugangsdaten, OAuth-Token und lokale Statusdateien bleiben auf dem Computer des Benutzers.
