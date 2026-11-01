"""Todoist API v1 extractor → raw JSON landing.

Usage:
    python -m ingestion.todoist --days 30
    python -m ingestion.todoist --start 2026-09-01 --end 2026-10-31

Two kinds of data:
- Snapshots (projects, active tasks): current state, landed under today's dt.
  Re-running the same day overwrites it; one file per day builds a history of the list.
- Events (completed tasks): landed under their completion date (UTC), one file per
  day in the range, empty days included, so re-runs overwrite cleanly.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("todoist")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / os.getenv("RAW_DIR", "data/raw") / "todoist"
BASE_URL = "https://api.todoist.com/api/v1"
PAGE_LIMIT = 200  # API max per page
MAX_WINDOW_DAYS = 90  # completed-tasks endpoint rejects ranges over 3 months


def get_session() -> requests.Session:
    token = os.getenv("TODOIST_TOKEN")
    if not token:
        raise SystemExit("TODOIST_TOKEN is not set (see .env.example)")
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    return session


def fetch_all(session: requests.Session, path: str, list_key: str = "results", **params) -> list[dict]:
    """Follow next_cursor until the API stops returning one."""
    items: list[dict] = []
    cursor = None
    while True:
        page_params = {"limit": PAGE_LIMIT, **params}
        if cursor:
            page_params["cursor"] = cursor
        resp = session.get(f"{BASE_URL}{path}", params=page_params, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        items.extend(body[list_key])
        cursor = body.get("next_cursor")
        if not cursor:
            return items


def land(entity: str, day: date, payload) -> Path:
    """Write one day's raw payload. Overwrites → idempotent re-runs."""
    out = RAW_DIR / entity / f"dt={day.isoformat()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def extract_snapshots(session: requests.Session, today: date) -> None:
    for entity, path in (("projects", "/projects"), ("tasks", "/tasks")):
        try:
            rows = fetch_all(session, path)
            land(entity, today, rows)
            log.info("Landed %d %s (snapshot %s)", len(rows), entity, today)
        except Exception as exc:  # one failing entity must not kill the run
            log.warning("%s snapshot failed: %s", entity, exc)


def extract_completed(session: requests.Session, start: date, end: date) -> None:
    by_day: dict[str, list] = {}
    window_start = start
    while window_start <= end:
        window_end = min(window_start + timedelta(days=MAX_WINDOW_DAYS - 1), end)
        rows = fetch_all(
            session,
            "/tasks/completed/by_completion_date",
            list_key="items",
            since=datetime.combine(window_start, time.min, timezone.utc).isoformat(),
            until=datetime.combine(window_end, time.max, timezone.utc).isoformat(),
        )
        for row in rows:
            by_day.setdefault(row["completed_at"][:10], []).append(row)
        window_start = window_end + timedelta(days=1)

    day = start
    while day <= end:
        land("completed_tasks", day, by_day.get(day.isoformat(), []))
        day += timedelta(days=1)
    log.info("Landed %d completed tasks for %s..%s", sum(map(len, by_day.values())), start, end)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--start", type=date.fromisoformat)
    p.add_argument("--end", type=date.fromisoformat)
    a = p.parse_args()
    end = a.end or date.today()
    start = a.start or end - timedelta(days=a.days - 1)
    session = get_session()
    extract_snapshots(session, date.today())
    try:
        extract_completed(session, start, end)
    except Exception as exc:
        log.warning("completed tasks failed: %s", exc)


if __name__ == "__main__":
    main()
