# Garmin raw data — notes

Profiling of the raw JSON landed by `ingestion/garmin.py` (DuckDB, `read_json_auto`).
Window: 2026-09-30 → 2026-11-01, one file per entity per day (33 files each).

## daily_stats
- Rows: 33 (one per day, no duplicate dates), 2026-09-30 → 2026-11-01.
- Columns: 94.
- Date column: `calendarDate` (DATE), top level.
- Nested columns:
  - `rule`, `bodyBatteryDynamicFeedbackEvent`, `endOfDayBodyBatteryDynamicFeedbackEvent` — STRUCT.
  - `bodyBatteryActivityEventList` — LIST of STRUCT (events per day) → needs unnesting into rows, not columns.
- `totalSteps`: no NULLs, no zeros, range 741–27,240.
- `dt` (from filename) = `calendarDate` on all 33 rows.
- Note: the latest day is landed while still in progress, so its values are partial until re-run.

## sleep
- Rows: 33, 2026-09-30 → 2026-11-01.
- Columns: 20, almost all nested.
- Date column: `dailySleepDTO.calendarDate` (inside a STRUCT).
- Nested columns:
  - `dailySleepDTO` — STRUCT with the nightly summary (sleep time, start/end, scores).
  - Time series as LIST of STRUCT(value, startGMT): `sleepHeartRate`, `sleepStress`, `sleepBodyBattery`,
    `hrvData`, `sleepMovement`, `sleepLevels`, `wellnessEpochRespiration...`.
  - Time formats are inconsistent: some `startGMT` fields are VARCHAR, others BIGINT (epoch ms).
- `dt` = `dailySleepDTO.calendarDate` on all 33 rows.
- Data quality: only 2 of 33 nights have sleep data (2026-10-08, 2026-10-14).
  Reason: the watch is usually not worn at night. The other rows exist but `sleepTimeSeconds` is NULL.

## activities
- Rows: 1 (only `dt=2026-09-30.json` has data; the other 32 files are `[]`).
  The single activity: paddle ball, 2026-09-30 20:35 local.
- Columns: 88.
- Nested columns: `activityType`, `eventType` — STRUCT (e.g. `activityType.typeKey`).
- Duplicate columns, same meaning under two names: `isPR`/`pr`, `isFavorite`/`favorite`, `isParent`/`parent`.
- Two timestamps, both without timezone: `startTimeLocal` and `startTimeGMT`.
  The one activity is +7h local vs GMT (recorded abroad), so local ≠ Israel time.
- Activity names can contain Hebrew → files must be read/written as UTF-8.
- History is thin: the bulk export is needed for `fct_workouts` to be meaningful.

## Decisions for staging (M2)
- Keep `dt` (from `filename=true` + `regexp_extract`) as lineage metadata on every row.
- Missing sleep = NULL, never 0. NULL means "not measured"; 0 would mean "measured, slept zero"
  and would wreck averages. Keep the rows in staging; the mart decides (filter or `has_sleep_data` flag).
- Flatten STRUCTs into columns; unnest LIST-of-STRUCT time series into separate tables.
- Pick one of each duplicate column pair in activities.
- Decide which timestamp drives `dim_date` (local is what the day "felt like"; GMT is unambiguous).
