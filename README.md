# StudIPSync

Synchronisiert neue Dateien aus den Stud.IP-Kursen der MLU Halle in einen
Google-Drive-Ordner – ein Unterordner pro Kurs.

> Richtung: **Stud.IP → Google Drive**. Änderungen im Google Drive werden nicht
> nach Stud.IP zurückgeschrieben.

## Struktur

```text
StudIPSync/
├─ studipsync/       Python-Anwendung als Paket
├─ tests/             Automatisierte Tests
├─ scripts/           Manuelle API- und Integrationstests
├─ site/              Statische Website
├─ packaging/         Windows- und Docker-Builds
├─ docs/              Ablauf- und Produktionsdokumentation
├─ assets/            Icons und Programmressourcen
├─ run_app.py         Einstiegspunkt für die Desktop-App
└─ requirements.txt   Python-Abhängigkeiten
```

Die Laufzeitdaten (`.env`, OAuth-Dateien, `temp/`, `sync_state.json`) bleiben
im Projektstamm, werden aber nicht versioniert.

## Dateien

| Datei | Zweck |
|---|---|
| `studipsync/sync.py` | Einstiegspunkt und Ablaufsteuerung der Synchronisation |
| `studipsync/studip_client.py` | Authentifizierter Zugriff auf die Stud.IP-JSON-API |
| `studipsync/drive_client.py` | Google-OAuth, Kursordner und Uploads |
| `studipsync/sync_state.py` | Status bereits hochgeladener Stud.IP-Dateien |
| `calendar_watch.py` | Meldet neue/geänderte Stud.IP-Termine zur manuellen Prüfung |
| `tests/` | Automatisierte Tests |
| `scripts/` | Manuelle API- und Integrationsskripte |
| `packaging/` | Windows-EXE- und Docker-Konfiguration |
| `site/` | Statische Homepage, Datenschutz und Impressum |
| `docs/` | Produktions- und Veröffentlichungsdokumentation |
| `.env.example` | Vorlage für Zugangsdaten und Drive-Zielordner |
| `credentials.json` / `token.json` | Google-OAuth – nicht ins Repository legen |
| `sync_state.json` | Lokaler Status bereits hochgeladener Stud.IP-Dateien |
| `calendar_watch_state.json` | Lokaler Ausgangsbestand für den Terminvergleich |
| `app.py` | Grafische Windows-Oberfläche und Einstiegspunkt der Desktop-App |
| `task_scheduler.py` | Einrichtung der täglichen Windows-Aufgabe |

Eine Ablaufskizze mit Programmstarts und dem Zeitpunkt der Objekterzeugung
steht in [docs/ablauf-und-objekte.md](docs/ablauf-und-objekte.md).

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

Die automatisierten Tests startest du aus dem Projektordner mit:

```powershell
\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

## Nutzung

```powershell
\.venv\Scripts\python.exe .\scripts\StudIP_API_Test.py
\.venv\Scripts\python.exe -m studipsync.sync
```

Die Synchronisation berücksichtigt die 22 Kurse, die das WiSe 2026/27
überschneiden. Bereits hochgeladene Dateien werden über `sync_state.json`
erkannt. Dateien im Drive werden weder gelöscht noch zurück nach Stud.IP
übertragen.

## Desktop-App für Windows

Nach der Installation der Abhängigkeiten kannst du die Oberfläche direkt starten:

```powershell
\.venv\Scripts\python.exe .\run_app.py
```

In der App trägst du Stud.IP-Kennung und Passwort ein und wählst den Google-
Drive-Zielordner aus. Die Google-OAuth-Konfiguration wird automatisch aus der
Produktions-EXE oder dem Projektordner verwendet; eine Datei muss in der App
nicht ausgewählt werden. Die Einstellungen, das Google-Anmeldetoken und der
Synchronisationsstatus werden lokal im Projektordner
gespeichert, wenn du Python verwendest. In der erstellten EXE liegen sie unter
`%LOCALAPPDATA%\StudIPSync`; Zugangsdaten werden nicht in die EXE eingebaut.
Beim ersten Start aus dem Projektordner übernimmt die EXE vorhandene
Einstellungen, OAuth-Anmeldung und den Synchronisationsstatus, damit bereits
hochgeladene Dateien nicht erneut übertragen werden. Danach öffnet sich bei
Bedarf der Browser für die Google-Anmeldung.

Für eine Weitergabe an andere Benutzer wird der Desktop-OAuth-Client beim
Build aus der lokalen `credentials.json` in die EXE eingebettet. Die Datei
bleibt aus dem Repository ausgeschlossen. Lege sie lokal in den Projektordner
und führe danach `packaging\windows\build_windows.ps1` aus. Die Benutzer müssen
keine OAuth-Datei selbst auswählen oder herunterladen; sie melden sich beim
ersten Start im Browser an und erlauben den Drive-Zugriff.

Mit **Jetzt synchronisieren** startest du einen Lauf manuell. **Automatik
aktivieren** erstellt eine tägliche Aufgabe in der Windows-Aufgabenplanung.
Sie läuft unabhängig von VS Code, solange du in Windows angemeldet bist.
Windows darf den PC dafür aus dem Energiesparmodus wecken; bei ausgeschaltetem
PC läuft sie nicht. Die letzte Ausgabe ist in der App und in `sync.log`
sichtbar. Mit **Deaktivieren** entfernst du die tägliche Aufgabe wieder.

Zum Erstellen der portablen Windows-App führe im Projektordner aus:

```powershell
.\packaging\windows\build_windows.ps1
```

Die Datei `dist\StudIPSync.exe` kann anschließend gestartet und an einen
passenden Ort kopiert werden. Bei einem anderen PC müssen dort die Zugangsdaten
und die Google-OAuth-Datei erneut in der App eingerichtet werden.

## Stud.IP-Termine beobachten

Der Terminbeobachter liest die Termine aus den belegten Kursen des Zielsemesters.
Beim einmaligen Start mit `--initialize` wird der aktuelle Bestand als
Ausgangspunkt gespeichert; bestehende Kalendereinträge werden dabei nicht
verändert. Danach zeigt ein normaler Lauf neue oder geänderte zukünftige Termine
mit Kurs, Zeit und Beschreibung an. Bitte prüfe in Stud.IP manuell, ob ein
Termin für deine Seminargruppe 9 gilt. Das Programm trägt nichts in Google
Calendar ein.

```powershell
\.venv\Scripts\python.exe -m studipsync.calendar_watch --initialize
\.venv\Scripts\python.exe -m studipsync.calendar_watch
```

`--report-only` zeigt Änderungen ohne Rückfrage und ohne den Status
fortzuschreiben. Wiederkehrende Stud.IP-Termine werden als Serienhinweis
angezeigt; der Beobachter legt dafür keine Kalendereinträge an.

## Sicherheit

Zugangsdaten stehen ausschließlich in `.env`. `.env`, `credentials.json`,
`token.json`, `sync_state.json` und `temp/` sind per `.gitignore` ausgeschlossen.
