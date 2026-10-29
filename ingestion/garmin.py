"""Garmin Connect extractor → raw JSON landing.

Usage:
    python -m ingestion.garmin --days 30
    python -m ingestion.garmin --start 2026-09-01 --end 2026-10-21

First run logs in with email/password from .env (prompts for an MFA code if the
account has 2FA) and caches tokens in GARMIN_TOKEN_DIR. Later runs reuse the
cached tokens, so the password is only needed once.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from garminconnect import Garmin

load_dotenv()
log = logging.getLogger("garmin")

RAW_DIR = Path(os.getenv("RAW_DIR", "data/raw")) / "garmin"
TOKEN_DIR = os.path.expanduser(os.getenv("GARMIN_TOKEN_DIR", "~/.garminconnect"))


def get_client() -> Garmin:
    """Reuse cached tokens; fall back to a full (possibly MFA) login."""
    try:
        client = Garmin()
        client.login(TOKEN_DIR)
        log.info("Logged in with cached tokens")
        return client
    except Exception as exc:  # no tokens yet, or expired
        log.info("Cached login failed (%s); doing full login", type(exc).__name__)

    client = Garmin(
        os.environ["GARMIN_EMAIL"],
        os.environ["GARMIN_PASSWORD"],
        prompt_mfa=lambda: input("Garmin MFA code: "),
    )
    client.login()
    Path(TOKEN_DIR).mkdir(parents=True, exist_ok=True)
    # Persist tokens. API differs between library versions; verify on first run.
    if hasattr(client, "garth"):
        client.garth.dump(TOKEN_DIR)
    log.info("Full login OK; tokens saved to %s", TOKEN_DIR)
    return client


def land(entity: str, day: date, payload) -> Path:
    """Write one day's raw payload. Overwrites → idempotent re-runs."""
    out = RAW_DIR / entity / f"dt={day.isoformat()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return out


def extract(client: Garmin, start: date, end: date) -> None:
    # Activities: one call for the whole range, then split by start date.
    activities = client.get_activities_by_date(start.isoformat(), end.isoformat())
    by_day: dict[str, list] = {}
    for act in activities:
        by_day.setdefault(act["startTimeLocal"][:10], []).append(act)

    day = start
    while day <= end:
        d = day.isoformat()
        land("activities", day, by_day.get(d, []))
        for entity, fn in (("daily_stats", client.get_stats), ("sleep", client.get_sleep_data)):
            try:
                land(entity, day, fn(d))
            except Exception as exc:  # one bad day must not kill the run
                log.warning("%s %s failed: %s", entity, d, exc)
        day += timedelta(days=1)
    log.info("Landed %d activities for %s..%s", len(activities), start, end)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--start", type=date.fromisoformat)
    p.add_argument("--end", type=date.fromisoformat)
    a = p.parse_args()
    end = a.end or date.today()
    start = a.start or end - timedelta(days=a.days - 1)
    extract(get_client(), start, end)


if __name__ == "__main__":
    main()
