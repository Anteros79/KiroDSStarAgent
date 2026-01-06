"""Tests for the Secret Scanner module.

This module contains unit tests for the secret scanner functionality
including pattern matching, file traversal, and secret masking.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.security.secret_scanner import (
    SecretScanner,
    SECRET_PATTERNS,
    SECRET_SEVERITY,
    EXCLUDE_PATTERNS,
)
from src.security.models import Severity, FindingCategory


class TestSecretMasking:
    """Unit tests for secret masking functionality."""
    
    def test_mask_long_secret(self):
        """Test masking a secret longer than 8 characters."""
        scanner = SecretScanner(".")
        result = scanner.mask_secret("sk-1234567890abcdef")
        assert result == "sk-1...ef"
        assert "1234567890abcd" not in result
    
    def test_mask_short_secret(self):
        """Test masking a secret 8 characters or shorter."""
        scanner = SecretScanner(".")
        result = scanner.mask_secret("short")
        assert result == "*****"
        assert "short" not in result
    
    def test_mask_exactly_8_chars(self):
        """Test masking a secret exactly 8 characters."""
        scanner = SecretScanner(".")
        result = scanner.mask_secret("12345678")
        assert result == "********"
    
    def test_mask_empty_secret(self):
        """Test masking an empty secret."""
        scanner = SecretScanner(".")
        result = scanner.mask_secret("")
        assert result == "****"
    
    def test_mask_9_char_secret(self):
        """Test masking a 9 character secret (boundary case)."""
        scanner = SecretScanner(".")
        result = scanner.mask_secret("123456789")
        assert result == "1234...89"


class TestExclusionPatterns:
    """Unit tests for file exclusion patterns."""
    
    def test_exclude_git_directory(self):
        """Test that .git directory is excluded."""
        scanner = SecretScanner(".")
        assert scanner._should_exclude_path(".git/config")
        assert scanner._should_exclude_path(".git/objects/abc")
    
    def test_exclude_node_modules(self):
        """Test that node_modules is excluded."""
        scanner = SecretScanner(".")
        assert scanner._should_exclude_path("node_modules/package/index.js")
    
    def test_exclude_venv(self):
        """Test that virtual environment directories are excluded."""
        scanner = SecretScanner(".")
        assert scanner._should_exclude_path(".venv/lib/python3.10/site.py")
        assert scanner._should_exclude_path("venv/bin/activate")
    
    def test_exclude_pycache(self):
        """Test that __pycache__ is excluded."""
        scanner = SecretScanner(".")
        assert scanner._should_exclude_path("src/__pycache__/module.cpython-310.pyc")
    
    def test_exclude_binary_extensions(self):
        """Test that binary file extensions are excluded."""
        scanner = SecretScanner(".")
        assert scanner._should_exclude_path("image.png")
        assert scanner._should_exclude_path("font.woff2")
        assert scanner._should_exclude_path("archive.zip")
    
    def test_include_source_files(self):
        """Test that source files are not excluded."""
        scanner = SecretScanner(".")
        assert not scanner._should_exclude_path("src/main.py")
        assert not scanner._should_exclude_path("src/api/server.py")
        assert not scanner._should_exclude_path("config.json")


class TestPatternMatching:
    """Unit tests for secret pattern matching."""
    
    def test_detect_api_key(self):
        """Test detection of API key patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            test_file.write_text('API_KEY = "sk-1234567890abcdefghij"\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_file(test_file)
            
            assert len(findings) >= 1
            assert any(f.secret_type == "api_key" for f in findings)
    
    def test_detect_aws_access_key(self):
        """Test detection of AWS access key patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            test_file.write_text('AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_file(test_file)
            
            assert len(findings) >= 1
            assert any(f.secret_type == "aws_credentials" for f in findings)
    
    def test_detect_generic_password(self):
        """Test detection of generic password patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            test_file.write_text('password = "supersecretpassword123"\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_file(test_file)
            
            assert len(findings) >= 1
            assert any(f.secret_type == "generic_secret" for f in findings)
    
    def test_detect_jwt_token(self):
        """Test detection of JWT token patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            # Valid JWT format: header.payload.signature
            jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
            test_file.write_text(f'token = "{jwt}"\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_file(test_file)
            
            assert len(findings) >= 1
            assert any(f.secret_type == "jwt_token" for f in findings)
    
    def test_detect_private_key(self):
        """Test detection of private key patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "key.py"
            test_file.write_text('key = """-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----"""\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_file(test_file)
            
            assert len(findings) >= 1
            assert any(f.secret_type == "private_key" for f in findings)
    
    def test_detect_connection_string(self):
        """Test detection of database connection string patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            test_file.write_text('DATABASE_URL = "postgresql://user:pass@localhost:5432/db"\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_file(test_file)
            
            assert len(findings) >= 1
            assert any(f.secret_type == "connection_string" for f in findings)
    
    def test_no_false_positive_on_clean_file(self):
        """Test that clean files don't produce false positives."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "clean.py"
            test_file.write_text('def hello():\n    print("Hello, World!")\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_file(test_file)
            
            assert len(findings) == 0


class TestSecretFindingStructure:
    """Unit tests for SecretFinding structure."""
    
    def test_finding_has_required_fields(self):
        """Test that findings have all required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            test_file.write_text('API_KEY = "sk-1234567890abcdefghij"\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_file(test_file)
            
            assert len(findings) >= 1
            finding = findings[0]
            
            assert finding.id is not None
            assert finding.category == FindingCategory.HARDCODED_SECRET
            assert finding.severity is not None
            assert finding.file_path is not None
            assert finding.line_number is not None
            assert finding.description is not None
            assert finding.evidence is not None
            assert finding.remediation is not None
            assert finding.secret_type is not None
            assert finding.masked_value is not None
    
    def test_finding_does_not_expose_secret(self):
        """Test that findings don't expose the actual secret value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            secret = "sk-1234567890abcdefghij"
            test_file.write_text(f'API_KEY = "{secret}"\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_file(test_file)
            
            assert len(findings) >= 1
            finding = findings[0]
            
            # The full secret should not appear in masked_value or evidence
            assert secret not in finding.masked_value
            assert secret not in finding.evidence


class TestScanOrchestration:
    """Unit tests for scan orchestration functionality."""
    
    def test_scan_all_files(self):
        """Test scanning all files in a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple files
            (Path(tmpdir) / "config.py").write_text('API_KEY = "sk-1234567890abcdefghij"\n')
            (Path(tmpdir) / "clean.py").write_text('print("hello")\n')
            (Path(tmpdir) / "db.py").write_text('password = "dbpassword123"\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_all_files()
            
            assert len(findings) >= 2  # At least API_KEY and password
    
    def test_summary_by_type(self):
        """Test summary generation by secret type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "config.py").write_text('API_KEY = "sk-1234567890abcdefghij"\n')
            (Path(tmpdir) / "db.py").write_text('password = "dbpassword123"\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_all_files()
            summary = scanner.get_summary_by_type(findings)
            
            assert isinstance(summary, dict)
            assert sum(summary.values()) == len(findings)
    
    def test_summary_by_severity(self):
        """Test summary generation by severity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "config.py").write_text('API_KEY = "sk-1234567890abcdefghij"\n')
            (Path(tmpdir) / "db.py").write_text('password = "dbpassword123"\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_all_files()
            summary = scanner.get_summary_by_severity(findings)
            
            assert isinstance(summary, dict)
            assert sum(summary.values()) == len(findings)
    
    def test_generate_scan_summary(self):
        """Test complete scan summary generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "config.py").write_text('API_KEY = "sk-1234567890abcdefghij"\n')
            
            scanner = SecretScanner(tmpdir)
            findings = scanner.scan_all_files()
            summary = scanner.generate_scan_summary(findings)
            
            assert "total_findings" in summary
            assert "by_type" in summary
            assert "by_severity" in summary
            assert "files_with_secrets" in summary
            assert summary["total_findings"] == len(findings)
