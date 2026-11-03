"""Application-tracker export → raw JSON landing.

Usage:
    python -m ingestion.tracker

The export is a markdown table that lives outside the repo (path in TRACKER_EXPORT_PATH;
the repo is public, so the file is never committed). It only holds current state, so each
run lands a snapshot under today's dt; history builds up one file per day and cannot be
backfilled. Values are kept as strings exactly as in the file; cleaning happens in staging.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("tracker")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / os.getenv("RAW_DIR", "data/raw") / "tracker"


def read_export() -> str:
    """Return the export's full text. Fails fast if the path is unset or missing."""
    tracker_path = os.getenv("TRACKER_EXPORT_PATH")
    if not tracker_path:
        raise SystemExit("TRACKER_EXPORT_PATH is not set (see .env.example)")

    file_path = Path(tracker_path)
    if not file_path.exists():
        raise SystemExit(f"Tracker export not found: {file_path}")

    # Read the file with UTF-8 encoding
    content = file_path.read_text(encoding="utf-8")
    return content



def land(entity: str, day: date, payload) -> Path:
    """Write one day's raw payload. Overwrites → idempotent re-runs."""
    out = RAW_DIR / entity / f"dt={day.isoformat()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out

def split_row(line: str) -> list[str]:
    """'| a | b |' → ['a', 'b']: drop the empty pieces outside the outer pipes, trim spaces."""
    return [cell.strip() for cell in line.strip().split("|")[1:-1]]


def parse_table(text: str) -> list[dict]:
    """Turn the markdown table into one dict per row (header → cell). No I/O, no cleaning.

    Assumes no cell contains a literal '|' (it would shift the columns).
    """
    table_lines = [line for line in text.splitlines() if line.startswith("|")]
    headers = split_row(table_lines[0])
    rows = []
    for line in table_lines[2:]:  # [1] is the |---|---| separator
        # strict=True: a row with a missing/extra cell raises instead of silently dropping data
        rows.append(dict(zip(headers, split_row(line), strict=True)))
    return rows


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    table = parse_table(read_export())
    out = land("applications", date.today(), table)
    log.info("Landed %d applications (snapshot) → %s", len(table), out)


if __name__ == "__main__":
    main()
