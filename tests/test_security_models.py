"""Tests for security audit data models.

This module contains unit tests and property-based tests for the security
audit data models using pytest and hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings

from src.security.models import (
    Severity,
    FindingCategory,
    SecurityFinding,
    SecretFinding,
    DependencyFinding,
    APIFinding,
    AuditReport,
)


# ============================================================================
# Hypothesis Strategies for generating test data
# ============================================================================

severity_strategy = st.sampled_from(list(Severity))
category_strategy = st.sampled_from(list(FindingCategory))

finding_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"),
    min_size=1,
    max_size=20
).filter(lambda x: len(x.strip()) > 0)

file_path_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="/_-."),
    min_size=1,
    max_size=100
).filter(lambda x: len(x.strip()) > 0)

description_strategy = st.text(min_size=1, max_size=500).filter(lambda x: len(x.strip()) > 0)


def security_finding_strategy():
    """Strategy for generating SecurityFinding instances."""
    return st.builds(
        SecurityFinding,
        id=finding_id_strategy,
        category=category_strategy,
        severity=severity_strategy,
        file_path=file_path_strategy,
        description=description_strategy,
        evidence=st.text(min_size=0, max_size=200),
        remediation=description_strategy,
        line_number=st.one_of(st.none(), st.integers(min_value=1, max_value=10000)),
        owasp_category=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        cve_id=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    )


# ============================================================================
# Unit Tests for Severity
# ============================================================================

class TestSeverity:
    """Unit tests for Severity enum."""
    
    def test_severity_values(self):
        """Test that all severity levels have correct string values."""
        assert Severity.CRITICAL.value == "Critical"
        assert Severity.HIGH.value == "High"
        assert Severity.MEDIUM.value == "Medium"
        assert Severity.LOW.value == "Low"
        assert Severity.INFO.value == "Info"
    
    def test_severity_ordering(self):
        """Test that severity levels are ordered correctly."""
        assert Severity.CRITICAL < Severity.HIGH
        assert Severity.HIGH < Severity.MEDIUM
        assert Severity.MEDIUM < Severity.LOW
        assert Severity.LOW < Severity.INFO
    
    def test_severity_equality(self):
        """Test severity equality comparison."""
        assert Severity.CRITICAL <= Severity.CRITICAL
        assert Severity.HIGH <= Severity.HIGH


# ============================================================================
# Unit Tests for FindingCategory
# ============================================================================

class TestFindingCategory:
    """Unit tests for FindingCategory enum."""
    
    def test_category_values(self):
        """Test that all categories have correct string values."""
        assert FindingCategory.HARDCODED_SECRET.value == "Hardcoded Secret"
        assert FindingCategory.VULNERABLE_DEPENDENCY.value == "Vulnerable Dependency"
        assert FindingCategory.MISSING_AUTHZ.value == "Missing Authorization"
        assert FindingCategory.INJECTION_RISK.value == "Injection Risk"
        assert FindingCategory.INSECURE_CONFIG.value == "Insecure Configuration"


# ============================================================================
# Unit Tests for SecurityFinding
# ============================================================================

class TestSecurityFinding:
    """Unit tests for SecurityFinding dataclass."""
    
    def test_create_basic_finding(self):
        """Test creating a basic security finding."""
        finding = SecurityFinding(
            id="SEC-001",
            category=FindingCategory.HARDCODED_SECRET,
            severity=Severity.CRITICAL,
            file_path="src/config.py",
            description="Hardcoded API key detected",
            evidence="api_key = 'sk-****...xy'",
            remediation="Move API key to environment variable",
            line_number=42,
        )
        
        assert finding.id == "SEC-001"
        assert finding.category == FindingCategory.HARDCODED_SECRET
        assert finding.severity == Severity.CRITICAL
        assert finding.file_path == "src/config.py"
        assert finding.line_number == 42
    
    def test_finding_optional_fields(self):
        """Test that optional fields default to None."""
        finding = SecurityFinding(
            id="SEC-002",
            category=FindingCategory.INJECTION_RISK,
            severity=Severity.HIGH,
            file_path="src/api.py",
            description="SQL injection risk",
            evidence="query = f'SELECT * FROM {table}'",
            remediation="Use parameterized queries",
        )
        
        assert finding.line_number is None
        assert finding.owasp_category is None
        assert finding.cve_id is None


# ============================================================================
# Unit Tests for SecretFinding
# ============================================================================

class TestSecretFinding:
    """Unit tests for SecretFinding dataclass."""
    
    def test_create_secret_finding(self):
        """Test creating a secret finding."""
        finding = SecretFinding(
            id="SEC-003",
            category=FindingCategory.HARDCODED_SECRET,
            severity=Severity.CRITICAL,
            file_path="src/config.py",
            description="AWS access key detected",
            evidence="AKIA****...XY",
            remediation="Use AWS Secrets Manager",
            secret_type="aws_credentials",
            masked_value="AKIA****...XY",
        )
        
        assert finding.secret_type == "aws_credentials"
        assert finding.masked_value == "AKIA****...XY"
        assert finding.category == FindingCategory.HARDCODED_SECRET


# ============================================================================
# Unit Tests for DependencyFinding
# ============================================================================

class TestDependencyFinding:
    """Unit tests for DependencyFinding dataclass."""
    
    def test_create_dependency_finding(self):
        """Test creating a dependency finding."""
        finding = DependencyFinding(
            id="DEP-001",
            category=FindingCategory.VULNERABLE_DEPENDENCY,
            severity=Severity.HIGH,
            file_path="requirements.txt",
            description="Vulnerable package detected",
            evidence="requests==2.25.0",
            remediation="Upgrade to requests>=2.31.0",
            package_name="requests",
            current_version="2.25.0",
            safe_version="2.31.0",
            cvss_score=7.5,
            cve_id="CVE-2023-32681",
        )
        
        assert finding.package_name == "requests"
        assert finding.current_version == "2.25.0"
        assert finding.safe_version == "2.31.0"
        assert finding.cvss_score == 7.5
        assert finding.cve_id == "CVE-2023-32681"


# ============================================================================
# Unit Tests for APIFinding
# ============================================================================

class TestAPIFinding:
    """Unit tests for APIFinding dataclass."""
    
    def test_create_api_finding(self):
        """Test creating an API finding."""
        finding = APIFinding(
            id="API-001",
            category=FindingCategory.MISSING_AUTHZ,
            severity=Severity.HIGH,
            file_path="src/api/server.py",
            description="Endpoint missing authorization",
            evidence="@app.get('/admin/users')",
            remediation="Add authentication middleware",
            endpoint_path="/admin/users",
            http_method="GET",
            vulnerability_type="missing_auth",
            owasp_category="A01:2021-Broken Access Control",
        )
        
        assert finding.endpoint_path == "/admin/users"
        assert finding.http_method == "GET"
        assert finding.vulnerability_type == "missing_auth"
        assert finding.owasp_category == "A01:2021-Broken Access Control"


# ============================================================================
# Unit Tests for AuditReport
# ============================================================================

class TestAuditReport:
    """Unit tests for AuditReport dataclass."""
    
    def test_create_empty_report(self):
        """Test creating an empty audit report."""
        report = AuditReport()
        
        assert report.total_findings == 0
        assert report.critical_count == 0
        assert report.high_count == 0
        assert report.medium_count == 0
        assert report.low_count == 0
        assert len(report.findings) == 0
        assert len(report.annotations_added) == 0
    
    def test_add_finding_updates_counts(self):
        """Test that adding findings updates the counts correctly."""
        report = AuditReport()
        
        critical_finding = SecurityFinding(
            id="SEC-001",
            category=FindingCategory.HARDCODED_SECRET,
            severity=Severity.CRITICAL,
            file_path="test.py",
            description="Test",
            evidence="test",
            remediation="test",
        )
        
        high_finding = SecurityFinding(
            id="SEC-002",
            category=FindingCategory.INJECTION_RISK,
            severity=Severity.HIGH,
            file_path="test.py",
            description="Test",
            evidence="test",
            remediation="test",
        )
        
        report.add_finding(critical_finding)
        report.add_finding(high_finding)
        
        assert report.total_findings == 2
        assert report.critical_count == 1
        assert report.high_count == 1
    
    def test_get_findings_by_severity(self):
        """Test sorting findings by severity."""
        report = AuditReport()
        
        # Add findings in random order
        report.add_finding(SecurityFinding(
            id="SEC-001", category=FindingCategory.HARDCODED_SECRET,
            severity=Severity.LOW, file_path="a.py",
            description="Low", evidence="", remediation=""
        ))
        report.add_finding(SecurityFinding(
            id="SEC-002", category=FindingCategory.HARDCODED_SECRET,
            severity=Severity.CRITICAL, file_path="b.py",
            description="Critical", evidence="", remediation=""
        ))
        report.add_finding(SecurityFinding(
            id="SEC-003", category=FindingCategory.HARDCODED_SECRET,
            severity=Severity.HIGH, file_path="c.py",
            description="High", evidence="", remediation=""
        ))
        
        sorted_findings = report.get_findings_by_severity()
        
        assert sorted_findings[0].severity == Severity.CRITICAL
        assert sorted_findings[1].severity == Severity.HIGH
        assert sorted_findings[2].severity == Severity.LOW
    
    def test_get_findings_by_category(self):
        """Test filtering findings by category."""
        report = AuditReport()
        
        report.add_finding(SecurityFinding(
            id="SEC-001", category=FindingCategory.HARDCODED_SECRET,
            severity=Severity.HIGH, file_path="a.py",
            description="Secret", evidence="", remediation=""
        ))
        report.add_finding(SecurityFinding(
            id="SEC-002", category=FindingCategory.INJECTION_RISK,
            severity=Severity.HIGH, file_path="b.py",
            description="Injection", evidence="", remediation=""
        ))
        report.add_finding(SecurityFinding(
            id="SEC-003", category=FindingCategory.HARDCODED_SECRET,
            severity=Severity.MEDIUM, file_path="c.py",
            description="Secret 2", evidence="", remediation=""
        ))
        
        secret_findings = report.get_findings_by_category(FindingCategory.HARDCODED_SECRET)
        
        assert len(secret_findings) == 2
        assert all(f.category == FindingCategory.HARDCODED_SECRET for f in secret_findings)


# ============================================================================
# Property-Based Tests
# ============================================================================

class TestAuditReportProperties:
    """Property-based tests for AuditReport."""
    
    @given(st.lists(severity_strategy, min_size=0, max_size=50))
    @settings(max_examples=100)
    def test_severity_counts_match_total(self, severities):
        """
        Property: The sum of severity counts should equal total_findings.
        Feature: security-audit-hardening, Property 3: Summary Count Accuracy
        Validates: Requirements 1.3
        """
        report = AuditReport()
        
        for i, severity in enumerate(severities):
            finding = SecurityFinding(
                id=f"SEC-{i:03d}",
                category=FindingCategory.HARDCODED_SECRET,
                severity=severity,
                file_path=f"file_{i}.py",
                description="Test finding",
                evidence="test",
                remediation="test",
            )
            report.add_finding(finding)
        
        # Property: sum of counts equals total
        count_sum = (
            report.critical_count +
            report.high_count +
            report.medium_count +
            report.low_count
        )
        # Note: INFO severity is not counted in the individual counts
        info_count = sum(1 for s in severities if s == Severity.INFO)
        
        assert count_sum + info_count == report.total_findings
        assert report.total_findings == len(severities)
    
    @given(st.lists(severity_strategy, min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_sorted_findings_maintain_severity_order(self, severities):
        """
        Property: Sorted findings should be in descending severity order.
        Feature: security-audit-hardening, Property 8: Findings Severity Ordering
        Validates: Requirements 4.5
        """
        report = AuditReport()
        
        for i, severity in enumerate(severities):
            finding = SecurityFinding(
                id=f"SEC-{i:03d}",
                category=FindingCategory.HARDCODED_SECRET,
                severity=severity,
                file_path=f"file_{i}.py",
                description="Test finding",
                evidence="test",
                remediation="test",
            )
            report.add_finding(finding)
        
        sorted_findings = report.get_findings_by_severity()
        
        # Property: each finding's severity should be <= the next finding's severity
        for i in range(len(sorted_findings) - 1):
            assert sorted_findings[i].severity <= sorted_findings[i + 1].severity
