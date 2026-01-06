"""Tests for the Annotation Injector module.

This module contains unit tests for the annotation injection functionality
including comment injection, file preservation, and rollback capabilities.
"""

import os
import tempfile
from pathlib import Path

import pytest

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
from src.security.models import (
    SecurityFinding,
    SecretFinding,
    APIFinding,
    Severity,
    FindingCategory,
)


class TestCommentPrefixes:
    """Unit tests for comment prefix detection."""
    
    def test_python_comment_prefix(self):
        """Test Python files get # prefix."""
        injector = AnnotationInjector(".")
        assert injector._get_comment_prefix("test.py") == "#"
    
    def test_javascript_comment_prefix(self):
        """Test JavaScript files get // prefix."""
        injector = AnnotationInjector(".")
        assert injector._get_comment_prefix("test.js") == "//"
        assert injector._get_comment_prefix("test.ts") == "//"
        assert injector._get_comment_prefix("test.tsx") == "//"
    
    def test_java_comment_prefix(self):
        """Test Java files get // prefix."""
        injector = AnnotationInjector(".")
        assert injector._get_comment_prefix("Test.java") == "//"
    
    def test_yaml_comment_prefix(self):
        """Test YAML files get # prefix."""
        injector = AnnotationInjector(".")
        assert injector._get_comment_prefix("config.yaml") == "#"
        assert injector._get_comment_prefix("config.yml") == "#"
    
    def test_unknown_extension_defaults_to_hash(self):
        """Test unknown extensions default to # prefix."""
        injector = AnnotationInjector(".")
        assert injector._get_comment_prefix("file.unknown") == "#"


class TestAnnotationBuilding:
    """Unit tests for annotation comment building."""
    
    def test_build_python_annotation(self):
        """Test building annotation for Python file."""
        injector = AnnotationInjector(".")
        finding = SecretFinding(
            id="SEC-001",
            category=FindingCategory.HARDCODED_SECRET,
            severity=Severity.CRITICAL,
            file_path="config.py",
            description="Hardcoded API key detected",
            evidence="Line 5: api_key = sk-1...xy",
            remediation="Move to environment variable",
            secret_type="api_key",
            masked_value="sk-1...xy",
        )
        
        annotation = injector._build_annotation_comment("config.py", finding)
        
        assert annotation.startswith("#")
        assert SECURITY_ANNOTATION in annotation
        assert "SEC-001" in annotation
        assert "Hardcoded Secret" in annotation
    
    def test_build_javascript_annotation(self):
        """Test building annotation for JavaScript file."""
        injector = AnnotationInjector(".")
        finding = APIFinding(
            id="API-001",
            category=FindingCategory.INJECTION_RISK,
            severity=Severity.CRITICAL,
            file_path="server.js",
            description="SQL injection risk",
            evidence="Line 10: query(req.body.id)",
            remediation="Use parameterized queries",
            endpoint_path="/api/users",
            http_method="POST",
            vulnerability_type="sql_injection",
        )
        
        annotation = injector._build_annotation_comment("server.js", finding)
        
        assert annotation.startswith("//")
        assert SECURITY_ANNOTATION in annotation
        assert "API-001" in annotation


class TestShouldAnnotateFinding:
    """Unit tests for finding annotation eligibility."""
    
    def test_critical_severity_should_annotate(self):
        """Test that critical severity findings should be annotated."""
        injector = AnnotationInjector(".")
        finding = SecretFinding(
            id="SEC-001",
            category=FindingCategory.HARDCODED_SECRET,
            severity=Severity.CRITICAL,
            file_path="config.py",
            description="Test",
            evidence="Test",
            remediation="Test",
            secret_type="api_key",
            masked_value="****",
        )
        
        assert injector._should_annotate_finding(finding) is True
    
    def test_high_severity_secret_should_annotate(self):
        """Test that high severity secrets should be annotated."""
        injector = AnnotationInjector(".")
        finding = SecretFinding(
            id="SEC-001",
            category=FindingCategory.HARDCODED_SECRET,
            severity=Severity.HIGH,
            file_path="config.py",
            description="Test",
            evidence="Test",
            remediation="Test",
            secret_type="api_key",
            masked_value="****",
        )
        
        assert injector._should_annotate_finding(finding) is True
    
    def test_medium_severity_should_not_annotate(self):
        """Test that medium severity findings should not be annotated."""
        injector = AnnotationInjector(".")
        finding = SecretFinding(
            id="SEC-001",
            category=FindingCategory.HARDCODED_SECRET,
            severity=Severity.MEDIUM,
            file_path="config.py",
            description="Test",
            evidence="Test",
            remediation="Test",
            secret_type="generic_secret",
            masked_value="****",
        )
        
        assert injector._should_annotate_finding(finding) is False
    
    def test_low_severity_should_not_annotate(self):
        """Test that low severity findings should not be annotated."""
        injector = AnnotationInjector(".")
        finding = SecurityFinding(
            id="SEC-001",
            category=FindingCategory.INSECURE_CONFIG,
            severity=Severity.LOW,
            file_path="config.py",
            description="Test",
            evidence="Test",
            remediation="Test",
        )
        
        assert injector._should_annotate_finding(finding) is False


class TestAnnotationInjection:
    """Unit tests for annotation injection functionality."""
    
    def test_inject_annotation_python_file(self):
        """Test injecting annotation into a Python file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            original_content = 'API_KEY = "sk-1234567890abcdefghij"\nprint("hello")\n'
            test_file.write_text(original_content)
            
            injector = AnnotationInjector(tmpdir)
            finding = SecretFinding(
                id="SEC-001",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.CRITICAL,
                file_path="config.py",
                line_number=1,
                description="Hardcoded API key",
                evidence="Line 1",
                remediation="Move to env var",
                secret_type="api_key",
                masked_value="sk-1...ij",
            )
            
            result = injector.inject_annotation(finding)
            
            assert result.success is True
            assert result.file_path == "config.py"
            
            # Verify annotation was added
            new_content = test_file.read_text()
            assert SECURITY_ANNOTATION in new_content
            assert "SEC-001" in new_content
            # Original code should still be there
            assert 'API_KEY = "sk-1234567890abcdefghij"' in new_content
    
    def test_inject_annotation_preserves_indentation(self):
        """Test that annotation preserves the indentation of the target line."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            original_content = 'def func():\n    secret = "password123"\n    return secret\n'
            test_file.write_text(original_content)
            
            injector = AnnotationInjector(tmpdir)
            finding = SecretFinding(
                id="SEC-001",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.CRITICAL,
                file_path="config.py",
                line_number=2,
                description="Hardcoded password",
                evidence="Line 2",
                remediation="Move to env var",
                secret_type="generic_secret",
                masked_value="pass...23",
            )
            
            result = injector.inject_annotation(finding)
            
            assert result.success is True
            
            new_content = test_file.read_text()
            lines = new_content.split('\n')
            # The annotation should be indented to match the target line
            annotation_line = [l for l in lines if SECURITY_ANNOTATION in l][0]
            assert annotation_line.startswith("    ")  # 4 spaces indentation
    
    def test_inject_annotation_file_not_found(self):
        """Test handling of non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            injector = AnnotationInjector(tmpdir)
            finding = SecretFinding(
                id="SEC-001",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.CRITICAL,
                file_path="nonexistent.py",
                line_number=1,
                description="Test",
                evidence="Test",
                remediation="Test",
                secret_type="api_key",
                masked_value="****",
            )
            
            result = injector.inject_annotation(finding)
            
            assert result.success is False
            assert "not found" in result.error_message.lower()
    
    def test_inject_annotation_line_out_of_bounds(self):
        """Test handling of line number out of bounds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            test_file.write_text('print("hello")\n')
            
            injector = AnnotationInjector(tmpdir)
            finding = SecretFinding(
                id="SEC-001",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.CRITICAL,
                file_path="config.py",
                line_number=100,  # Way beyond file length
                description="Test",
                evidence="Test",
                remediation="Test",
                secret_type="api_key",
                masked_value="****",
            )
            
            result = injector.inject_annotation(finding)
            
            assert result.success is False
            assert "out of bounds" in result.error_message.lower()
    
    def test_inject_annotation_dry_run(self):
        """Test dry run mode doesn't modify files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            original_content = 'API_KEY = "sk-1234567890abcdefghij"\n'
            test_file.write_text(original_content)
            
            injector = AnnotationInjector(tmpdir, dry_run=True)
            finding = SecretFinding(
                id="SEC-001",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.CRITICAL,
                file_path="config.py",
                line_number=1,
                description="Test",
                evidence="Test",
                remediation="Test",
                secret_type="api_key",
                masked_value="****",
            )
            
            result = injector.inject_annotation(finding)
            
            assert result.success is True
            # File should not be modified
            assert test_file.read_text() == original_content
    
    def test_skip_already_annotated(self):
        """Test that already annotated lines are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            # File already has annotation
            content = f'# {SECURITY_ANNOTATION} [SEC-001]: Test\nAPI_KEY = "sk-1234567890abcdefghij"\n'
            test_file.write_text(content)
            
            injector = AnnotationInjector(tmpdir)
            finding = SecretFinding(
                id="SEC-002",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.CRITICAL,
                file_path="config.py",
                line_number=2,
                description="Test",
                evidence="Test",
                remediation="Test",
                secret_type="api_key",
                masked_value="****",
            )
            
            result = injector.inject_annotation(finding)
            
            assert result.success is True
            assert "Already annotated" in (result.error_message or "")


class TestMultipleAnnotations:
    """Unit tests for handling multiple annotations."""
    
    def test_inject_multiple_findings_same_file(self):
        """Test injecting multiple annotations in the same file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            original_content = 'API_KEY = "sk-1234567890abcdefghij"\nPASSWORD = "secret123456"\nprint("done")\n'
            test_file.write_text(original_content)
            
            injector = AnnotationInjector(tmpdir)
            findings = [
                SecretFinding(
                    id="SEC-001",
                    category=FindingCategory.HARDCODED_SECRET,
                    severity=Severity.CRITICAL,
                    file_path="config.py",
                    line_number=1,
                    description="API key",
                    evidence="Line 1",
                    remediation="Fix",
                    secret_type="api_key",
                    masked_value="****",
                ),
                SecretFinding(
                    id="SEC-002",
                    category=FindingCategory.HARDCODED_SECRET,
                    severity=Severity.CRITICAL,
                    file_path="config.py",
                    line_number=2,
                    description="Password",
                    evidence="Line 2",
                    remediation="Fix",
                    secret_type="generic_secret",
                    masked_value="****",
                ),
            ]
            
            report = injector.inject_annotations_for_findings(findings)
            
            assert len(report.annotations_added) == 2
            
            # Verify both annotations are in the file
            new_content = test_file.read_text()
            assert "SEC-001" in new_content
            assert "SEC-002" in new_content


class TestRollback:
    """Unit tests for rollback functionality."""
    
    def test_revert_annotations(self):
        """Test reverting annotations restores original content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            original_content = 'API_KEY = "sk-1234567890abcdefghij"\n'
            test_file.write_text(original_content)
            
            injector = AnnotationInjector(tmpdir)
            finding = SecretFinding(
                id="SEC-001",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.CRITICAL,
                file_path="config.py",
                line_number=1,
                description="Test",
                evidence="Test",
                remediation="Test",
                secret_type="api_key",
                masked_value="****",
            )
            
            # Inject annotation
            injector.inject_annotation(finding)
            
            # Verify annotation was added
            assert SECURITY_ANNOTATION in test_file.read_text()
            
            # Revert
            reverted = injector.revert_annotations()
            
            assert len(reverted) == 1
            assert test_file.read_text() == original_content


class TestAnnotationReport:
    """Unit tests for annotation report generation."""
    
    def test_format_annotation_report_with_additions(self):
        """Test formatting report with successful annotations."""
        report = AnnotationReport(
            annotations_added=["config.py:1", "server.js:10"],
        )
        
        markdown = format_annotation_report_markdown(report)
        
        assert "## Security Annotations" in markdown
        assert "### Annotations Added" in markdown
        assert "config.py:1" in markdown
        assert "server.js:10" in markdown
    
    def test_format_annotation_report_with_failures(self):
        """Test formatting report with failed annotations."""
        report = AnnotationReport(
            annotations_failed=[("readonly.py:5", "File is read-only")],
        )
        
        markdown = format_annotation_report_markdown(report)
        
        assert "### Annotation Failures" in markdown
        assert "readonly.py:5" in markdown
        assert "File is read-only" in markdown
    
    def test_format_annotation_report_with_reverts(self):
        """Test formatting report with reverted annotations."""
        report = AnnotationReport(
            annotations_reverted=["config.py:1"],
            conflicts=["Annotation at config.py:1 reverted due to test failure"],
        )
        
        markdown = format_annotation_report_markdown(report)
        
        assert "### Annotations Reverted" in markdown
        assert "### Conflicts" in markdown
    
    def test_format_empty_report(self):
        """Test formatting empty report."""
        report = AnnotationReport()
        
        markdown = format_annotation_report_markdown(report)
        
        assert "No annotations were added" in markdown


class TestGetAnnotatableFindings:
    """Unit tests for get_annotatable_findings utility."""
    
    def test_filters_critical_findings(self):
        """Test that critical findings are included."""
        findings = [
            SecretFinding(
                id="SEC-001",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.CRITICAL,
                file_path="config.py",
                description="Test",
                evidence="Test",
                remediation="Test",
                secret_type="api_key",
                masked_value="****",
            ),
            SecretFinding(
                id="SEC-002",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.LOW,
                file_path="config.py",
                description="Test",
                evidence="Test",
                remediation="Test",
                secret_type="generic_secret",
                masked_value="****",
            ),
        ]
        
        annotatable = get_annotatable_findings(findings)
        
        assert len(annotatable) == 1
        assert annotatable[0].id == "SEC-001"
    
    def test_includes_high_severity_secrets(self):
        """Test that high severity secrets are included."""
        findings = [
            SecretFinding(
                id="SEC-001",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.HIGH,
                file_path="config.py",
                description="Test",
                evidence="Test",
                remediation="Test",
                secret_type="api_key",
                masked_value="****",
            ),
        ]
        
        annotatable = get_annotatable_findings(findings)
        
        assert len(annotatable) == 1
    
    def test_excludes_medium_severity(self):
        """Test that medium severity findings are excluded."""
        findings = [
            SecurityFinding(
                id="SEC-001",
                category=FindingCategory.MISSING_AUTHZ,
                severity=Severity.MEDIUM,
                file_path="server.py",
                description="Test",
                evidence="Test",
                remediation="Test",
            ),
        ]
        
        annotatable = get_annotatable_findings(findings)
        
        assert len(annotatable) == 0


class TestTestVerificationAndRollback:
    """Unit tests for test verification and rollback functionality."""
    
    def test_verify_and_rollback_dry_run_skips_tests(self):
        """Test that dry run mode skips test verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            test_file.write_text('API_KEY = "sk-1234567890abcdefghij"\n')
            
            injector = AnnotationInjector(tmpdir, dry_run=True)
            finding = SecretFinding(
                id="SEC-001",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.CRITICAL,
                file_path="config.py",
                line_number=1,
                description="Test",
                evidence="Test",
                remediation="Test",
                secret_type="api_key",
                masked_value="****",
            )
            
            # Inject annotation
            injector.inject_annotations_for_findings([finding])
            
            # Verify and rollback should skip tests in dry run
            tests_passed, report = injector.verify_and_rollback_on_failure()
            
            assert tests_passed is True
            # File should not be modified in dry run
            assert SECURITY_ANNOTATION not in test_file.read_text()
    
    def test_backup_and_restore_preserves_content(self):
        """Test that backup and restore preserves exact file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            original_content = 'API_KEY = "sk-1234567890abcdefghij"\n# Comment\ndef func():\n    pass\n'
            test_file.write_text(original_content)
            
            injector = AnnotationInjector(tmpdir)
            
            # Backup
            assert injector._backup_file(test_file) is True
            
            # Modify file
            test_file.write_text("modified content")
            
            # Restore
            assert injector._restore_file(test_file) is True
            
            # Content should be exactly the same
            assert test_file.read_text() == original_content
    
    def test_clear_backups(self):
        """Test clearing backup store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            test_file.write_text('print("hello")\n')
            
            injector = AnnotationInjector(tmpdir)
            
            # Create backup
            injector._backup_file(test_file)
            assert len(injector._backup_store) == 1
            
            # Clear backups
            injector.clear_backups()
            assert len(injector._backup_store) == 0
    
    def test_get_annotation_report(self):
        """Test getting the annotation report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            test_file.write_text('API_KEY = "sk-1234567890abcdefghij"\n')
            
            injector = AnnotationInjector(tmpdir)
            finding = SecretFinding(
                id="SEC-001",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.CRITICAL,
                file_path="config.py",
                line_number=1,
                description="Test",
                evidence="Test",
                remediation="Test",
                secret_type="api_key",
                masked_value="****",
            )
            
            injector.inject_annotations_for_findings([finding])
            
            report = injector.get_annotation_report()
            
            assert isinstance(report, AnnotationReport)
            assert len(report.annotations_added) == 1
    
    def test_multiple_files_rollback(self):
        """Test rollback works across multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "config1.py"
            file2 = Path(tmpdir) / "config2.py"
            original1 = 'API_KEY = "sk-1234567890abcdefghij"\n'
            original2 = 'PASSWORD = "secret123456789"\n'
            file1.write_text(original1)
            file2.write_text(original2)
            
            injector = AnnotationInjector(tmpdir)
            findings = [
                SecretFinding(
                    id="SEC-001",
                    category=FindingCategory.HARDCODED_SECRET,
                    severity=Severity.CRITICAL,
                    file_path="config1.py",
                    line_number=1,
                    description="API key",
                    evidence="Line 1",
                    remediation="Fix",
                    secret_type="api_key",
                    masked_value="****",
                ),
                SecretFinding(
                    id="SEC-002",
                    category=FindingCategory.HARDCODED_SECRET,
                    severity=Severity.CRITICAL,
                    file_path="config2.py",
                    line_number=1,
                    description="Password",
                    evidence="Line 1",
                    remediation="Fix",
                    secret_type="generic_secret",
                    masked_value="****",
                ),
            ]
            
            # Inject annotations
            injector.inject_annotations_for_findings(findings)
            
            # Verify annotations were added
            assert SECURITY_ANNOTATION in file1.read_text()
            assert SECURITY_ANNOTATION in file2.read_text()
            
            # Revert all
            reverted = injector.revert_annotations()
            
            assert len(reverted) == 2
            assert file1.read_text() == original1
            assert file2.read_text() == original2


class TestAnnotationReportConflicts:
    """Unit tests for conflict logging in annotation reports."""
    
    def test_report_logs_read_only_conflicts(self):
        """Test that read-only file conflicts are logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "readonly.py"
            test_file.write_text('API_KEY = "sk-1234567890abcdefghij"\n')
            
            # Make file read-only
            os.chmod(test_file, 0o444)
            
            try:
                injector = AnnotationInjector(tmpdir)
                finding = SecretFinding(
                    id="SEC-001",
                    category=FindingCategory.HARDCODED_SECRET,
                    severity=Severity.CRITICAL,
                    file_path="readonly.py",
                    line_number=1,
                    description="Test",
                    evidence="Test",
                    remediation="Test",
                    secret_type="api_key",
                    masked_value="****",
                )
                
                report = injector.inject_annotations_for_findings([finding])
                
                # Should have a failure logged
                assert len(report.annotations_failed) == 1
                assert "readonly.py" in report.annotations_failed[0][0]
            finally:
                # Restore permissions for cleanup
                os.chmod(test_file, 0o644)
    
    def test_annotation_report_tracks_all_operations(self):
        """Test that annotation report tracks all operation types."""
        report = AnnotationReport()
        
        # Add various entries
        report.annotations_added.append("file1.py:10")
        report.annotations_failed.append(("file2.py:5", "Read-only"))
        report.annotations_reverted.append("file3.py:15")
        report.test_failures.append("Test failed: assertion error")
        report.conflicts.append("Conflict at file3.py:15")
        
        assert len(report.annotations_added) == 1
        assert len(report.annotations_failed) == 1
        assert len(report.annotations_reverted) == 1
        assert len(report.test_failures) == 1
        assert len(report.conflicts) == 1


class TestNonDestructiveOperation:
    """Unit tests verifying non-destructive operation."""
    
    def test_annotation_only_adds_comment_line(self):
        """Test that annotation only adds a comment line, no other changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "config.py"
            original_lines = [
                'API_KEY = "sk-1234567890abcdefghij"',
                'def process():',
                '    return API_KEY',
                '',
            ]
            original_content = '\n'.join(original_lines)
            test_file.write_text(original_content)
            
            injector = AnnotationInjector(tmpdir)
            finding = SecretFinding(
                id="SEC-001",
                category=FindingCategory.HARDCODED_SECRET,
                severity=Severity.CRITICAL,
                file_path="config.py",
                line_number=1,
                description="API key",
                evidence="Line 1",
                remediation="Fix",
                secret_type="api_key",
                masked_value="****",
            )
            
            injector.inject_annotation(finding)
            
            new_content = test_file.read_text()
            new_lines = new_content.split('\n')
            
            # Should have exactly one more line (the annotation)
            assert len(new_lines) == len(original_lines) + 1
            
            # All original lines should still be present
            for orig_line in original_lines:
                assert orig_line in new_lines
            
            # The annotation line should be a comment
            annotation_line = [l for l in new_lines if SECURITY_ANNOTATION in l][0]
            assert annotation_line.strip().startswith('#')
    
    def test_business_logic_unchanged(self):
        """Test that business logic code is unchanged after annotation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "app.py"
            original_code = '''def calculate_total(items):
    """Calculate total price of items."""
    password = "admin123456"  # Bad practice
    total = sum(item.price for item in items)
    return total * 1.1  # Add tax

class Order:
    def __init__(self, items):
        self.items = items
        self.api_key = "sk-1234567890abcdefghij"
    
    def process(self):
        return calculate_total(self.items)
'''
            test_file.write_text(original_code)
            
            injector = AnnotationInjector(tmpdir)
            findings = [
                SecretFinding(
                    id="SEC-001",
                    category=FindingCategory.HARDCODED_SECRET,
                    severity=Severity.CRITICAL,
                    file_path="app.py",
                    line_number=3,
                    description="Password",
                    evidence="Line 3",
                    remediation="Fix",
                    secret_type="generic_secret",
                    masked_value="****",
                ),
                SecretFinding(
                    id="SEC-002",
                    category=FindingCategory.HARDCODED_SECRET,
                    severity=Severity.CRITICAL,
                    file_path="app.py",
                    line_number=10,
                    description="API key",
                    evidence="Line 10",
                    remediation="Fix",
                    secret_type="api_key",
                    masked_value="****",
                ),
            ]
            
            injector.inject_annotations_for_findings(findings)
            
            new_content = test_file.read_text()
            
            # Remove annotation lines and compare
            new_lines = [l for l in new_content.split('\n') if SECURITY_ANNOTATION not in l]
            original_lines = original_code.split('\n')
            
            # All original code lines should be present
            for orig_line in original_lines:
                assert orig_line in new_lines
