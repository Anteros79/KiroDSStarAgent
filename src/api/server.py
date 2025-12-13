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
    from strands_bedrock import BedrockModel
except ImportError:
    print("Warning: strands-agents package not installed.")
    BedrockModel = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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


class SystemStatus(BaseModel):
    status: str
    model: str
    region: str
    specialists: list[str]
    data_loaded: bool


class StreamEvent(BaseModel):
    type: str  # "agent_start", "routing", "tool_call", "agent_end", "response", "error"
    data: Dict[str, Any]
    timestamp: str


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
        
        # Initialize Bedrock model
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
    
    return SystemStatus(
        status="ready",
        model=config.model_id,
        region=config.region,
        specialists=["data_analyst", "ml_engineer", "visualization_expert"],
        data_loaded=True
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
