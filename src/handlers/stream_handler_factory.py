"""Stream handler factory for request-scoped WebSocket handlers.

This module provides factory methods for creating request-scoped stream handlers
that are bound to specific WebSocket connections and sessions. This ensures
that concurrent users receive only their own data streams.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from typing import Any, Dict, Optional, Protocol, runtime_checkable
from datetime import datetime
import asyncio
import logging

from src.handlers.stream_handler import InvestigationStreamHandler

logger = logging.getLogger(__name__)


@runtime_checkable
class WebSocketProtocol(Protocol):
    """Protocol for WebSocket-like objects."""
    
    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON data through the WebSocket."""
        ...


class WebSocketStreamHandler(InvestigationStreamHandler):
    """WebSocket-specific stream handler - request-scoped, never shared.
    
    This handler extends InvestigationStreamHandler to provide WebSocket-specific
    functionality. Each instance is bound to a specific WebSocket connection
    and session, ensuring message isolation between concurrent users.
    
    Attributes:
        _websocket: The WebSocket connection this handler is bound to
        _session_id: The session ID this handler is associated with
        _closed: Whether this handler has been closed
        _message_queue: Queue of messages to send (for async handling)
    
    Requirements:
        - 2.1: Create new stream handler instance for each WebSocket query
        - 2.3: Route responses to correct client connection
    """
    
    def __init__(self, websocket: WebSocketProtocol, session_id: str):
        """Initialize WebSocket stream handler.
        
        Args:
            websocket: The WebSocket connection to send messages to
            session_id: The session ID this handler is associated with
        """
        super().__init__(verbose=False)
        self._websocket = websocket
        self._session_id = session_id
        self._closed = False
        self._message_count = 0
        self._created_at = datetime.utcnow()
        self._last_message_at: Optional[datetime] = None
    
    @property
    def session_id(self) -> str:
        """Get the session ID this handler is bound to."""
        return self._session_id
    
    @property
    def is_closed(self) -> bool:
        """Check if this handler has been closed."""
        return self._closed
    
    @property
    def message_count(self) -> int:
        """Get the number of messages sent through this handler."""
        return self._message_count
    
    async def send(self, message: Dict[str, Any]) -> bool:
        """Send message to this specific WebSocket only.
        
        Args:
            message: The message dictionary to send
            
        Returns:
            True if message was sent successfully, False otherwise
            
        Requirements:
            - 2.3: Route response to correct client connection
            - 2.4: Handle disconnection gracefully
        """
        if self._closed:
            logger.debug(f"Handler for session {self._session_id} is closed, skipping message")
            return False
        
        try:
            # Add session metadata to message
            enriched_message = {
                **message,
                "_session_id": self._session_id,
                "_timestamp": datetime.utcnow().isoformat()
            }
            await self._websocket.send_json(enriched_message)
            self._message_count += 1
            self._last_message_at = datetime.utcnow()
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to session {self._session_id}: {e}")
            self._closed = True
            return False
    
    def send_sync(self, message: Dict[str, Any]) -> bool:
        """Synchronous wrapper for send method.
        
        This method schedules the async send in the event loop.
        Use this when calling from synchronous code.
        
        Args:
            message: The message dictionary to send
            
        Returns:
            True if message was scheduled, False if handler is closed
        """
        if self._closed:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule the coroutine to run
                asyncio.create_task(self.send(message))
                return True
            else:
                # Run synchronously if no event loop
                return loop.run_until_complete(self.send(message))
        except RuntimeError:
            # No event loop available
            logger.warning(f"No event loop available for session {self._session_id}")
            return False
    
    def close(self) -> None:
        """Mark handler as closed - cleanup.
        
        This method marks the handler as closed, preventing any further
        messages from being sent. It does not close the underlying WebSocket
        connection, as that is managed by the server.
        
        Requirements:
            - 2.4: Clean up only this user's stream handler resources
            - 2.5: Isolate errors to affected session only
        """
        if not self._closed:
            logger.debug(f"Closing handler for session {self._session_id}, sent {self._message_count} messages")
            self._closed = True
    
    def on_agent_start(self, agent_name: str, query: str) -> None:
        """Called when an agent begins processing a query.
        
        Overrides parent to send via WebSocket instead of printing.
        """
        super().on_agent_start(agent_name, query)
        self.send_sync({
            "type": "agent_start",
            "agent_name": agent_name,
            "query": query,
            "timestamp": self._format_timestamp()
        })
    
    def on_routing_decision(self, specialist: str, reasoning: str) -> None:
        """Called when the orchestrator makes a routing decision.
        
        Overrides parent to send via WebSocket instead of printing.
        """
        super().on_routing_decision(specialist, reasoning)
        self.send_sync({
            "type": "routing_decision",
            "specialist": specialist,
            "reasoning": reasoning,
            "timestamp": self._format_timestamp()
        })
    
    def on_tool_start(self, tool_name: str, inputs: Dict[str, Any]) -> None:
        """Called when a tool invocation begins.
        
        Overrides parent to send via WebSocket instead of printing.
        """
        super().on_tool_start(tool_name, inputs)
        self.send_sync({
            "type": "tool_start",
            "tool_name": tool_name,
            "inputs": inputs,
            "timestamp": self._format_timestamp()
        })
    
    def on_tool_end(self, tool_name: str, result: Any) -> None:
        """Called when a tool invocation completes.
        
        Overrides parent to send via WebSocket instead of printing.
        """
        super().on_tool_end(tool_name, result)
        # Truncate large results for WebSocket transmission
        result_str = str(result) if result is not None else None
        if result_str and len(result_str) > 1000:
            result_str = result_str[:997] + "..."
        
        self.send_sync({
            "type": "tool_end",
            "tool_name": tool_name,
            "result": result_str,
            "timestamp": self._format_timestamp()
        })
    
    def on_agent_end(self, agent_name: str, response: str) -> None:
        """Called when an agent completes processing.
        
        Overrides parent to send via WebSocket instead of printing.
        """
        super().on_agent_end(agent_name, response)
        self.send_sync({
            "type": "agent_end",
            "agent_name": agent_name,
            "response": response,
            "timestamp": self._format_timestamp()
        })
    
    def on_error(self, error: Exception, context: str) -> None:
        """Called when an error occurs during processing.
        
        Overrides parent to send via WebSocket instead of printing.
        
        Requirements:
            - 2.5: Isolate error to affected session only
        """
        super().on_error(error, context)
        self.send_sync({
            "type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": self._format_timestamp()
        })
    
    def __repr__(self) -> str:
        """String representation of the handler."""
        status = "closed" if self._closed else "open"
        return f"WebSocketStreamHandler(session={self._session_id}, status={status}, messages={self._message_count})"



class StreamHandlerFactory:
    """Factory for creating request-scoped stream handlers.
    
    This factory creates new stream handler instances for each WebSocket
    connection, ensuring that no global state is modified and each handler
    is properly isolated to its session.
    
    Requirements:
        - 2.2: No global state modification
    """
    
    # Class-level counter for tracking created handlers (for debugging only)
    _handler_count: int = 0
    
    @classmethod
    def create_websocket_handler(
        cls,
        websocket: WebSocketProtocol,
        session_id: str
    ) -> WebSocketStreamHandler:
        """Create a new stream handler bound to a specific WebSocket and session.
        
        This method creates a fresh handler instance for each request,
        ensuring complete isolation between concurrent users.
        
        Args:
            websocket: The WebSocket connection to bind to
            session_id: The session ID to associate with this handler
            
        Returns:
            A new WebSocketStreamHandler instance
            
        Requirements:
            - 2.1: Create new stream handler instance for each WebSocket query
            - 2.2: No global state modification (each call creates new instance)
        """
        cls._handler_count += 1
        handler = WebSocketStreamHandler(websocket, session_id)
        logger.debug(f"Created handler #{cls._handler_count} for session {session_id}")
        return handler
    
    @classmethod
    def get_handler_count(cls) -> int:
        """Get the total number of handlers created (for debugging/monitoring).
        
        Returns:
            Total number of handlers created by this factory
        """
        return cls._handler_count
    
    @classmethod
    def reset_handler_count(cls) -> None:
        """Reset the handler count (for testing purposes only)."""
        cls._handler_count = 0
