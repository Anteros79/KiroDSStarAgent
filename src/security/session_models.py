"""Data models for session management and row-level security.

This module defines the core data structures for session individualization
and row-level security, including session contexts, user attributes,
permission policies, and security configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List, Callable


class DataScope(Enum):
    """Data visibility scope levels."""
    STATION = "station"
    REGION = "region"
    COMPANY = "company"


class AccessDecision(Enum):
    """Access decision outcomes for audit logging."""
    ALLOWED = "allowed"
    DENIED = "denied"
    OPEN_ACCESS = "open_access"


class ProviderType(Enum):
    """Supported identity provider types."""
    LOCAL = "local"
    AZURE_AD = "azure_ad"
    AWS_IAM = "aws_iam"


@dataclass
class SessionContext:
    """Request-scoped session context - never stored in global state.
    
    Attributes:
        session_id: Unique cryptographically secure session identifier
        user_id: User identifier from identity provider
        identity: Full identity dictionary from provider
        permissions: Permission policy for this session
        data_scope: Data visibility scope (station, region, company)
        station: Optional station assignment
        created_at: Session creation timestamp
        expires_at: Session expiration timestamp
    """
    session_id: str
    user_id: str
    identity: Dict[str, Any]
    permissions: Dict[str, Any]
    data_scope: str  # "station", "region", "company"
    station: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


@dataclass
class UserAttributes:
    """Standardized user attributes from any identity provider.
    
    Attributes:
        user_id: Unique user identifier
        name: Display name
        email: Email address (optional)
        roles: List of assigned roles
        groups: List of group memberships
        station: Station assignment (optional)
        region: Region assignment (optional)
        custom_attributes: Additional provider-specific attributes
    """
    user_id: str
    name: str
    email: Optional[str]
    roles: List[str]
    groups: List[str]
    station: Optional[str]
    region: Optional[str]
    custom_attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PermissionPolicy:
    """Defines access rules for a data entity.
    
    Attributes:
        entity_type: Type of entity (e.g., "investigation", "kpi_data")
        allowed_scopes: List of allowed data scopes
        owner_field: Field name containing owner identifier
        scope_field: Field name containing scope identifier
        custom_filter: Optional custom filter function
    """
    entity_type: str
    allowed_scopes: List[DataScope]
    owner_field: str
    scope_field: str
    custom_filter: Optional[Callable[[Dict, "SessionContext"], bool]] = None


@dataclass
class SecurityConfig:
    """Security configuration settings.
    
    Attributes:
        open_access_mode: Whether to bypass RLS (default: True)
        session_ttl_hours: Session time-to-live in hours
        identity_provider: Identity provider type
        enable_audit_logging: Whether to log access decisions
        azure_ad_tenant_id: Azure AD tenant ID (for future use)
        azure_ad_client_id: Azure AD client ID (for future use)
        aws_region: AWS region (for future use)
        aws_role_arn: AWS role ARN (for future use)
    """
    open_access_mode: bool = True
    session_ttl_hours: int = 24
    identity_provider: str = "local"
    enable_audit_logging: bool = True
    
    # Azure AD settings (for future use)
    azure_ad_tenant_id: Optional[str] = None
    azure_ad_client_id: Optional[str] = None
    
    # AWS IAM settings (for future use)
    aws_region: Optional[str] = None
    aws_role_arn: Optional[str] = None


@dataclass
class AuditLogEntry:
    """Audit log entry for access decisions.
    
    Attributes:
        timestamp: When the access decision was made
        session_id: Session that made the request
        user_id: User that made the request
        action: Type of action (read, write, delete)
        entity_type: Type of entity accessed
        entity_id: ID of specific entity (optional)
        decision: Access decision outcome
        reason: Reason for the decision
        metadata: Additional context
    """
    timestamp: datetime
    session_id: str
    user_id: str
    action: str
    entity_type: str
    entity_id: Optional[str]
    decision: AccessDecision
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
