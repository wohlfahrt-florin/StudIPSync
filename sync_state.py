"""Persistenter Status der bereits synchronisierten Stud.IP-Dateien."""

import json
from pathlib import Path


class SyncState:
    """Speichert erfolgreiche Uploads, ohne den Inhalt von Drive auszulesen."""

    def __init__(self, path):
        """Legt den Speicherort der JSON-Statusdatei fest."""
        self.path = Path(path)
        self.entries = self._load()

    def _load(self):
        """Lädt vorhandene Einträge oder startet mit einem leeren Status."""
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SystemExit(
                f"Die Statusdatei {self.path} enthält kein gültiges JSON."
            ) from error

    def contains(self, key):
        """Prüft, ob die Stud.IP-Datei bereits erfolgreich hochgeladen wurde."""
        return key in self.entries

    def remember(self, key, details):
        """Speichert eine Datei erst nach erfolgreichem Drive-Upload."""
        self.entries[key] = details
        self.path.write_text(
            json.dumps(self.entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
