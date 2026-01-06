"""Tests for the Dependency Analyzer module.

This module contains unit tests for dependency file parsing and CVE lookup
functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.security.dependency_analyzer import (
    DependencyAnalyzer,
    Dependency,
    cvss_to_severity,
    severity_string_to_enum,
)
from src.security.models import Severity, FindingCategory


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def analyzer(temp_project_dir):
    """Create a DependencyAnalyzer instance for testing."""
    return DependencyAnalyzer(str(temp_project_dir))


# ============================================================================
# Severity Conversion Tests
# ============================================================================

class TestSeverityConversion:
    """Tests for severity conversion functions."""
    
    def test_cvss_to_severity_critical(self):
        """CVSS >= 9.0 should map to CRITICAL."""
        assert cvss_to_severity(9.0) == Severity.CRITICAL
        assert cvss_to_severity(10.0) == Severity.CRITICAL
    
    def test_cvss_to_severity_high(self):
        """CVSS 7.0-8.9 should map to HIGH."""
        assert cvss_to_severity(7.0) == Severity.HIGH
        assert cvss_to_severity(8.9) == Severity.HIGH
    
    def test_cvss_to_severity_medium(self):
        """CVSS 4.0-6.9 should map to MEDIUM."""
        assert cvss_to_severity(4.0) == Severity.MEDIUM
        assert cvss_to_severity(6.9) == Severity.MEDIUM
    
    def test_cvss_to_severity_low(self):
        """CVSS 0.1-3.9 should map to LOW."""
        assert cvss_to_severity(0.1) == Severity.LOW
        assert cvss_to_severity(3.9) == Severity.LOW
    
    def test_cvss_to_severity_info(self):
        """CVSS 0.0 should map to INFO."""
        assert cvss_to_severity(0.0) == Severity.INFO
    
    def test_cvss_to_severity_none(self):
        """None CVSS should default to MEDIUM."""
        assert cvss_to_severity(None) == Severity.MEDIUM
    
    def test_severity_string_to_enum(self):
        """Test string to severity enum conversion."""
        assert severity_string_to_enum("critical") == Severity.CRITICAL
        assert severity_string_to_enum("high") == Severity.HIGH
        assert severity_string_to_enum("moderate") == Severity.MEDIUM
        assert severity_string_to_enum("medium") == Severity.MEDIUM
        assert severity_string_to_enum("low") == Severity.LOW
        assert severity_string_to_enum("info") == Severity.INFO
        assert severity_string_to_enum("unknown") == Severity.MEDIUM


# ============================================================================
# Requirements.txt Parser Tests
# ============================================================================

class TestRequirementsTxtParser:
    """Tests for requirements.txt parsing."""
    
    def test_parse_simple_requirements(self, temp_project_dir, analyzer):
        """Test parsing simple requirements with exact versions."""
        req_file = temp_project_dir / "requirements.txt"
        req_file.write_text("requests==2.28.0\nflask==2.0.1\n")
        
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert len(deps) == 2
        assert deps[0].name == "requests"
        assert deps[0].version == "2.28.0"
        assert deps[1].name == "flask"
        assert deps[1].version == "2.0.1"
    
    def test_parse_requirements_with_operators(self, temp_project_dir, analyzer):
        """Test parsing requirements with various version operators."""
        req_file = temp_project_dir / "requirements.txt"
        req_file.write_text("requests>=2.28.0\nflask~=2.0.1\ndjango<=4.0\n")
        
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert len(deps) == 3
        assert deps[0].name == "requests"
        assert deps[0].version == "2.28.0"
        assert deps[1].name == "flask"
        assert deps[1].version == "2.0.1"
        assert deps[2].name == "django"
        assert deps[2].version == "4.0"
    
    def test_parse_requirements_with_extras(self, temp_project_dir, analyzer):
        """Test parsing requirements with extras."""
        req_file = temp_project_dir / "requirements.txt"
        req_file.write_text("uvicorn[standard]==0.20.0\ncelery[redis]==5.2.0\n")
        
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert len(deps) == 2
        assert deps[0].name == "uvicorn"
        assert deps[0].version == "0.20.0"
        assert deps[1].name == "celery"
        assert deps[1].version == "5.2.0"
    
    def test_parse_requirements_without_version(self, temp_project_dir, analyzer):
        """Test parsing requirements without version specifiers."""
        req_file = temp_project_dir / "requirements.txt"
        req_file.write_text("requests\nflask\n")
        
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert len(deps) == 2
        assert deps[0].name == "requests"
        assert deps[0].version == ""
        assert deps[1].name == "flask"
        assert deps[1].version == ""
    
    def test_parse_requirements_with_comments(self, temp_project_dir, analyzer):
        """Test parsing requirements with comments."""
        req_file = temp_project_dir / "requirements.txt"
        req_file.write_text("# This is a comment\nrequests==2.28.0\n# Another comment\nflask==2.0.1\n")
        
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert len(deps) == 2
        assert deps[0].name == "requests"
        assert deps[1].name == "flask"
    
    def test_parse_requirements_with_inline_comments(self, temp_project_dir, analyzer):
        """Test parsing requirements with inline comments."""
        req_file = temp_project_dir / "requirements.txt"
        req_file.write_text("requests==2.28.0  # HTTP library\nflask==2.0.1  # Web framework\n")
        
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert len(deps) == 2
        assert deps[0].name == "requests"
        assert deps[0].version == "2.28.0"
    
    def test_parse_requirements_skip_flags(self, temp_project_dir, analyzer):
        """Test that -r, -e, and other flags are skipped."""
        req_file = temp_project_dir / "requirements.txt"
        req_file.write_text("-r base.txt\n-e git+https://github.com/user/repo.git\nrequests==2.28.0\n")
        
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert len(deps) == 1
        assert deps[0].name == "requests"
    
    def test_parse_missing_requirements_file(self, temp_project_dir, analyzer):
        """Test handling of missing requirements.txt file."""
        deps = analyzer.parse_requirements_txt(temp_project_dir / "nonexistent.txt")
        
        assert len(deps) == 0
        assert len(analyzer.warnings) == 1
        assert "not found" in analyzer.warnings[0]


# ============================================================================
# Package.json Parser Tests
# ============================================================================

class TestPackageJsonParser:
    """Tests for package.json parsing."""
    
    def test_parse_simple_package_json(self, temp_project_dir, analyzer):
        """Test parsing simple package.json with dependencies."""
        pkg_file = temp_project_dir / "package.json"
        pkg_file.write_text(json.dumps({
            "name": "test-project",
            "dependencies": {
                "react": "^18.2.0",
                "lodash": "~4.17.21"
            }
        }))
        
        deps = analyzer.parse_package_json(pkg_file)
        
        assert len(deps) == 2
        assert deps[0].name == "react"
        assert deps[0].version == "18.2.0"
        assert deps[1].name == "lodash"
        assert deps[1].version == "4.17.21"
    
    def test_parse_package_json_with_dev_dependencies(self, temp_project_dir, analyzer):
        """Test parsing package.json with devDependencies."""
        pkg_file = temp_project_dir / "package.json"
        pkg_file.write_text(json.dumps({
            "name": "test-project",
            "dependencies": {
                "react": "^18.2.0"
            },
            "devDependencies": {
                "typescript": "^5.0.0",
                "jest": "^29.0.0"
            }
        }))
        
        deps = analyzer.parse_package_json(pkg_file)
        
        assert len(deps) == 3
        names = [d.name for d in deps]
        assert "react" in names
        assert "typescript" in names
        assert "jest" in names
    
    def test_parse_package_json_exact_versions(self, temp_project_dir, analyzer):
        """Test parsing package.json with exact versions."""
        pkg_file = temp_project_dir / "package.json"
        pkg_file.write_text(json.dumps({
            "name": "test-project",
            "dependencies": {
                "express": "4.18.2"
            }
        }))
        
        deps = analyzer.parse_package_json(pkg_file)
        
        assert len(deps) == 1
        assert deps[0].name == "express"
        assert deps[0].version == "4.18.2"
    
    def test_parse_package_json_range_versions(self, temp_project_dir, analyzer):
        """Test parsing package.json with range versions."""
        pkg_file = temp_project_dir / "package.json"
        pkg_file.write_text(json.dumps({
            "name": "test-project",
            "dependencies": {
                "package1": ">=1.0.0",
                "package2": "<=2.0.0",
                "package3": ">3.0.0"
            }
        }))
        
        deps = analyzer.parse_package_json(pkg_file)
        
        assert len(deps) == 3
        assert deps[0].version == "1.0.0"
        assert deps[1].version == "2.0.0"
        assert deps[2].version == "3.0.0"
    
    def test_parse_package_json_star_version(self, temp_project_dir, analyzer):
        """Test parsing package.json with * version."""
        pkg_file = temp_project_dir / "package.json"
        pkg_file.write_text(json.dumps({
            "name": "test-project",
            "dependencies": {
                "any-package": "*"
            }
        }))
        
        deps = analyzer.parse_package_json(pkg_file)
        
        assert len(deps) == 1
        assert deps[0].version == "latest"
    
    def test_parse_missing_package_json(self, temp_project_dir, analyzer):
        """Test handling of missing package.json file."""
        deps = analyzer.parse_package_json(temp_project_dir / "nonexistent.json")
        
        assert len(deps) == 0
        assert len(analyzer.warnings) == 1
        assert "not found" in analyzer.warnings[0]
    
    def test_parse_malformed_package_json(self, temp_project_dir, analyzer):
        """Test handling of malformed package.json file."""
        pkg_file = temp_project_dir / "package.json"
        pkg_file.write_text("{ invalid json }")
        
        deps = analyzer.parse_package_json(pkg_file)
        
        assert len(deps) == 0
        assert len(analyzer.warnings) == 1
        assert "Malformed" in analyzer.warnings[0]
    
    def test_parse_package_json_no_dependencies(self, temp_project_dir, analyzer):
        """Test parsing package.json with no dependencies."""
        pkg_file = temp_project_dir / "package.json"
        pkg_file.write_text(json.dumps({
            "name": "test-project",
            "version": "1.0.0"
        }))
        
        deps = analyzer.parse_package_json(pkg_file)
        
        assert len(deps) == 0


# ============================================================================
# Find Dependency Files Tests
# ============================================================================

class TestFindDependencyFiles:
    """Tests for finding dependency files in repository."""
    
    def test_find_root_dependency_files(self, temp_project_dir, analyzer):
        """Test finding dependency files in root directory."""
        (temp_project_dir / "requirements.txt").write_text("requests==2.28.0\n")
        (temp_project_dir / "package.json").write_text('{"name": "test"}')
        
        files = analyzer.find_dependency_files()
        
        assert len(files["requirements.txt"]) == 1
        assert len(files["package.json"]) == 1
    
    def test_find_nested_dependency_files(self, temp_project_dir, analyzer):
        """Test finding dependency files in nested directories."""
        # Create nested structure
        (temp_project_dir / "backend").mkdir()
        (temp_project_dir / "frontend").mkdir()
        
        (temp_project_dir / "backend" / "requirements.txt").write_text("flask==2.0.1\n")
        (temp_project_dir / "frontend" / "package.json").write_text('{"name": "frontend"}')
        
        files = analyzer.find_dependency_files()
        
        assert len(files["requirements.txt"]) == 1
        assert len(files["package.json"]) == 1
    
    def test_skip_node_modules(self, temp_project_dir, analyzer):
        """Test that node_modules directory is skipped."""
        (temp_project_dir / "node_modules").mkdir()
        (temp_project_dir / "node_modules" / "package.json").write_text('{"name": "dep"}')
        (temp_project_dir / "package.json").write_text('{"name": "root"}')
        
        files = analyzer.find_dependency_files()
        
        assert len(files["package.json"]) == 1
        assert "node_modules" not in str(files["package.json"][0])


# ============================================================================
# Parse All Dependencies Tests
# ============================================================================

class TestParseAllDependencies:
    """Tests for parsing all dependencies."""
    
    def test_parse_all_dependencies(self, temp_project_dir, analyzer):
        """Test parsing all dependency files."""
        (temp_project_dir / "requirements.txt").write_text("requests==2.28.0\nflask==2.0.1\n")
        (temp_project_dir / "package.json").write_text(json.dumps({
            "name": "test",
            "dependencies": {"react": "^18.2.0"}
        }))
        
        deps = analyzer.parse_all_dependencies()
        
        assert len(deps) == 3
        names = [d.name for d in deps]
        assert "requests" in names
        assert "flask" in names
        assert "react" in names
    
    def test_parse_all_no_files(self, temp_project_dir, analyzer):
        """Test parsing when no dependency files exist."""
        deps = analyzer.parse_all_dependencies()
        
        assert len(deps) == 0
        assert len(analyzer.warnings) >= 1


# ============================================================================
# CVE Lookup Tests (Mocked)
# ============================================================================

class TestCVELookup:
    """Tests for CVE lookup functionality."""
    
    def test_check_python_cves_pip_audit_not_installed(self, temp_project_dir, analyzer):
        """Test handling when pip-audit is not installed."""
        deps = [Dependency("requests", "2.28.0", "requirements.txt")]
        
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            findings = analyzer.check_python_cves(deps)
        
        assert len(findings) == 0
        assert any("pip-audit not installed" in w for w in analyzer.warnings)
    
    def test_check_python_cves_with_vulnerabilities(self, temp_project_dir, analyzer):
        """Test parsing pip-audit output with vulnerabilities."""
        deps = [Dependency("requests", "2.25.0", "requirements.txt")]
        
        mock_output = json.dumps([{
            "name": "requests",
            "version": "2.25.0",
            "vulns": [{
                "id": "CVE-2023-12345",
                "description": "Test vulnerability",
                "fix_versions": ["2.28.0"]
            }]
        }])
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            findings = analyzer.check_python_cves(deps)
        
        assert len(findings) == 1
        assert findings[0].package_name == "requests"
        assert findings[0].cve_id == "CVE-2023-12345"
        assert findings[0].safe_version == "2.28.0"
        assert findings[0].category == FindingCategory.VULNERABLE_DEPENDENCY
    
    def test_check_npm_cves_npm_not_installed(self, temp_project_dir, analyzer):
        """Test handling when npm is not installed."""
        # Create package.json and node_modules
        (temp_project_dir / "package.json").write_text('{"name": "test"}')
        (temp_project_dir / "node_modules").mkdir()
        
        deps = [Dependency("lodash", "4.17.0", str(temp_project_dir / "package.json"))]
        
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            findings = analyzer.check_npm_cves(deps)
        
        assert len(findings) == 0
        assert any("npm not installed" in w for w in analyzer.warnings)
    
    def test_check_npm_cves_no_node_modules(self, temp_project_dir, analyzer):
        """Test handling when node_modules doesn't exist."""
        (temp_project_dir / "package.json").write_text('{"name": "test"}')
        
        deps = [Dependency("lodash", "4.17.0", str(temp_project_dir / "package.json"))]
        
        findings = analyzer.check_npm_cves(deps)
        
        assert len(findings) == 0
        assert any("node_modules not found" in w for w in analyzer.warnings)


# ============================================================================
# Summary Tests
# ============================================================================

class TestSummary:
    """Tests for summary generation."""
    
    def test_get_summary(self, temp_project_dir, analyzer):
        """Test summary generation."""
        deps = [
            Dependency("requests", "2.28.0", "requirements.txt"),
            Dependency("flask", "2.0.1", "requirements.txt"),
            Dependency("react", "18.2.0", "package.json"),
        ]
        
        from src.security.models import DependencyFinding, FindingCategory, Severity
        
        findings = [
            DependencyFinding(
                id="DEP-001",
                category=FindingCategory.VULNERABLE_DEPENDENCY,
                severity=Severity.HIGH,
                file_path="requirements.txt",
                description="Test",
                evidence="Test",
                remediation="Test",
                package_name="requests",
                current_version="2.28.0",
            ),
            DependencyFinding(
                id="DEP-002",
                category=FindingCategory.VULNERABLE_DEPENDENCY,
                severity=Severity.CRITICAL,
                file_path="requirements.txt",
                description="Test",
                evidence="Test",
                remediation="Test",
                package_name="flask",
                current_version="2.0.1",
            ),
        ]
        
        summary = analyzer.get_summary(deps, findings)
        
        assert summary["total_dependencies"] == 3
        assert summary["total_vulnerabilities"] == 2
        assert summary["python_dependencies"] == 2
        assert summary["node_dependencies"] == 1
        assert summary["by_severity"]["High"] == 1
        assert summary["by_severity"]["Critical"] == 1
