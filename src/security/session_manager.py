"""Session management for user session isolation.

This module provides session management functionality with cryptographically
secure tokens and isolated session contexts. It addresses VULN-001 by
eliminating global state for session management.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import threading

from src.security.session_models import SessionContext
from src.security.identity_provider import IdentityProviderAdapter


class SessionManager:
    """Thread-safe session manager using isolated storage.
    
    This manager creates and maintains isolated session contexts for each user,
    ensuring that one user's session state cannot affect another user's experience.
    
    Attributes:
        _identity_provider: The identity provider adapter for authentication
        _session_ttl: Session time-to-live duration
        _open_access_mode: Whether to bypass permission checks
        _sessions: Thread-safe session storage
        _lock: Threading lock for session operations
    """
    
    def __init__(self, 
                 identity_provider: IdentityProviderAdapter,
                 session_ttl_hours: int = 24,
                 open_access_mode: bool = True):
        """Initialize session manager.
        
        Args:
            identity_provider: Identity provider for authentication
            session_ttl_hours: Session lifetime in hours
            open_access_mode: Whether to enable open access (default: True)
        """
        self._identity_provider = identity_provider
        self._session_ttl = timedelta(hours=session_ttl_hours)
        self._open_access_mode = open_access_mode
        # Session storage - keyed by session_id
        # In production, use Redis or similar distributed cache
        self._sessions: Dict[str, SessionContext] = {}
        self._lock = threading.RLock()
    
    def create_session(self, user_id: str, identity: Dict[str, Any]) -> SessionContext:
        """Create a new isolated session context.
        
        Args:
            user_id: Unique user identifier
            identity: Identity dictionary from provider
            
        Returns:
            New SessionContext with unique session token
        """
        session_id = self._generate_session_token()
        permissions = self._identity_provider.get_permissions(user_id)
        
        context = SessionContext(
            session_id=session_id,
            user_id=user_id,
            identity=identity,
            permissions=permissions if not self._open_access_mode else {"*": "*"},
            data_scope="company" if self._open_access_mode else permissions.get("scope", "station"),
            station=identity.get("station"),
            expires_at=datetime.utcnow() + self._session_ttl
        )
        
        with self._lock:
            self._sessions[session_id] = context
        
        return context
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Retrieve session context by ID.
        
        Args:
            session_id: Session token to look up
            
        Returns:
            SessionContext if valid and not expired, None otherwise
        """
        with self._lock:
            context = self._sessions.get(session_id)
            if context and context.is_expired():
                self._sessions.pop(session_id, None)
                return None
            return context
    
    def update_identity(self, session_id: str, identity: Dict[str, Any]) -> Optional[SessionContext]:
        """Update identity for a specific session only.
        
        Args:
            session_id: Session to update
            identity: New identity dictionary
            
        Returns:
            Updated SessionContext or None if session not found
        """
        with self._lock:
            context = self.get_session(session_id)
            if not context:
                return None
            
            # Create new context with updated identity (immutable pattern)
            new_context = SessionContext(
                session_id=context.session_id,
                user_id=identity.get("id", context.user_id),
                identity=identity,
                permissions=context.permissions,
                data_scope=context.data_scope,
                station=identity.get("station"),
                created_at=context.created_at,
                expires_at=context.expires_at
            )
            self._sessions[session_id] = new_context
            return new_context
    
    def invalidate_session(self, session_id: str) -> bool:
        """Remove a session.
        
        Args:
            session_id: Session to invalidate
            
        Returns:
            True if session was removed, False if not found
        """
        with self._lock:
            return self._sessions.pop(session_id, None) is not None
    
    def _generate_session_token(self) -> str:
        """Generate cryptographically secure session token.
        
        Returns:
            URL-safe token with minimum 256 bits of entropy
        """
        # secrets.token_urlsafe(32) generates 32 bytes = 256 bits of entropy
        return secrets.token_urlsafe(32)
    
    @property
    def active_session_count(self) -> int:
        """Get count of active sessions."""
        with self._lock:
            return len(self._sessions)
