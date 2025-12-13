"""Tests for InvestigationStreamHandler."""

import pytest
from io import StringIO
import sys
from src.handlers.stream_handler import InvestigationStreamHandler


class TestInvestigationStreamHandler:
    """Unit tests for InvestigationStreamHandler."""
    
    def test_initialization(self):
        """Test handler can be initialized with default and custom verbose settings."""
        handler_default = InvestigationStreamHandler()
        assert handler_default.verbose is False
        
        handler_verbose = InvestigationStreamHandler(verbose=True)
        assert handler_verbose.verbose is True
    
    def test_on_agent_start(self, capsys):
        """Test agent start event is logged correctly."""
        handler = InvestigationStreamHandler(verbose=False)
        handler.on_agent_start("TestAgent", "What is the weather?")
        
        captured = capsys.readouterr()
        assert "Agent Started: TestAgent" in captured.out
        assert "🤖" in captured.out
    
    def test_on_agent_start_verbose(self, capsys):
        """Test agent start event includes query in verbose mode."""
        handler = InvestigationStreamHandler(verbose=True)
        handler.on_agent_start("TestAgent", "What is the weather?")
        
        captured = capsys.readouterr()
        assert "Agent Started: TestAgent" in captured.out
        assert "Query: What is the weather?" in captured.out
    
    def test_on_routing_decision(self, capsys):
        """Test routing decision is logged correctly."""
        handler = InvestigationStreamHandler(verbose=False)
        handler.on_routing_decision("DataAnalyst", "Query contains data analysis keywords")
        
        captured = capsys.readouterr()
        assert "Routing to: DataAnalyst" in captured.out
        assert "🎯" in captured.out
    
    def test_on_routing_decision_verbose(self, capsys):
        """Test routing decision includes reasoning in verbose mode."""
        handler = InvestigationStreamHandler(verbose=True)
        handler.on_routing_decision("DataAnalyst", "Query contains data analysis keywords")
        
        captured = capsys.readouterr()
        assert "Routing to: DataAnalyst" in captured.out
        assert "Reasoning: Query contains data analysis keywords" in captured.out
    
    def test_on_tool_start(self, capsys):
        """Test tool start event is logged correctly."""
        handler = InvestigationStreamHandler(verbose=False)
        handler.on_tool_start("query_airline_data", {"query": "SELECT * FROM flights"})
        
        captured = capsys.readouterr()
        assert "Tool: query_airline_data" in captured.out
        assert "🔧" in captured.out
    
    def test_on_tool_start_verbose(self, capsys):
        """Test tool start event includes inputs in verbose mode."""
        handler = InvestigationStreamHandler(verbose=True)
        handler.on_tool_start("query_airline_data", {"query": "SELECT * FROM flights"})
        
        captured = capsys.readouterr()
        assert "Tool: query_airline_data" in captured.out
        assert "query: SELECT * FROM flights" in captured.out
    
    def test_on_tool_end(self, capsys):
        """Test tool end event is logged correctly."""
        handler = InvestigationStreamHandler(verbose=False)
        handler.on_tool_start("query_airline_data", {})
        handler.on_tool_end("query_airline_data", "Query executed successfully")
        
        captured = capsys.readouterr()
        assert "Tool Complete: query_airline_data" in captured.out
        assert "✓" in captured.out
        assert "ms)" in captured.out  # Duration should be included
    
    def test_on_tool_end_verbose(self, capsys):
        """Test tool end event includes result in verbose mode."""
        handler = InvestigationStreamHandler(verbose=True)
        handler.on_tool_start("query_airline_data", {})
        handler.on_tool_end("query_airline_data", "Query executed successfully")
        
        captured = capsys.readouterr()
        assert "Tool Complete: query_airline_data" in captured.out
        assert "Result: Query executed successfully" in captured.out
    
    def test_on_agent_end(self, capsys):
        """Test agent end event is logged correctly."""
        handler = InvestigationStreamHandler(verbose=False)
        handler.on_agent_start("TestAgent", "test query")
        handler.on_agent_end("TestAgent", "Analysis complete")
        
        captured = capsys.readouterr()
        assert "Agent Complete: TestAgent" in captured.out
        assert "✅" in captured.out
        assert "ms)" in captured.out  # Duration should be included
    
    def test_on_agent_end_verbose(self, capsys):
        """Test agent end event includes response in verbose mode."""
        handler = InvestigationStreamHandler(verbose=True)
        handler.on_agent_start("TestAgent", "test query")
        handler.on_agent_end("TestAgent", "Analysis complete with detailed results")
        
        captured = capsys.readouterr()
        assert "Agent Complete: TestAgent" in captured.out
        assert "Response: Analysis complete with detailed results" in captured.out
    
    def test_on_error(self, capsys):
        """Test error event is logged correctly."""
        handler = InvestigationStreamHandler(verbose=False)
        error = ValueError("Invalid input")
        handler.on_error(error, "data processing")
        
        captured = capsys.readouterr()
        assert "Error in data processing: ValueError" in captured.out
        assert "❌" in captured.out
    
    def test_on_error_verbose(self, capsys):
        """Test error event includes details in verbose mode."""
        handler = InvestigationStreamHandler(verbose=True)
        error = ValueError("Invalid input")
        handler.on_error(error, "data processing")
        
        captured = capsys.readouterr()
        assert "Error in data processing: ValueError" in captured.out
        assert "Details: Invalid input" in captured.out
    
    def test_reset(self):
        """Test reset clears handler state."""
        handler = InvestigationStreamHandler()
        handler.on_agent_start("TestAgent", "test")
        handler.on_tool_start("test_tool", {})
        
        # State should have entries
        assert len(handler._start_times) > 0
        assert handler._indent_level > 0
        
        handler.reset()
        
        # State should be cleared
        assert len(handler._start_times) == 0
        assert handler._indent_level == 0
    
    def test_event_ordering(self, capsys):
        """Test that events are logged in correct order."""
        handler = InvestigationStreamHandler(verbose=True)
        
        handler.on_agent_start("Orchestrator", "Analyze flight delays")
        handler.on_routing_decision("DataAnalyst", "Data analysis required")
        handler.on_tool_start("query_airline_data", {"query": "delays"})
        handler.on_tool_end("query_airline_data", "Results: 100 rows")
        handler.on_agent_end("Orchestrator", "Analysis complete")
        
        captured = capsys.readouterr()
        output_lines = captured.out.strip().split('\n')
        
        # Verify order of events
        assert "Agent Started" in output_lines[0]
        assert "Routing to" in output_lines[2]
        assert "Tool:" in output_lines[4]
        assert "Tool Complete" in output_lines[6]
        assert "Agent Complete" in output_lines[8]
    
    def test_long_value_truncation(self, capsys):
        """Test that long values are truncated in output."""
        handler = InvestigationStreamHandler(verbose=True)
        
        long_input = "x" * 200
        handler.on_tool_start("test_tool", {"data": long_input})
        
        captured = capsys.readouterr()
        assert "..." in captured.out
        assert len(captured.out) < len(long_input) + 100  # Should be truncated
    
    def test_indentation_levels(self, capsys):
        """Test that indentation increases and decreases correctly."""
        handler = InvestigationStreamHandler(verbose=False)
        
        # Start first agent - this increases indent level
        handler.on_agent_start("Agent1", "query1")
        agent_output = capsys.readouterr()
        
        # Tool call should be indented relative to agent start
        handler.on_tool_start("tool1", {})
        tool_output = capsys.readouterr()
        
        # Verify tool has more indentation than agent start
        # Agent start message itself is at indent 0, but increases indent for subsequent messages
        # Tool message should be at indent 1 (2 spaces)
        assert "  [" in tool_output.out or tool_output.out.startswith("  ")
        
        # End agent (decreases indent)
        handler.on_agent_end("Agent1", "done")
        
        # Verify indent level was properly managed
        assert handler._indent_level == 0
