# Programmablauf und Objekte

Diese Seite zeigt, welche Programmstarts es gibt, wann dabei Objekte entstehen
und wie die wichtigsten Aufrufe zusammenhängen. Eine Klassendefinition ist
zunächst nur ein Bauplan. Ein Objekt entsteht erst beim Aufruf der Klasse,
zum Beispiel mit `StudIPClient(...)`.

## Desktop-App: Start der Oberfläche

Start mit `python .\run_app.py` oder durch Öffnen der Windows-App:

```text
app.py
└─ if __name__ == "__main__"
   └─ main()
      ├─ Argumente lesen
      └─ kein --sync
         ├─ app = StudIPSyncApp()
         │  └─ StudIPSyncApp.__init__()
         │     ├─ CTk-Hauptfenster initialisieren
         │     ├─ event_queue und is_syncing anlegen
         │     ├─ _build_ui()
         │     │  ├─ Frames, Labels, Buttons und Eingabefelder erzeugen
         │     │  └─ Button-Aktionen mit App-Methoden verbinden
         │     ├─ _load_configuration()
         │     └─ regelmäßige Verarbeitung der Event-Queue einplanen
         └─ app.mainloop()
            └─ wartet auf Klicks und verarbeitet UI-Ereignisse
```

`StudIPSyncApp` erbt von `customtkinter.CTk`. Die Widgets sind ebenfalls
Objekte. Sie werden in `_build_ui()` erzeugt und meist als `self.<name>`
gespeichert, damit andere Methoden der Fensterinstanz sie aktualisieren können.

### Klick auf „Jetzt synchronisieren“

```text
Klick auf Sync-Button
└─ StudIPSyncApp._start_sync()
   ├─ Einstellungen speichern und Eingaben prüfen
   ├─ worker-Funktion definieren
   └─ threading.Thread(...).start()
      └─ worker()
         └─ run_sync(event_queue.put)
            ├─ Log-Schreiber definieren
            └─ synchronize(data_dir(), log=log)
               ├─ StudIPClient(username, password)
               ├─ aktuelle Person und Semesterkurse lesen
               ├─ DriveClient(project_dir, root_folder_id)
               ├─ SyncState(project_dir / "sync_state.json")
               └─ pro Kurs und neue Datei:
                  ├─ Stud.IP-Datei herunterladen
                  ├─ in Google Drive hochladen
                  └─ erfolgreichen Upload im SyncState speichern
         └─ Ergebnis in die Event-Queue legen
            └─ _process_events() aktualisiert Status und Oberfläche
```

Die Synchronisierung läuft in einem Hintergrund-Thread, damit das Fenster
währenddessen reagieren kann. Die Widgets werden über die Event-Queue und
`_process_events()` von der UI-Schleife aktualisiert.

Die drei zentralen Arbeitsobjekte entstehen **pro Synchronisierungslauf** in
`synchronize()`:

| Objekt | Erzeugt in | Aufgabe |
|---|---|---|
| `StudIPClient` | `studipsync.synchronize()` | Stud.IP-API lesen und Dateien herunterladen |
| `DriveClient` | `studipsync.synchronize()` | Google-Drive-Zugriff, Kursordner und Uploads |
| `SyncState` | `studipsync.synchronize()` | Bereits erfolgreich synchronisierte Dateien speichern |

Die Klassen implementieren ihre Aufgaben in
[studip_client.py](../studipsync/studip_client.py),
[drive_client.py](../studipsync/drive_client.py) und
[sync_state.py](../studipsync/sync_state.py). Die Ablaufsteuerung liegt in
[sync.py](../studipsync/sync.py).

### Klick auf „Ordner auswählen“

```text
Klick auf „Ordner auswählen“
└─ _choose_drive_folder()
   ├─ Einstellungen speichern
   └─ Hintergrund-Thread
      └─ pick_drive_folder(data_dir())
         └─ Google-Anmeldung und Drive-Ordnerauswahl im Browser
   └─ Ergebnis über Event-Queue an _process_events()
```

Für diese Auswahl wird nicht erst ein `DriveClient` erzeugt.
`pick_drive_folder` ist ein eigener Ablauf im Modul
[drive_client.py](../studipsync/drive_client.py). Die ausgewählte Ordner-ID
wird intern gespeichert; in der Oberfläche wird der Ordnername angezeigt.
Die OAuth-App-Konfiguration wird aus der EXE in den lokalen App-Datenordner
kopiert. Das persönliche Google-Anmeldungstoken wird separat als `token.json`
dort gespeichert, sodass jedes Windows-Konto sein eigenes Google-Konto nutzt.

## Synchronisierung ohne Oberfläche

Die Windows-Aufgabenplanung startet die App mit `--sync`. Das ist derselbe
Einstiegspunkt, aber ohne Fenster:

```text
app.py --sync
└─ main()
   └─ run_sync(...)
      └─ synchronize(...)
         ├─ StudIPClient(...)
         ├─ DriveClient(...)
         └─ SyncState(...)
```

Beim Einrichten der Automatik erzeugt `_enable_schedule()` eine Windows-Aufgabe.
`task_scheduler.py` speichert dafür den Befehl mit `--sync`. Später startet
Windows diesen Befehl selbstständig; die Oberfläche und `mainloop()` laufen
dabei nicht.

 Auch `python -m studipsync.sync` startet direkt den Synchronisationsablauf:

```text
studipsync.py
└─ if __name__ == "__main__"
   └─ synchronize()
```

## Terminbeobachter

`python -m studipsync.calendar_watch` ist ein unabhängiger Kommandozeilenablauf. Er
erstellt einen `StudIPClient`, liest Kurse und Termine und vergleicht sie mit
dem gespeicherten Terminstand. Er verwendet weder die Desktop-App noch die
Google-Drive-Synchronisierung:

```text
calendar_watch.py
└─ main()
   ├─ Argumente und gespeicherten Stand prüfen
   ├─ StudIPClient(username, password)
   ├─ Benutzer und Semesterkurse lesen
   ├─ Termine erfassen und mit dem vorherigen Stand vergleichen
   └─ Änderungen anzeigen und optional als geprüft speichern
```

## Wo sind die Einstiege?

| Start | Einstieg | Ergebnis |
|---|---|---|
| Desktop-App | `app.py` → `main()` | Fenster und UI-Ereignisschleife |
| Geplante Synchronisierung | `app.py --sync` → `main()` | Synchronisierung ohne Fenster |
| Direkter Sync-Aufruf | `studipsync.py` → `synchronize()` | Synchronisierung ohne Fenster |
| Terminbeobachtung | `calendar_watch.py` → `main()` | Bericht über neue/geänderte Termine |

Tests und Skripte unter `tests/` und `scripts/` sind weitere, separate
Programmeinstiege für Entwicklung und manuelle Prüfungen. Sie werden beim
normalen Start der Desktop-App nicht automatisch ausgeführt.

## Beim Ändern der Anwendung

Wenn ein neues Objekt oder ein neuer Startweg dazukommt, ergänze den passenden
Baum und die Einstiegspunkt-Tabelle. Entscheidend sind:

1. Wo wird die Klasse mit `Klassenname(...)` aufgerufen?
2. Wer ruft diese Stelle auf?
3. Wird das beim Programmstart, durch eine UI-Aktion oder in einem separaten
   Prozess ausgelöst?
