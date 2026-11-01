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
- **Todoist**: API v1 (`https://api.todoist.com/api/v1`), token in `TODOIST_TOKEN`. (M1)
- **Application tracker**: markdown table → structured rows. (M1)

## Status
- M0 ✅ (mostly): repo on GitHub, Garmin login + token cache work, 30 days landed.
  Known: 0 activities in the last 30 days — I haven't been recording workouts on the watch yet;
  daily_stats and sleep have data.
- Next: explore raw Garmin JSON with DuckDB → `docs/garmin-notes.md` → M1 (Todoist).

## Roadmap
- M0 Repo + Garmin raw landing
- M1 Todoist + application tracker; DuckDB raw tables
- M2 dbt staging/marts (fct_workouts, fct_tasks, fct_applications, dim_date) + tests
- M3 Orchestration (Dagster vs Airflow — decide based on job postings)
- M4 Dashboard + one cloud (BigQuery likely)
- M5 (optional) MCP server over the warehouse + weekly-review agent
