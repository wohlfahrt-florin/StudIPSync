"""Meldet neue oder geänderte Stud.IP-Termine zur manuellen Prüfung."""

import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .studip_client import StudIPClient, TARGET_SEMESTER


PROJECT_DIR = Path(__file__).resolve().parents[1]
STATE_PATH = PROJECT_DIR / "calendar_watch_state.json"


def event_fingerprint(attributes):
    """Erzeugt einen stabilen Fingerabdruck ohne Eventtexte im Status zu speichern."""
    relevant = {
        key: attributes.get(key)
        for key in (
            "title",
            "description",
            "start",
            "end",
            "location",
            "categories",
            "is-cancelled",
            "recurrence",
        )
    }
    encoded = json.dumps(
        relevant,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def make_snapshot(courses, studip):
    """Liefert den aktuellen Kurs-/Terminbestand und seine Eventdaten."""
    snapshot = {}
    events_by_key = {}
    for course_id, course_name in courses:
        for event in studip.course_events(course_id):
            event_key = f"{course_id}:{event['id']}"
            attributes = event.get("attributes", {})
            snapshot[event_key] = event_fingerprint(attributes)
            events_by_key[event_key] = {
                "course_name": course_name,
                "attributes": attributes,
            }
    return snapshot, events_by_key


def diff_snapshots(previous, current):
    """Ordnet neue und geänderte Event-IDs für die manuelle Prüfung ein."""
    added = sorted(current.keys() - previous.keys())
    changed = sorted(
        key
        for key in current.keys() & previous.keys()
        if current[key] != previous[key]
    )
    return added, changed


def _is_relevant_for_review(attributes):
    if attributes.get("is-cancelled"):
        return True

    start = attributes.get("start")
    if not start:
        return True
    event_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
    if event_start.tzinfo is None:
        event_start = event_start.astimezone()
    return event_start >= datetime.now().astimezone() or bool(
        attributes.get("recurrence")
    )


def _format_datetime(value):
    if not value:
        return "unbekannt"
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone().strftime("%d.%m.%Y %H:%M")


def _print_review_item(label, item):
    attributes = item["attributes"]
    title = attributes.get("title") or "(ohne Titel)"
    print(f"\n{label}: {title}")
    print(f"  Kurs: {item['course_name']}")
    print(
        "  Zeit: "
        f"{_format_datetime(attributes.get('start'))} – "
        f"{_format_datetime(attributes.get('end'))}"
    )
    if attributes.get("location"):
        print(f"  Ort: {attributes['location']}")
    if attributes.get("recurrence"):
        print(f"  Wiederholung laut Stud.IP: {attributes['recurrence']}")
    if attributes.get("is-cancelled"):
        print("  Hinweis: Dieser Termin ist in Stud.IP abgesagt.")
    if attributes.get("description"):
        print(f"  Beschreibung: {attributes['description']}")


def _load_state():
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(
            f"Die Statusdatei {STATE_PATH} enthält kein gültiges JSON."
        ) from error
    if not isinstance(state, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in state.items()
    ):
        raise SystemExit(f"Die Statusdatei {STATE_PATH} hat ein ungültiges Format.")
    return state


def _save_state(snapshot):
    STATE_PATH.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Neue oder geänderte Stud.IP-Termine manuell prüfen."
    )
    parser.add_argument(
        "--initialize",
        action="store_true",
        help="Aktuellen Terminbestand als Ausgangspunkt speichern.",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Änderungen anzeigen, aber den Status nicht fortschreiben.",
    )
    args = parser.parse_args()

    if not STATE_PATH.exists() and not args.initialize:
        raise SystemExit(
            "Noch kein Ausgangsbestand vorhanden. Zuerst mit "
            "'python .\\calendar_watch.py --initialize' initialisieren."
        )
    if STATE_PATH.exists() and args.initialize:
        raise SystemExit(
            f"Es existiert bereits {STATE_PATH}; die Initialisierung "
            "überschreibt den gespeicherten Ausgangsbestand nicht."
        )

    load_dotenv(PROJECT_DIR / ".env")
    studip = StudIPClient(
        os.environ["STUDIP_USER"],
        os.environ["STUDIP_PASSWORD"],
    )
    user = studip.current_user()
    courses = studip.semester_courses(user["id"], TARGET_SEMESTER)
    snapshot, events_by_key = make_snapshot(courses, studip)

    if args.initialize:
        _save_state(snapshot)
        print(
            f"Ausgangsbestand gespeichert: {len(courses)} Kurse, "
            f"{len(snapshot)} Termine. Ab jetzt werden neue und geänderte "
            "Termine angezeigt."
        )
        return

    previous = _load_state()
    added, changed = diff_snapshots(previous, snapshot)
    review_items = [
        (label, events_by_key[key])
        for label, keys in (("Neu", added), ("Geändert", changed))
        for key in keys
        if _is_relevant_for_review(events_by_key[key]["attributes"])
    ]

    if not review_items:
        print("Keine neuen oder geänderten zukünftigen Termine gefunden.")
        if not args.report_only:
            _save_state(snapshot)
        return

    print(
        f"{len(review_items)} neue/geänderte Termin(e) zur Prüfung. "
        "Bitte in Stud.IP kontrollieren, ob sie für deine Seminargruppe 9 "
        "gelten. Es werden keine Google-Kalender-Einträge angelegt."
    )
    for label, item in review_items:
        _print_review_item(label, item)

    if args.report_only:
        return

    try:
        answer = input(
            "\nSind die Änderungen geprüft? "
            "Mit j werden sie als gesehen markiert [j/N]: "
        )
    except EOFError:
        raise SystemExit(
            "Keine interaktive Eingabe verfügbar; Status wurde nicht geändert. "
            "Für einen nicht-interaktiven Bericht --report-only verwenden."
        )
    if answer.strip().lower() == "j":
        _save_state(snapshot)
        print("Änderungen als geprüft markiert.")
    else:
        print("Status unverändert; die Termine werden beim nächsten Lauf erneut gezeigt.")


if __name__ == "__main__":
    main()
