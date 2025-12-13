"""Orchestrator Agent for DS-Star multi-agent system.

This module implements the central coordinator that receives user queries,
analyzes intent, routes to appropriate specialist agents, and synthesizes
final responses in the DS-Star star topology architecture.
"""

import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from src.config import Config
from src.models import AgentResponse, SpecialistResponse, ToolCall
from src.handlers.stream_handler import InvestigationStreamHandler

logger = logging.getLogger(__name__)

# Import Strands components
try:
    from strands import Agent
    from strands_bedrock import BedrockModel
except ImportError:
    # Fallback for testing without strands installed
    class Agent:
        """Fallback Agent class for testing."""
        pass
    
    class BedrockModel:
        """Fallback BedrockModel class for testing."""
        pass


# System prompt for the Orchestrator Agent
ORCHESTRATOR_SYSTEM_PROMPT = """You are the Orchestrator Agent in a DS-Star multi-agent system for airline operations analysis.

Your role is to:
1. Analyze user queries to understand their intent and requirements
2. Determine which specialist agent(s) should handle the query
3. Route queries to the appropriate specialists with relevant context
4. Synthesize responses from multiple specialists into a coherent answer
5. Maintain conversation context across multiple turns

**Available Specialist Agents:**

1. **Data Analyst** - Handles data analysis queries
   - Statistical analysis and data exploration
   - KPI calculations (on-time performance, load factors, delays)
   - Trend analysis and pattern identification
   - Data quality assessment
   - Keywords: analyze, statistics, calculate, trend, pattern, data, metrics, KPI

2. **ML Engineer** - Handles machine learning queries
   - Model recommendations and algorithm selection
   - Feature engineering suggestions
   - ML code generation (scikit-learn, pandas)
   - Predictive modeling guidance
   - Keywords: predict, forecast, model, machine learning, ML, algorithm, classification, regression

3. **Visualization Expert** - Handles visualization queries
   - Chart type recommendations
   - Matplotlib and Plotly code generation
   - Chart specification creation for web integration
   - Data visualization best practices
   - Keywords: visualize, chart, graph, plot, show, display, heatmap, bar chart, line chart

**Routing Guidelines:**

- **Single Domain Queries**: Route to the most appropriate specialist
  - "What's the average delay by airline?" → Data Analyst
  - "Build a model to predict delays" → ML Engineer
  - "Create a bar chart of delays" → Visualization Expert

- **Multi-Domain Queries**: Route to multiple specialists in logical order
  - "Analyze delays and create a visualization" → Data Analyst, then Visualization Expert
  - "Predict cancellations and show the results" → ML Engineer, then Visualization Expert
  - "Calculate OTP and recommend improvements" → Data Analyst, then ML Engineer

- **Ambiguous Queries**: Default to Data Analyst for exploratory analysis

**Context Management:**

- Pass relevant conversation history to specialists
- Include previous analysis results when needed for follow-up queries
- Maintain coherent narrative across multi-turn conversations

**Response Synthesis:**

- Combine specialist responses into a unified answer
- Attribute insights to the appropriate specialist
- Highlight key findings and actionable recommendations
- Include chart specifications when visualizations are generated

Always prioritize clarity, accuracy, and actionable insights in your responses.
"""


class OrchestratorAgent:
    """Central coordinator implementing DS-Star hub.
    
    The orchestrator receives all user queries, analyzes intent, routes to
    appropriate specialist agents, and synthesizes final responses. It maintains
    conversation context and coordinates multi-agent interactions.
    
    Attributes:
        model: BedrockModel instance for the orchestrator
        specialists: Dictionary mapping specialist names to their tool functions
        stream_handler: Handler for investigation stream output
        config: System configuration
        conversation_history: List of previous query-response pairs
    """
    
    def __init__(
        self,
        model: BedrockModel,
        specialists: Dict[str, Callable],
        stream_handler: InvestigationStreamHandler,
        config: Config
    ):
        """Initialize the Orchestrator Agent.
        
        Args:
            model: BedrockModel instance configured for the orchestrator
            specialists: Dictionary mapping specialist names to their tool functions
                        e.g., {"data_analyst": data_analyst_func, ...}
            stream_handler: Investigation stream handler for real-time output
            config: System configuration
        """
        self.model = model
        self.specialists = specialists
        self.stream_handler = stream_handler
        self.config = config
        self.conversation_history: List[Dict[str, str]] = []
        
        logger.info(f"Orchestrator initialized with {len(specialists)} specialists")
        logger.info(f"Available specialists: {list(specialists.keys())}")

    
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process a user query through the DS-Star system.
        
        This is the main entry point for query processing. It handles routing,
        specialist invocation, and response synthesis.
        
        Args:
            query: The user's natural language query
            context: Optional additional context (e.g., output_dir for charts)
        
        Returns:
            AgentResponse containing routing info, specialist responses, and synthesis
        """
        start_time = time.time()
        
        try:
            # Notify stream handler
            self.stream_handler.on_agent_start("Orchestrator", query)
            
            # Step 1: Route the query to determine which specialists to invoke
            routing = self._route_query(query)
            
            logger.info(f"Query routed to: {routing}")
            
            # Step 2: Invoke specialists in sequence
            specialist_responses = []
            
            for specialist_name in routing:
                if specialist_name not in self.specialists:
                    logger.warning(f"Unknown specialist: {specialist_name}")
                    continue
                
                # Prepare context for specialist
                specialist_context = context or {}
                specialist_context["conversation_history"] = self._get_relevant_history()
                specialist_context["previous_responses"] = specialist_responses
                
                # Invoke specialist
                try:
                    self.stream_handler.on_routing_decision(
                        specialist_name,
                        f"Routing to {specialist_name} for domain expertise"
                    )
                    
                    specialist_func = self.specialists[specialist_name]
                    
                    # Call specialist (they return JSON strings)
                    self.stream_handler.on_tool_start(specialist_name, {"query": query})
                    
                    response_json = specialist_func(query, specialist_context)
                    
                    # Parse response
                    response_data = json.loads(response_json)
                    specialist_response = SpecialistResponse(
                        agent_name=response_data["agent_name"],
                        query=response_data["query"],
                        response=response_data["response"],
                        tool_calls=[
                            ToolCall(
                                tool_name=tc["tool_name"],
                                inputs=tc["inputs"],
                                output=tc["output"],
                                duration_ms=tc["duration_ms"]
                            )
                            for tc in response_data["tool_calls"]
                        ],
                        execution_time_ms=response_data["execution_time_ms"]
                    )
                    
                    specialist_responses.append(specialist_response)
                    
                    self.stream_handler.on_tool_end(specialist_name, specialist_response.response[:100])
                    
                except Exception as e:
                    logger.error(f"Error invoking {specialist_name}: {e}", exc_info=True)
                    self.stream_handler.on_error(e, f"specialist_{specialist_name}")
                    
                    # Create error response
                    error_response = SpecialistResponse(
                        agent_name=specialist_name,
                        query=query,
                        response=f"I encountered an error processing this request. Please try rephrasing your question.",
                        tool_calls=[],
                        execution_time_ms=0
                    )
                    specialist_responses.append(error_response)
            
            # Step 3: Synthesize responses
            synthesized_response = self._synthesize_responses(query, specialist_responses)
            
            # Step 4: Extract chart specifications if any
            charts = self._extract_charts(specialist_responses)
            
            # Calculate total time
            total_time_ms = int((time.time() - start_time) * 1000)
            
            # Create agent response
            agent_response = AgentResponse(
                query=query,
                routing=routing,
                specialist_responses=specialist_responses,
                synthesized_response=synthesized_response,
                charts=charts,
                total_time_ms=total_time_ms
            )
            
            # Update conversation history
            self._update_history(query, synthesized_response)
            
            # Notify stream handler
            self.stream_handler.on_agent_end("Orchestrator", synthesized_response[:150])
            
            logger.info(f"Query processed in {total_time_ms}ms")
            
            return agent_response
        
        except Exception as e:
            logger.error(f"Error in orchestrator: {e}", exc_info=True)
            self.stream_handler.on_error(e, "orchestrator")
            
            # Return error response
            total_time_ms = int((time.time() - start_time) * 1000)
            return AgentResponse(
                query=query,
                routing=[],
                specialist_responses=[],
                synthesized_response=f"I encountered an error processing your query: {str(e)}. Please try again or rephrase your question.",
                charts=[],
                total_time_ms=total_time_ms
            )

    
    def _route_query(self, query: str) -> List[str]:
        """Analyze query intent and determine appropriate specialist routing.
        
        This method uses keyword matching and pattern recognition to determine
        which specialist agent(s) should handle the query. It supports both
        single-domain and multi-domain routing.
        
        Args:
            query: The user's query
        
        Returns:
            List of specialist names to invoke in order
        """
        query_lower = query.lower()
        routing = []
        
        # Define keyword patterns for each specialist
        data_analyst_keywords = [
            "analyze", "analysis", "statistics", "statistical", "calculate", 
            "trend", "pattern", "data", "metrics", "kpi", "average", "mean",
            "median", "count", "sum", "total", "distribution", "compare",
            "comparison", "performance", "delay", "cancellation", "on-time",
            "otp", "load factor", "turnaround", "explore", "summary"
        ]
        
        ml_engineer_keywords = [
            "predict", "prediction", "forecast", "model", "machine learning",
            "ml", "algorithm", "classification", "regression", "cluster",
            "feature", "train", "accuracy", "neural", "random forest", 
            "xgboost", "scikit", "sklearn", "build a model"
        ]
        
        visualization_keywords = [
            "visualize", "visualization", "chart", "graph", "plot", 
            "display", "draw", "create chart", "create graph", "bar chart",
            "line chart", "scatter", "pie chart", "histogram", "heatmap",
            "matplotlib", "plotly", "show the results", "show results",
            "show the", "create a chart"
        ]
        
        # Check for each specialist's keywords
        has_data_analyst = any(keyword in query_lower for keyword in data_analyst_keywords)
        has_ml_engineer = any(keyword in query_lower for keyword in ml_engineer_keywords)
        has_visualization = any(keyword in query_lower for keyword in visualization_keywords)
        
        # Determine routing based on keyword matches
        # Priority order: Check for multi-domain first, then single domain
        if has_data_analyst and has_ml_engineer and has_visualization:
            # All three domains
            routing = ["data_analyst", "ml_engineer", "visualization_expert"]
        elif has_data_analyst and has_visualization:
            # Data analysis followed by visualization
            routing = ["data_analyst", "visualization_expert"]
        elif has_ml_engineer and has_visualization:
            # ML modeling followed by visualization
            routing = ["ml_engineer", "visualization_expert"]
        elif has_data_analyst and has_ml_engineer:
            # Data analysis followed by ML
            routing = ["data_analyst", "ml_engineer"]
        elif has_ml_engineer:
            # ML only
            routing = ["ml_engineer"]
        elif has_visualization:
            # Visualization only (may need data analyst first for data prep)
            # Check if query mentions specific data or just asks for a chart
            if any(word in query_lower for word in ["delay", "cancellation", "airline", "route", "data"]):
                routing = ["data_analyst", "visualization_expert"]
            else:
                routing = ["visualization_expert"]
        elif has_data_analyst:
            # Data analysis only
            routing = ["data_analyst"]
        else:
            # Default to data analyst for exploratory queries
            routing = ["data_analyst"]
        
        return routing

    
    def _synthesize_responses(
        self, 
        query: str, 
        specialist_responses: List[SpecialistResponse]
    ) -> str:
        """Synthesize responses from multiple specialists into a unified answer.
        
        This method combines insights from different specialists, attributes
        findings appropriately, and creates a coherent narrative.
        
        Args:
            query: The original user query
            specialist_responses: List of responses from invoked specialists
        
        Returns:
            Synthesized response string
        """
        if not specialist_responses:
            return "I wasn't able to process your query. Please try rephrasing it."
        
        # If only one specialist, return their response with minimal wrapping
        if len(specialist_responses) == 1:
            response = specialist_responses[0]
            return f"**{response.agent_name.replace('_', ' ').title()} Response:**\n\n{response.response}"
        
        # Multiple specialists - synthesize their responses
        synthesis_parts = []
        
        # Add introduction
        specialist_names = [r.agent_name.replace('_', ' ').title() for r in specialist_responses]
        synthesis_parts.append(
            f"I've consulted with multiple specialists to answer your query. "
            f"Here's what they found:\n"
        )
        
        # Add each specialist's contribution
        for i, response in enumerate(specialist_responses, 1):
            specialist_name = response.agent_name.replace('_', ' ').title()
            synthesis_parts.append(f"\n## {i}. {specialist_name}\n")
            synthesis_parts.append(response.response)
        
        # Add summary if multiple specialists
        if len(specialist_responses) > 1:
            synthesis_parts.append("\n## Summary\n")
            synthesis_parts.append(
                "The analysis above combines insights from data analysis"
            )
            
            if any("ml_engineer" in r.agent_name for r in specialist_responses):
                synthesis_parts.append(", machine learning recommendations")
            
            if any("visualization" in r.agent_name for r in specialist_responses):
                synthesis_parts.append(", and visualization guidance")
            
            synthesis_parts.append(
                " to provide a comprehensive answer to your query."
            )
        
        return "".join(synthesis_parts)

    
    def _update_history(self, query: str, response: str) -> None:
        """Update conversation history with the latest query-response pair.
        
        Args:
            query: The user's query
            response: The synthesized response
        """
        self.conversation_history.append({
            "role": "user",
            "content": query
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Truncate history if it exceeds token limits
        self._truncate_history_if_needed()
    
    def _get_relevant_history(self, max_turns: int = 3) -> List[Dict[str, str]]:
        """Get relevant conversation history for context.
        
        Returns the most recent conversation turns, limited by max_turns.
        
        Args:
            max_turns: Maximum number of conversation turns to include
        
        Returns:
            List of recent conversation history entries
        """
        # Get the last N turns (each turn is 2 entries: user + assistant)
        max_entries = max_turns * 2
        return self.conversation_history[-max_entries:] if self.conversation_history else []
    
    def _truncate_history_if_needed(self) -> None:
        """Truncate conversation history to stay within token limits.
        
        Uses a simple heuristic: 4 characters ≈ 1 token.
        Keeps the most recent entries and removes oldest first.
        """
        max_tokens = self.config.max_tokens // 2  # Reserve half for context
        
        # Estimate current token count (rough heuristic: 4 chars = 1 token)
        total_chars = sum(len(entry["content"]) for entry in self.conversation_history)
        estimated_tokens = total_chars // 4
        
        # Remove oldest entries if over limit
        while estimated_tokens > max_tokens and len(self.conversation_history) > 2:
            # Remove oldest pair (user + assistant)
            removed = self.conversation_history.pop(0)
            if self.conversation_history:
                removed = self.conversation_history.pop(0)
            
            # Recalculate
            total_chars = sum(len(entry["content"]) for entry in self.conversation_history)
            estimated_tokens = total_chars // 4
            
            logger.info(f"Truncated conversation history to {estimated_tokens} estimated tokens")
    
    def _extract_charts(self, specialist_responses: List[SpecialistResponse]) -> List[Dict[str, Any]]:
        """Extract chart specifications from specialist responses.
        
        Args:
            specialist_responses: List of specialist responses
        
        Returns:
            List of chart specification dictionaries
        """
        charts = []
        
        for response in specialist_responses:
            # Check if this is a visualization expert response
            if "visualization" in response.agent_name:
                # Try to extract chart specifications from the response
                # In a real implementation, this would parse structured chart data
                # For now, we'll create a placeholder
                charts.append({
                    "type": "chart_specification",
                    "source": response.agent_name,
                    "query": response.query
                })
        
        return charts
    
    def clear_history(self) -> None:
        """Clear conversation history.
        
        Useful when starting a new session or when explicitly requested by user.
        """
        self.conversation_history.clear()
        logger.info("Conversation history cleared")
    
    def get_history_summary(self) -> Dict[str, Any]:
        """Get a summary of conversation history.
        
        Returns:
            Dictionary with history statistics
        """
        total_turns = len(self.conversation_history) // 2
        total_chars = sum(len(entry["content"]) for entry in self.conversation_history)
        estimated_tokens = total_chars // 4
        
        return {
            "total_turns": total_turns,
            "total_entries": len(self.conversation_history),
            "estimated_tokens": estimated_tokens,
            "max_tokens": self.config.max_tokens // 2
        }
