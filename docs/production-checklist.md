# Produktions-Checkliste für Google OAuth

## Google Cloud

- [ ] Separates Google-Cloud-Projekt für Produktion anlegen.
- [ ] Google Drive API aktivieren.
- [ ] OAuth-App-Audience auf `External` setzen.
- [ ] App-Name, Support-E-Mail und Entwicklerkontakt eintragen.
- [ ] `https://www.googleapis.com/auth/drive.file` als benötigten Scope
      dokumentieren.
- [ ] Homepage und veröffentlichte Datenschutzerklärung auf einer eigenen,
      verifizierten Domain hinterlegen.
- [ ] Desktop-OAuth-Client anlegen und `credentials.json` lokal speichern.
- [ ] OAuth-Consent-Screen mit einem Testkonto prüfen.
- [ ] Nach erfolgreicher Prüfung auf `In production` veröffentlichen.

## StudIPSync-Release

- [ ] `credentials.json` niemals committen oder veröffentlichen.
- [ ] `credentials.json` in den Projektordner legen.
- [ ] `build_windows.ps1` ausführen.
- [ ] Die erzeugte `dist/StudIPSync.exe` auf einem zweiten Windows-PC testen.
- [ ] Mit einem Test-Drive-Ordner synchronisieren.
- [ ] Erneuten Lauf testen: bereits synchronisierte Dateien dürfen nicht erneut
      hochgeladen werden.
- [ ] Erst danach die EXE an Freunde verteilen.

## Noch offen

Die aktuelle Version fragt die Zielordner-ID manuell ab. Für eine besonders
komfortable öffentliche Version sollte anschließend Google Picker integriert
werden, damit Benutzer den Drive-Ordner direkt in einem Google-Auswahldialog
auswählen können.
