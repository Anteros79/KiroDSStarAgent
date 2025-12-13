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

logger = logging.getLogger(__name__)

# Import tool decorator and Agent from strands
try:
    from strands import tool, Agent
    from strands_bedrock import BedrockModel
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
        
        # Step 1: Analyze the query to understand what data analysis is needed
        analysis_plan = _plan_analysis(query)
        
        # Step 2: Execute the data query using the airline data tool
        query_start = time.time()
        data_result = query_airline_data(query)
        query_duration = int((time.time() - query_start) * 1000)
        
        # Record the tool call
        tool_calls.append(ToolCall(
            tool_name="query_airline_data",
            inputs={"query": query},
            output=data_result,
            duration_ms=query_duration
        ))
        
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
