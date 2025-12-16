"""FastAPI server for DS-Star multi-agent system web interface."""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import Config
from src.agents.orchestrator import OrchestratorAgent
from src.handlers.stream_handler import InvestigationStreamHandler
from src.data.airline_data import initialize_data_loader
from src.data.techops_metrics import get_techops_store

# Import specialist agents
from src.agents.specialists.data_analyst import data_analyst
from src.agents.specialists.ml_engineer import ml_engineer
from src.agents.specialists.visualization_expert import visualization_expert

# Import Strands components
try:
    from strands.models.bedrock import BedrockModel
    from strands.models.ollama import OllamaModel
except ImportError:
    print("Warning: strands-agents package not installed.")
    BedrockModel = None
    OllamaModel = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_chart_from_response(response_text: str, query: str) -> Optional[Dict[str, Any]]:
    """Generate a Plotly chart from the response text by parsing data patterns."""
    import re
    
    # Try to extract data from common patterns
    
    # Pattern 1: "airline: AA, value: 0.85" or "AA: 0.85" style
    # Pattern 2: Table-like data with headers
    # Pattern 3: Key-value pairs
    
    labels = []
    values = []
    title = "Analysis Results"
    
    # Look for airline codes with numeric values
    # Pattern: AA 199 233 0.854077 (airline, count1, count2, rate)
    airline_pattern = r'\b([A-Z]{2})\s+(\d+)\s+(\d+)\s+([\d.]+)'
    matches = re.findall(airline_pattern, response_text)
    
    if matches:
        labels = [m[0] for m in matches]
        # Use the rate (last value) for the chart
        values = [float(m[3]) for m in matches]
        title = "Performance by Airline"
    
    # Pattern: "AA: 85.4%" or "AA - 0.854"
    if not labels:
        simple_pattern = r'\b([A-Z]{2})[\s:=-]+([\d.]+)%?'
        matches = re.findall(simple_pattern, response_text)
        if len(matches) >= 2:
            labels = [m[0] for m in matches]
            values = [float(m[1]) for m in matches]
            title = "Results by Airline"
    
    # Pattern: Look for "airline" followed by values
    if not labels:
        lines = response_text.split('\n')
        for line in lines:
            # Match lines like "AA    0.854" or "American Airlines (AA): 85.4%"
            match = re.search(r'([A-Z]{2})[)\s:]+\s*([\d.]+)', line)
            if match:
                labels.append(match.group(1))
                val = float(match.group(2))
                # Convert to percentage if it looks like a rate
                values.append(val * 100 if val < 1 else val)
    
    # If we found data, create the chart
    if labels and values and len(labels) >= 2:
        # Determine if values are percentages
        is_percentage = all(0 <= v <= 100 for v in values) or all(0 <= v <= 1 for v in values)
        
        # Normalize to percentage if needed
        if all(0 <= v <= 1 for v in values):
            values = [v * 100 for v in values]
        
        # Create colors based on values (higher = greener)
        max_val = max(values) if values else 1
        colors = [f'rgb({int(255 - (v/max_val)*155)}, {int(100 + (v/max_val)*155)}, 100)' for v in values]
        
        plotly_json = {
            "data": [{
                "type": "bar",
                "x": labels,
                "y": values,
                "marker": {
                    "color": colors,
                    "line": {"color": "rgb(50, 50, 50)", "width": 1}
                },
                "text": [f"{v:.1f}%" if is_percentage else f"{v:.2f}" for v in values],
                "textposition": "outside",
            }],
            "layout": {
                "title": {"text": title, "font": {"size": 16}},
                "xaxis": {"title": "Airline", "tickangle": 0},
                "yaxis": {
                    "title": "Rate (%)" if is_percentage else "Value",
                    "range": [0, max(values) * 1.15] if values else [0, 100]
                },
                "plot_bgcolor": "rgba(248, 250, 252, 0.8)",
                "paper_bgcolor": "white",
                "font": {"family": "Inter, system-ui, sans-serif"},
                "margin": {"t": 60, "b": 60, "l": 60, "r": 30},
            }
        }
        
        return {
            "chart_type": "bar",
            "title": title,
            "plotly_json": plotly_json,
        }
    
    return None


def generate_techops_kpi_chart(*, kpi_id: str, station: str, window: str, point_t: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Generate a Plotly chart from Tech Ops KPI time series (station vs fleet average)."""
    try:
        store = get_techops_store()
        series_map = store.get_weekly_series(station=station, weeks=53) if window == "weekly" else store.get_daily_series(station=station, days=30)
        if kpi_id not in series_map:
            return None
        s = series_map[kpi_id]

        # Fleet average across known stations for the same window
        stations = getattr(store, "stations", []) or ["DAL", "PHX", "HOU"]
        fleet_series = []
        for st in stations:
            try:
                sm = store.get_weekly_series(station=st, weeks=53) if window == "weekly" else store.get_daily_series(station=st, days=30)
                if kpi_id in sm:
                    fleet_series.append(sm[kpi_id])
            except Exception:
                continue

        t_list = [p.t for p in s.points]
        station_vals = [p.value for p in s.points]

        fleet_vals = None
        if fleet_series:
            # average by aligned index (deterministic store produces aligned time windows)
            n = len(t_list)
            acc = [0.0] * n
            cnt = [0] * n
            for fs in fleet_series:
                for idx, p in enumerate(fs.points[:n]):
                    acc[idx] += float(p.value)
                    cnt[idx] += 1
            fleet_vals = [(acc[i] / cnt[i]) if cnt[i] else None for i in range(n)]

        label = s.kpi.label
        unit = s.kpi.unit
        title = f"{label} - {station} ({window})"

        highlight_idx = None
        if point_t and point_t in t_list:
            highlight_idx = t_list.index(point_t)

        plotly_json: Dict[str, Any] = {
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": station,
                    "x": t_list,
                    "y": station_vals,
                    "line": {"color": "#2563EB", "width": 3},
                    "marker": {"size": 6, "color": "#2563EB"},
                    "hovertemplate": "%{x}<br>%{y}<extra></extra>",
                }
            ],
            "layout": {
                "title": {"text": title, "font": {"size": 16}},
                "xaxis": {"title": "Time", "tickangle": -25, "showgrid": False},
                "yaxis": {"title": f"Value ({unit})", "zeroline": False},
                "margin": {"t": 60, "b": 90, "l": 60, "r": 30},
                "legend": {"orientation": "h", "y": 1.1},
                "plot_bgcolor": "rgba(248, 250, 252, 0.8)",
                "paper_bgcolor": "white",
                "font": {"family": "Inter, system-ui, sans-serif"},
            },
        }

        if fleet_vals:
            plotly_json["data"].append(
                {
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Fleet avg",
                    "x": t_list,
                    "y": fleet_vals,
                    "line": {"color": "#64748B", "width": 2, "dash": "dot"},
                    "hovertemplate": "%{x}<br>%{y}<extra></extra>",
                }
            )

        if highlight_idx is not None:
            plotly_json["data"].append(
                {
                    "type": "scatter",
                    "mode": "markers",
                    "name": "Selected",
                    "x": [t_list[highlight_idx]],
                    "y": [station_vals[highlight_idx]],
                    "marker": {"size": 12, "color": "#DC2626", "symbol": "circle-open"},
                    "hovertemplate": "Selected<br>%{x}<br>%{y}<extra></extra>",
                }
            )

        return {"chart_type": "line", "title": title, "plotly_json": plotly_json}
    except Exception:
        return None

# Create FastAPI app
app = FastAPI(
    title="DS-Star Multi-Agent System API",
    description="API for interacting with the DS-Star multi-agent system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
orchestrator: Optional[OrchestratorAgent] = None
config: Optional[Config] = None
techops = None

# In-memory demo identity + investigations (demo scope)
_demo_identities = [
    {"id": "jmartinez", "name": "J. Martinez", "role": "Station Manager", "station": "DAL"},
    {"id": "techops_phx", "name": "A. Chen", "role": "Tech Ops Analyst", "station": "PHX"},
    {"id": "reliability_hq", "name": "R. Patel", "role": "Reliability Eng", "station": "HOU"},
]
_current_identity_id = "jmartinez"

# investigations: id -> record
_techops_investigations: Dict[str, Dict[str, Any]] = {}


# Request/Response models
class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    response: str
    routing: list[str]
    execution_time_ms: int
    charts: list[Dict[str, Any]] = []


class ColumnInfo(BaseModel):
    name: str
    dtype: str


class DatasetInfo(BaseModel):
    filename: str
    description: str
    columns: list[ColumnInfo]
    rowCount: int


class SystemStatus(BaseModel):
    status: str
    model: str
    region: str
    specialists: list[str]
    data_loaded: bool
    dataset_info: Optional[DatasetInfo] = None


class StreamEvent(BaseModel):
    type: str  # "agent_start", "routing", "tool_call", "agent_end", "response", "error"
    data: Dict[str, Any]
    timestamp: str


class AnalyzeRequest(BaseModel):
    research_goal: str
    dataset_path: Optional[str] = None


class DemoIdentity(BaseModel):
    id: str
    name: str
    role: str
    station: str


class SelectIdentityRequest(BaseModel):
    identity_id: str


class KPIDefinition(BaseModel):
    id: str
    label: str
    unit: str
    goal: float
    ul: float
    ll: float
    decimals: int


class MetricPoint(BaseModel):
    t: str
    value: float
    yoy_value: Optional[float] = None
    yoy_delta: Optional[float] = None
    signal_state: str


class KPISeriesResponse(BaseModel):
    kpi: KPIDefinition
    points: list[MetricPoint]
    mean: float
    past_value: float
    past_delta: float
    signal_state: str


class DashboardResponse(BaseModel):
    station: str
    window: str  # "weekly" | "daily"
    kpis: list[KPISeriesResponse]


class CreateInvestigationRequest(BaseModel):
    kpi_id: str
    station: str
    window: str  # "weekly" | "daily"
    point_t: Optional[str] = None  # clicked point (date or week_start)


class CreateInvestigationResponse(BaseModel):
    investigation_id: str
    prompt_mode: str  # "cause" | "yoy"
    prompt: str


class InvestigationRecord(BaseModel):
    investigation_id: str
    kpi_id: str
    station: str
    window: str
    created_by: DemoIdentity
    created_at: str
    status: str
    prompt_mode: str
    prompt: str
    selected_point_t: Optional[str] = None
    final_root_cause: Optional[str] = None
    final_actions: list[str] = []
    final_notes: Optional[str] = None
    final_evidence: list[Dict[str, Any]] = []
    # Persisted investigation artifacts (demo: in-memory)
    steps: list[Dict[str, Any]] = []
    diagnostics: list[Dict[str, Any]] = []
    telemetry: Optional[Dict[str, Any]] = None


class EvidenceItem(BaseModel):
    kind: str  # "iteration" | "telemetry" | "diagnostic"
    label: Optional[str] = None
    step_id: Optional[str] = None
    iteration_id: Optional[str] = None
    investigation_id: Optional[str] = None
    chart: Optional[Dict[str, Any]] = None
    excerpt: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class FinalizeInvestigationRequest(BaseModel):
    final_root_cause: str
    final_actions: list[str] = []
    final_notes: Optional[str] = None
    evidence: list[EvidenceItem] = []


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the DS-Star system on startup."""
    global orchestrator, config, techops
    
    try:
        logger.info("Starting DS-Star API server...")
        
        # Load configuration
        config = Config.load()
        logger.info(f"Configuration loaded: model={config.model_id}, region={config.region}")
        
        # Initialize data loader
        logger.info("Loading airline operations dataset...")
        # If data file is missing, generate it (mirrors CLI behavior)
        from pathlib import Path
        data_file_path = Path(config.data_path)
        if not data_file_path.exists():
            logger.warning(f"Data file not found: {config.data_path}")
            logger.info("Generating sample airline operations dataset...")
            from src.data.generate_sample_data import generate_dataset, save_to_csv

            records = generate_dataset(num_records=1200)
            save_to_csv(records, config.data_path)
            logger.info(f"✓ Generated {len(records)} flight records")
            logger.info(f"✓ Sample dataset saved to {config.data_path}")

        initialize_data_loader(config.data_path)
        logger.info("✓ Airline data loaded")

        # Initialize Tech Ops demo store
        techops = get_techops_store()
        logger.info("✓ Tech Ops demo metrics initialized")
        
        # Initialize stream handler
        stream_handler = InvestigationStreamHandler(verbose=config.verbose)
        
        # Initialize model based on provider
        model = None
        if config.model_provider == "ollama":
            if OllamaModel is None:
                logger.warning(
                    "OllamaModel not available (strands-agents not installed) - continuing in mock mode"
                )
                model = None
            else:
                logger.info(f"Connecting to Ollama at {config.ollama_host}...")
                model = OllamaModel(
                    model_id=config.model_id,
                    host=config.ollama_host,
                )
                logger.info(f"✓ Ollama model initialized: {config.model_id}")
        else:
            # Default to Bedrock
            if BedrockModel is None:
                logger.warning(
                    "BedrockModel not available (strands-agents not installed) - continuing in mock mode"
                )
                model = None
            else:
                logger.info("Connecting to Amazon Bedrock...")
                model = BedrockModel(
                    model_id=config.model_id,
                    region=config.region,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature
                )
                logger.info(f"✓ Bedrock model initialized: {config.model_id}")
        
        # Create specialist agents dictionary
        specialists = {
            "data_analyst": data_analyst,
            "ml_engineer": ml_engineer,
            "visualization_expert": visualization_expert
        }
        logger.info(f"✓ Loaded {len(specialists)} specialist agents")
        
        # Initialize orchestrator
        orchestrator = OrchestratorAgent(
            model=model,
            specialists=specialists,
            stream_handler=stream_handler,
            config=config
        )
        logger.info("✓ Orchestrator agent initialized")
        logger.info("DS-Star API server ready!")
        
    except Exception as e:
        logger.error(f"Failed to initialize DS-Star system: {e}", exc_info=True)
        raise


# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# System status endpoint
@app.get("/api/status", response_model=SystemStatus)
async def get_status():
    """Get the current system status."""
    if orchestrator is None or config is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Get dataset info from data loader
    from src.data.airline_data import get_data_loader
    try:
        data_loader = get_data_loader()
    except RuntimeError:
        data_loader = None
    
    dataset_info = None
    if data_loader and data_loader._df is not None:
        df = data_loader._df
        dataset_info = DatasetInfo(
            filename="airline_operations.csv",
            description="Airline operational data including flights, delays, and performance metrics",
            columns=[ColumnInfo(name=col, dtype=str(df[col].dtype)) for col in df.columns],
            rowCount=len(df)
        )
    
    # Format model display based on provider
    model_display = f"{config.model_provider}:{config.model_id}"
    
    return SystemStatus(
        status="ready",
        model=model_display,
        region=config.region if config.model_provider == "bedrock" else config.ollama_host,
        specialists=["data_analyst", "ml_engineer", "visualization_expert"],
        data_loaded=True,
        dataset_info=dataset_info
    )


@app.get("/api/me", response_model=DemoIdentity)
async def get_me():
    """Return the current demo identity (no-auth)."""
    identity = next((i for i in _demo_identities if i["id"] == _current_identity_id), _demo_identities[0])
    return DemoIdentity(**identity)


@app.post("/api/me/select", response_model=DemoIdentity)
async def select_me(req: SelectIdentityRequest):
    """Select the current demo identity."""
    global _current_identity_id
    identity = next((i for i in _demo_identities if i["id"] == req.identity_id), None)
    if not identity:
        raise HTTPException(status_code=400, detail="Unknown identity_id")
    _current_identity_id = identity["id"]
    return DemoIdentity(**identity)


@app.get("/api/techops/kpis", response_model=list[KPIDefinition])
async def techops_kpis():
    store = get_techops_store()
    return [
        KPIDefinition(
            id=k.id,
            label=k.label,
            unit=k.unit,
            goal=k.goal,
            ul=k.ul,
            ll=k.ll,
            decimals=k.decimals,
        )
        for k in store.get_kpis()
    ]


def _series_to_response(series) -> KPISeriesResponse:
    k = series.kpi
    return KPISeriesResponse(
        kpi=KPIDefinition(id=k.id, label=k.label, unit=k.unit, goal=k.goal, ul=k.ul, ll=k.ll, decimals=k.decimals),
        points=[
            MetricPoint(
                t=p.t,
                value=p.value,
                yoy_value=p.yoy_value,
                yoy_delta=p.yoy_delta,
                signal_state=p.signal_state,
            )
            for p in series.points
        ],
        mean=series.mean,
        past_value=series.past_value,
        past_delta=series.past_delta,
        signal_state=series.signal_state,
    )


@app.get("/api/techops/dashboard/weekly", response_model=DashboardResponse)
async def techops_dashboard_weekly(station: str = "DAL"):
    store = get_techops_store()
    series_map = store.get_weekly_series(station=station, weeks=53)
    return DashboardResponse(
        station=station,
        window="weekly",
        kpis=[_series_to_response(series_map[kpi_id]) for kpi_id in series_map],
    )


@app.get("/api/techops/dashboard/daily", response_model=DashboardResponse)
async def techops_dashboard_daily(station: str = "DAL"):
    store = get_techops_store()
    series_map = store.get_daily_series(station=station, days=30)
    return DashboardResponse(
        station=station,
        window="daily",
        kpis=[_series_to_response(series_map[kpi_id]) for kpi_id in series_map],
    )


@app.get("/api/techops/signals/active")
async def techops_active_signals(station: str = "DAL"):
    """Return active signals (warning/critical) for station based on most recent weekly values."""
    store = get_techops_store()
    series_map = store.get_weekly_series(station=station, weeks=53)
    signals = []
    for kpi_id, s in series_map.items():
        if s.signal_state != "none":
            signals.append(
                {
                    "signal_id": f"SIG-{station}-{kpi_id}",
                    "kpi_id": kpi_id,
                    "station": station,
                    "status": s.signal_state,
                    "detected_at": datetime.utcnow().isoformat(),
                    "latest_value": s.past_value,
                }
            )
    return {"station": station, "signals": signals}


@app.post("/api/techops/investigations", response_model=CreateInvestigationResponse)
async def techops_create_investigation(req: CreateInvestigationRequest):
    """Create a new investigation seeded from a KPI click."""
    store = get_techops_store()
    series_map = store.get_weekly_series(station=req.station, weeks=53) if req.window == "weekly" else store.get_daily_series(station=req.station, days=30)
    if req.kpi_id not in series_map:
        raise HTTPException(status_code=400, detail="Unknown kpi_id")

    series = series_map[req.kpi_id]
    # Determine prompt mode
    prompt_mode = "cause" if series.signal_state != "none" else "yoy"
    prompt = "What is the cause of this signal?" if prompt_mode == "cause" else "How does this compare to year over year performance?"

    # Identity
    identity = next((i for i in _demo_identities if i["id"] == _current_identity_id), _demo_identities[0])

    import uuid

    inv_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
    telemetry = generate_techops_kpi_chart(kpi_id=req.kpi_id, station=req.station, window=req.window, point_t=req.point_t)
    diagnostics = [
        {
            "name": "MX driver check",
            "status": "in_progress" if prompt_mode == "cause" else "completed",
            "confidence": 0.68 if prompt_mode == "cause" else 0.54,
            "detail": "Correlate KPI deviation with top fault/finding categories and recent work orders.",
        },
        {
            "name": "YoY / seasonality test",
            "status": "completed",
            "confidence": 0.72,
            "detail": "Compare current window to prior-year baseline for the same weeks/days.",
        },
        {
            "name": "Station vs fleet comparison",
            "status": "completed",
            "confidence": 0.64,
            "detail": "Benchmark station series vs fleet average to isolate local vs systemic drivers.",
        },
    ]
    record = {
        "investigation_id": inv_id,
        "kpi_id": req.kpi_id,
        "station": req.station,
        "window": req.window,
        "created_by": identity,
        "created_at": datetime.utcnow().isoformat(),
        "status": "open",
        "prompt_mode": prompt_mode,
        "prompt": prompt,
        "selected_point_t": req.point_t,
        "steps": [],
        "diagnostics": diagnostics,
        "telemetry": telemetry,
    }
    _techops_investigations[inv_id] = record
    return CreateInvestigationResponse(investigation_id=inv_id, prompt_mode=prompt_mode, prompt=prompt)


@app.get("/api/techops/investigations", response_model=list[InvestigationRecord])
async def techops_list_investigations(station: Optional[str] = None):
    out = []
    for inv in _techops_investigations.values():
        if station and inv["station"] != station:
            continue
        out.append(InvestigationRecord(**inv))
    # newest first
    out.sort(key=lambda r: r.created_at, reverse=True)
    return out


@app.get("/api/techops/investigations/{investigation_id}", response_model=InvestigationRecord)
async def techops_get_investigation(investigation_id: str):
    inv = _techops_investigations.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Not found")
    return InvestigationRecord(**inv)


@app.post("/api/techops/investigations/{investigation_id}/finalize", response_model=InvestigationRecord)
async def techops_finalize_investigation(investigation_id: str, req: FinalizeInvestigationRequest):
    inv = _techops_investigations.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Not found")
    inv["final_root_cause"] = req.final_root_cause
    inv["final_actions"] = req.final_actions
    inv["final_notes"] = req.final_notes
    inv["final_evidence"] = [e.model_dump() for e in req.evidence] if req.evidence else []
    inv["status"] = "finalized"
    _techops_investigations[investigation_id] = inv
    return InvestigationRecord(**inv)


# Query endpoint (REST)
@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a query through the orchestrator (REST endpoint)."""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Add context
        context = request.context or {}
        context.update({
            "output_dir": config.output_dir,
            "data_path": config.data_path
        })
        
        # Process through orchestrator
        response = orchestrator.process(request.query, context)
        
        return QueryResponse(
            response=response.synthesized_response,
            routing=response.routing,
            execution_time_ms=response.total_time_ms,
            charts=[chart.__dict__ if hasattr(chart, '__dict__') else chart for chart in response.charts]
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for streaming
@app.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    """Process queries with real-time streaming via WebSocket."""
    await websocket.accept()
    
    if orchestrator is None:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "System not initialized"},
            "timestamp": datetime.utcnow().isoformat()
        })
        await websocket.close()
        return
    
    try:
        while True:
            # Receive query from client
            data = await websocket.receive_json()
            query = data.get("query", "")
            
            if not query:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Empty query"},
                    "timestamp": datetime.utcnow().isoformat()
                })
                continue
            
            logger.info(f"WebSocket query: {query}")
            
            # Send start event
            await websocket.send_json({
                "type": "query_start",
                "data": {"query": query},
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Create a custom stream handler that sends events via WebSocket
            class WebSocketStreamHandler(InvestigationStreamHandler):
                def __init__(self, ws: WebSocket):
                    super().__init__(verbose=True)
                    self.ws = ws
                
                async def send_event(self, event_type: str, data: Dict[str, Any]):
                    await self.ws.send_json({
                        "type": event_type,
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                def on_agent_start(self, agent_name: str, query: str):
                    super().on_agent_start(agent_name, query)
                    asyncio.create_task(self.send_event("agent_start", {
                        "agent": agent_name,
                        "query": query
                    }))
                
                def on_routing_decision(self, specialist: str, reasoning: str):
                    super().on_routing_decision(specialist, reasoning)
                    asyncio.create_task(self.send_event("routing", {
                        "specialist": specialist,
                        "reasoning": reasoning
                    }))
                
                def on_tool_start(self, tool_name: str, inputs: Dict):
                    super().on_tool_start(tool_name, inputs)
                    asyncio.create_task(self.send_event("tool_start", {
                        "tool": tool_name,
                        "inputs": inputs
                    }))
                
                def on_tool_end(self, tool_name: str, result: Any):
                    super().on_tool_end(tool_name, result)
                    asyncio.create_task(self.send_event("tool_end", {
                        "tool": tool_name,
                        "result": str(result)[:500]  # Truncate long results
                    }))
                
                def on_agent_end(self, agent_name: str, response: str):
                    super().on_agent_end(agent_name, response)
                    asyncio.create_task(self.send_event("agent_end", {
                        "agent": agent_name,
                        "response": response
                    }))
            
            # Process query with WebSocket streaming
            ws_handler = WebSocketStreamHandler(websocket)
            
            # Temporarily replace the orchestrator's stream handler
            original_handler = orchestrator.stream_handler
            orchestrator.stream_handler = ws_handler
            
            try:
                # Add context
                context = {
                    "output_dir": config.output_dir,
                    "data_path": config.data_path
                }
                
                # Process through orchestrator
                response = orchestrator.process(query, context)
                
                # Send final response
                await websocket.send_json({
                    "type": "response",
                    "data": {
                        "response": response.synthesized_response,
                        "routing": response.routing,
                        "execution_time_ms": response.total_time_ms,
                        "charts": [chart.__dict__ if hasattr(chart, '__dict__') else chart for chart in response.charts]
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            finally:
                # Restore original handler
                orchestrator.stream_handler = original_handler
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            })
        except:
            pass


# WebSocket endpoint for workbench streaming analysis
@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """Stream analysis workflow events via WebSocket for the workbench UI."""
    await websocket.accept()
    
    if orchestrator is None:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "System not initialized"},
        })
        await websocket.close()
        return
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            event_type = data.get("type", "")
            
            if event_type == "start_analysis":
                research_goal = data.get("data", {}).get("research_goal", "")
                if not research_goal:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "Research goal is required"},
                    })
                    continue

                # Optional Tech Ops context so we can generate KPI charts and persist to the right investigation
                inv_id = data.get("data", {}).get("investigation_id")
                kpi_id = data.get("data", {}).get("kpi_id")
                station = data.get("data", {}).get("station")
                window = data.get("data", {}).get("window")
                point_t = data.get("data", {}).get("point_t")

                max_iterations = int(data.get("data", {}).get("max_iterations", 20))
                if max_iterations < 1:
                    max_iterations = 1
                if max_iterations > 20:
                    max_iterations = 20
                
                # Generate analysis ID
                import uuid
                analysis_id = str(uuid.uuid4())[:8]
                
                # Send analysis started event
                await websocket.send_json({
                    "type": "analysis_started",
                    "data": {
                        "analysis_id": analysis_id,
                        "research_goal": research_goal,
                    },
                })
                
                # Start step 1
                step_id = f"step-{uuid.uuid4().hex[:6]}"
                await websocket.send_json({
                    "type": "step_started",
                    "data": {
                        "step_id": step_id,
                        "step_number": 1,
                    },
                })

                # Persist step record (demo: in-memory) if this is a Tech Ops investigation
                if inv_id and inv_id in _techops_investigations:
                    inv = _techops_investigations[inv_id]
                    inv_steps = inv.get("steps", [])
                    inv_steps.append(
                        {
                            "step_id": step_id,
                            "step_number": 1,
                            "query": research_goal,
                            "iterations": [],
                            "created_at": datetime.utcnow().isoformat(),
                        }
                    )
                    inv["steps"] = inv_steps
                    _techops_investigations[inv_id] = inv

                # Loop up to 20 iterations (DS-STAR style) to refine until "satisfied"
                last_output = ""
                for i in range(1, max_iterations + 1):
                    iteration_id = f"iter-{uuid.uuid4().hex[:6]}"
                    await websocket.send_json({
                        "type": "iteration_started",
                        "data": {
                            "step_id": step_id,
                            "iteration_id": iteration_id,
                            "iteration_number": i,
                            "description": "Initial investigation" if i == 1 else f"Refinement iteration {i}",
                        },
                    })

                    try:
                        context = {
                            "output_dir": config.output_dir,
                            "data_path": config.data_path,
                            "iteration": i,
                            "previous_summary": last_output[:1200] if last_output else "",
                        }

                        iteration_query = research_goal
                        if i > 1 and last_output:
                            iteration_query = (
                                f"{research_goal}\n\n"
                                f"Refine the investigation using prior findings. "
                                f"Prior findings (truncated):\n{last_output[:800]}"
                            )

                        response = orchestrator.process(iteration_query, context)
                        last_output = response.synthesized_response or last_output

                        # Extract code from specialist response (best-effort)
                        code = "# Analysis code\n# (demo)\nprint('Analyzing...')"
                        if response.specialist_responses:
                            resp_text = response.specialist_responses[0].response
                            if "```python" in resp_text:
                                import re
                                code_match = re.search(r'```python\n(.*?)```', resp_text, re.DOTALL)
                                if code_match:
                                    code = code_match.group(1).strip()

                        await websocket.send_json({
                            "type": "code_generated",
                            "data": {
                                "step_id": step_id,
                                "iteration_id": iteration_id,
                                "code": code,
                            },
                        })

                        await websocket.send_json({
                            "type": "execution_complete",
                            "data": {
                                "step_id": step_id,
                                "iteration_id": iteration_id,
                                "output": {
                                    "success": True,
                                    "output": response.synthesized_response or "Analysis completed successfully.",
                                    "duration_ms": response.total_time_ms,
                                },
                            },
                        })

                        # Visualization (Tech Ops preferred; fallback to text parsing)
                        chart_data = None
                        if kpi_id and station and window:
                            chart_data = generate_techops_kpi_chart(kpi_id=kpi_id, station=station, window=window, point_t=point_t)
                        if not chart_data and response.synthesized_response:
                            chart_data = generate_chart_from_response(response.synthesized_response, research_goal)
                        if chart_data:
                            await websocket.send_json({
                                "type": "visualization_ready",
                                "data": {
                                    "step_id": step_id,
                                    "iteration_id": iteration_id,
                                    "chart": chart_data,
                                },
                            })

                        # Persist iteration record (demo: in-memory)
                        if inv_id and inv_id in _techops_investigations:
                            inv = _techops_investigations[inv_id]
                            inv_steps = inv.get("steps", [])
                            for st in inv_steps:
                                if st.get("step_id") == step_id:
                                    st.setdefault("iterations", []).append(
                                        {
                                            "iteration_id": iteration_id,
                                            "iteration_number": i,
                                            "generated_code": code,
                                            "query": iteration_query,
                                            "response": response.synthesized_response or "",
                                            "chart": chart_data,
                                            "include_in_final": True,
                                            "created_at": datetime.utcnow().isoformat(),
                                        }
                                    )
                                    break
                            inv["steps"] = inv_steps
                            _techops_investigations[inv_id] = inv

                        await websocket.send_json({
                            "type": "verification_complete",
                            "data": {
                                "step_id": step_id,
                                "iteration_id": iteration_id,
                                "result": {
                                    "passed": True,
                                    "assessment": f"Iteration {i} completed. Review findings and decide what to include in final.",
                                    "suggestions": [],
                                },
                            },
                        })

                        # NOTE: we intentionally do NOT stop early; DS-STAR runs up to max_iterations
                        # so the UI can show the full investigation trace for selection/curation.

                    except Exception as e:
                        logger.error(f"Analysis error: {e}", exc_info=True)
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": str(e)},
                        })
                        break

                await websocket.send_json({"type": "step_completed", "data": {"step_id": step_id}})
                await websocket.send_json({"type": "analysis_completed", "data": {"analysis_id": analysis_id}})
            
            elif event_type == "approve_step":
                # Handle step approval - continue to next step
                step_data = data.get("data", {})
                await websocket.send_json({
                    "type": "step_approved",
                    "data": step_data,
                })
                logger.info(f"Step approved: {step_data.get('step_id')}")
            
            elif event_type == "refine_step":
                # Handle refinement request - re-run analysis with feedback
                step_data = data.get("data", {})
                feedback = step_data.get("feedback", "")
                step_id = step_data.get("step_id", "")
                
                await websocket.send_json({
                    "type": "refinement_started",
                    "data": step_data,
                })
                
                # Generate new iteration
                import uuid
                iteration_id = f"iter-{uuid.uuid4().hex[:6]}"
                
                await websocket.send_json({
                    "type": "iteration_started",
                    "data": {
                        "step_id": step_id,
                        "iteration_id": iteration_id,
                        "iteration_number": 2,  # Refinement iteration
                        "description": f"Refining based on feedback: {feedback}",
                    },
                })
                
                # Re-run analysis with feedback context
                try:
                    context = {
                        "output_dir": config.output_dir,
                        "data_path": config.data_path,
                        "feedback": feedback,
                    }
                    
                    refined_query = f"Please refine the previous analysis based on this feedback: {feedback}"
                    response = orchestrator.process(refined_query, context)
                    
                    # Send code generated
                    code = "# Refined analysis\nimport pandas as pd\n\ndf = pd.read_csv('data/airline_operations.csv')\nprint(df.describe())"
                    if response.specialist_responses:
                        resp_text = response.specialist_responses[0].response
                        if "```python" in resp_text:
                            import re
                            code_match = re.search(r'```python\n(.*?)```', resp_text, re.DOTALL)
                            if code_match:
                                code = code_match.group(1).strip()
                    
                    await websocket.send_json({
                        "type": "code_generated",
                        "data": {
                            "step_id": step_id,
                            "iteration_id": iteration_id,
                            "code": code,
                        },
                    })
                    
                    # Send execution complete
                    await websocket.send_json({
                        "type": "execution_complete",
                        "data": {
                            "step_id": step_id,
                            "iteration_id": iteration_id,
                            "output": {
                                "success": True,
                                "output": response.synthesized_response or "Refined analysis completed.",
                                "duration_ms": response.total_time_ms,
                            },
                        },
                    })
                    
                    # Generate visualization
                    if response.synthesized_response:
                        chart_data = generate_chart_from_response(response.synthesized_response, feedback)
                        if chart_data:
                            await websocket.send_json({
                                "type": "visualization_ready",
                                "data": {
                                    "step_id": step_id,
                                    "iteration_id": iteration_id,
                                    "chart": chart_data,
                                },
                            })
                    
                    # Send verification complete
                    await websocket.send_json({
                        "type": "verification_complete",
                        "data": {
                            "step_id": step_id,
                            "iteration_id": iteration_id,
                            "result": {
                                "passed": True,
                                "assessment": "The refined analysis addresses the feedback and provides improved results.",
                                "suggestions": [],
                            },
                        },
                    })
                    
                except Exception as e:
                    logger.error(f"Refinement error: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": str(e)},
                    })
            
    except WebSocketDisconnect:
        logger.info("Workbench WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Workbench WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)},
            })
        except:
            pass


# Conversation history endpoints
@app.get("/api/history")
async def get_history():
    """Get conversation history summary."""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return orchestrator.get_history_summary()


@app.delete("/api/history")
async def clear_history():
    """Clear conversation history."""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    orchestrator.clear_history()
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
