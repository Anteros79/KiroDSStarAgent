"""Session-isolated investigation storage with row-level security.

This module provides thread-safe investigation storage with session isolation
and row-level security filtering. It addresses VULN-003 by ensuring
investigations are associated with session contexts and access is controlled.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
import uuid

from src.security.session_models import SessionContext
from src.security.rls_engine import RowLevelSecurityEngine


class InvestigationStore:
    """Thread-safe investigation storage with session isolation.
    
    This store maintains investigations with session/user association,
    ensuring that access is controlled through the RLS engine.
    
    Attributes:
        _investigations: Thread-safe storage for investigations
        _rls_engine: Row-level security engine for access control
        _lock: Reentrant lock for thread-safe operations
    """
    
    def __init__(self, rls_engine: RowLevelSecurityEngine):
        """Initialize investigation store.
        
        Args:
            rls_engine: Row-level security engine for access filtering
        """
        self._investigations: Dict[str, Dict[str, Any]] = {}
        self._rls_engine = rls_engine
        self._lock = threading.RLock()
    
    def create(self,
               data: Dict[str, Any],
               context: SessionContext,
               investigation_id: Optional[str] = None) -> Dict[str, Any]:
        """Create investigation associated with session context.
        
        Args:
            data: Investigation data dictionary
            context: Session context of the creating user
            investigation_id: Optional ID (generated if not provided)
            
        Returns:
            Created investigation record with metadata
            
        Requirements: 3.1
        """
        with self._lock:
            # Generate ID if not provided
            if investigation_id is None:
                investigation_id = str(uuid.uuid4())
            
            # Create record with session association
            record = {
                **data,
                "id": investigation_id,
                "created_by": context.user_id,
                "session_id": context.session_id,
                "station": context.station,
                "region": context.identity.get("region"),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            
            self._investigations[investigation_id] = record
            return record

    def get(self,
            investigation_id: str,
            context: SessionContext) -> Optional[Dict[str, Any]]:
        """Get investigation if user has access.
        
        Args:
            investigation_id: ID of investigation to retrieve
            context: Session context of the requesting user
            
        Returns:
            Investigation record if found and accessible, None otherwise
            
        Requirements: 3.2, 3.3
        """
        with self._lock:
            inv = self._investigations.get(investigation_id)
            if not inv:
                return None
            
            # Check access through RLS engine
            if not self._rls_engine.check_single_access("investigation", inv, context):
                return None  # Access denied
            
            return inv.copy()  # Return copy to prevent external modification
    
    def list(self,
             context: SessionContext,
             station: Optional[str] = None,
             limit: Optional[int] = None,
             offset: int = 0) -> List[Dict[str, Any]]:
        """List investigations user has access to.
        
        Args:
            context: Session context of the requesting user
            station: Optional station filter
            limit: Optional maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of accessible investigations
            
        Requirements: 3.2
        """
        with self._lock:
            # Get all investigations
            all_invs = list(self._investigations.values())
            
            # Apply station filter if provided
            if station:
                all_invs = [i for i in all_invs if i.get("station") == station]
            
            # Apply RLS filtering
            filtered = self._rls_engine.filter_results("investigation", all_invs, context)
            
            # Sort by created_at descending (newest first)
            filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            # Apply pagination
            if offset > 0:
                filtered = filtered[offset:]
            if limit is not None:
                filtered = filtered[:limit]
            
            # Return copies to prevent external modification
            return [inv.copy() for inv in filtered]
    
    def update(self,
               investigation_id: str,
               updates: Dict[str, Any],
               context: SessionContext) -> Optional[Dict[str, Any]]:
        """Update investigation if user has access.
        
        Args:
            investigation_id: ID of investigation to update
            updates: Dictionary of fields to update
            context: Session context of the requesting user
            
        Returns:
            Updated investigation record if accessible, None otherwise
            
        Requirements: 3.3, 3.4
        """
        with self._lock:
            # First check if user has access
            inv = self.get(investigation_id, context)
            if not inv:
                return None
            
            # Get the actual stored record (not the copy)
            stored_inv = self._investigations.get(investigation_id)
            if not stored_inv:
                return None
            
            # Prevent modification of protected fields
            protected_fields = {"id", "created_by", "session_id", "created_at"}
            safe_updates = {k: v for k, v in updates.items() if k not in protected_fields}
            
            # Apply updates
            stored_inv.update(safe_updates)
            stored_inv["updated_at"] = datetime.utcnow().isoformat()
            
            return stored_inv.copy()
    
    def delete(self,
               investigation_id: str,
               context: SessionContext) -> bool:
        """Delete investigation if user has access.
        
        Args:
            investigation_id: ID of investigation to delete
            context: Session context of the requesting user
            
        Returns:
            True if deleted, False if not found or access denied
            
        Requirements: 3.3, 3.4
        """
        with self._lock:
            # First check if user has access
            inv = self.get(investigation_id, context)
            if not inv:
                return False
            
            # Delete the investigation
            del self._investigations[investigation_id]
            return True
    
    def count(self, context: SessionContext, station: Optional[str] = None) -> int:
        """Count investigations user has access to.
        
        Args:
            context: Session context of the requesting user
            station: Optional station filter
            
        Returns:
            Number of accessible investigations
        """
        return len(self.list(context, station=station))
    
    def exists(self, investigation_id: str, context: SessionContext) -> bool:
        """Check if investigation exists and is accessible.
        
        Args:
            investigation_id: ID of investigation to check
            context: Session context of the requesting user
            
        Returns:
            True if exists and accessible, False otherwise
        """
        return self.get(investigation_id, context) is not None
    
    @property
    def total_count(self) -> int:
        """Get total count of all investigations (admin use only)."""
        with self._lock:
            return len(self._investigations)
    
    def clear(self) -> None:
        """Clear all investigations (for testing purposes)."""
        with self._lock:
            self._investigations.clear()
