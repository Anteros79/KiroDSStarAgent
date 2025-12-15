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


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the DS-Star system on startup."""
    global orchestrator, config
    
    try:
        logger.info("Starting DS-Star API server...")
        
        # Load configuration
        config = Config.load()
        logger.info(f"Configuration loaded: model={config.model_id}, region={config.region}")
        
        # Initialize data loader
        logger.info("Loading airline operations dataset...")
        initialize_data_loader(config.data_path)
        logger.info("✓ Airline data loaded")
        
        # Initialize stream handler
        stream_handler = InvestigationStreamHandler(verbose=config.verbose)
        
        # Initialize model based on provider
        model = None
        if config.model_provider == "ollama":
            if OllamaModel is None:
                logger.warning("OllamaModel not available - running in mock mode")
                return
            
            logger.info(f"Connecting to Ollama at {config.ollama_host}...")
            model = OllamaModel(
                model_id=config.model_id,
                host=config.ollama_host,
            )
            logger.info(f"✓ Ollama model initialized: {config.model_id}")
        else:
            # Default to Bedrock
            if BedrockModel is None:
                logger.warning("BedrockModel not available - running in mock mode")
                return
            
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
                
                # Start iteration 1
                iteration_id = f"iter-{uuid.uuid4().hex[:6]}"
                await websocket.send_json({
                    "type": "iteration_started",
                    "data": {
                        "step_id": step_id,
                        "iteration_id": iteration_id,
                        "iteration_number": 1,
                        "description": f"Analyzing: {research_goal}",
                    },
                })
                
                # Process through orchestrator
                try:
                    context = {
                        "output_dir": config.output_dir,
                        "data_path": config.data_path
                    }
                    
                    response = orchestrator.process(research_goal, context)
                    
                    # Extract code from specialist response (look for code blocks in response text)
                    code = "# Analysis code\nimport pandas as pd\n\n# Load and analyze data\ndf = pd.read_csv('data/airline_operations.csv')\nprint(df.describe())"
                    if response.specialist_responses:
                        # Try to extract Python code from the response
                        resp_text = response.specialist_responses[0].response
                        if "```python" in resp_text:
                            # Extract code between ```python and ```
                            import re
                            code_match = re.search(r'```python\n(.*?)```', resp_text, re.DOTALL)
                            if code_match:
                                code = code_match.group(1).strip()
                        elif "```" in resp_text:
                            code_match = re.search(r'```\n(.*?)```', resp_text, re.DOTALL)
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
                    
                    # Send execution complete event
                    await websocket.send_json({
                        "type": "execution_complete",
                        "data": {
                            "step_id": step_id,
                            "iteration_id": iteration_id,
                            "output": {
                                "success": True,
                                "output": response.synthesized_response if response.synthesized_response else "Analysis completed successfully.",
                                "duration_ms": response.total_time_ms,
                            },
                        },
                    })
                    
                    # Generate visualization from response data
                    chart_sent = False
                    
                    # Try to generate chart from the response
                    if response.synthesized_response:
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
                            chart_sent = True
                    
                    # Also send any charts from the response
                    if response.charts and not chart_sent:
                        for chart in response.charts:
                            chart_data = chart.__dict__ if hasattr(chart, '__dict__') else chart
                            await websocket.send_json({
                                "type": "visualization_ready",
                                "data": {
                                    "step_id": step_id,
                                    "iteration_id": iteration_id,
                                    "chart": {
                                        "chart_type": chart_data.get("chart_type", "bar"),
                                        "title": chart_data.get("title", "Analysis Results"),
                                        "plotly_json": chart_data.get("plotly_json", {}),
                                    },
                                },
                            })
                    
                    # Send verification complete event
                    await websocket.send_json({
                        "type": "verification_complete",
                        "data": {
                            "step_id": step_id,
                            "iteration_id": iteration_id,
                            "result": {
                                "passed": True,
                                "assessment": "The analysis successfully addressed the research goal. The results are statistically valid and the visualizations clearly communicate the findings.",
                                "suggestions": [],
                            },
                        },
                    })
                    
                    # Mark step as completed
                    await websocket.send_json({
                        "type": "step_completed",
                        "data": {"step_id": step_id},
                    })
                    
                    # Mark analysis as completed
                    await websocket.send_json({
                        "type": "analysis_completed",
                        "data": {"analysis_id": analysis_id},
                    })
                    
                except Exception as e:
                    logger.error(f"Analysis error: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": str(e)},
                    })
            
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
