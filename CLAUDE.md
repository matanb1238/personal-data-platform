# Personal Data Platform — context for Claude

## What this is
My (Matan's) single data-engineering portfolio project. Pipeline from my own data
(Garmin, Todoist, job-application tracker) → raw layer → DuckDB → dbt → orchestration → dashboard.
Goal: close the DE gaps interviewers ask about (dbt, orchestration, cloud) and have one
end-to-end story to present. Time cap: 5–6 h/week; job search always comes first.

## How to work with me (most important)
- I'm learning. **Do not write or edit code unless I explicitly ask** ("write it", "fix it").
- Default mode: explain concepts, give me a small task + hints, then review the code I wrote.
- Ask me questions that test understanding (why, trade-offs, what breaks).
- You may run read-only / verification commands freely (git status, running the pipeline,
  querying DuckDB, tests). Ask before installing packages or deleting files.
- Point out interview angles: how I'd explain a decision to an interviewer.
- Explanations in Hebrew; code, comments, commit messages and technical terms in English.
- Keep answers short and concrete.

## Environment
- Windows + PowerShell, PyCharm.
- Python 3.13 in `.venv` (created with `py -3.13 -m venv .venv`).
  ⚠️ Plain `python` outside the venv points to 3.9 — always activate first:
  `.venv\Scripts\Activate.ps1` (prompt must show `(.venv)`).
- Secrets in `.env` (gitignored). Template: `.env.example`.
- PyCharm 2023.1 predates Python 3.13: it labels the venv "Python 3.10" (cosmetic) and its package
  list needs `setuptools<81` in the venv (for `pkg_resources`). Not a project dependency.

## Architecture & conventions
- `ingestion/<source>.py` — one extractor per source, run as `python -m ingestion.<source> --days N`.
- Raw layer is immutable: `data/raw/<source>/<entity>/dt=YYYY-MM-DD.json` (Hive-style partitions).
- Loads are idempotent: re-running a day overwrites that day's file.
- One failing day/entity must not kill the run (log a warning, continue).
- Always write files with `encoding="utf-8"` (Hebrew activity names; Windows default is cp1252).
- `data/raw/` and `*.duckdb` are gitignored.

## Sources
- **Garmin**: `garminconnect` >= 0.3 (unofficial, breaks when Garmin changes auth).
  `Garmin(email, pw, prompt_mfa=...).login(TOKEN_DIR)` loads cached tokens or logs in and saves
  them to `~/.garminconnect/garmin_tokens.json`. Entities: activities, daily_stats, sleep.
  Fallback: official Garmin bulk export.
- **Todoist**: API v1 (`https://api.todoist.com/api/v1`), token in `TODOIST_TOKEN`.
  Cursor pagination (`next_cursor`). Entities: projects + tasks (snapshots, dt = extraction day),
  completed_tasks (events, dt = completion date in UTC; endpoint returns `items`, max 3-month range).
- **Application tracker**: markdown table → structured rows. (M1)

## Status (2026-11-03)
- Done: M0 (Garmin raw, profiled in `docs/garmin-notes.md`); Todoist extractor (projects, tasks, completed).
- Current: M1 — application tracker + DuckDB raw tables.
- Next: define/locate the application-tracker markdown file, then ingest it.
- Blockers: tracker file not set up yet; Garmin history thin (1 activity, sleep on 2 of 33 nights)
  until the bulk export arrives.

## End of session (always)
Before we finish a session: update the "## Status" section (dated, max 6 lines:
done / current milestone / next step / blockers), then commit and push.
Unpushed status is invisible to the rest of my system (other agents read this file from GitHub).

## Roadmap
- M0 Repo + Garmin raw landing
- M1 Todoist + application tracker; DuckDB raw tables
- M2 dbt staging/marts (fct_workouts, fct_tasks, fct_applications, dim_date) + tests
- M3 Orchestration — Airflow (decided 2026-11-02; more common in Israeli DE job postings)
- M4 Dashboard + one cloud (BigQuery likely)
- M5 (optional) MCP server over the warehouse + weekly-review agent
