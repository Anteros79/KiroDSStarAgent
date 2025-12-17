---
title: Data & Storage Model
---

# Data & Storage Model (DB Structures)

This project currently runs without a database:

- Airline ops data is loaded from a CSV (`data/airline_operations.csv`).
- Tech Ops dashboard data is deterministic in-memory demo data (`src/data/techops_metrics.py`).
- Tech Ops investigations are stored in-memory for the life of the API process (`src/api/server.py`).

This document describes:
1. The actual runtime data structures (as implemented)
2. A recommended relational schema if you want to persist the same data in a DB (Postgres/SQLite)
3. Example queries/criteria and API calls to exercise the system end-to-end

---

## 1) Runtime Data Sources

### 1.1 Airline Operations Dataset (CSV)

- File: `data/airline_operations.csv`
- Loaded by: `src/data/airline_data.py` (via `initialize_data_loader(...)`)
- Role: used by the multi-agent tools to compute airline ops KPIs (OTP, delays, etc.)
- Note: if the file does not exist, the API and CLI generate a sample dataset at startup.

### 1.2 Tech Ops KPI Time Series (In-Memory)

- Generator + store: `src/data/techops_metrics.py` (`TechOpsStore`)
- Stations (seeded): `DAL`, `PHX`, `HOU`
- Windows:
  - Daily: last 30 days (YoY derived via a 365-day lookback)
  - Weekly: last 53 weeks (YoY derived via a 53-week lookback)

Each point can include Wheeler stage-aware control limits:
- `cl`, `ucl`, `lcl`: control limits for that point's detected stage/phase
- `phase_number`: stage/phase identifier

The dashboard APIs accept `summary_level=station|region|company` and the store returns the appropriately aggregated series.

### 1.3 Tech Ops Investigations (In-Memory)

- Store: `_techops_investigations: Dict[str, Dict[str, Any]]` in `src/api/server.py`
- Lifecycle:
  - Created via `POST /api/techops/investigations`
  - Updated via workbench streaming events (steps/iterations)
  - Finalized via `POST /api/techops/investigations/{id}/finalize`
- Persistence: resets when the API process restarts

---

## 2) Core Domain Entities

### 2.1 `station`

Represents a maintenance station (e.g., DAL, PHX, HOU).

Key fields:
- `station_code` (PK): `DAL`
- `display_name`: `Dallas Love Field`

### 2.2 `kpi_definition`

Represents a Tech Ops KPI definition (label, units, thresholds, aggregation).

Source:
- `KPIDef` in `src/data/techops_metrics.py`

Key fields:
- `kpi_id` (PK): `OTP_MX_RATE`
- `label`: `OTP MX Rate`
- `unit`: `%`, `rate`, or `count`
- `agg`: `mean` or `sum`
- `goal`, `ul`, `ll`
- `decimals`

### 2.3 `kpi_point`

Represents a single time-series point (daily or weekly), optionally with YoY values and signal classification.

Source:
- `MetricPoint` in `src/data/techops_metrics.py`

Key fields:
- `t`: `YYYY-MM-DD` (daily) or `week_start` (weekly)
- `value`
- `yoy_value`, `yoy_delta` (optional)
- `signal_state`: `none | warning | critical`
- `cl`, `ucl`, `lcl` (optional): stage-aware (Wheeler phase) limits for that point
- `phase_number` (optional): Wheeler stage/phase identifier for that point

### 2.4 `kpi_series`

Represents a windowed series response with summary stats.

Source:
- `KPISeries` in `src/data/techops_metrics.py`

Key fields:
- `mean`, `past_value`, `past_delta`
- `signal_state` (rolled up)
- `npl_*` (latest phase NPL values): `npl_cl`, `npl_ucl`, `npl_lcl`, `npl_sigma`, `npl_mr_bar`

### 2.5 `investigation`

Represents a KPI investigation opened from the dashboard.

Source:
- `InvestigationRecord` in `src/api/server.py`

Key fields:
- `investigation_id` (PK): `INV-XXXXXXXX`
- `kpi_id`, `station`, `window`
- `summary_level`: `station | region | company`
- `created_by` (demo identity), `created_at`, `status`
- `prompt_mode`, `prompt`, `selected_point_t`
- `telemetry` (chart payload), `diagnostics` (list), `steps` (workbench trace)
- `final_*` fields + evidence

---

## 3) Recommended Relational Schema (Postgres/SQLite)

This schema mirrors the in-memory JSON structures so you can persist the Tech Ops dashboard + investigations.

### 3.1 Tables

#### `stations`

```sql
create table stations (
  station_code text primary key,
  display_name text
);
```

#### `kpi_definitions`

```sql
create table kpi_definitions (
  kpi_id text primary key,
  label text not null,
  unit text not null,          -- '%', 'rate', 'count'
  agg text not null,           -- 'mean' | 'sum'
  goal double precision not null,
  ul double precision not null,
  ll double precision not null,
  decimals integer not null default 2
);
```

#### `kpi_points_daily`

```sql
create table kpi_points_daily (
  station_code text not null references stations(station_code),
  kpi_id text not null references kpi_definitions(kpi_id),
  t date not null,
  value double precision not null,
  yoy_value double precision,
  yoy_delta double precision,
  signal_state text not null,  -- 'none' | 'warning' | 'critical'
  cl double precision,
  ucl double precision,
  lcl double precision,
  phase_number integer,
  primary key (station_code, kpi_id, t)
);

create index kpi_points_daily_station_kpi_time
  on kpi_points_daily (station_code, kpi_id, t desc);
```

#### `kpi_points_weekly`

```sql
create table kpi_points_weekly (
  station_code text not null references stations(station_code),
  kpi_id text not null references kpi_definitions(kpi_id),
  week_start date not null,
  value double precision not null,
  yoy_value double precision,
  yoy_delta double precision,
  signal_state text not null,
  cl double precision,
  ucl double precision,
  lcl double precision,
  phase_number integer,
  primary key (station_code, kpi_id, week_start)
);

create index kpi_points_weekly_station_kpi_time
  on kpi_points_weekly (station_code, kpi_id, week_start desc);
```

#### `demo_identities`

```sql
create table demo_identities (
  identity_id text primary key,
  name text not null,
  role text not null,
  station_code text not null references stations(station_code)
);
```

#### `investigations`

```sql
create table investigations (
  investigation_id text primary key,
  kpi_id text not null references kpi_definitions(kpi_id),
  station_code text not null references stations(station_code),
  window text not null,                     -- 'daily' | 'weekly'
  summary_level text not null default 'station',  -- 'station' | 'region' | 'company'
  created_by_identity_id text not null references demo_identities(identity_id),
  created_at timestamptz not null,
  status text not null,                     -- 'open' | 'finalized'
  prompt_mode text not null,                -- 'cause' | 'yoy'
  prompt text not null,
  selected_point_t text,
  telemetry jsonb,                          -- chart payload
  diagnostics jsonb,                        -- list
  final_root_cause text,
  final_actions jsonb,
  final_notes text,
  final_evidence jsonb
);

create index investigations_station_time
  on investigations (station_code, created_at desc);
```

#### `investigation_steps`

```sql
create table investigation_steps (
  investigation_id text not null references investigations(investigation_id),
  step_id text not null,
  step_number integer not null,
  query text not null,
  created_at timestamptz not null,
  primary key (investigation_id, step_id)
);
```

#### `investigation_iterations`

```sql
create table investigation_iterations (
  investigation_id text not null,
  step_id text not null,
  iteration_id text not null,
  iteration_number integer not null,
  query text not null,
  generated_code text,
  response text,
  chart jsonb,
  include_in_final boolean not null default true,
  created_at timestamptz not null,
  primary key (investigation_id, step_id, iteration_id),
  foreign key (investigation_id, step_id)
    references investigation_steps(investigation_id, step_id)
);
```

---

## 4) Example Criteria / Queries

### 4.1 "Show me active signals for DAL"

API:
- `GET /api/techops/signals/active?station=DAL&summary_level=station`

DB:
```sql
select kpi_id, value, signal_state
from kpi_points_weekly
where station_code = 'DAL'
  and week_start = (select max(week_start) from kpi_points_weekly where station_code='DAL')
  and signal_state in ('warning','critical');
```

### 4.2 "List the last 10 investigations for DAL"

```sql
select investigation_id, kpi_id, window, status, created_at
from investigations
where station_code = 'DAL'
order by created_at desc
limit 10;
```

### 4.3 "Pull the series behind a KPI card (weekly window)"

```sql
select week_start, value, yoy_value, yoy_delta, signal_state, cl, ucl, lcl, phase_number
from kpi_points_weekly
where station_code = 'DAL' and kpi_id = 'OTP_MX_RATE'
order by week_start desc
limit 53;
```

---

## 5) How To Exercise the System (End-to-End)

### 5.1 Start the app

- Recommended: run `start_application.bat` and use the ports it prints.
- For fixed-port API examples: run `start_backend.bat` (backend on `http://127.0.0.1:8000`).

### 5.2 Verify Tech Ops endpoints (fixed-port backend)

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/techops/kpis
curl "http://127.0.0.1:8000/api/techops/dashboard/weekly?station=DAL&summary_level=station"
curl "http://127.0.0.1:8000/api/techops/dashboard/daily?station=DAL&summary_level=station"
curl "http://127.0.0.1:8000/api/techops/signals/active?station=DAL&summary_level=station"
```

### 5.3 Create and finalize an investigation (fixed-port backend)

```bash
curl -X POST http://127.0.0.1:8000/api/techops/investigations ^
  -H "Content-Type: application/json" ^
  -d "{\"kpi_id\":\"OTP_MX_RATE\",\"station\":\"DAL\",\"window\":\"weekly\",\"summary_level\":\"station\"}"
```

```bash
curl -X POST http://127.0.0.1:8000/api/techops/investigations/INV-REPLACE_ME/finalize ^
  -H "Content-Type: application/json" ^
  -d "{\"final_root_cause\":\"Example\",\"final_actions\":[\"Inspect X\",\"Validate Y\"],\"final_notes\":\"Example\"}"
```

---

## 6) Chart Telemetry Format (Stored as JSON)

Investigation telemetry is stored as a JSON payload compatible with Plotly:

```json
{
  "chart_type": "plotly",
  "title": "OTP MX Rate - DAL (weekly)",
  "plotly_json": {
    "data": [],
    "layout": {}
  }
}
```

In this repo, telemetry is generated server-side in `src/api/server.py` (notably `generate_techops_xmr_combo_chart(...)` and `generate_techops_kpi_chart(...)`).
