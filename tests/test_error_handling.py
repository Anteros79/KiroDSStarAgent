"""Tests for error handling components.

This module tests the BedrockRetryHandler and safe_specialist_call
error handling utilities.
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.handlers.retry_handler import BedrockRetryHandler, with_retry
from src.handlers.error_handler import safe_specialist_call, safe_specialist_call_with_context
from src.models import SpecialistResponse


class TestBedrockRetryHandler:
    """Tests for BedrockRetryHandler class."""
    
    def test_initialization_defaults(self):
        """Test handler initializes with correct defaults."""
        handler = BedrockRetryHandler()
        assert handler.max_attempts == 3
        assert handler.base_delay == 1.0
    
    def test_initialization_custom_values(self):
        """Test handler initializes with custom values."""
        handler = BedrockRetryHandler(max_attempts=5, base_delay=2.0)
        assert handler.max_attempts == 5
        assert handler.base_delay == 2.0
    
    def test_initialization_invalid_max_attempts(self):
        """Test handler rejects invalid max_attempts."""
        with pytest.raises(ValueError, match="max_attempts must be >= 1"):
            BedrockRetryHandler(max_attempts=0)
    
    def test_initialization_invalid_base_delay(self):
        """Test handler rejects invalid base_delay."""
        with pytest.raises(ValueError, match="base_delay must be > 0"):
            BedrockRetryHandler(base_delay=0)
    
    def test_successful_execution_first_attempt(self):
        """Test successful execution on first attempt."""
        handler = BedrockRetryHandler()
        mock_func = Mock(return_value="success")
        
        result = handler.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_throttling_exception(self):
        """Test retry logic for throttling exceptions."""
        handler = BedrockRetryHandler(max_attempts=3, base_delay=0.1)
        
        # Mock function that fails twice then succeeds
        mock_func = Mock(side_effect=[
            Exception("ThrottlingException: Rate limit exceeded"),
            Exception("ThrottlingException: Rate limit exceeded"),
            "success"
        ])
        
        start_time = time.time()
        result = handler.execute_with_retry(mock_func)
        elapsed = time.time() - start_time
        
        assert result == "success"
        assert mock_func.call_count == 3
        # Should have delays of 0.1s and 0.2s (total ~0.3s)
        assert elapsed >= 0.3
    
    def test_exponential_backoff_delays(self):
        """Test that delays follow exponential backoff pattern."""
        handler = BedrockRetryHandler(max_attempts=3, base_delay=0.1)
        
        # Mock function that always fails with retryable error
        mock_func = Mock(side_effect=Exception("ServiceUnavailableException"))
        
        start_time = time.time()
        with pytest.raises(Exception):
            handler.execute_with_retry(mock_func)
        elapsed = time.time() - start_time
        
        # Expected delays: 0.1s (2^0), 0.2s (2^1) = 0.3s total
        assert elapsed >= 0.3
        assert mock_func.call_count == 3
    
    def test_non_retryable_error_raises_immediately(self):
        """Test that non-retryable errors are raised immediately."""
        handler = BedrockRetryHandler()
        
        # Mock function with non-retryable error
        mock_func = Mock(side_effect=ValueError("Invalid input"))
        
        with pytest.raises(ValueError, match="Invalid input"):
            handler.execute_with_retry(mock_func)
        
        # Should only be called once (no retries)
        assert mock_func.call_count == 1
    
    def test_max_attempts_exhausted(self):
        """Test that exception is raised after max attempts."""
        handler = BedrockRetryHandler(max_attempts=2, base_delay=0.05)
        
        # Mock function that always fails
        mock_func = Mock(side_effect=Exception("ThrottlingException"))
        
        with pytest.raises(Exception, match="ThrottlingException"):
            handler.execute_with_retry(mock_func)
        
        assert mock_func.call_count == 2
    
    def test_is_retryable_error_patterns(self):
        """Test retryable error detection."""
        handler = BedrockRetryHandler()
        
        # Test retryable errors
        assert handler._is_retryable_error(Exception("ThrottlingException"))
        assert handler._is_retryable_error(Exception("ServiceUnavailableException"))
        assert handler._is_retryable_error(Exception("Rate limit exceeded"))
        assert handler._is_retryable_error(Exception("Connection timeout"))
        assert handler._is_retryable_error(Exception("Service temporarily unavailable"))
        
        # Test non-retryable errors
        assert not handler._is_retryable_error(ValueError("Invalid input"))
        assert not handler._is_retryable_error(KeyError("Missing key"))
        assert not handler._is_retryable_error(Exception("Unknown error"))


class TestWithRetryDecorator:
    """Tests for with_retry decorator."""
    
    def test_decorator_successful_execution(self):
        """Test decorator with successful function."""
        @with_retry(max_attempts=3, base_delay=0.1)
        def successful_func():
            return "success"
        
        result = successful_func()
        assert result == "success"
    
    def test_decorator_with_retries(self):
        """Test decorator retries on failure."""
        call_count = {"count": 0}
        
        @with_retry(max_attempts=3, base_delay=0.05)
        def failing_func():
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise Exception("ThrottlingException")
            return "success"
        
        result = failing_func()
        assert result == "success"
        assert call_count["count"] == 3


class TestSafeSpecialistCall:
    """Tests for safe_specialist_call wrapper."""
    
    def test_successful_specialist_call(self):
        """Test wrapper with successful specialist call."""
        # Mock specialist that returns valid JSON
        def mock_specialist(query):
            return '{"agent_name": "test_agent", "query": "test", "response": "success", "tool_calls": [], "execution_time_ms": 100}'
        
        response = safe_specialist_call(mock_specialist, "test query")
        
        assert isinstance(response, SpecialistResponse)
        assert response.agent_name == "test_agent"
        assert response.response == "success"
    
    def test_specialist_call_with_plain_text_response(self):
        """Test wrapper with plain text response."""
        def mock_specialist(query):
            return "Plain text response"
        
        response = safe_specialist_call(mock_specialist, "test query")
        
        assert isinstance(response, SpecialistResponse)
        assert response.agent_name == "mock_specialist"
        assert response.response == "Plain text response"
    
    def test_specialist_call_with_error(self):
        """Test wrapper catches and handles errors."""
        def failing_specialist(query):
            raise Exception("Something went wrong")
        
        response = safe_specialist_call(failing_specialist, "test query")
        
        assert isinstance(response, SpecialistResponse)
        assert response.agent_name == "failing_specialist"
        assert "encountered an issue" in response.response.lower()
        assert len(response.tool_calls) == 0
    
    def test_specialist_call_timeout_error_message(self):
        """Test custom error message for timeout errors."""
        def timeout_specialist(query):
            raise TimeoutError("Request timed out")
        
        response = safe_specialist_call(timeout_specialist, "test query")
        
        assert "taking longer than expected" in response.response
    
    def test_specialist_call_connection_error_message(self):
        """Test custom error message for connection errors."""
        def connection_specialist(query):
            raise ConnectionError("Network error")
        
        response = safe_specialist_call(connection_specialist, "test query")
        
        assert "connection issues" in response.response.lower()
    
    def test_specialist_call_with_context(self):
        """Test safe_specialist_call_with_context wrapper."""
        def mock_specialist_with_context(query, context):
            return '{"agent_name": "test_agent", "query": "test", "response": "success with context", "tool_calls": [], "execution_time_ms": 100}'
        
        response = safe_specialist_call_with_context(
            mock_specialist_with_context,
            "test query",
            {"previous": "context"}
        )
        
        assert isinstance(response, SpecialistResponse)
        assert response.response == "success with context"
    
    def test_specialist_call_with_context_error(self):
        """Test safe_specialist_call_with_context handles errors."""
        def failing_specialist_with_context(query, context):
            raise ValueError("Invalid context")
        
        response = safe_specialist_call_with_context(
            failing_specialist_with_context,
            "test query",
            {"test": "context"}
        )
        
        assert isinstance(response, SpecialistResponse)
        # The error message contains "invalid" which triggers the invalid request message
        assert "invalid request" in response.response.lower() or "encountered an issue" in response.response.lower()
