"""Modern Windows desktop interface for StudIPSync."""

import argparse
from datetime import datetime
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading

import customtkinter as ctk
from dotenv import dotenv_values, set_key
from tkinter import filedialog, messagebox

from app_paths import bundled_credentials_path, data_dir
from studipsync import synchronize
from task_scheduler import create_daily_task, delete_daily_task


APP_NAME = "StudIPSync"


def runtime_command():
    """Return the command to run this app's non-interactive sync entry point."""
    if getattr(sys, "frozen", False):
        return sys.executable, None
    return sys.executable, str(Path(__file__).resolve())


def save_configuration(username, password, folder_id, credentials_source):
    """Save secrets and the Google OAuth client outside the packaged executable."""
    directory = data_dir()
    env_file = directory / ".env"
    values = {
        "STUDIP_USER": username.strip(),
        "STUDIP_PASSWORD": password,
        "DRIVE_ROOT_FOLDER_ID": folder_id.strip(),
    }
    if not all(values.values()):
        raise ValueError("Bitte Stud.IP-Zugangsdaten und Drive-Ordner-ID ausfüllen.")

    credentials_target = directory / "credentials.json"
    source = Path(credentials_source) if credentials_source else credentials_target
    if not source.is_file():
        source = bundled_credentials_path() or source
    if not source.is_file():
        raise FileNotFoundError(
            "Die Google-OAuth-Konfiguration fehlt. Bitte die Produktions-EXE neu bauen."
        )
    if source.resolve() != credentials_target.resolve():
        shutil.copy2(source, credentials_target)

    for key, value in values.items():
        set_key(str(env_file), key, value, quote_mode="always")
    return directory


def append_log(directory, message):
    """Append a timestamped status line to the persistent application log."""
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "sync.log").open("a", encoding="utf-8") as log_file:
        log_file.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {message}\n")


def run_sync(log_callback):
    """Run one sync and report failures without hiding them."""
    directory = data_dir()

    def log(message):
        append_log(directory, message)
        log_callback(message)

    try:
        log("Synchronisation wird gestartet.")
        synchronize(directory, log=log)
        return True, "Synchronisation abgeschlossen."
    except Exception as error:
        log(f"Fehler: {error}")
        return False, str(error)


class StudIPSyncApp(ctk.CTk):
    """Single-window interface for configuration, sync, and daily scheduling."""

    def __init__(self):
        super().__init__()
        self.title("StudIPSync")
        self.geometry("760x640")
        self.minsize(640, 500)
        self.configure(fg_color="#f8fafd")
        self.event_queue = queue.Queue()
        self.is_syncing = False

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self._build_ui()
        self._load_configuration()
        self.after(150, self._process_events)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=0, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(20, 8))
        ctk.CTkLabel(
            header,
            text="StudIPSync",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#202124",
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Kursdateien sicher von Stud.IP nach Google Drive übertragen",
            font=ctk.CTkFont(size=14),
            text_color="#5f6368",
        ).pack(anchor="w", pady=(3, 0))

        self.status_card = ctk.CTkFrame(self.content, corner_radius=14, fg_color="white")
        self.status_card.grid(row=1, column=0, sticky="ew", padx=32, pady=10)
        self.status_label = ctk.CTkLabel(
            self.status_card,
            text="Bereit für die Synchronisierung",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#202124",
        )
        self.status_label.pack(anchor="w", padx=20, pady=(16, 2))
        ctk.CTkLabel(
            self.status_card,
            text="Es werden nur neue Dateien hochgeladen. Dateien in Drive bleiben unangetastet.",
            font=ctk.CTkFont(size=12),
            text_color="#5f6368",
        ).pack(anchor="w", padx=20, pady=(0, 16))

        config = ctk.CTkFrame(self.content, corner_radius=14, fg_color="white")
        config.grid(row=2, column=0, sticky="ew", padx=32, pady=10)
        config.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            config,
            text="Verbindung einrichten",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#202124",
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(18, 12))

        self.username_entry = self._add_entry(config, 1, "Stud.IP-Kennung")
        self.password_entry = self._add_entry(config, 2, "Stud.IP-Passwort", show="•")
        self.folder_entry = self._add_entry(config, 3, "Google-Drive-Ordner-ID")

        ctk.CTkLabel(
            config,
            text="Google OAuth",
            text_color="#5f6368",
            font=ctk.CTkFont(size=13),
        ).grid(row=4, column=0, sticky="w", padx=(20, 12), pady=(8, 14))
        self.credentials_source = ""
        self.credentials_label = ctk.CTkLabel(
            config,
            text="Noch keine Datei ausgewählt",
            text_color="#5f6368",
            anchor="w",
        )
        self.credentials_label.grid(row=4, column=1, sticky="ew", pady=(8, 14))
        ctk.CTkButton(
            config,
            text="Datei wählen",
            width=110,
            height=34,
            command=self._choose_credentials,
        ).grid(row=4, column=2, padx=(8, 20), pady=(8, 14))
        ctk.CTkButton(
            config,
            text="Einstellungen speichern",
            height=36,
            fg_color="#e8f0fe",
            hover_color="#d2e3fc",
            text_color="#1967d2",
            command=self._save_settings,
        ).grid(row=5, column=0, columnspan=3, sticky="e", padx=20, pady=(0, 18))

        actions = ctk.CTkFrame(self.content, corner_radius=14, fg_color="white")
        actions.grid(row=3, column=0, sticky="nsew", padx=32, pady=10)
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(
            actions,
            text="Synchronisierung",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#202124",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 10))
        controls = ctk.CTkFrame(actions, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        self.sync_button = ctk.CTkButton(
            controls,
            text="Jetzt synchronisieren",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_sync,
        )
        self.sync_button.pack(side="left")

        ctk.CTkLabel(
            controls,
            text="Täglich um",
            text_color="#5f6368",
        ).pack(side="left", padx=(22, 8))
        self.time_entry = ctk.CTkEntry(controls, width=76, height=36, placeholder_text="08:00")
        self.time_entry.insert(0, "08:00")
        self.time_entry.pack(side="left")
        self.schedule_button = ctk.CTkButton(
            controls,
            text="Automatik aktivieren",
            height=36,
            fg_color="#188038",
            hover_color="#137333",
            command=self._enable_schedule,
        )
        self.schedule_button.pack(side="left", padx=(10, 0))
        self.disable_schedule_button = ctk.CTkButton(
            controls,
            text="Deaktivieren",
            width=105,
            height=36,
            fg_color="#f1f3f4",
            hover_color="#e8eaed",
            text_color="#3c4043",
            command=self._disable_schedule,
        )
        self.disable_schedule_button.pack(side="left", padx=(8, 0))

        self.log_box = ctk.CTkTextbox(
            actions,
            corner_radius=9,
            fg_color="#f8fafd",
            text_color="#3c4043",
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            height=150,
        )
        self.log_box.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 18))
        self.log_box.insert(
            "end",
            "Bereit. Die Automatik läuft über die Windows-Aufgabenplanung und benötigt kein geöffnetes VS Code.\n",
        )
        self.log_box.configure(state="disabled")

        ctk.CTkLabel(
            self.content,
            text="Windows kann den PC aus dem Energiesparmodus wecken; ausgeschaltet läuft er nicht.",
            text_color="#70757a",
            font=ctk.CTkFont(size=11),
        ).grid(row=4, column=0, pady=(0, 14))

    def _add_entry(self, parent, row, label, show=None):
        ctk.CTkLabel(
            parent,
            text=label,
            text_color="#5f6368",
            font=ctk.CTkFont(size=13),
        ).grid(row=row, column=0, sticky="w", padx=(20, 12), pady=7)
        entry = ctk.CTkEntry(parent, height=36, show=show)
        entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(0, 20), pady=7)
        return entry

    def _load_configuration(self):
        directory = data_dir()
        values = dotenv_values(directory / ".env")
        self.username_entry.insert(0, values.get("STUDIP_USER") or "")
        self.password_entry.insert(0, values.get("STUDIP_PASSWORD") or "")
        self.folder_entry.insert(0, values.get("DRIVE_ROOT_FOLDER_ID") or "")
        credentials_file = directory / "credentials.json"
        if credentials_file.is_file():
            self.credentials_source = str(credentials_file)
            self.credentials_label.configure(text="Google-Zugangsdaten vorhanden")
        else:
            bundled_credentials = bundled_credentials_path()
            if bundled_credentials:
                self.credentials_source = str(bundled_credentials)
                self.credentials_label.configure(text="Google-Zugangsdaten integriert")

    def _choose_credentials(self):
        path = filedialog.askopenfilename(
            title="Google-OAuth-Datei auswählen",
            filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")],
        )
        if path:
            self.credentials_source = path
            self.credentials_label.configure(text=Path(path).name)

    def _save_settings(self, show_confirmation=True):
        try:
            directory = save_configuration(
                self.username_entry.get(),
                self.password_entry.get(),
                self.folder_entry.get(),
                self.credentials_source,
            )
        except (OSError, ValueError) as error:
            messagebox.showerror("Einstellungen", str(error), parent=self)
            return None

        self.credentials_source = str(directory / "credentials.json")
        self.credentials_label.configure(text="Google-Zugangsdaten gespeichert")
        if show_confirmation:
            messagebox.showinfo("Einstellungen", "Einstellungen wurden gespeichert.", parent=self)
        return directory

    def _start_sync(self):
        if self.is_syncing:
            return
        if self._save_settings(show_confirmation=False) is None:
            return
        self.is_syncing = True
        self.sync_button.configure(state="disabled", text="Synchronisierung läuft …")
        self.status_label.configure(text="Synchronisierung läuft …")
        def worker():
            success, message = run_sync(self.event_queue.put)
            self.event_queue.put(("finished", success, message))

        threading.Thread(target=worker, daemon=True).start()

    def _enable_schedule(self):
        if self._save_settings(show_confirmation=False) is None:
            return
        executable, script = runtime_command()
        try:
            create_daily_task(self.time_entry.get().strip(), executable, script)
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            details = (
                getattr(error, "stderr", None)
                or getattr(error, "stdout", None)
                or str(error)
            )
            messagebox.showerror("Automatik", details, parent=self)
            return
        self._append_log(f"Tägliche Synchronisierung für {self.time_entry.get()} eingerichtet.")
        messagebox.showinfo(
            "Automatik aktiviert",
            "Die tägliche Aufgabe wurde eingerichtet. Sie läuft auch ohne VS Code, "
            "solange du in Windows angemeldet bist. Aus dem Energiesparmodus kann Windows ihn wecken.",
            parent=self,
        )

    def _disable_schedule(self):
        try:
            delete_daily_task()
        except (OSError, subprocess.CalledProcessError) as error:
            details = (
                getattr(error, "stderr", None)
                or getattr(error, "stdout", None)
                or str(error)
            )
            if "cannot find" not in details.lower() and "nicht finden" not in details.lower():
                messagebox.showerror("Automatik", details, parent=self)
                return
        self._append_log("Tägliche Synchronisierung wurde deaktiviert.")

    def _append_log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _process_events(self):
        try:
            while True:
                event = self.event_queue.get_nowait()
                if isinstance(event, tuple) and event[0] == "finished":
                    _, success, message = event
                    self.is_syncing = False
                    self.sync_button.configure(state="normal", text="Jetzt synchronisieren")
                    self.status_label.configure(
                        text="Synchronisierung abgeschlossen" if success else "Synchronisierung fehlgeschlagen"
                    )
                    if not success:
                        messagebox.showerror("Synchronisierung fehlgeschlagen", message, parent=self)
                else:
                    self._append_log(event)
        except queue.Empty:
            pass
        self.after(150, self._process_events)


def main():
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Synchronisiert ohne grafische Oberfläche (für die Aufgabenplanung).",
    )
    args = parser.parse_args()

    if args.sync:
        success, _ = run_sync(lambda _message: None)
        return 0 if success else 1

    ctk.set_appearance_mode("light")
    app = StudIPSyncApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
