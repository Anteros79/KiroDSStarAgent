"""Error handling utilities for specialist agent invocations.

This module provides safe wrappers for specialist agent calls that
catch errors and return fallback responses to maintain system stability.
"""

import logging
import time
from typing import Callable, Dict, Any, Optional

from src.models import SpecialistResponse, ToolCall

logger = logging.getLogger(__name__)


def safe_specialist_call(
    specialist_func: Callable[[str], str],
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> SpecialistResponse:
    """Wraps specialist calls with error handling and fallback responses.
    
    This function provides a safety wrapper around specialist agent invocations.
    If the specialist encounters an error, this wrapper catches it, logs the
    details, and returns a user-friendly fallback response instead of propagating
    the error to the orchestrator.
    
    This ensures the demo remains stable during presentations and provides
    graceful degradation when individual specialists fail.
    
    Args:
        specialist_func: The specialist agent function to invoke
        query: The query to pass to the specialist
        context: Optional context dictionary from conversation history
    
    Returns:
        SpecialistResponse with either the specialist's response or a fallback
        error response
    
    Example:
        >>> from src.agents.specialists.data_analyst import data_analyst
        >>> response = safe_specialist_call(data_analyst, "What is the average delay?")
        >>> print(response.response)
    """
    start_time = time.time()
    agent_name = specialist_func.__name__
    
    try:
        logger.info(f"Invoking specialist: {agent_name}")
        
        # Call the specialist function
        # Most specialists return JSON string, so we need to parse it
        result = specialist_func(query)
        
        # Try to parse as SpecialistResponse JSON
        try:
            import json
            result_dict = json.loads(result)
            
            # Reconstruct SpecialistResponse from dict
            tool_calls = [
                ToolCall(
                    tool_name=tc["tool_name"],
                    inputs=tc["inputs"],
                    output=tc["output"],
                    duration_ms=tc["duration_ms"]
                )
                for tc in result_dict.get("tool_calls", [])
            ]
            
            response = SpecialistResponse(
                agent_name=result_dict.get("agent_name", agent_name),
                query=result_dict.get("query", query),
                response=result_dict.get("response", result),
                tool_calls=tool_calls,
                execution_time_ms=result_dict.get("execution_time_ms", 0)
            )
            
            logger.info(f"Specialist {agent_name} completed successfully")
            return response
        
        except (json.JSONDecodeError, KeyError, TypeError):
            # If result is not JSON or doesn't match expected format,
            # treat it as a plain string response
            execution_time = int((time.time() - start_time) * 1000)
            
            response = SpecialistResponse(
                agent_name=agent_name,
                query=query,
                response=str(result),
                tool_calls=[],
                execution_time_ms=execution_time
            )
            
            logger.info(f"Specialist {agent_name} completed successfully (plain text response)")
            return response
    
    except Exception as e:
        # Log the error with full details for debugging
        logger.error(
            f"Error in specialist {agent_name}: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        
        # Calculate execution time up to the point of failure
        execution_time = int((time.time() - start_time) * 1000)
        
        # Create a user-friendly fallback response
        fallback_message = _create_fallback_message(agent_name, e)
        
        fallback_response = SpecialistResponse(
            agent_name=agent_name,
            query=query,
            response=fallback_message,
            tool_calls=[],
            execution_time_ms=execution_time
        )
        
        logger.warning(f"Returning fallback response for {agent_name}")
        return fallback_response


def _create_fallback_message(agent_name: str, error: Exception) -> str:
    """Create a user-friendly fallback message based on the error type.
    
    Args:
        agent_name: Name of the specialist agent that failed
        error: The exception that occurred
    
    Returns:
        User-friendly error message with suggestions
    """
    error_type = type(error).__name__
    error_message = str(error).lower()
    
    # Customize message based on agent type
    agent_display_name = agent_name.replace("_", " ").title()
    
    # Check for specific error patterns
    if "timeout" in error_message or "timeout" in error_type.lower():
        return (
            f"I'm sorry, but the {agent_display_name} is taking longer than expected to respond. "
            f"This might be due to high system load. Please try your question again, "
            f"or try rephrasing it to be more specific."
        )
    
    elif "connection" in error_message or "network" in error_message:
        return (
            f"I'm experiencing connection issues with the {agent_display_name}. "
            f"Please check your network connection and try again."
        )
    
    elif "authentication" in error_message or "credentials" in error_message:
        return (
            f"There's an authentication issue with the {agent_display_name}. "
            f"Please verify your AWS credentials are properly configured."
        )
    
    elif "not found" in error_message or "missing" in error_message:
        return (
            f"The {agent_display_name} couldn't find the required resources. "
            f"Please ensure all data files and dependencies are properly set up."
        )
    
    elif "invalid" in error_message or "malformed" in error_message:
        return (
            f"The {agent_display_name} received an invalid request. "
            f"Please try rephrasing your question or providing more context."
        )
    
    else:
        # Generic fallback message
        return (
            f"I encountered an issue while processing your request with the {agent_display_name}. "
            f"Please try rephrasing your question or ask for something different. "
            f"If the problem persists, you may want to check the system logs for more details."
        )


def safe_specialist_call_with_context(
    specialist_func: Callable[[str, Dict[str, Any]], str],
    query: str,
    context: Dict[str, Any]
) -> SpecialistResponse:
    """Wraps specialist calls that accept context with error handling.
    
    This is a variant of safe_specialist_call for specialists that accept
    a context parameter in addition to the query.
    
    Args:
        specialist_func: The specialist agent function to invoke (accepts query and context)
        query: The query to pass to the specialist
        context: Context dictionary from conversation history
    
    Returns:
        SpecialistResponse with either the specialist's response or a fallback
        error response
    
    Example:
        >>> response = safe_specialist_call_with_context(
        ...     data_analyst,
        ...     "What about delays?",
        ...     {"previous_query": "Show me flight data"}
        ... )
    """
    start_time = time.time()
    agent_name = specialist_func.__name__
    
    try:
        logger.info(f"Invoking specialist with context: {agent_name}")
        
        # Call the specialist function with context
        result = specialist_func(query, context)
        
        # Try to parse as SpecialistResponse JSON
        try:
            import json
            result_dict = json.loads(result)
            
            # Reconstruct SpecialistResponse from dict
            tool_calls = [
                ToolCall(
                    tool_name=tc["tool_name"],
                    inputs=tc["inputs"],
                    output=tc["output"],
                    duration_ms=tc["duration_ms"]
                )
                for tc in result_dict.get("tool_calls", [])
            ]
            
            response = SpecialistResponse(
                agent_name=result_dict.get("agent_name", agent_name),
                query=result_dict.get("query", query),
                response=result_dict.get("response", result),
                tool_calls=tool_calls,
                execution_time_ms=result_dict.get("execution_time_ms", 0)
            )
            
            logger.info(f"Specialist {agent_name} completed successfully")
            return response
        
        except (json.JSONDecodeError, KeyError, TypeError):
            # If result is not JSON or doesn't match expected format,
            # treat it as a plain string response
            execution_time = int((time.time() - start_time) * 1000)
            
            response = SpecialistResponse(
                agent_name=agent_name,
                query=query,
                response=str(result),
                tool_calls=[],
                execution_time_ms=execution_time
            )
            
            logger.info(f"Specialist {agent_name} completed successfully (plain text response)")
            return response
    
    except Exception as e:
        # Log the error with full details for debugging
        logger.error(
            f"Error in specialist {agent_name}: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        
        # Calculate execution time up to the point of failure
        execution_time = int((time.time() - start_time) * 1000)
        
        # Create a user-friendly fallback response
        fallback_message = _create_fallback_message(agent_name, e)
        
        fallback_response = SpecialistResponse(
            agent_name=agent_name,
            query=query,
            response=fallback_message,
            tool_calls=[],
            execution_time_ms=execution_time
        )
        
        logger.warning(f"Returning fallback response for {agent_name}")
        return fallback_response
