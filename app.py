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
from tkinter import messagebox

from app_paths import bundled_credentials_path, data_dir
from drive_client import pick_drive_folder
from studipsync import synchronize
from task_scheduler import create_daily_task, delete_daily_task


APP_NAME = "StudIPSync"
COLORS = {
    "background": "#f7f8f5",
    "surface": "#ffffff",
    "ink": "#172019",
    "muted": "#68736b",
    "line": "#dfe5df",
    "green": "#2f6b4f",
    "green_dark": "#1f513a",
    "green_light": "#e3eee5",
    "log": "#f2f5f1",
}


def runtime_command():
    """Return the command to run this app's non-interactive sync entry point."""
    if getattr(sys, "frozen", False):
        return sys.executable, None
    return sys.executable, str(Path(__file__).resolve())


def save_configuration(username, password, folder_id, folder_name=""):
    """Save secrets and the Google OAuth client outside the packaged executable."""
    directory = data_dir()
    env_file = directory / ".env"
    values = {
        "STUDIP_USER": username.strip(),
        "STUDIP_PASSWORD": password,
        "DRIVE_ROOT_FOLDER_ID": folder_id.strip(),
        "DRIVE_ROOT_FOLDER_NAME": folder_name.strip(),
    }
    if not values["STUDIP_USER"] or not values["STUDIP_PASSWORD"]:
        raise ValueError("Bitte Stud.IP-Kennung und Passwort ausfüllen.")

    credentials_target = directory / "credentials.json"
    source = credentials_target
    if not source.is_file():
        source = bundled_credentials_path()
    if source is None or not source.is_file():
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
        self.geometry("940x720")
        self.minsize(820, 620)
        self.configure(fg_color=COLORS["background"])
        self.event_queue = queue.Queue()
        self.is_syncing = False

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        self._build_ui()
        self._load_configuration()
        self.after(150, self._process_events)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=COLORS["line"],
            scrollbar_button_hover_color="#cbd4cc",
        )
        self.content.grid(row=0, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1, uniform="content")
        self.content.grid_columnconfigure(1, weight=1, uniform="content")

        header = ctk.CTkFrame(self.content, fg_color="transparent", height=78)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=38, pady=(24, 18))
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            header,
            text="S",
            width=38,
            height=38,
            corner_radius=10,
            fg_color=COLORS["green"],
            text_color="white",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 12))
        ctk.CTkLabel(
            header,
            text="StudIPSync",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["ink"],
        ).grid(row=0, column=1, sticky="sw")
        ctk.CTkLabel(
            header,
            text="Stud.IP  →  Google Drive",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"],
        ).grid(row=1, column=1, sticky="nw")
        ctk.CTkLabel(
            header,
            text="LOKALE WINDOWS-APP",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["muted"],
        ).grid(row=0, column=2, rowspan=2, sticky="e")

        self.status_card = ctk.CTkFrame(
            self.content,
            corner_radius=18,
            fg_color=COLORS["green_dark"],
        )
        self.status_card.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=38,
            pady=(0, 20),
        )
        self.status_card.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(
            self.status_card,
            text="Bereit für die Synchronisierung",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white",
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=24, pady=(19, 2))
        ctk.CTkLabel(
            self.status_card,
            text="Neue Kursdateien aus Stud.IP – automatisch in eurem Google Drive.",
            font=ctk.CTkFont(size=12),
            text_color="#c8d8cc",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 19))

        config = ctk.CTkFrame(
            self.content,
            corner_radius=18,
            fg_color=COLORS["surface"],
            border_width=1,
            border_color=COLORS["line"],
        )
        config.grid(row=2, column=0, sticky="nsew", padx=(38, 10), pady=(0, 20))
        config.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            config,
            text="Verbindung",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["ink"],
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(22, 2))
        ctk.CTkLabel(
            config,
            text="Zugangsdaten und Zielordner",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 17))

        self.username_entry = self._add_entry(config, 2, "Stud.IP-Kennung")
        self.password_entry = self._add_entry(config, 4, "Stud.IP-Passwort", show="•")

        ctk.CTkLabel(
            config,
            text="Google-Drive-Zielordner",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11, weight="bold"),
        ).grid(row=6, column=0, sticky="w", padx=24, pady=(0, 5))
        folder_row = ctk.CTkFrame(config, fg_color="transparent")
        folder_row.grid(row=7, column=0, sticky="ew", padx=24, pady=(0, 12))
        folder_row.grid_columnconfigure(0, weight=1)
        self.folder_label = ctk.CTkLabel(
            folder_row,
            text="Noch kein Ordner ausgewählt",
            text_color=COLORS["muted"],
            anchor="w",
            font=ctk.CTkFont(size=12),
        )
        self.folder_label.grid(row=0, column=0, sticky="ew")
        self.picker_button = ctk.CTkButton(
            folder_row,
            text="Ordner auswählen",
            width=118,
            height=36,
            corner_radius=9,
            fg_color=COLORS["green_light"],
            hover_color="#d4e5d7",
            text_color=COLORS["green_dark"],
            command=self._choose_drive_folder,
        )
        self.picker_button.grid(row=0, column=1, padx=(10, 0))
        self.folder_id = ""
        self.folder_name = ""

        ctk.CTkLabel(
            config,
            text="Google OAuth",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11, weight="bold"),
        ).grid(row=8, column=0, sticky="w", padx=24, pady=(2, 5))
        self.credentials_label = ctk.CTkLabel(
            config,
            text="Google-OAuth-Konfiguration wird automatisch verwendet",
            text_color=COLORS["muted"],
            anchor="w",
            font=ctk.CTkFont(size=12),
        )
        self.credentials_label.grid(row=9, column=0, sticky="ew", padx=24, pady=(0, 14))
        ctk.CTkButton(
            config,
            text="Einstellungen speichern",
            height=42,
            corner_radius=10,
            fg_color=COLORS["green_light"],
            hover_color="#d4e5d7",
            text_color=COLORS["green_dark"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save_settings,
        ).grid(row=10, column=0, sticky="ew", padx=24, pady=(0, 24))

        actions = ctk.CTkFrame(
            self.content,
            corner_radius=18,
            fg_color=COLORS["surface"],
            border_width=1,
            border_color=COLORS["line"],
        )
        actions.grid(row=2, column=1, sticky="nsew", padx=(10, 38), pady=(0, 20))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_rowconfigure(8, weight=1)
        ctk.CTkLabel(
            actions,
            text="Synchronisierung",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["ink"],
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(22, 2))
        ctk.CTkLabel(
            actions,
            text="Manuell starten oder täglich ausführen",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 17))
        self.sync_button = ctk.CTkButton(
            actions,
            text="Jetzt synchronisieren",
            height=46,
            corner_radius=10,
            fg_color=COLORS["green"],
            hover_color=COLORS["green_dark"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_sync,
        )
        self.sync_button.grid(row=2, column=0, sticky="ew", padx=24)

        ctk.CTkLabel(
            actions,
            text="TÄGLICHE AUTOMATIK",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=3, column=0, sticky="w", padx=24, pady=(22, 8))
        schedule_controls = ctk.CTkFrame(actions, fg_color="transparent")
        schedule_controls.grid(row=4, column=0, sticky="ew", padx=24)
        schedule_controls.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            schedule_controls,
            text="Startzeit",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.time_entry = ctk.CTkEntry(
            schedule_controls,
            width=82,
            height=36,
            corner_radius=9,
            placeholder_text="08:00",
            fg_color=COLORS["background"],
            border_color=COLORS["line"],
        )
        self.time_entry.insert(0, "08:00")
        self.time_entry.grid(row=0, column=1, sticky="w")
        self.schedule_button = ctk.CTkButton(
            schedule_controls,
            text="Aktivieren",
            width=95,
            height=36,
            corner_radius=9,
            fg_color=COLORS["green_light"],
            hover_color="#d4e5d7",
            text_color=COLORS["green_dark"],
            command=self._enable_schedule,
        )
        self.schedule_button.grid(row=0, column=2, padx=(10, 0))
        self.disable_schedule_button = ctk.CTkButton(
            actions,
            text="Automatik deaktivieren",
            height=32,
            fg_color="transparent",
            hover_color=COLORS["background"],
            text_color=COLORS["muted"],
            command=self._disable_schedule,
        )
        self.disable_schedule_button.grid(row=5, column=0, sticky="ew", padx=24, pady=(7, 12))

        ctk.CTkLabel(
            actions,
            text="AKTIVITÄT",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=6, column=0, sticky="w", padx=24, pady=(4, 8))
        self.log_box = ctk.CTkTextbox(
            actions,
            corner_radius=10,
            fg_color=COLORS["log"],
            text_color=COLORS["ink"],
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            height=118,
            border_width=1,
            border_color=COLORS["line"],
        )
        self.log_box.grid(row=8, column=0, sticky="nsew", padx=24, pady=(0, 24))
        self.log_box.insert(
            "end",
            "Bereit. Die Automatik läuft über die Windows-Aufgabenplanung.\n",
        )
        self.log_box.configure(state="disabled")

        ctk.CTkLabel(
            self.content,
            text="Die Synchronisierung läuft einseitig von Stud.IP zu Google Drive.",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11),
        ).grid(row=3, column=0, columnspan=2, pady=(0, 22))

    def _add_entry(self, parent, row, label, show=None):
        ctk.CTkLabel(
            parent,
            text=label,
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11, weight="bold"),
        ).grid(row=row, column=0, sticky="w", padx=24, pady=(0, 5))
        entry = ctk.CTkEntry(
            parent,
            height=40,
            corner_radius=9,
            show=show,
            fg_color=COLORS["background"],
            border_color=COLORS["line"],
            text_color=COLORS["ink"],
        )
        entry.grid(row=row + 1, column=0, sticky="ew", padx=24, pady=(0, 12))
        return entry

    def _load_configuration(self):
        directory = data_dir()
        values = dotenv_values(directory / ".env")
        self.username_entry.insert(0, values.get("STUDIP_USER") or "")
        self.password_entry.insert(0, values.get("STUDIP_PASSWORD") or "")
        self.folder_id = values.get("DRIVE_ROOT_FOLDER_ID") or ""
        self.folder_name = values.get("DRIVE_ROOT_FOLDER_NAME") or ""
        self.folder_label.configure(
            text=self.folder_name or self.folder_id or "Noch kein Ordner ausgewählt"
        )
        credentials_file = directory / "credentials.json"
        if credentials_file.is_file():
            self.credentials_label.configure(text="Google-Zugangsdaten vorhanden")
        else:
            bundled_credentials = bundled_credentials_path()
            if bundled_credentials:
                self.credentials_label.configure(text="Google-Zugangsdaten integriert")
            else:
                self.credentials_label.configure(text="Google-OAuth-Konfiguration fehlt")

    def _save_settings(self, show_confirmation=True):
        try:
            directory = save_configuration(
                self.username_entry.get(),
                self.password_entry.get(),
                self.folder_id,
                self.folder_name,
            )
        except (OSError, ValueError) as error:
            messagebox.showerror("Einstellungen", str(error), parent=self)
            return None

        self.credentials_label.configure(text="Google-Zugangsdaten gespeichert")
        if show_confirmation:
            messagebox.showinfo("Einstellungen", "Einstellungen wurden gespeichert.", parent=self)
        return directory

    def _choose_drive_folder(self):
        if self._save_settings(show_confirmation=False) is None:
            return
        self.picker_button.configure(state="disabled", text="Browser wird geöffnet …")
        self.status_label.configure(text="Google-Ordnerauswahl läuft …")

        def worker():
            try:
                folder_id, folder_name = pick_drive_folder(data_dir())
            except Exception as error:
                self.event_queue.put(("picker_finished", None, None, str(error)))
            else:
                self.event_queue.put(("picker_finished", folder_id, folder_name, None))

        threading.Thread(target=worker, daemon=True).start()

    def _start_sync(self):
        if self.is_syncing:
            return
        if self._save_settings(show_confirmation=False) is None:
            return
        if not self.folder_id:
            messagebox.showerror(
                "Einstellungen",
                "Bitte zuerst einen Google-Drive-Zielordner auswählen.",
                parent=self,
            )
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
        if not self.folder_id:
            messagebox.showerror(
                "Einstellungen",
                "Bitte zuerst einen Google-Drive-Zielordner auswählen.",
                parent=self,
            )
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
                elif isinstance(event, tuple) and event[0] == "picker_finished":
                    _, folder_id, folder_name, error = event
                    self.picker_button.configure(state="normal", text="Ordner auswählen")
                    if error:
                        self.status_label.configure(text="Ordnerauswahl fehlgeschlagen")
                        messagebox.showerror("Google-Ordnerauswahl", error, parent=self)
                    else:
                        self.folder_id = folder_id
                        self.folder_name = folder_name
                        self.folder_label.configure(text=folder_name)
                        if self._save_settings(show_confirmation=False) is not None:
                            self.status_label.configure(text="Google-Ordner ausgewählt")
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
