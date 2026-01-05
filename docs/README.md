# DS-STAR Documentation

**Last Updated:** January 4, 2026

This directory contains project documentation including HTML specs and markdown guides.

## Documentation Index

### HTML Documentation

| File | Description |
|------|-------------|
| `index.html` | Documentation landing page |
| `prd.html` | Product requirements document |
| `architecture.html` | System architecture (star topology, data flow) |
| `agent-flow.html` | Agent flow diagrams (routing, streaming) |
| `functional-spec.html` | Functional specification |
| `technical-spec.html` | Technical specification |
| `project-management.html` | Project management notes |

### Markdown Documentation

| File | Description |
|------|-------------|
| `data-storage.md` | Data model for Tech Ops dashboard + investigations |
| `tech-ops-implementation-backlog.md` | Living backlog for Tech Ops features |

### Root-Level Documentation

| File | Description |
|------|-------------|
| `README.md` | Main project README |
| `CODE_REVIEW_SUMMARY.md` | Security audit and code quality findings |
| `AGENTIC_FRAMEWORK_ANALYSIS.md` | Agent prompt analysis and improvements |
| `PROVIDER_QUICK_REFERENCE.md` | LLM provider configuration guide |
| `LEMONADE_INTEGRATION.md` | Lemonade-specific integration notes |
| `OPENAI_INTEGRATION_REVIEW.md` | OpenAI integration notes |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  React + TypeScript + Tailwind + Plotly                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Dashboard  │  │  Workbench  │  │   Admin     │         │
│  │   Page      │  │    Page     │  │   Review    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└────────────────────────┬────────────────────────────────────┘
                         │ REST + WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                     FastAPI Server                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    REST     │  │  WebSocket  │  │   Tech Ops  │         │
│  │  Endpoints  │  │  Streaming  │  │    APIs     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Orchestrator Agent                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Query Analysis → Routing → Synthesis → Response    │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │         │          │          │         │
┌───▼───┐ ┌──▼───┐ ┌────▼────┐ ┌──▼───┐ ┌───▼───┐
│ Data  │ │  ML  │ │   Viz   │ │Stats │ │Domain │
│Analyst│ │ Eng  │ │ Expert  │ │Expert│ │Expert │
└───────┘ └──────┘ └─────────┘ └──────┘ └───────┘
```

## Key Components

### Orchestrator Agent
- Central coordinator in star topology
- Keyword-based query routing
- Multi-specialist coordination
- Response synthesis
- Conversation context management

### Specialist Agents
- **Data Analyst**: Statistical analysis, KPI calculations
- **ML Engineer**: Model recommendations, code generation
- **Visualization Expert**: Chart creation, Plotly JSON
- **Statistics Expert**: Hypothesis testing, statistical guidance
- **Domain Expert**: Airline industry knowledge, benchmarks

### Tech Ops Module
- Wheeler XmR statistical process control
- Phase-aware control limits
- Diagnostic test suite
- Demo scenario support

### Frontend
- React + TypeScript
- Tailwind CSS styling
- Plotly.js charting
- WebSocket streaming

## Viewing Documentation

Open `docs/index.html` in a browser and navigate via links.

## Updating Documentation

1. Prefer updating markdown sources when possible
2. If regenerating HTML docs, verify links from `index.html`
3. Keep `CODE_REVIEW_SUMMARY.md` updated after code changes
4. Update `AGENTIC_FRAMEWORK_ANALYSIS.md` after prompt changes

## Test Coverage

| Component | Test File | Status |
|-----------|-----------|--------|
| Configuration | `tests/test_config.py` | ✅ 11/11 |
| Orchestrator | `tests/test_orchestrator.py` | ✅ |
| Specialists | `tests/test_specialists.py` | ✅ |
| Frontend | `npm run build` | ✅ |

## Security Notes

See `CODE_REVIEW_SUMMARY.md` for detailed security findings:

- CORS restricted to localhost
- No authentication (demo mode)
- In-memory storage (no persistence)
- API keys from environment variables
- Pydantic validation on all endpoints
