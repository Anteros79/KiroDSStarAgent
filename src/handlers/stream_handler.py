"""Investigation stream handler for DS-Star multi-agent system.

This module provides real-time streaming of agent reasoning steps, tool calls,
and intermediate results during query processing.
"""

from typing import Any, Dict, Optional
from datetime import datetime
import json


class InvestigationStreamHandler:
    """Streams all reasoning steps, tool calls, and results in real-time.
    
    This handler extends the Strands CallbackHandler pattern to provide
    visibility into the DS-Star agent orchestration process. It supports
    both verbose and summary output modes.
    
    Attributes:
        verbose: If True, displays detailed reasoning and tool parameters.
                If False, shows only high-level summaries.
    """
    
    def __init__(self, verbose: bool = False):
        """Initialize the investigation stream handler.
        
        Args:
            verbose: Enable detailed output including reasoning steps and
                    tool call parameters. Defaults to False.
        """
        self.verbose = verbose
        self._indent_level = 0
        self._start_times: Dict[str, datetime] = {}
    
    def _print(self, message: str, indent_offset: int = 0) -> None:
        """Print a message with appropriate indentation.
        
        Args:
            message: The message to print
            indent_offset: Additional indentation levels (can be negative)
        """
        indent = "  " * max(0, self._indent_level + indent_offset)
        print(f"{indent}{message}")
    
    def _format_timestamp(self) -> str:
        """Format current timestamp for display.
        
        Returns:
            Formatted timestamp string
        """
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    def on_agent_start(self, agent_name: str, query: str) -> None:
        """Called when an agent begins processing a query.
        
        Args:
            agent_name: Name of the agent starting execution
            query: The query being processed
        """
        timestamp = self._format_timestamp()
        self._start_times[agent_name] = datetime.now()
        
        self._print(f"[{timestamp}] 🤖 Agent Started: {agent_name}")
        
        if self.verbose:
            self._indent_level += 1
            self._print(f"Query: {query}")
            self._indent_level -= 1
        
        self._indent_level += 1
    
    def on_routing_decision(self, specialist: str, reasoning: str) -> None:
        """Called when the orchestrator makes a routing decision.
        
        Args:
            specialist: Name of the specialist agent being routed to
            reasoning: Explanation of why this specialist was chosen
        """
        timestamp = self._format_timestamp()
        self._print(f"[{timestamp}] 🎯 Routing to: {specialist}")
        
        if self.verbose and reasoning:
            self._indent_level += 1
            self._print(f"Reasoning: {reasoning}")
            self._indent_level -= 1
    
    def on_tool_start(self, tool_name: str, inputs: Dict[str, Any]) -> None:
        """Called when a tool invocation begins.
        
        Args:
            tool_name: Name of the tool being invoked
            inputs: Input parameters passed to the tool
        """
        timestamp = self._format_timestamp()
        self._start_times[f"tool_{tool_name}"] = datetime.now()
        
        self._print(f"[{timestamp}] 🔧 Tool: {tool_name}")
        
        if self.verbose and inputs:
            self._indent_level += 1
            # Format inputs for display
            for key, value in inputs.items():
                # Truncate long values
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:97] + "..."
                self._print(f"{key}: {value_str}")
            self._indent_level -= 1
    
    def on_tool_end(self, tool_name: str, result: Any) -> None:
        """Called when a tool invocation completes.
        
        Args:
            tool_name: Name of the tool that completed
            result: The result returned by the tool
        """
        timestamp = self._format_timestamp()
        
        # Calculate duration if we have a start time
        duration_ms = None
        tool_key = f"tool_{tool_name}"
        if tool_key in self._start_times:
            duration = datetime.now() - self._start_times[tool_key]
            duration_ms = int(duration.total_seconds() * 1000)
            del self._start_times[tool_key]
        
        duration_str = f" ({duration_ms}ms)" if duration_ms is not None else ""
        self._print(f"[{timestamp}] ✓ Tool Complete: {tool_name}{duration_str}")
        
        if self.verbose and result is not None:
            self._indent_level += 1
            result_str = str(result)
            if len(result_str) > 200:
                result_str = result_str[:197] + "..."
            self._print(f"Result: {result_str}")
            self._indent_level -= 1
    
    def on_agent_end(self, agent_name: str, response: str) -> None:
        """Called when an agent completes processing.
        
        Args:
            agent_name: Name of the agent that completed
            response: The final response from the agent
        """
        self._indent_level = max(0, self._indent_level - 1)
        
        timestamp = self._format_timestamp()
        
        # Calculate duration if we have a start time
        duration_ms = None
        if agent_name in self._start_times:
            duration = datetime.now() - self._start_times[agent_name]
            duration_ms = int(duration.total_seconds() * 1000)
            del self._start_times[agent_name]
        
        duration_str = f" ({duration_ms}ms)" if duration_ms is not None else ""
        self._print(f"[{timestamp}] ✅ Agent Complete: {agent_name}{duration_str}")
        
        if self.verbose and response:
            self._indent_level += 1
            # Show first part of response
            response_preview = response[:150] + "..." if len(response) > 150 else response
            self._print(f"Response: {response_preview}")
            self._indent_level -= 1
    
    def on_error(self, error: Exception, context: str) -> None:
        """Called when an error occurs during processing.
        
        Args:
            error: The exception that occurred
            context: Description of where/when the error occurred
        """
        timestamp = self._format_timestamp()
        self._print(f"[{timestamp}] ❌ Error in {context}: {type(error).__name__}")
        
        if self.verbose:
            self._indent_level += 1
            self._print(f"Details: {str(error)}")
            self._indent_level -= 1
    
    def reset(self) -> None:
        """Reset the handler state.
        
        Clears indent level and timing information. Useful when starting
        a new query in the same session.
        """
        self._indent_level = 0
        self._start_times.clear()
