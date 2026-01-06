## Executive Summary
**Grade: Fail.** The system exposes unauthenticated API/WS surfaces, performs file writes without honoring configured output paths, and shares mutable global state across requests. Automated dependency auditing could not complete due to registry restrictions, and Python dependencies are unpinned, leaving supply-chain risk unmanaged.

## Dependency Check
- `npm audit --audit-level=high` (frontend): **Failed** – registry returned HTTP 403, so vulnerability data could not be retrieved. Manual review still recommended for packages such as React 18.2.x, Vite 5.0.x, and Plotly 2.27.x (see `frontend/package.json`).
- `pip audit`: **Unavailable** – `pip` lacks the `audit` command in this environment. Requirements are unpinned in `requirements.txt`, preventing deterministic vulnerability evaluation.

## Critical Findings
1. **Unauthenticated API and WebSocket exposure** – All REST and WS endpoints are publicly accessible and CORS is open to browser origins. This allows arbitrary external callers to trigger orchestrations and demo workflows, exposing internal data and compute. _Location: `src/api/server.py` L134-L149, L595-L1066._
2. **Background task leaks in WebSocket handlers** – WS handlers spawn tasks with `asyncio.create_task` but never track or cancel them. Clients that disconnect mid-flight leave tasks running, risking resource leaks and unhandled exceptions. _Location: `src/api/server.py` L666-L712, L760-L1046._
3. **Hardcoded output path for chart artifacts** – Visualization specialist instantiates `ChartOutputHandler("./output")` instead of using the configured `output_dir` passed via context, enabling writes to unintended directories and complicating multi-tenant isolation. _Location: `src/agents/specialists/visualization_expert.py` L685-L703._
4. **Global mutable dataset shared across requests** – `query_airline_data` mutates the global DataFrame (adds `route`) on each call without copying or synchronization, so concurrent requests can interfere with one another and return tainted results. _Location: `src/data/airline_data.py` L295-L309._
5. **High-complexity orchestration path** – `OrchestratorAgent.process` contains nested routing, tool invocation, and error-handling branches (multiple try/excepts and loops), pushing cyclomatic complexity beyond recommended limits (>15) and increasing the chance of unhandled states or logic bugs. _Location: `src/agents/orchestrator.py` L139-L238._
6. **Model initialization can continue with `None` backends** – Startup proceeds even when Bedrock/Ollama classes are unavailable, leaving `model=None` in production paths and deferring failures to request time. _Location: `src/api/server.py` L329-L364._

## Refactoring Roadmap
1. **Enforce authentication/authorization and tighten CORS** – Add auth middleware (e.g., JWT/API key) for REST and WS routes, restrict allowed origins, and set rate limits to prevent abuse.
2. **Stabilize resource handling and data isolation** – Track and cancel WS tasks on disconnects; avoid mutating shared DataFrames by copying or using per-request contexts; propagate the configured `output_dir` to all writers.
3. **Harden startup and reduce complexity** – Fail fast when model backends are unavailable; refactor `OrchestratorAgent.process` into smaller, testable units with explicit error contracts to lower cyclomatic complexity and improve observability.
