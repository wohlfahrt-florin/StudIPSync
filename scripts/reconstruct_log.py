"""Reconstruct historical "Neu" log entries from the persisted sync state."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
LOG_PATH = PROJECT_DIR / "sync.log"
STATE_PATH = PROJECT_DIR / "sync_state.json"
CUTOFF_DATE = datetime(2026, 11, 16).date()


def main() -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    historical = []
    for item in state.values():
        changed = item.get("studip_changed")
        if not changed:
            continue
        changed_at = datetime.fromisoformat(changed)
        if changed_at.date() < CUTOFF_DATE:
            historical.append((changed_at, item["file_name"]))

    historical.sort(key=lambda entry: (entry[0], entry[1].casefold()))
    current_log = LOG_PATH.read_text(encoding="utf-8") if LOG_PATH.exists() else ""
    candidates = [
        f"{changed_at:%Y-%m-%d %H:%M:%S}  Neu: {file_name}"
        for changed_at, file_name in historical
    ]
    existing_lines = set(current_log.splitlines())
    reconstructed = [line for line in candidates if line not in existing_lines]
    prefix = "\n".join(reconstructed)
    if prefix:
        prefix += "\n"
    LOG_PATH.write_text(prefix + current_log, encoding="utf-8")
    print(f"{len(reconstructed)} historische Einträge ergänzt.")


if __name__ == "__main__":
    main()
