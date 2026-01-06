"""Data models for security audit findings.

This module defines the core data structures used throughout the security
audit system, including severity levels, finding categories, and various
finding types for secrets, dependencies, and API vulnerabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class Severity(Enum):
    """Severity levels for security findings, ordered from most to least severe."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"
    
    def __lt__(self, other: "Severity") -> bool:
        """Enable comparison for sorting (Critical < High means Critical comes first)."""
        order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
        return order.index(self) < order.index(other)
    
    def __le__(self, other: "Severity") -> bool:
        return self == other or self < other


class FindingCategory(Enum):
    """Categories of security findings."""
    HARDCODED_SECRET = "Hardcoded Secret"
    VULNERABLE_DEPENDENCY = "Vulnerable Dependency"
    MISSING_AUTHZ = "Missing Authorization"
    INJECTION_RISK = "Injection Risk"
    INSECURE_CONFIG = "Insecure Configuration"


@dataclass
class SecurityFinding:
    """Base class for all security findings.
    
    Attributes:
        id: Unique identifier for the finding (e.g., "SEC-001")
        category: The category of security issue
        severity: The severity level of the finding
        file_path: Path to the file containing the vulnerability
        line_number: Line number where the issue was found (optional)
        description: Human-readable description of the issue
        evidence: Redacted/masked evidence of the vulnerability
        remediation: Recommended steps to fix the issue
        owasp_category: OWASP Top 10 category if applicable
        cve_id: CVE identifier if applicable
    """
    id: str
    category: FindingCategory
    severity: Severity
    file_path: str
    description: str
    evidence: str
    remediation: str
    line_number: Optional[int] = None
    owasp_category: Optional[str] = None
    cve_id: Optional[str] = None


@dataclass
class SecretFinding(SecurityFinding):
    """Finding for hardcoded secrets detected in source code.
    
    Attributes:
        secret_type: Type of secret (e.g., "api_key", "aws_credentials")
        masked_value: The secret value with sensitive parts masked
    """
    secret_type: str = ""
    masked_value: str = ""
    
    def __post_init__(self):
        """Ensure category is set correctly for secret findings."""
        if self.category != FindingCategory.HARDCODED_SECRET:
            self.category = FindingCategory.HARDCODED_SECRET


@dataclass
class DependencyFinding(SecurityFinding):
    """Finding for vulnerable dependencies.
    
    Attributes:
        package_name: Name of the vulnerable package
        current_version: Currently installed version
        safe_version: Recommended safe version to upgrade to
        cvss_score: CVSS severity score (0.0-10.0)
    """
    package_name: str = ""
    current_version: str = ""
    safe_version: Optional[str] = None
    cvss_score: Optional[float] = None
    
    def __post_init__(self):
        """Ensure category is set correctly for dependency findings."""
        if self.category != FindingCategory.VULNERABLE_DEPENDENCY:
            self.category = FindingCategory.VULNERABLE_DEPENDENCY


@dataclass
class APIFinding(SecurityFinding):
    """Finding for API endpoint security issues.
    
    Attributes:
        endpoint_path: The API endpoint path (e.g., "/api/users")
        http_method: HTTP method (GET, POST, PUT, DELETE, etc.)
        vulnerability_type: Type of vulnerability (e.g., "missing_auth", "injection")
    """
    endpoint_path: str = ""
    http_method: str = ""
    vulnerability_type: str = ""


@dataclass
class AuditReport:
    """Complete security audit report.
    
    Attributes:
        scan_timestamp: ISO format timestamp of when the scan was performed
        total_findings: Total number of findings across all categories
        critical_count: Number of critical severity findings
        high_count: Number of high severity findings
        medium_count: Number of medium severity findings
        low_count: Number of low severity findings
        findings: List of all security findings
        annotations_added: List of file paths where annotations were added
    """
    scan_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    findings: List[SecurityFinding] = field(default_factory=list)
    annotations_added: List[str] = field(default_factory=list)
    
    def add_finding(self, finding: SecurityFinding) -> None:
        """Add a finding and update counts."""
        self.findings.append(finding)
        self.total_findings += 1
        
        if finding.severity == Severity.CRITICAL:
            self.critical_count += 1
        elif finding.severity == Severity.HIGH:
            self.high_count += 1
        elif finding.severity == Severity.MEDIUM:
            self.medium_count += 1
        elif finding.severity == Severity.LOW:
            self.low_count += 1
    
    def get_findings_by_severity(self) -> List[SecurityFinding]:
        """Return findings sorted by severity (Critical first)."""
        return sorted(self.findings, key=lambda f: f.severity)
    
    def get_findings_by_category(self, category: FindingCategory) -> List[SecurityFinding]:
        """Return findings filtered by category."""
        return [f for f in self.findings if f.category == category]
