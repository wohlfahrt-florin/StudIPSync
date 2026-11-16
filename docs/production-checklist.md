# Produktions-Checkliste für Google OAuth

## Google Cloud

- [ ] Separates Google-Cloud-Projekt für Produktion anlegen.
- [ ] Google Drive API aktivieren.
- [ ] Google Picker API aktivieren.
- [ ] OAuth-App-Audience auf `External` setzen.
- [ ] App-Name, Support-E-Mail und Entwicklerkontakt eintragen.
- [ ] `https://www.googleapis.com/auth/drive.file` als benötigten Scope
      dokumentieren.
- [ ] Homepage und veröffentlichte Datenschutzerklärung auf einer eigenen,
      verifizierten Domain hinterlegen.
- [ ] Desktop-OAuth-Client anlegen und `credentials.json` lokal speichern.
- [ ] OAuth-Consent-Screen mit einem Testkonto prüfen.
- [ ] Mit einem Testkonto Google-Anmeldung und Picker-Ordnerauswahl prüfen.
- [ ] Nach erfolgreicher Prüfung auf `In production` veröffentlichen.

## StudIPSync-Release

- [ ] `credentials.json` nicht als lose Datei committen oder verteilen.
- [ ] Die OAuth-Desktop-App-Konfiguration `credentials.json` für den Build
      bereitstellen; sie wird in die EXE eingebettet.
- [ ] Inno Setup 6 installieren und `ISCC.exe` zum `PATH` hinzufügen oder am
      Standardinstallationsort installieren.
- [ ] `packaging/windows/build_windows.ps1` ausführen; es erzeugt die EXE und
      `dist/StudIPSync-Setup-1.0.0.exe`.
- [ ] Den Installer auf einem zweiten Windows-PC installieren, starten und
      über Windows **Installierte Apps** wieder deinstallieren.
- [ ] Prüfen, dass ein zweites Windows-Konto sich mit einem eigenen Google-
      Konto anmelden und einen eigenen Drive-Ordner auswählen kann.
- [ ] Mit einem Test-Drive-Ordner synchronisieren.
- [ ] Erneuten Lauf testen: bereits synchronisierte Dateien dürfen nicht erneut
      hochgeladen werden.
- [ ] Erst danach den Installer als Release-Asset verteilen.

## Google-Drive-Auswahl

Die Windows-App verwendet den Google-Desktop-Picker: Nutzer melden sich im
Browser bei Google an, wählen dort einen Drive-Ordner aus und kehren zur App
zurück. Die Ordner-ID wird für die Drive API intern gespeichert; die App zeigt
den Ordnernamen an. `credentials.json` ist die OAuth-App-Konfiguration des
Projekts und wird beim Einrichten in den jeweiligen lokalen App-Datenordner
kopiert; sie ist nicht das persönliche Google-Konto. Die Anmeldung jedes
Nutzers erzeugt separat ein `token.json` in `%LOCALAPPDATA%\StudIPSync`.
Dadurch bleiben Tokens und Einstellungen pro Windows-Konto getrennt. Nach
Änderungen muss eine neue EXE gebaut und als neues Release verteilt werden.

## Windows-Installer

`packaging/windows/StudIPSync.iss` definiert einen Inno Setup-Installer für
den aktuellen Windows-Benutzer. Er erstellt einen Startmenü-Eintrag und bietet
optional eine Desktopverknüpfung an. Die Deinstallation entfernt die
geplante Aufgabe, bewahrt aber persönliche Einstellungen unter
`%LOCALAPPDATA%\StudIPSync`; diese können vor der Deinstallation über den
Papierkorb-Button in der App gelöscht werden.
