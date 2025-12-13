"""Tests for Orchestrator Agent."""

import json
import pytest
from unittest.mock import Mock, MagicMock
from src.agents.orchestrator import OrchestratorAgent
from src.config import Config
from src.handlers.stream_handler import InvestigationStreamHandler
from src.models import AgentResponse, SpecialistResponse


class TestOrchestratorRouting:
    """Tests for query routing logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.stream_handler = InvestigationStreamHandler(verbose=False)
        self.model = Mock()
        
        # Create mock specialists
        self.specialists = {
            "data_analyst": Mock(return_value=self._create_mock_response("data_analyst")),
            "ml_engineer": Mock(return_value=self._create_mock_response("ml_engineer")),
            "visualization_expert": Mock(return_value=self._create_mock_response("visualization_expert"))
        }
        
        self.orchestrator = OrchestratorAgent(
            model=self.model,
            specialists=self.specialists,
            stream_handler=self.stream_handler,
            config=self.config
        )
    
    def _create_mock_response(self, agent_name: str) -> str:
        """Create a mock specialist response."""
        response = SpecialistResponse(
            agent_name=agent_name,
            query="test query",
            response=f"Response from {agent_name}",
            tool_calls=[],
            execution_time_ms=100
        )
        return response.to_json()
    
    def test_route_data_analysis_query(self):
        """Test routing of data analysis queries."""
        queries = [
            "What is the average delay by airline?",
            "Calculate the on-time performance",
            "Show me statistics on cancellations",
            "Analyze the trend in load factors"
        ]
        
        for query in queries:
            routing = self.orchestrator._route_query(query)
            assert "data_analyst" in routing
    
    def test_route_ml_query(self):
        """Test routing of ML queries."""
        queries = [
            "How can I predict flight delays?",
            "Build a model for cancellation prediction",
            "What algorithm should I use for forecasting?",
            "Recommend a machine learning approach"
        ]
        
        for query in queries:
            routing = self.orchestrator._route_query(query)
            assert "ml_engineer" in routing
    
    def test_route_visualization_query(self):
        """Test routing of visualization queries."""
        queries = [
            "Create a bar chart of delays",
            "Show me a line graph of trends",
            "Visualize the delay distribution",
            "Plot the load factors over time"
        ]
        
        for query in queries:
            routing = self.orchestrator._route_query(query)
            assert "visualization_expert" in routing
    
    def test_route_multi_domain_query_analysis_viz(self):
        """Test routing of queries requiring both analysis and visualization."""
        queries = [
            "Analyze delays and create a chart",
            "Calculate OTP and visualize it",
            "Show me delay statistics in a graph"
        ]
        
        for query in queries:
            routing = self.orchestrator._route_query(query)
            assert "data_analyst" in routing
            assert "visualization_expert" in routing
            # Data analyst should come before visualization
            assert routing.index("data_analyst") < routing.index("visualization_expert")
    
    def test_route_multi_domain_query_ml_viz(self):
        """Test routing of queries requiring both ML and visualization."""
        queries = [
            "Predict delays and show the results",
            "Build a model and visualize predictions",
            "Forecast cancellations and create a chart"
        ]
        
        for query in queries:
            routing = self.orchestrator._route_query(query)
            assert "ml_engineer" in routing
            assert "visualization_expert" in routing
            # ML engineer should come before visualization
            assert routing.index("ml_engineer") < routing.index("visualization_expert")
    
    def test_route_ambiguous_query_defaults_to_data_analyst(self):
        """Test that ambiguous queries default to data analyst."""
        queries = [
            "Tell me about the airline data",
            "What can you help me with?",
            "Show me something interesting"
        ]
        
        for query in queries:
            routing = self.orchestrator._route_query(query)
            assert "data_analyst" in routing


class TestOrchestratorProcessing:
    """Tests for query processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.stream_handler = InvestigationStreamHandler(verbose=False)
        self.model = Mock()
        
        # Create mock specialists
        self.specialists = {
            "data_analyst": Mock(return_value=self._create_mock_response("data_analyst")),
            "ml_engineer": Mock(return_value=self._create_mock_response("ml_engineer")),
            "visualization_expert": Mock(return_value=self._create_mock_response("visualization_expert"))
        }
        
        self.orchestrator = OrchestratorAgent(
            model=self.model,
            specialists=self.specialists,
            stream_handler=self.stream_handler,
            config=self.config
        )
    
    def _create_mock_response(self, agent_name: str) -> str:
        """Create a mock specialist response."""
        response = SpecialistResponse(
            agent_name=agent_name,
            query="test query",
            response=f"Response from {agent_name}",
            tool_calls=[],
            execution_time_ms=100
        )
        return response.to_json()
    
    def test_process_returns_agent_response(self):
        """Test that process returns an AgentResponse."""
        query = "What is the average delay?"
        result = self.orchestrator.process(query)
        
        assert isinstance(result, AgentResponse)
        assert result.query == query
        assert len(result.routing) > 0
        assert len(result.specialist_responses) > 0
        assert result.synthesized_response
        assert result.total_time_ms >= 0
    
    def test_process_invokes_correct_specialists(self):
        """Test that process invokes the correct specialists."""
        query = "Analyze delays and create a chart"
        result = self.orchestrator.process(query)
        
        # Should have routed to data_analyst and visualization_expert
        assert "data_analyst" in result.routing
        assert "visualization_expert" in result.routing
        
        # Should have responses from both
        agent_names = [r.agent_name for r in result.specialist_responses]
        assert "data_analyst" in agent_names
        assert "visualization_expert" in agent_names
    
    def test_process_handles_single_specialist(self):
        """Test processing with a single specialist."""
        query = "Calculate the average delay"
        result = self.orchestrator.process(query)
        
        # Should route to data_analyst only
        assert result.routing == ["data_analyst"]
        assert len(result.specialist_responses) == 1
        assert result.specialist_responses[0].agent_name == "data_analyst"
    
    def test_process_handles_multiple_specialists(self):
        """Test processing with multiple specialists."""
        query = "Predict delays and visualize the results"
        result = self.orchestrator.process(query)
        
        # Should route to multiple specialists (may include data_analyst, ml_engineer, visualization_expert)
        assert len(result.routing) >= 2
        assert len(result.specialist_responses) >= 2
        
        # Should include ml_engineer and visualization_expert at minimum
        assert "ml_engineer" in result.routing
        assert "visualization_expert" in result.routing


class TestResponseSynthesis:
    """Tests for response synthesis."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.stream_handler = InvestigationStreamHandler(verbose=False)
        self.model = Mock()
        self.specialists = {}
        
        self.orchestrator = OrchestratorAgent(
            model=self.model,
            specialists=self.specialists,
            stream_handler=self.stream_handler,
            config=self.config
        )
    
    def test_synthesize_single_response(self):
        """Test synthesis of a single specialist response."""
        responses = [
            SpecialistResponse(
                agent_name="data_analyst",
                query="test",
                response="Analysis result",
                tool_calls=[],
                execution_time_ms=100
            )
        ]
        
        synthesis = self.orchestrator._synthesize_responses("test", responses)
        
        assert "Data Analyst" in synthesis
        assert "Analysis result" in synthesis
    
    def test_synthesize_multiple_responses(self):
        """Test synthesis of multiple specialist responses."""
        responses = [
            SpecialistResponse(
                agent_name="data_analyst",
                query="test",
                response="Analysis result",
                tool_calls=[],
                execution_time_ms=100
            ),
            SpecialistResponse(
                agent_name="visualization_expert",
                query="test",
                response="Visualization result",
                tool_calls=[],
                execution_time_ms=100
            )
        ]
        
        synthesis = self.orchestrator._synthesize_responses("test", responses)
        
        # Should mention both specialists
        assert "Data Analyst" in synthesis
        assert "Visualization Expert" in synthesis
        
        # Should include both responses
        assert "Analysis result" in synthesis
        assert "Visualization result" in synthesis
        
        # Should have a summary section
        assert "Summary" in synthesis
    
    def test_synthesize_empty_responses(self):
        """Test synthesis with no responses."""
        synthesis = self.orchestrator._synthesize_responses("test", [])
        
        assert "wasn't able to process" in synthesis.lower()


class TestConversationHistory:
    """Tests for conversation history management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.stream_handler = InvestigationStreamHandler(verbose=False)
        self.model = Mock()
        self.specialists = {}
        
        self.orchestrator = OrchestratorAgent(
            model=self.model,
            specialists=self.specialists,
            stream_handler=self.stream_handler,
            config=self.config
        )
    
    def test_update_history_adds_entries(self):
        """Test that update_history adds query-response pairs."""
        self.orchestrator._update_history("query1", "response1")
        
        assert len(self.orchestrator.conversation_history) == 2
        assert self.orchestrator.conversation_history[0]["role"] == "user"
        assert self.orchestrator.conversation_history[0]["content"] == "query1"
        assert self.orchestrator.conversation_history[1]["role"] == "assistant"
        assert self.orchestrator.conversation_history[1]["content"] == "response1"
    
    def test_get_relevant_history_limits_turns(self):
        """Test that get_relevant_history limits the number of turns."""
        # Add multiple turns
        for i in range(10):
            self.orchestrator._update_history(f"query{i}", f"response{i}")
        
        # Get last 3 turns (6 entries)
        history = self.orchestrator._get_relevant_history(max_turns=3)
        
        assert len(history) == 6
        # Should be the most recent entries
        assert "query9" in history[-2]["content"]
        assert "response9" in history[-1]["content"]
    
    def test_truncate_history_removes_oldest_first(self):
        """Test that truncation removes oldest entries first."""
        # Set a very low token limit
        self.config.max_tokens = 100
        
        # Add entries that will exceed the limit
        for i in range(20):
            self.orchestrator._update_history(
                f"query{i}" * 50,  # Long query
                f"response{i}" * 50  # Long response
            )
        
        # History should be truncated
        assert len(self.orchestrator.conversation_history) < 40
        
        # Most recent entries should still be there
        last_entry = self.orchestrator.conversation_history[-1]["content"]
        assert "response19" in last_entry
    
    def test_clear_history_removes_all_entries(self):
        """Test that clear_history removes all entries."""
        # Add some history
        self.orchestrator._update_history("query1", "response1")
        self.orchestrator._update_history("query2", "response2")
        
        assert len(self.orchestrator.conversation_history) > 0
        
        # Clear history
        self.orchestrator.clear_history()
        
        assert len(self.orchestrator.conversation_history) == 0
    
    def test_get_history_summary_returns_stats(self):
        """Test that get_history_summary returns correct statistics."""
        # Add some history
        self.orchestrator._update_history("query1", "response1")
        self.orchestrator._update_history("query2", "response2")
        
        summary = self.orchestrator.get_history_summary()
        
        assert summary["total_turns"] == 2
        assert summary["total_entries"] == 4
        assert summary["estimated_tokens"] > 0
        assert "max_tokens" in summary


class TestErrorHandling:
    """Tests for error handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.stream_handler = InvestigationStreamHandler(verbose=False)
        self.model = Mock()
        
        # Create a specialist that raises an error
        def error_specialist(query, context=None):
            raise ValueError("Test error")
        
        self.specialists = {
            "data_analyst": error_specialist
        }
        
        self.orchestrator = OrchestratorAgent(
            model=self.model,
            specialists=self.specialists,
            stream_handler=self.stream_handler,
            config=self.config
        )
    
    def test_process_handles_specialist_errors(self):
        """Test that process handles specialist errors gracefully."""
        query = "Calculate average delay"
        result = self.orchestrator.process(query)
        
        # Should still return a valid AgentResponse
        assert isinstance(result, AgentResponse)
        assert result.query == query
        
        # Should have an error response from the specialist
        assert len(result.specialist_responses) > 0
        assert "error" in result.specialist_responses[0].response.lower()
