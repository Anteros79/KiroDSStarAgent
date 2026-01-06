"""Security audit, hardening, and session management module.

This module provides comprehensive security capabilities including:
- Hardcoded secrets detection
- Dependency vulnerability analysis
- API endpoint security auditing
- Security report generation
- Security annotation injection
- Main orchestrator for coordinating all scanning phases
- Session management and isolation
- Row-level security (RLS) engine
- Identity provider adapters
"""

from src.security.models import (
    Severity,
    FindingCategory,
    SecurityFinding,
    SecretFinding,
    DependencyFinding,
    APIFinding,
    AuditReport,
)

# Session management and RLS models
from src.security.session_models import (
    DataScope,
    AccessDecision,
    ProviderType,
    SessionContext,
    UserAttributes,
    PermissionPolicy,
    SecurityConfig,
    AuditLogEntry,
)

# Session manager
from src.security.session_manager import SessionManager

# Identity providers
from src.security.identity_provider import (
    IdentityProviderAdapter,
    LocalIdentityProvider,
    AzureADProvider,
    AWSIAMProvider,
)

# Row-level security engine
from src.security.rls_engine import RowLevelSecurityEngine
from src.security.secret_scanner import (
    SecretScanner,
    SECRET_PATTERNS,
    SECRET_SEVERITY,
    EXCLUDE_PATTERNS,
)
from src.security.dependency_analyzer import (
    DependencyAnalyzer,
    Dependency,
    CVERecord,
)
from src.security.api_auditor import (
    APIAuditor,
    APIEndpoint,
    ENDPOINT_PATTERNS,
    AUTHZ_INDICATORS,
    INJECTION_RISK_PATTERNS,
    OWASP_MAPPING,
)
from src.security.report_generator import (
    ReportGenerator,
    REMEDIATION_EFFORT,
)
from src.security.annotation_injector import (
    AnnotationInjector,
    AnnotationResult,
    AnnotationReport,
    COMMENT_PREFIXES,
    SECURITY_ANNOTATION,
    CRITICAL_ANNOTATION_CATEGORIES,
    get_annotatable_findings,
    format_annotation_report_markdown,
)
from src.security.security_scanner import (
    SecurityScanner,
)
from src.security.cli import (
    main as cli_main,
)

__all__ = [
    # Security audit models
    "Severity",
    "FindingCategory",
    "SecurityFinding",
    "SecretFinding",
    "DependencyFinding",
    "APIFinding",
    "AuditReport",
    # Session management models
    "DataScope",
    "AccessDecision",
    "ProviderType",
    "SessionContext",
    "UserAttributes",
    "PermissionPolicy",
    "SecurityConfig",
    "AuditLogEntry",
    # Session manager
    "SessionManager",
    # Identity providers
    "IdentityProviderAdapter",
    "LocalIdentityProvider",
    "AzureADProvider",
    "AWSIAMProvider",
    # RLS engine
    "RowLevelSecurityEngine",
    # Security scanning
    "SecretScanner",
    "SECRET_PATTERNS",
    "SECRET_SEVERITY",
    "EXCLUDE_PATTERNS",
    "DependencyAnalyzer",
    "Dependency",
    "CVERecord",
    "APIAuditor",
    "APIEndpoint",
    "ENDPOINT_PATTERNS",
    "AUTHZ_INDICATORS",
    "INJECTION_RISK_PATTERNS",
    "OWASP_MAPPING",
    "ReportGenerator",
    "REMEDIATION_EFFORT",
    "AnnotationInjector",
    "AnnotationResult",
    "AnnotationReport",
    "COMMENT_PREFIXES",
    "SECURITY_ANNOTATION",
    "CRITICAL_ANNOTATION_CATEGORIES",
    "get_annotatable_findings",
    "format_annotation_report_markdown",
    "SecurityScanner",
    "cli_main",
]
