"""Data Analyst specialist agent for DS-Star multi-agent system.

This agent handles data analysis queries on airline operations data,
providing statistical analysis, data exploration, KPI calculations,
and trend analysis.
"""

import logging
import time
from typing import Dict, Any

from src.models import SpecialistResponse, ToolCall
from src.data.airline_data import query_airline_data
from src.data.techops_metrics import get_techops_store
from src.techops.investigation_tests import TechOpsContext, format_test_result, run_test
from src.llm.ollama_client import chat as ollama_chat

logger = logging.getLogger(__name__)

# Import tool decorator and Agent from strands
try:
    from strands import tool, Agent
    from strands.models.bedrock import BedrockModel
except ImportError:
    # Fallback for testing without strands installed
    def tool(func):
        """Fallback tool decorator for testing."""
        return func
    
    class Agent:
        """Fallback Agent class for testing."""
        pass
    
    class BedrockModel:
        """Fallback BedrockModel class for testing."""
        pass


# System prompt for the Data Analyst agent
DATA_ANALYST_SYSTEM_PROMPT = """You are an expert Data Analyst specializing in airline operations analysis.

Your role is to:
- Analyze airline operations data using pandas and statistical methods
- Calculate key performance indicators (KPIs) such as on-time performance, load factors, and delay metrics
- Identify trends and patterns in flight operations
- Provide clear, step-by-step explanations of your analysis approach
- Present findings in a structured, easy-to-understand format

You have access to a comprehensive airline operations dataset with the following information:
- Flight identifiers and airline codes
- Origin and destination airports
- Scheduled and actual departure times
- Delay minutes and delay causes
- Load factors (passenger capacity utilization)
- Turnaround times
- Cancellation status

When analyzing data:
1. Start by understanding what the user wants to know
2. Explain your analysis approach step-by-step
3. Use the query_airline_data tool to access and analyze the dataset
4. Show intermediate results when helpful
5. Provide clear conclusions with supporting data
6. Suggest follow-up analyses when relevant

Always be thorough but concise, and focus on actionable insights.
"""


@tool
def data_analyst(query: str, context: Dict[str, Any] = None) -> str:
    """Process data analysis queries on airline operations data.
    
    This specialist agent handles statistical analysis, data exploration,
    KPI calculations, trend analysis, and data quality assessment for
    airline operations data.
    
    The agent uses pandas and statistical tools to analyze flight records,
    calculate metrics like on-time performance and load factors, and
    identify operational trends.
    
    Args:
        query: The data analysis question or task to process
        context: Optional context from previous conversation turns
    
    Returns:
        Structured response containing analysis results and explanations
    """
    start_time = time.time()
    tool_calls = []
    
    try:
        logger.info(f"Data Analyst processing query: {query}")
        
        # Create the Data Analyst agent with appropriate configuration
        # In a real implementation, this would use the BedrockModel
        # For now, we'll simulate the agent's behavior
        
        ctx = context or {}

        # If Tech Ops context is present, run deterministic KPI spike tests instead of the airline dataset query.
        if ctx.get("kpi_id") and ctx.get("station") and ctx.get("window"):
            store = get_techops_store()
            test_name = str(ctx.get("test_name") or "signal_characterization")
            executed = set(ctx.get("executed_tests") or [])
            evidence_log = str(ctx.get("evidence_log") or "").strip()
            precomputed = str(ctx.get("techops_test_output") or "").strip()

            if test_name in executed:
                data_result = f"Skipping duplicate test: {test_name}"
            elif precomputed:
                data_result = precomputed
                tool_calls.append(
                    ToolCall(
                        tool_name="techops_run_test",
                        inputs={
                            "test_name": test_name,
                            "kpi_id": str(ctx.get("kpi_id")),
                            "station": str(ctx.get("station")),
                            "window": str(ctx.get("window")),
                            "point_t": str(ctx.get("point_t")) if ctx.get("point_t") else None,
                        },
                        output={"precomputed": True, "formatted": data_result},
                        duration_ms=0,
                    )
                )
            else:
                tctx = TechOpsContext(
                    kpi_id=str(ctx["kpi_id"]),
                    station=str(ctx["station"]),
                    window=str(ctx["window"]),
                    point_t=str(ctx.get("point_t")) if ctx.get("point_t") else None,
                )
                query_start = time.time()
                result = run_test(store=store, ctx=tctx, test_name=test_name)
                query_duration = int((time.time() - query_start) * 1000)

                tool_calls.append(
                    ToolCall(
                        tool_name="techops_run_test",
                        inputs={"test_name": test_name, "kpi_id": tctx.kpi_id, "station": tctx.station, "window": tctx.window, "point_t": tctx.point_t},
                        output=result,
                        duration_ms=query_duration,
                    )
                )
                data_result = format_test_result(result)

            analysis_plan = f"Run Tech Ops diagnostic test: {test_name}"

            # Use local Ollama model to interpret the test output (proves DS-STAR runs locally).
            model_provider = str(ctx.get("model_provider") or "ollama")
            model_id = str(ctx.get("model_id") or "")
            ollama_host = str(ctx.get("ollama_host") or "http://127.0.0.1:11434")

            model_note = f"{model_provider}:{model_id}" if model_id else model_provider
            llm_block = ""
            if model_provider == "ollama" and model_id and "Skipping duplicate test" not in data_result:
                prompt = (
                    "You are the DS-STAR Data Analyst agent.\n"
                    "You are investigating: What caused this signal spike?\n\n"
                    f"CURRENT TEST: {test_name}\n\n"
                    "TEST OUTPUT (authoritative):\n"
                    f"{data_result}\n\n"
                    + (f"PRIOR TEST OUTPUTS:\n{evidence_log}\n\n" if evidence_log else "")
                    + "Task:\n"
                    "- Explain what this test suggests about the cause of the signal spike (1-4 bullets)\n"
                    "- State whether we have enough to answer the user now.\n"
                    "- Finish with a single line exactly like: SATISFIED: true|false\n\n"
                    "Do not include internal reasoning.\n"
                )
                llm_text, llm_ms, _raw = ollama_chat(
                    host=ollama_host,
                    model=model_id,
                    prompt=prompt,
                    num_predict=1024,
                    temperature=0.2,
                    timeout_s=240,
                )
                if llm_text:
                    llm_block = f"\n\n---\nMODEL ({model_note})\nLATENCY_MS: {llm_ms}\n{llm_text}\n"
                else:
                    err = ""
                    if isinstance(_raw, dict) and _raw.get("error"):
                        err = f"ERROR: {_raw.get('error')}\n"
                    llm_block = (
                        f"\n\n---\nMODEL ({model_note})\nLATENCY_MS: {llm_ms}\n"
                        f"{err}"
                        "Model returned empty output.\n"
                        "If you're running locally, verify Ollama is up and the model is pulled:\n"
                        f"- `ollama serve`\n- `ollama pull {model_id}`\n"
                        "SATISFIED: false\n"
                    )
            elif model_provider != "ollama":
                llm_block = f"\n\n---\nMODEL ({model_note})\nNOTE: Only Ollama is supported for this Tech Ops demo path.\nSATISFIED: false\n"
            elif not model_id:
                llm_block = f"\n\n---\nMODEL ({model_note})\nERROR: No model_id configured.\nSATISFIED: false\n"

            response = _formulate_response(query, analysis_plan, data_result, context) + llm_block

        else:
            # Step 1: Analyze the query to understand what data analysis is needed
            analysis_plan = _plan_analysis(query)

            # Step 2: Execute the data query using the airline data tool
            query_start = time.time()
            data_result = query_airline_data(query)
            query_duration = int((time.time() - query_start) * 1000)

            # Record the tool call
            tool_calls.append(
                ToolCall(
                    tool_name="query_airline_data",
                    inputs={"query": query},
                    output=data_result,
                    duration_ms=query_duration,
                )
            )

            # Step 3: Formulate the response with analysis and insights
            response = _formulate_response(query, analysis_plan, data_result, context)
        
        # Calculate total execution time
        execution_time = int((time.time() - start_time) * 1000)
        
        # Create structured response
        specialist_response = SpecialistResponse(
            agent_name="data_analyst",
            query=query,
            response=response,
            tool_calls=tool_calls,
            execution_time_ms=execution_time
        )
        
        logger.info(f"Data Analyst completed in {execution_time}ms")
        
        # Return as JSON string for the tool interface
        return specialist_response.to_json()
    
    except Exception as e:
        logger.error(f"Error in Data Analyst: {e}", exc_info=True)
        
        # Return error response
        execution_time = int((time.time() - start_time) * 1000)
        error_response = SpecialistResponse(
            agent_name="data_analyst",
            query=query,
            response=f"I encountered an error while analyzing the data: {str(e)}. Please try rephrasing your question or ask for a dataset summary.",
            tool_calls=tool_calls,
            execution_time_ms=execution_time
        )
        
        return error_response.to_json()


def _plan_analysis(query: str) -> str:
    """Plan the analysis approach based on the query.
    
    Args:
        query: The user's data analysis query
    
    Returns:
        A brief description of the analysis plan
    """
    query_lower = query.lower()
    
    if "delay" in query_lower:
        return "Analyze flight delay patterns and statistics"
    elif "cancellation" in query_lower or "cancelled" in query_lower:
        return "Examine cancellation rates and patterns"
    elif "on-time" in query_lower or "otp" in query_lower:
        return "Calculate on-time performance metrics"
    elif "load factor" in query_lower:
        return "Analyze passenger load factors and capacity utilization"
    elif "airline" in query_lower and "compare" in query_lower:
        return "Compare performance metrics across airlines"
    elif "route" in query_lower:
        return "Analyze route-specific performance metrics"
    elif "trend" in query_lower or "over time" in query_lower:
        return "Identify trends and patterns over time"
    else:
        return "Perform exploratory data analysis"


def _formulate_response(query: str, analysis_plan: str, data_result: str, context: Dict[str, Any] = None) -> str:
    """Formulate a comprehensive response with analysis and insights.
    
    Args:
        query: The original query
        analysis_plan: The planned analysis approach
        data_result: Results from the data query
        context: Optional conversation context
    
    Returns:
        Formatted response string
    """
    response_parts = []
    
    # Add analysis approach
    response_parts.append(f"**Analysis Approach:** {analysis_plan}")
    response_parts.append("")
    
    # Add the data results
    response_parts.append("**Results:**")
    response_parts.append(data_result)
    response_parts.append("")
    
    # Add insights based on the results
    insights = _generate_insights(query, data_result)
    if insights:
        response_parts.append("**Key Insights:**")
        response_parts.append(insights)
    
    return "\n".join(response_parts)


def _generate_insights(query: str, data_result: str) -> str:
    """Generate insights from the data results.
    
    Args:
        query: The original query
        data_result: Results from the data analysis
    
    Returns:
        Insights text or empty string
    """
    # This is a simplified insight generation
    # In a real implementation, this would use the LLM to generate insights
    
    insights = []
    
    if "delay" in data_result.lower():
        insights.append("- Delay patterns vary significantly across airlines and routes")
        insights.append("- Consider investigating the root causes of delays for targeted improvements")
    
    if "cancellation" in data_result.lower():
        insights.append("- Cancellation rates impact overall operational reliability")
        insights.append("- High cancellation routes may need additional capacity or schedule adjustments")
    
    if "on-time" in data_result.lower() or "otp" in data_result.lower():
        insights.append("- On-time performance is a critical customer satisfaction metric")
        insights.append("- Airlines with higher OTP rates typically have better operational processes")
    
    if "load factor" in data_result.lower():
        insights.append("- Load factor indicates revenue optimization and demand patterns")
        insights.append("- Routes with consistently low load factors may need schedule optimization")
    
    return "\n".join(insights) if insights else ""
