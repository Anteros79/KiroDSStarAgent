# Remediation Plan

This plan addresses the Top 3 Critical/High vulnerabilities identified in the audit.

## Fix 1: Resolve Concurrency & Race Conditions (VULN-001)

**Issue:** `orchestrator.stream_handler` is being swapped globally.
**Solution:** Pass the stream handler *per request* to the `process()` method, instead of attaching it to the agent instance at initialization.

### Steps

1. Modify `OrchestratorAgent.process` signature in `src/agents/orchestrator.py` to accept an optional `stream_handler`.
2. Update `OrchestratorAgent.__init__` to NOT require a stream handler (or set a default no-op).
3. Update `src/api/server.py` to pass the local `WebSocketStreamHandler` directly to `process()`.

#### Code Snippet (Proposal) - `src/agents/orchestrator.py`

```python
# Change process signature
def process(self, query: str, context: Optional[Dict[str, Any]] = None, stream_handler: Optional[InvestigationStreamHandler] = None) -> AgentResponse:
    # Use passed handler or fall back to default
    handler = stream_handler or self.stream_handler
    
    # Update all self.stream_handler calls to use 'handler' local variable
    handler.on_agent_start("Orchestrator", query)
    # ...
```

## Fix 2: Session-Based Identity (VULN-002)

**Issue:** `_current_identity_id` is global.
**Solution:** Implement a simple session token mechanism or (for PoC) use a dependency injection that reads a header `X-User-ID`.

### Steps

1. Remove global `_current_identity_id`.
2. Create a dependency `get_current_user` in `src/api/server.py`.
3. Require this dependency in endpoints that need identity.

#### Code Snippet (Proposal) - `src/api/server.py`

```python
from fastapi import Header

async def get_current_identity_id(x_user_id: str = Header("jmartinez", alias="X-User-ID")):
    # Validate user exists in _demo_identities
    user = next((u for u in _demo_identities if u["id"] == x_user_id), None)
    if not user:
        raise HTTPException(401, "Invalid User ID")
    return user["id"]

# Update endpoints
@app.post("/api/techops/investigations")
async def techops_create_investigation(req: CreateInvestigationRequest, user_id: str = Depends(get_current_identity_id)):
    # Use user_id instead of global variable
```

## Fix 3: Isolate Data Storage (VULN-003)

**Issue:** `_techops_investigations` is global and shared.
**Solution:** For a PoC, key the investigations by User ID. For production, use a Database (SQLite/Postgres).

### Steps: (PoC Quick Fix)

1. Filter list results by the `user_id` from the context/header.
2. Actually, better: Just enforce that `created_by` matches the current user when acting on an investigation.

## Recommended "Fix" Agent

To automate these fixes, a **Senior Backend Engineer** agent is recommended.
**Prompt:** "Refactor `src/api/server.py` and `src/agents/orchestrator.py` to support stateless, concurrent execution. Remove global state variables and implement per-request StreamHandler injection."
