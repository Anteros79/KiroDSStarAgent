"""Response models for DS-Star multi-agent system."""

import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    """Represents a single tool invocation by an agent.
    
    Attributes:
        tool_name: Name of the tool that was invoked
        inputs: Dictionary of input parameters passed to the tool
        output: The result returned by the tool
        duration_ms: Execution time in milliseconds
    """
    
    tool_name: str
    inputs: Dict[str, Any]
    output: Any
    duration_ms: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the tool call
        """
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2, default=str)


@dataclass
class SpecialistResponse:
    """Response from a specialist agent.
    
    Attributes:
        agent_name: Name of the specialist agent (e.g., "data_analyst")
        query: The query that was processed
        response: The agent's response text
        tool_calls: List of tools invoked during processing
        execution_time_ms: Total execution time in milliseconds
    """
    
    agent_name: str
    query: str
    response: str
    tool_calls: List[ToolCall]
    execution_time_ms: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the specialist response
        """
        return {
            "agent_name": self.agent_name,
            "query": self.query,
            "response": self.response,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "execution_time_ms": self.execution_time_ms
        }
    
    def to_json(self) -> str:
        """Convert to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2, default=str)


@dataclass
class AgentResponse:
    """Complete response from the orchestrator agent.
    
    Attributes:
        query: The original user query
        routing: List of specialist agent names that were invoked
        specialist_responses: Responses from each specialist
        synthesized_response: Final combined response from orchestrator
        charts: List of chart specifications generated (if any)
        total_time_ms: Total processing time in milliseconds
    """
    
    query: str
    routing: List[str]
    specialist_responses: List[SpecialistResponse]
    synthesized_response: str
    charts: List[Dict[str, Any]]  # ChartSpecification will be defined in handlers/chart_handler.py
    total_time_ms: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the agent response
        """
        return {
            "query": self.query,
            "routing": self.routing,
            "specialist_responses": [sr.to_dict() for sr in self.specialist_responses],
            "synthesized_response": self.synthesized_response,
            "charts": self.charts,
            "total_time_ms": self.total_time_ms
        }
    
    def to_json(self) -> str:
        """Convert to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResponse":
        """Create AgentResponse from dictionary.
        
        Args:
            data: Dictionary containing response data
        
        Returns:
            AgentResponse instance
        """
        specialist_responses = [
            SpecialistResponse(
                agent_name=sr["agent_name"],
                query=sr["query"],
                response=sr["response"],
                tool_calls=[
                    ToolCall(
                        tool_name=tc["tool_name"],
                        inputs=tc["inputs"],
                        output=tc["output"],
                        duration_ms=tc["duration_ms"]
                    )
                    for tc in sr["tool_calls"]
                ],
                execution_time_ms=sr["execution_time_ms"]
            )
            for sr in data["specialist_responses"]
        ]
        
        return cls(
            query=data["query"],
            routing=data["routing"],
            specialist_responses=specialist_responses,
            synthesized_response=data["synthesized_response"],
            charts=data.get("charts", []),
            total_time_ms=data["total_time_ms"]
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "AgentResponse":
        """Create AgentResponse from JSON string.
        
        Args:
            json_str: JSON string containing response data
        
        Returns:
            AgentResponse instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
