# DS-STAR Multi-Agent System

Implementation of the DS-STAR (Data Science Star) multi-agent framework using the AWS Strands Agents SDK. Supports Lemonade (default), Anthropic Claude, OpenAI, local Ollama models, and Amazon Bedrock.

**Last Updated:** January 6, 2026  
**Version:** 1.1.0

## Overview

This system uses a star topology where a central Orchestrator coordinates five specialist agents:

```
                    ┌─────────────────┐
                    │   Orchestrator  │
                    │     Agent       │
                    └────────┬────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    │           │            │            │           │
┌───▼───┐  ┌───▼───┐   ┌────▼────┐  ┌───▼───┐  ┌───▼───┐
│ Data  │  │  ML   │   │  Viz    │  │ Stats │  │Domain │
│Analyst│  │Engineer│  │ Expert  │  │Expert │  │Expert │
└───────┘  └───────┘   └─────────┘  └───────┘  └───────┘
```

### Specialist Agents

| Agent | Capabilities |
|-------|-------------|
| **Data Analyst** | Data exploration, statistical analysis, KPI calculations, trend identification |
| **ML Engineer** | Model recommendations, algorithm selection, code generation, feature engineering |
| **Visualization Expert** | Chart type selection, matplotlib/Plotly code generation, design best practices |
| **Statistics Expert** | Hypothesis testing, statistical test selection, p-value interpretation |
| **Domain Expert** | Airline industry knowledge, benchmarks, regulatory context, best practices |

### Key Features

- **Multi-provider LLM support**: Lemonade (default), Anthropic, OpenAI, Ollama, Bedrock
- **Real-time streaming**: WebSocket-based investigation updates
- **Wheeler XmR SPC**: Statistical process control for signal detection
- **Tech Ops Dashboard**: KPI visualization with phase-aware control limits
- **Investigation Workbench**: Multi-step analysis workflow with approve/refine controls
- **Things to Consider**: Guided query suggestions with field advice and industry factors
- **Responsive Design**: Mobile-optimized interface with adaptive layouts
- **Demo Scenarios**: Pre-built scenarios for presentations

## Project Structure

```
.
├── src/                      # Python backend
│   ├── agents/
│   │   ├── orchestrator.py   # Central coordinator
│   │   └── specialists/      # 5 specialist agents
│   ├── api/
│   │   └── server.py         # FastAPI + WebSockets (~2000 lines)
│   ├── data/                 # Data loaders + demo generators
│   ├── handlers/             # Stream, chart, error, retry handlers
│   ├── llm/                  # LLM clients (generic multi-provider + Ollama)
│   ├── security/             # Security audit and hardening tools
│   │   ├── models.py         # Security finding data models
│   │   ├── secret_scanner.py # Hardcoded secrets detection
│   │   ├── dependency_analyzer.py # CVE vulnerability scanning
│   │   └── api_auditor.py    # API endpoint security analysis
│   ├── spc/                  # Wheeler XmR implementation
│   └── techops/              # Investigation diagnostic tests
├── frontend/                 # React/TypeScript UI
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── hooks/            # React hooks (useAnalysis, useWebSocket)
│   │   ├── services/         # API and WebSocket services
│   │   └── techops/          # Tech Ops dashboard components
├── docs/                     # HTML + markdown documentation
├── demo/                     # Demo scripts + sample queries
├── data/                     # Sample datasets (CSV)
├── tests/                    # pytest test suite
├── start_application.bat     # Starts backend + frontend
├── start_backend.bat         # Starts backend only
├── .env.example              # Environment variable template
├── CODE_REVIEW_SUMMARY.md    # Code review findings
└── AGENTIC_FRAMEWORK_ANALYSIS.md  # Agent prompt analysis
```

## Quick Start

### 1. Install Dependencies

```bash
# Python backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### 2. Configure Model Provider

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### 3. Run the Application

**Windows (recommended):**
```bat
start_application.bat
```

**Manual:**
```bash
# Terminal 1: Backend
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DS_STAR_MODEL_PROVIDER` | `lemonade` | Provider: `lemonade`, `anthropic`, `openai`, `ollama`, `bedrock` |
| `DS_STAR_MODEL_ID` | `Qwen3-Next-80B-A3B-Instruct-GGUF` | Model identifier |
| `DS_STAR_LEMONADE_BASE_URL` | `http://localhost:8000/api/v1` | Lemonade server URL |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `DS_STAR_OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `AWS_REGION` | `us-west-2` | AWS region for Bedrock |

### Provider Setup

<details>
<summary><b>Lemonade (Default)</b></summary>

```bash
# Ensure Lemonade server is running
export DS_STAR_LEMONADE_BASE_URL=http://localhost:8000/api/v1
```
</details>

<details>
<summary><b>Anthropic Claude</b></summary>

```bash
export DS_STAR_MODEL_PROVIDER=anthropic
export DS_STAR_MODEL_ID=claude-3-5-sonnet-20241022
export ANTHROPIC_API_KEY=your-api-key
```
</details>

<details>
<summary><b>OpenAI</b></summary>

```bash
export DS_STAR_MODEL_PROVIDER=openai
export DS_STAR_MODEL_ID=gpt-4o
export OPENAI_API_KEY=your-api-key
```
</details>

<details>
<summary><b>Ollama (Local)</b></summary>

```bash
ollama pull qwen3:30b
export DS_STAR_MODEL_PROVIDER=ollama
export DS_STAR_MODEL_ID=qwen3:30b
```
</details>

<details>
<summary><b>AWS Bedrock</b></summary>

```bash
aws configure
export DS_STAR_MODEL_PROVIDER=bedrock
export DS_STAR_MODEL_ID=us.amazon.nova-lite-v1:0
```
</details>

## API Reference

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/status` | GET | System status |
| `/api/me` | GET | Current identity |
| `/api/me/select` | POST | Select identity |
| `/api/query` | POST | Process query |
| `/api/history` | GET/DELETE | Conversation history |
| `/api/techops/kpis` | GET | KPI definitions |
| `/api/techops/dashboard/weekly` | GET | Weekly dashboard data |
| `/api/techops/dashboard/daily` | GET | Daily dashboard data |
| `/api/techops/signals/active` | GET | Active signals |
| `/api/techops/investigations` | GET/POST | List/create investigations |
| `/api/techops/investigations/{id}` | GET | Get investigation |
| `/api/techops/investigations/{id}/finalize` | POST | Finalize investigation |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/query` | Streamed agent execution events |
| `/ws/stream` | Investigation workbench streaming |

## Tech Ops Dashboard

### Features

- **Weekly View**: Line+markers chart with Wheeler phase limits (proper SPC style)
- **Daily View**: Bar chart with day-of-week labels (7-30 day slider)
- **Stage Detection**: Automatic phase change detection with visual markers
- **XmR Charts**: Individuals (line+markers) + Moving Range combo charts
- **Signal Detection**: Rule #1 violations highlighted in red with distinct markers
- **Things to Consider**: Guided query suggestions to help station managers learn effective DS-Star usage

### Things to Consider Feature

The "Things to Consider" section provides two types of guided query suggestions:

#### Advice from the Field
- **Dynamic suggestions** based on investigation diagnostics and findings
- **Similar conditions** from other stations with comparable signals
- **Context-aware prompts** that include station, KPI, and time window information
- **Automatic generation** from stage changes, YoY deltas, and peer comparisons

#### Common Industry Causal Factors
- **Standard factors** to check during root cause analysis
- **KPI-specific relevance** with factors prioritized by industry best practices
- **Template-based queries** with automatic context interpolation
- **Comprehensive coverage** of environmental, resource, fleet, supply chain, and process factors

#### Responsive Design
- **Mobile-optimized** layout with single-column stacking on viewports < 768px
- **Adaptive spacing** and typography that scales appropriately across devices
- **Touch-friendly** suggestion chips with proper sizing and spacing
- **Consistent styling** that maintains visual hierarchy on all screen sizes

### Diagnostic Tests

When an investigation is created, these tests run automatically:

| Test | Purpose | Confidence Factors |
|------|---------|-------------------|
| Signal Characterization | Identify Rule #1 violations, stage changes | Beyond NPL: 0.92, Stage change: 0.88 |
| YoY Seasonality | Compare to year-over-year baseline | Large delta: 0.85, Small delta: 0.65 |
| Cross-Station | Benchmark against peer stations | Clear isolation: 0.95, Similar: 0.70 |
| Pre/Post Shift | Detect mean shifts | Large shift: 0.90, Small shift: 0.68 |
| Final Summary | Synthesize findings | With root cause: 0.92 |

### Demo Scenarios

Pre-built scenarios in `src/data/demo_scenarios.py`:

1. **PHX Parts Shortage**: Parts availability issue at Phoenix
2. **DAL Weather Cascade**: Weather-triggered maintenance delays at Dallas
3. **Fleet-Wide Fault Rate**: Company-wide software update impact

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py -v

# Run security module tests
pytest tests/test_secret_scanner.py tests/test_dependency_analyzer.py tests/test_api_auditor.py -v

# Frontend build check
cd frontend && npm run build
```

### Test Coverage

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_config.py` | 11 | ✅ All passing |
| `test_orchestrator.py` | Routing, processing, synthesis | ✅ |
| `test_specialists.py` | All 5 specialists | ✅ |
| `test_secret_scanner.py` | Secret detection, masking | ✅ |
| `test_dependency_analyzer.py` | Dependency parsing, CVE lookup | ✅ |
| `test_api_auditor.py` | Endpoint detection, auth checks | ✅ |
| `test_security_models.py` | Data model validation | ✅ |

## Documentation

| Document | Description |
|----------|-------------|
| `CODE_REVIEW_SUMMARY.md` | Security audit and code quality findings |
| `AGENTIC_FRAMEWORK_ANALYSIS.md` | Agent prompt analysis and improvements |
| `PROVIDER_QUICK_REFERENCE.md` | LLM provider configuration guide |
| `LEMONADE_INTEGRATION.md` | Lemonade-specific integration notes |
| `.kiro/specs/security-audit-hardening/` | Security module spec and tasks |
| `docs/` | HTML documentation (architecture, specs) |
| `demo/` | Demo scripts and sample queries |

## Generic LLM Client

The `src/llm/generic_client.py` module provides a unified interface for calling multiple LLM providers without external SDK dependencies (uses only `urllib`).

### Usage

```python
from src.llm.generic_client import chat

# Call any supported provider with the same interface
content, latency_ms, raw_response = chat(
    provider="openai",      # or "ollama", "lemonade", "anthropic"
    model="gpt-4o",
    prompt="Analyze this data...",
    max_tokens=1024,
    temperature=0.2,
)

if content:
    print(f"Response ({latency_ms}ms): {content}")
else:
    print(f"Error: {raw_response.get('error')}")
```

### Supported Providers

| Provider | API Key Required | Notes |
|----------|-----------------|-------|
| `lemonade` | No | Local server, OpenAI-compatible (auth header omitted) |
| `openai` | Yes (`OPENAI_API_KEY`) | Uses `/chat/completions` |
| `anthropic` | Yes (`ANTHROPIC_API_KEY`) | Uses Messages API |
| `ollama` | No | Local server at `localhost:11434` |
| `bedrock` | N/A | Requires boto3 SDK (use main agent flow) |

### URL Handling

The generic client intelligently handles various base URL formats:
- `http://localhost:8000/api/v1` → appends `/chat/completions`
- `http://localhost:8000` → appends `/v1/chat/completions`
- `http://localhost:8000/v1/chat/completions` → uses as-is

For local servers like Lemonade that don't require authentication, the `Authorization` header is automatically omitted when `api_key` is `None` or `"not-needed"`.

### Return Value

Returns a tuple: `(content, latency_ms, raw_response)`
- `content`: The response text (or `None` on error)
- `latency_ms`: Request latency in milliseconds
- `raw_response`: Full API response dict (includes `error` key on failure)

## Security Audit Module

The `src/security/` module provides comprehensive security scanning capabilities:

### Secret Scanner
Detects hardcoded secrets in source code using regex pattern matching:
- API keys and tokens
- AWS credentials (Access Key ID, Secret Access Key)
- Private keys (RSA, OPENSSH, EC, DSA)
- JWT tokens
- Database connection strings
- Generic passwords and secrets

```python
from src.security.secret_scanner import SecretScanner

scanner = SecretScanner("./")
findings = scanner.scan_all_files()
summary = scanner.generate_scan_summary(findings)
```

### Dependency Analyzer
Cross-references project dependencies against CVE databases:
- Parses `requirements.txt` (Python) and `package.json` (Node.js)
- Integrates with `pip-audit` and `npm audit`
- Reports CVE IDs, severity scores, and safe versions

```python
from src.security.dependency_analyzer import DependencyAnalyzer

analyzer = DependencyAnalyzer("./")
dependencies, findings = analyzer.analyze_all()
summary = analyzer.get_summary(dependencies, findings)
```

### API Auditor
Analyzes API endpoints for OWASP Top 10 vulnerabilities:
- Detects FastAPI, Flask, and Express endpoints
- Checks for missing authorization controls
- Identifies injection risks (SQL, command, code execution)
- Flags unvalidated user inputs

```python
from src.security.api_auditor import APIAuditor

auditor = APIAuditor("./")
findings = auditor.audit_all_files()
summary = auditor.get_summary(findings)
```

### Report Generator
Generates comprehensive SECURITY_AUDIT.md reports:
- Executive summary with overall risk assessment
- Key metrics table (findings by severity)
- Category breakdown (secrets, dependencies, auth, injection)
- Effort estimates for remediation planning

```python
from src.security.report_generator import ReportGenerator
from src.security.models import AuditReport

report = AuditReport()
# ... add findings to report ...
generator = ReportGenerator(report)
risk_level = generator.calculate_risk_assessment(findings)
summary_md = generator.generate_executive_summary(findings)
```

### Security Models
All findings use structured data models with severity levels:
- `Severity`: CRITICAL, HIGH, MEDIUM, LOW, INFO
- `FindingCategory`: HARDCODED_SECRET, VULNERABLE_DEPENDENCY, MISSING_AUTHZ, INJECTION_RISK, INSECURE_CONFIG
- `AuditReport`: Aggregates findings with summary counts

---

## Security Considerations

- **CORS**: Restricted to localhost dev servers
- **Authentication**: Demo mode with hardcoded identities (add auth for production)
- **Storage**: In-memory (add database for persistence)
- **API Keys**: Loaded from environment variables
- **Input Validation**: Pydantic models on all endpoints

## Contributing

1. Run tests before committing: `pytest`
2. Check TypeScript: `cd frontend && npm run build`
3. Follow existing code patterns
4. Update documentation for significant changes

## License

[Add license information]
