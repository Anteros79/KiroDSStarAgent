"""Row-Level Security Engine for data access filtering.

This module provides row-level security filtering based on user
permissions and data scope. It addresses VULN-002 by implementing
proper access control for data queries.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from src.security.session_models import (
    DataScope,
    PermissionPolicy,
    SessionContext,
    AccessDecision,
    AuditLogEntry,
)

logger = logging.getLogger(__name__)


class RowLevelSecurityEngine:
    """Filters data based on user permissions and scope.
    
    This engine applies permission policies to filter query results,
    ensuring users only see data they are authorized to access.
    In Open Access Mode (default), all filtering is bypassed.
    
    Attributes:
        _open_access_mode: Whether to bypass all filtering
        _policies: Registered permission policies by entity type
        _audit_log: List of access decision audit entries
    """
    
    def __init__(self, open_access_mode: bool = True):
        """Initialize RLS engine.
        
        Args:
            open_access_mode: Whether to bypass filtering (default: True)
        """
        self._open_access_mode = open_access_mode
        self._policies: Dict[str, PermissionPolicy] = {}
        self._audit_log: List[AuditLogEntry] = []
    
    def register_policy(self, policy: PermissionPolicy) -> None:
        """Register a permission policy for an entity type.
        
        Args:
            policy: Permission policy to register
        """
        self._policies[policy.entity_type] = policy
    
    def filter_results(self, 
                       entity_type: str,
                       results: List[Dict[str, Any]], 
                       context: SessionContext) -> List[Dict[str, Any]]:
        """Filter results based on user's permissions.
        
        Args:
            entity_type: Type of entity being queried
            results: List of result dictionaries to filter
            context: Session context with user permissions
            
        Returns:
            Filtered list of results user can access
        """
        # Bypass filtering in open access mode
        if self._open_access_mode:
            self._log_access(
                entity_type=entity_type,
                count=len(results),
                context=context,
                action="read",
                decision=AccessDecision.OPEN_ACCESS,
                reason="open_access_mode"
            )
            return results
        
        policy = self._policies.get(entity_type)
        if not policy:
            # No policy = open access (default)
            self._log_access(
                entity_type=entity_type,
                count=len(results),
                context=context,
                action="read",
                decision=AccessDecision.ALLOWED,
                reason="no_policy_defined"
            )
            return results
        
        filtered = []
        denied_count = 0
        for item in results:
            if self._check_access(item, policy, context):
                filtered.append(item)
            else:
                denied_count += 1
                # Log each denied access
                self._log_access(
                    entity_type=entity_type,
                    count=1,
                    context=context,
                    action="read",
                    entity_id=item.get("id"),
                    decision=AccessDecision.DENIED,
                    reason="policy_check_failed"
                )
        
        # Log allowed access for filtered results
        if filtered:
            self._log_access(
                entity_type=entity_type,
                count=len(filtered),
                context=context,
                action="read",
                decision=AccessDecision.ALLOWED,
                reason="policy_check_passed"
            )
        
        return filtered
    
    def check_single_access(self,
                            entity_type: str,
                            item: Dict[str, Any],
                            context: SessionContext) -> bool:
        """Check if user can access a single item.
        
        Args:
            entity_type: Type of entity
            item: Item to check access for
            context: Session context with user permissions
            
        Returns:
            True if access allowed, False otherwise
        """
        if self._open_access_mode:
            self._log_access(
                entity_type=entity_type,
                count=1,
                context=context,
                action="read",
                entity_id=item.get("id"),
                decision=AccessDecision.OPEN_ACCESS,
                reason="open_access_mode"
            )
            return True
        
        policy = self._policies.get(entity_type)
        if not policy:
            self._log_access(
                entity_type=entity_type,
                count=1,
                context=context,
                action="read",
                entity_id=item.get("id"),
                decision=AccessDecision.ALLOWED,
                reason="no_policy_defined"
            )
            return True
        
        access_allowed = self._check_access(item, policy, context)
        
        self._log_access(
            entity_type=entity_type,
            count=1,
            context=context,
            action="read",
            entity_id=item.get("id"),
            decision=AccessDecision.ALLOWED if access_allowed else AccessDecision.DENIED,
            reason="policy_check_passed" if access_allowed else "policy_check_failed"
        )
        
        return access_allowed
    
    def _check_access(self, 
                      item: Dict[str, Any], 
                      policy: PermissionPolicy,
                      context: SessionContext) -> bool:
        """Internal access check logic.
        
        Args:
            item: Item to check
            policy: Permission policy to apply
            context: Session context
            
        Returns:
            True if access allowed
        """
        # Custom filter takes precedence
        if policy.custom_filter:
            return policy.custom_filter(item, context)
        
        # Check ownership
        owner = item.get(policy.owner_field)
        if owner == context.user_id:
            return True
        
        # Check scope
        try:
            user_scope = DataScope(context.data_scope)
        except ValueError:
            # Invalid scope defaults to most restrictive
            user_scope = DataScope.STATION
        
        item_scope_value = item.get(policy.scope_field)
        
        if user_scope == DataScope.COMPANY:
            return True
        elif user_scope == DataScope.REGION:
            # User can see items in their region
            return item_scope_value == context.identity.get("region")
        elif user_scope == DataScope.STATION:
            # User can only see items at their station
            return item_scope_value == context.station
        
        return False
    
    def _log_access(self, 
                    entity_type: str, 
                    count: int, 
                    context: SessionContext,
                    action: str = "read",
                    entity_id: Optional[str] = None,
                    decision: Optional[AccessDecision] = None,
                    reason: Optional[str] = None) -> None:
        """Log access decision for audit.
        
        Args:
            entity_type: Type of entity accessed
            count: Number of items requested
            context: Session context
            action: Type of action (read, write, delete)
            entity_id: Specific entity ID if applicable
            decision: Access decision outcome
            reason: Reason for the decision
        """
        if decision is None:
            decision = AccessDecision.OPEN_ACCESS if self._open_access_mode else AccessDecision.ALLOWED
        if reason is None:
            reason = "open_access_mode" if self._open_access_mode else "policy_check"
        
        entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            session_id=context.session_id,
            user_id=context.user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            decision=decision,
            reason=reason,
            metadata={
                "items_requested": count,
                "data_scope": context.data_scope,
            }
        )
        self._audit_log.append(entry)
        
        logger.info(
            f"RLS: user={context.user_id} entity={entity_type} "
            f"count={count} scope={context.data_scope} decision={decision.value}"
        )
    
    @property
    def audit_log(self) -> List[AuditLogEntry]:
        """Get audit log entries."""
        return self._audit_log.copy()
    
    @property
    def open_access_mode(self) -> bool:
        """Check if open access mode is enabled."""
        return self._open_access_mode
    
    def set_open_access_mode(self, enabled: bool) -> None:
        """Set open access mode.
        
        Args:
            enabled: Whether to enable open access mode
        """
        self._open_access_mode = enabled
