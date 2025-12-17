# DS-STAR Multi-Agent System

Implementation of the DS-STAR (Data Science Star) multi-agent framework using the AWS Strands Agents SDK. Supports local Ollama models (default) and Amazon Bedrock.

## Overview

This system uses a star topology where a central Orchestrator coordinates three specialists:

- Data Analyst Agent: data exploration, statistical analysis, KPI calculations
- ML Engineer Agent: model recommendations and code generation
- Visualization Expert Agent: chart generation (matplotlib + Plotly JSON)

Key features:
- Real-time investigation streaming (steps, tool calls, intermediate results)
- Multi-domain routing across specialists
- Chart-ready JSON for UI integration
- Conversation context across turns
- Retry + backoff for model/API failures

## Project Structure

```
.
├─ src/                      # Python backend (agents + API)
│  ├─ agents/
│  │  ├─ specialists/
│  │  └─ orchestrator.py
│  ├─ api/                   # FastAPI server + WebSockets
│  ├─ data/                  # Data loading + Tech Ops demo generator
│  ├─ handlers/              # Stream + chart output handlers
│  └─ spc/                   # Wheeler rules / SPC utilities
├─ frontend/                 # React UI (Tech Ops dashboard + investigation workbench)
├─ docs/                     # HTML + markdown docs
├─ demo/                     # Demo scripts + sample queries
├─ data/                     # Sample datasets (CSV)
├─ tests/
├─ start_application.bat      # Starts backend+frontend on free ports
├─ start_backend.bat          # Starts backend on :8000
└─ .env.example              # Environment variable template
```

## Setup

### 1) Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2) Configure model provider

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

Environment variables (common):

| Variable | Default | Description |
|----------|---------|-------------|
| `DS_STAR_MODEL_PROVIDER` | `ollama` | `ollama` or `bedrock` |
| `DS_STAR_MODEL_ID` | `qwen3:30b` | Ollama tag or Bedrock model id |
| `DS_STAR_OLLAMA_HOST` | `http://localhost:11434` | Ollama base URL |
| `AWS_REGION` | `us-west-2` | Bedrock region |

For Ollama:

```bash
ollama pull qwen3:30b
```

## Running

### Recommended (Windows): start everything

```bat
start_application.bat
```

This picks free ports for backend + frontend, sets `VITE_BACKEND_PORT`/`VITE_DEV_PORT`, and opens the browser.

If you see `ECONNREFUSED 127.0.0.1:8000` in the Vite terminal, your backend is not running on the port the frontend is proxying to (use `start_application.bat`, or set `VITE_BACKEND_PORT` correctly).

### Run backend only

```bat
start_backend.bat
```

Or directly:

```bash
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000
```

### Run frontend only

```bash
cd frontend
npm install
npm run dev
```

## Frontend UI

### Investigation Workbench

- Step-by-step iterative investigation flow (approve/decline/refine)
- Streaming updates over WebSockets
- Plotly charts rendered from JSON payloads

### Tech Ops SPC Dashboard (Demo)

The app includes a Tech Ops SPC dashboard intended to demonstrate DS-STAR investigations on KPI signal spikes.

- Weekly: Individuals-style line chart with stage-aware (Wheeler phase) limits
- Daily (30d): bar chart with day-of-week labels and a slider to zoom from 7 to 30 days
- Stage zoom: weekly slider to zoom to the last N detected stages/phases
- Stage markers: dotted vertical reference lines at detected stage changes
- Investigation telemetry: Individuals + Moving Range charts displayed at the top of an investigation
- Export PDF: uses the browser print dialog ("Print to PDF")

## Web API

### REST endpoints (high level)

- `GET /health`
- `GET /api/status`
- `GET /api/me`
- `POST /api/me/select`
- `POST /api/query`
- `GET /api/history`, `DELETE /api/history`
- Tech Ops:
  - `GET /api/techops/kpis`
  - `GET /api/techops/dashboard/weekly`
  - `GET /api/techops/dashboard/daily`
  - `GET /api/techops/signals/active`
  - `POST /api/techops/investigations`
  - `GET /api/techops/investigations`
  - `GET /api/techops/investigations/{investigation_id}`
  - `POST /api/techops/investigations/{investigation_id}/finalize`

### WebSockets

- `GET /ws/query`: streamed agent execution events for `/api/query`
- `GET /ws/stream`: streamed events for the Investigation Workbench UI

Workbench event directions:

**Client -> Server**
- `start_analysis`
- `approve_step`
- `refine_step`

**Server -> Client**
- `analysis_started`
- `step_started`
- `iteration_started`
- `code_generated`
- `execution_complete`
- `visualization_ready`
- `verification_complete`
- `step_completed`
- `analysis_completed`
- `error`

## Architecture

```
User
  |
Orchestrator (central hub)
  |
  +-- Data Analyst
  +-- ML Engineer
  +-- Visualization Expert
  |
Synthesized response (+ charts)
```

## Testing

```bash
pytest
```
