# DS‑STAR Tech Ops — Implementation Backlog (Living Jira Plan)

This backlog is a **living plan**. As we implement and test, we will keep this file updated: mark items done, add follow‑ups, and adjust sequencing.

## Design anchor (logo-driven)

- **Brand cues**: deep navy + aviation/ops seriousness, bold gold for primary CTA, red for critical status.
- **Palette starting point (tunable)**:
  - **Navy**: `#1E3A8A` (Primary)
  - **Navy-2**: `#1E40AF` (Hover/secondary)
  - **Gold**: `#CA8A04` (Primary CTA / highlights)
  - **Red**: `#DC2626` (Critical)
  - **Amber**: `#F59E0B` (Warning)
  - **Green**: `#16A34A` (Passed)
  - **Bg**: `#F8FAFC` (Light background)
  - **Text**: `#0F172A` (Primary text)
  - **Border**: `#E2E8F0` (Borders/dividers)
- **Typography** (from UI/UX Pro Max):
  - Option A (**accessibility-first**): **Lexend** (headings) + **Source Sans 3** (body)
  - Option B (**simple**): **Inter** (all)
- **UI direction** (UI/UX Pro Max product guidance):
  - **Data-dense monitoring dashboard** with drill-down, comparative time series, and strong status color semantics.

> **Logo asset note**: add the provided logo to `frontend/src/assets/branding/tech-ops-logo.png` (or `.svg` if you have it). Until then, we’ll use a placeholder and make the path swappable.

---

## Epic A — Foundations: Routing, App Shell, Identity (Demo)

### A1. App shell + navigation framework
- **Story A1.1**: Add top navigation (`Dashboard`, `Investigation`, `Fleet Status`, `Reports`) and breadcrumbs
  - Subtasks:
    - Create route structure with `react-router` (or equivalent if already present)
    - Add `TopNav` component + active tab styling
    - Add breadcrumbs component that can be configured per page
    - Add page layout containers and consistent max-width rules
  - Acceptance:
    - All pages render within a shared shell; navigation works; keyboard focus states visible.
  - Estimate: **M**

- **Story A1.2**: Add logo + brand header
  - Subtasks:
    - Add `BrandMark` component supporting PNG/SVG and fallback
    - Add theme tokens derived from the logo palette (Tailwind config + CSS vars)
    - Replace existing header branding across screens
  - Acceptance:
    - Logo appears in top-left; primary CTA/buttons use gold; critical states use red; contrast passes WCAG AA.
  - Estimate: **S**

### A2. Demo identity / persona system
- **Story A2.1**: Implement demo identities (no auth)
  - Subtasks:
    - Backend: `GET /api/me` returns current identity
    - Backend: `POST /api/me/select` switches between pre-seeded identities
    - Frontend: identity switcher in header (Radix `DropdownMenu`)
    - Persist selection in local storage (frontend) and/or server memory
  - Acceptance:
    - Switching identity updates name/role/station everywhere and affects data scoping.
  - Estimate: **S**

### A3. Station scoping + filters
- **Story A3.1**: Implement station selector and global filter context
  - Subtasks:
    - Create `StationContext` (DAL/PHX/etc.)
    - Add station selector UI
    - Scope dashboard and investigations to station by default
  - Acceptance:
    - Switching station updates dashboard metrics and investigation lists.
  - Estimate: **S**

---

## Epic B — Data Model + Test Data (Daily + Weekly + YoY)

### B1. Define KPI catalog + thresholds
- **Story B1.1**: Create KPI definitions in a single source of truth
  - Subtasks:
    - Define `KPI` schema: id, label, unit, goal, UL/LL, formatting, display order
    - Implement `GET /api/kpis`
    - Add seeded defaults for your KPI set:
      - `OTP_MX_RATE`, `EMO_MX_RATE`, `MX_EXTREME_DELAY_RATE`, `FAULT_RATE`, `FINDING_RATE`, `OTS_RATE`, `MEL_RATE`, `MEL_CX_RATE`, `INJURY_COUNT`, `PREMIUM_PAY_RATE`
  - Acceptance:
    - UI renders KPI tiles from API (no hard-coded KPI list in UI).
  - Estimate: **S**

### B2. Generate deterministic demo time series (daily + weekly)
- **Story B2.1**: Add a test data generator with deterministic seeds
  - Subtasks:
    - Implement generator module `src/data/techops_metrics.py`
    - Inputs: station list, KPI list, seed, “today” date
    - Output:
      - Daily series: last **30 days**
      - Weekly series: last **53 weeks**
      - Year-over-year reference values (weekly and daily)
  - Acceptance:
    - Same seed produces identical datasets; daily and weekly are internally consistent.
  - Estimate: **M**

- **Story B2.2**: Signal injection rules (warning/critical)
  - Subtasks:
    - Create deterministic “critical breach” windows for a subset of KPIs
    - Create “warning” windows for another subset
    - Store `signal_state` per KPI per window
    - Implement `GET /api/signals/active`
  - Acceptance:
    - Dashboard always shows some active signals for demo; clicking them drills into investigation.
  - Estimate: **M**

### B3. Persistence for demo
- **Story B3.1**: Add persistence for generated data + investigations
  - Subtasks:
    - Pick storage:
      - **Option A**: SQLite (recommended)
      - **Option B**: JSON snapshot + in-memory cache
    - Create schema/migrations (if SQLite)
    - Ensure “seed + regenerate” command for demos
  - Acceptance:
    - Refreshing the app does not lose investigations/finals (unless reset).
  - Estimate: **M**

---

## Epic C — Dashboard (Weekly KPI View)

### C1. Dashboard page layout (matches screenshot)
- **Story C1.1**: Build “Operational Metrics Dashboard” page
  - Subtasks:
    - Page header with date range picker
    - “Active Signals” chip row (critical/warning/none)
    - KPI grid with two-column layout of cards like screenshot
  - Acceptance:
    - Layout matches target: dense KPI cards with trend, mean, UL/LL, goal, “past week” summary.
  - Estimate: **M**

### C2. Weekly trend cards (53-week)
- **Story C2.1**: Implement 53-week trend sparkline with UL/LL bands
  - Subtasks:
    - Use Plotly for consistent charting
    - Add UL/LL dotted lines + shading
    - Add hover tooltip with week label + value + delta
    - Add clickable interaction:
      - click card or click point opens investigation flow
  - Acceptance:
    - Clicking a KPI triggers creation/opening of an investigation seeded with KPI + window.
  - Estimate: **M**

### C3. Click-to-investigate + prompt mode selection
- **Story C3.1**: Determine prompt mode on click
  - Rules:
    - If `signal_state != none` → prompt: **“What is the cause of this signal?”**
    - Else → prompt: **“How does this compare to year-over-year performance?”**
  - Subtasks:
    - Implement click handler that calls `POST /api/investigations` with prompt mode + selected KPI point(s)
    - Deep link to `/investigations/:id`
  - Acceptance:
    - Correct prompt mode chosen automatically; user lands on DS-STAR Investigation screen.
  - Estimate: **S**

---

## Epic D — Daily Alt View (Last Week Bars + Last 30 Days)

### D1. Daily “last week” bar view toggle
- **Story D1.1**: Add dashboard toggle (`Weekly Trend` / `Daily Bars`)
  - Subtasks:
    - Implement toggle control (Radix `Tabs`)
    - Persist last-selected view in local storage
  - Acceptance:
    - Switching toggles doesn’t lose station/date selections.
  - Estimate: **S**

- **Story D1.2**: Render last 7 days as bars for each KPI
  - Subtasks:
    - Bar chart with UL/LL overlay
    - Click a bar → open investigation seeded to that date window
  - Acceptance:
    - Daily drilldown works identically to weekly drilldown.
  - Estimate: **M**

### D2. Daily “last 30 days” reporting support
- **Story D2.1**: Add 30-day daily trend/detail panel
  - Subtasks:
    - Provide a detail drawer/modal when a KPI is selected
    - Show 30-day line chart + YoY overlay
  - Acceptance:
    - User can see last 30 days and compare to YoY for the same KPI.
  - Estimate: **M**

---

## Epic E — DS‑STAR Investigation Screen (Triage + Assistant + Evidence)

### E1. Investigation “case” header (matches screenshot)
- **Story E1.1**: Build Investigation header section
  - Subtasks:
    - Case title: `Investigation #SIG-...` and `Signal #...`
    - Status badge (`Open - Triage`, etc.)
    - Summary chips: detection time, asset id, flight phase, station
    - Share + Export PDF buttons (Export can be stubbed first)
  - Acceptance:
    - Header can be driven by investigation record from API.
  - Estimate: **M**

### E2. KPI diagnostic test cards
- **Story E2.1**: Build “DS‑STAR Diagnostic Tests” cards row
  - Subtasks:
    - Implement card component with status (warning/passed/check) + confidence/probability
    - Map from investigation context + demo data to deterministic test outcomes
  - Acceptance:
    - Always renders 3+ cards with mixed states for demo; clicking a card can add evidence to the investigation.
  - Estimate: **M**

### E3. Telemetry chart + comparison
- **Story E3.1**: Pressure/metric telemetry chart with comparison series
  - Subtasks:
    - Show “current signal” vs “fleet average” overlay
    - Range toggle `1H | 24H | 7D` (or weekly/daily equivalents)
    - Tooltips with value + deviation
  - Acceptance:
    - Chart updates when range toggles change; supports click to select evidence window.
  - Estimate: **M**

### E4. Assistant panel integration (reuse your existing Workbench)
- **Story E4.1**: Embed DS‑STAR assistant chat / streaming panel
  - Subtasks:
    - Adapt `InvestigationWorkbench` to accept `investigation_id` + initial prompt
    - Connect WS events to the correct investigation instance (no global mixing)
  - Acceptance:
    - A user can run analysis, approve/refine, and it is stored under the investigation.
  - Estimate: **M**

### E5. Field insights module
- **Story E5.1**: Add “Field Insights” list
  - Subtasks:
    - Seed with station-specific insights from demo data
    - Allow “Add to evidence” action
  - Acceptance:
    - Selecting an insight attaches it to evidence and is visible on finalization screen.
  - Estimate: **S**

---

## Epic F — Investigation Conclusion + Finalization (Root Cause + Actions + Evidence)

### F1. Investigation conclusion screen (matches screenshot)
- **Story F1.1**: Build finalization page layout
  - Subtasks:
    - Incident details card
    - Contributing factors form (primary root cause, impact level, department attribution)
    - Memo editor (can start as textarea; upgrade to rich text later)
    - Conclusion & Actions panel:
      - final determination text
      - required action checklist + add action
      - submit final button
  - Acceptance:
    - User can fill required fields, save draft, submit final.
  - Estimate: **L**

### F2. Evidence linking (what data led to conclusion)
- **Story F2.1**: Evidence model + UI
  - Subtasks:
    - Define evidence entities: chart snapshots, selected KPI points, diagnostic tests, field insights, analysis outputs
    - Show “Evidence” section on final screen
    - On submit, persist evidence references
  - Acceptance:
    - Final record clearly lists the evidence items backing root cause/actions.
  - Estimate: **M**

### F3. Select an investigation to finalize
- **Story F3.1**: Investigation list + selection UI
  - Subtasks:
    - Add `Investigation` tab list view with filtering (station, status, KPI, date)
    - Add “Continue” and “Finalize” actions per row
  - Acceptance:
    - User can open any existing investigation and finalize it.
  - Estimate: **M**

---

## Epic G — Backend Contracts + Realistic Demo Workflow

### G1. REST endpoints for dashboards + investigations
- **Story G1.1**: KPI + dashboard endpoints
  - Subtasks:
    - `GET /api/dashboard/weekly`
    - `GET /api/dashboard/daily`
    - `GET /api/signals/active`
    - `GET /api/kpis`
  - Acceptance:
    - Frontend no longer uses mock datasets; all data comes from API.
  - Estimate: **M**

- **Story G1.2**: Investigation endpoints
  - Subtasks:
    - `POST /api/investigations`
    - `GET /api/investigations`
    - `GET /api/investigations/:id`
    - `POST /api/investigations/:id/draft`
    - `POST /api/investigations/:id/finalize`
  - Acceptance:
    - Full lifecycle supported; finalization persists.
  - Estimate: **M**

### G2. WebSocket event schema stabilization
- **Story G2.1**: Versioned WS schema and strict typing
  - Subtasks:
    - Add `schema_version` to WS events
    - Include `investigation_id`, `step_id`, `iteration_id` consistently
    - Frontend: strict TS types + runtime guards
  - Acceptance:
    - WS reconnection doesn’t corrupt state; multiple investigations can be handled without mixing.
  - Estimate: **M**

---

## Epic H — Testing, QA, and Demo Readiness

### H1. Backend tests
- **Story H1.1**: Test generator invariants
  - Subtasks:
    - 53-week length, 30-day length
    - deterministic seed
    - signal injection rules
    - YoY values exist
  - Estimate: **S**

- **Story H1.2**: API contract tests
  - Subtasks:
    - Status codes, shapes, station scoping, pagination
  - Estimate: **S**

### H2. Frontend tests
- **Story H2.1**: Component tests (Vitest)
  - Subtasks:
    - KPI card rendering (thresholds, status)
    - navigation click triggers create/open investigation
    - finalization form required validation
  - Estimate: **M**

- **Story H2.2**: E2E tests (Playwright)
  - Subtasks:
    - Dashboard → click KPI → investigation → finalize
    - Daily bars → click day → investigation
    - Switch identity/station → data updates
  - Estimate: **M**

### H3. Performance + UX polish
- Virtualize long lists (investigation list, evidence)
- Ensure hover/focus/empty/loading states everywhere
- Export PDF (can be stubbed, then implemented with server-side PDF)

---

## Suggested delivery slices (keeps momentum + demo usable early)

1. **Slice 1 (Demo usable)**: A1, A2, B1, B2 (seeded), C1–C3 → click KPI opens an investigation with correct prompt mode.
2. **Slice 2**: D1–D2 (daily views) + investigation list (F3).
3. **Slice 3**: Investigation screen polish (E1–E5) + evidence linking (F2).
4. **Slice 4**: Finalization (F1) + persistence (B3) + tests (H1–H2).


