"""Annotation Injector Module for Security Audit.

This module provides functionality to inject security annotations (TODO comments)
into source files at locations where critical vulnerabilities are found.
The injector operates non-destructively, preserving original code while adding
warning comments.
"""

import os
import subprocess
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from src.security.models import (
    SecurityFinding,
    Severity,
    FindingCategory,
)


# ============================================================================
# Constants
# ============================================================================

# Comment prefixes for different file types
COMMENT_PREFIXES: Dict[str, str] = {
    ".py": "#",
    ".js": "//",
    ".ts": "//",
    ".tsx": "//",
    ".jsx": "//",
    ".java": "//",
    ".c": "//",
    ".cpp": "//",
    ".h": "//",
    ".hpp": "//",
    ".cs": "//",
    ".go": "//",
    ".rs": "//",
    ".swift": "//",
    ".kt": "//",
    ".scala": "//",
    ".rb": "#",
    ".php": "//",
    ".sh": "#",
    ".bash": "#",
    ".zsh": "#",
    ".yaml": "#",
    ".yml": "#",
    ".toml": "#",
    ".ini": "#",
    ".cfg": "#",
    ".conf": "#",
}

# The security annotation marker
SECURITY_ANNOTATION = "TODO: SECURITY CRITICAL"

# Categories that warrant critical annotations
CRITICAL_ANNOTATION_CATEGORIES: Set[FindingCategory] = {
    FindingCategory.HARDCODED_SECRET,
    FindingCategory.INJECTION_RISK,
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class AnnotationResult:
    """Result of an annotation operation on a single file."""
    file_path: str
    success: bool
    line_number: int
    error_message: Optional[str] = None
    original_content: Optional[str] = None


@dataclass
class AnnotationReport:
    """Report of all annotation operations."""
    annotations_added: List[str] = field(default_factory=list)
    annotations_failed: List[Tuple[str, str]] = field(default_factory=list)
    annotations_reverted: List[str] = field(default_factory=list)
    test_failures: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)


# ============================================================================
# Annotation Injector Class
# ============================================================================

class AnnotationInjector:
    """Injects security annotations into source files at vulnerability locations."""

    def __init__(self, root_path: str, dry_run: bool = False):
        """Initialize the annotation injector.
        
        Args:
            root_path: Root directory path of the repository
            dry_run: If True, don't actually modify files
        """
        self.root_path = Path(root_path).resolve()
        self.dry_run = dry_run
        self._backup_store: Dict[str, str] = {}
        self._annotation_report = AnnotationReport()

    def _get_comment_prefix(self, file_path: str) -> str:
        """Get the appropriate comment prefix for a file type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Comment prefix string (e.g., "#" for Python, "//" for JS)
        """
        ext = Path(file_path).suffix.lower()
        return COMMENT_PREFIXES.get(ext, "#")

    def _build_annotation_comment(self, file_path: str, finding: SecurityFinding) -> str:
        """Build the annotation comment string.
        
        Args:
            file_path: Path to the file being annotated
            finding: The security finding to annotate
            
        Returns:
            Complete annotation comment string
        """
        prefix = self._get_comment_prefix(file_path)
        finding_id = finding.id
        category = finding.category.value
        description = finding.description
        
        return f"{prefix} {SECURITY_ANNOTATION} [{finding_id}]: {category} - {description}"

    def _should_annotate_finding(self, finding: SecurityFinding) -> bool:
        """Determine if a finding should receive an annotation.
        
        Only critical findings (hardcoded secrets, injection risks) get annotations.
        
        Args:
            finding: The security finding to check
            
        Returns:
            True if the finding should be annotated
        """
        # Annotate critical severity findings
        if finding.severity == Severity.CRITICAL:
            return True
        
        # Annotate high severity findings in critical categories
        if finding.severity == Severity.HIGH and finding.category in CRITICAL_ANNOTATION_CATEGORIES:
            return True
        
        return False

    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content with encoding fallback.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as string, or None if unreadable
        """
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except (IOError, OSError):
                return None
        
        return None

    def _write_file_content(self, file_path: Path, content: str) -> bool:
        """Write content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except (IOError, OSError):
            return False

    def _backup_file(self, file_path: Path) -> bool:
        """Create a backup of a file before modification.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            True if backup successful
        """
        content = self._read_file_content(file_path)
        if content is not None:
            self._backup_store[str(file_path)] = content
            return True
        return False

    def _restore_file(self, file_path: Path) -> bool:
        """Restore a file from backup.
        
        Args:
            file_path: Path to the file to restore
            
        Returns:
            True if restore successful
        """
        path_str = str(file_path)
        if path_str in self._backup_store:
            return self._write_file_content(file_path, self._backup_store[path_str])
        return False

    def _line_already_annotated(self, line: str, file_path: str) -> bool:
        """Check if a line already has a security annotation.
        
        Args:
            line: The line to check
            file_path: Path to the file (for comment prefix)
            
        Returns:
            True if line already has annotation
        """
        return SECURITY_ANNOTATION in line

    def inject_annotation(
        self,
        finding: SecurityFinding,
    ) -> AnnotationResult:
        """Inject a security annotation for a single finding.
        
        Args:
            finding: The security finding to annotate
            
        Returns:
            AnnotationResult with operation details
        """
        file_path = self.root_path / finding.file_path
        line_number = finding.line_number or 1
        
        # Check if file exists
        if not file_path.exists():
            return AnnotationResult(
                file_path=finding.file_path,
                success=False,
                line_number=line_number,
                error_message=f"File not found: {finding.file_path}",
            )
        
        # Check if file is writable
        if not os.access(file_path, os.W_OK):
            return AnnotationResult(
                file_path=finding.file_path,
                success=False,
                line_number=line_number,
                error_message=f"File is read-only: {finding.file_path}",
            )
        
        # Read file content
        content = self._read_file_content(file_path)
        if content is None:
            return AnnotationResult(
                file_path=finding.file_path,
                success=False,
                line_number=line_number,
                error_message=f"Could not read file: {finding.file_path}",
            )
        
        # Store original content for potential rollback
        original_content = content
        
        # Split into lines
        lines = content.split('\n')
        
        # Validate line number
        if line_number < 1 or line_number > len(lines):
            return AnnotationResult(
                file_path=finding.file_path,
                success=False,
                line_number=line_number,
                error_message=f"Line number {line_number} out of bounds (file has {len(lines)} lines)",
            )
        
        # Check if already annotated
        target_line_idx = line_number - 1
        if target_line_idx > 0:
            prev_line = lines[target_line_idx - 1]
            if self._line_already_annotated(prev_line, finding.file_path):
                return AnnotationResult(
                    file_path=finding.file_path,
                    success=True,
                    line_number=line_number,
                    error_message="Already annotated",
                    original_content=original_content,
                )
        
        # Build annotation comment
        annotation = self._build_annotation_comment(finding.file_path, finding)
        
        # Get indentation from target line
        target_line = lines[target_line_idx]
        indentation = ""
        for char in target_line:
            if char in (' ', '\t'):
                indentation += char
            else:
                break
        
        # Insert annotation line before the target line
        annotated_line = indentation + annotation
        lines.insert(target_line_idx, annotated_line)
        
        # Join lines back
        new_content = '\n'.join(lines)
        
        # Write if not dry run
        if not self.dry_run:
            # Backup first
            self._backup_file(file_path)
            
            if not self._write_file_content(file_path, new_content):
                return AnnotationResult(
                    file_path=finding.file_path,
                    success=False,
                    line_number=line_number,
                    error_message=f"Failed to write file: {finding.file_path}",
                )
        
        return AnnotationResult(
            file_path=finding.file_path,
            success=True,
            line_number=line_number,
            original_content=original_content,
        )

    def inject_annotations_for_findings(
        self,
        findings: List[SecurityFinding],
    ) -> AnnotationReport:
        """Inject annotations for all critical findings.
        
        Args:
            findings: List of security findings
            
        Returns:
            AnnotationReport with all operation results
        """
        report = AnnotationReport()
        
        # Filter to only annotatable findings
        annotatable_findings = [f for f in findings if self._should_annotate_finding(f)]
        
        # Group findings by file to handle multiple findings in same file
        findings_by_file: Dict[str, List[SecurityFinding]] = {}
        for finding in annotatable_findings:
            if finding.file_path not in findings_by_file:
                findings_by_file[finding.file_path] = []
            findings_by_file[finding.file_path].append(finding)
        
        # Sort findings within each file by line number (descending)
        # This ensures we inject from bottom to top, preserving line numbers
        for file_path in findings_by_file:
            findings_by_file[file_path].sort(
                key=lambda f: f.line_number or 0,
                reverse=True
            )
        
        # Inject annotations
        for file_path, file_findings in findings_by_file.items():
            for finding in file_findings:
                result = self.inject_annotation(finding)
                
                if result.success:
                    location = f"{file_path}:{finding.line_number}"
                    report.annotations_added.append(location)
                else:
                    report.annotations_failed.append(
                        (f"{file_path}:{finding.line_number}", result.error_message or "Unknown error")
                    )
        
        self._annotation_report = report
        return report

    def run_tests(self, test_command: Optional[str] = None) -> Tuple[bool, str]:
        """Run the project's test suite.
        
        Args:
            test_command: Optional custom test command. 
                         Defaults to pytest for Python projects.
            
        Returns:
            Tuple of (success, output)
        """
        if test_command is None:
            # Try to detect test framework
            if (self.root_path / "pytest.ini").exists() or \
               (self.root_path / "pyproject.toml").exists() or \
               (self.root_path / "setup.py").exists():
                test_command = "python -m pytest --tb=short -q"
            elif (self.root_path / "package.json").exists():
                test_command = "npm test"
            else:
                test_command = "python -m pytest --tb=short -q"
        
        try:
            result = subprocess.run(
                test_command,
                shell=True,
                cwd=str(self.root_path),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            return success, output
            
        except subprocess.TimeoutExpired:
            return False, "Test execution timed out after 5 minutes"
        except Exception as e:
            return False, f"Failed to run tests: {str(e)}"

    def revert_annotations(self) -> List[str]:
        """Revert all annotations by restoring from backups.
        
        Returns:
            List of file paths that were reverted
        """
        reverted = []
        
        for file_path_str in list(self._backup_store.keys()):
            file_path = Path(file_path_str)
            if self._restore_file(file_path):
                reverted.append(str(file_path.relative_to(self.root_path)))
        
        # Clear backup store
        self._backup_store.clear()
        
        return reverted

    def verify_and_rollback_on_failure(
        self,
        test_command: Optional[str] = None,
    ) -> Tuple[bool, AnnotationReport]:
        """Run tests and rollback annotations if tests fail.
        
        Args:
            test_command: Optional custom test command
            
        Returns:
            Tuple of (tests_passed, updated_report)
        """
        if self.dry_run:
            # In dry run mode, skip test verification
            return True, self._annotation_report
        
        # Run tests
        tests_passed, test_output = self.run_tests(test_command)
        
        if not tests_passed:
            # Record test failure
            self._annotation_report.test_failures.append(test_output)
            
            # Revert all annotations
            reverted = self.revert_annotations()
            self._annotation_report.annotations_reverted.extend(reverted)
            
            # Record conflicts
            for location in self._annotation_report.annotations_added:
                self._annotation_report.conflicts.append(
                    f"Annotation at {location} reverted due to test failure"
                )
            
            # Clear successful annotations since they were reverted
            self._annotation_report.annotations_added.clear()
        
        return tests_passed, self._annotation_report

    def get_annotation_report(self) -> AnnotationReport:
        """Get the current annotation report.
        
        Returns:
            The annotation report
        """
        return self._annotation_report

    def clear_backups(self) -> None:
        """Clear all stored backups."""
        self._backup_store.clear()


# ============================================================================
# Utility Functions
# ============================================================================

def get_annotatable_findings(findings: List[SecurityFinding]) -> List[SecurityFinding]:
    """Filter findings to only those that should be annotated.
    
    Args:
        findings: List of all security findings
        
    Returns:
        List of findings that warrant annotations
    """
    result = []
    for finding in findings:
        # Critical severity always gets annotated
        if finding.severity == Severity.CRITICAL:
            result.append(finding)
        # High severity in critical categories gets annotated
        elif finding.severity == Severity.HIGH and finding.category in CRITICAL_ANNOTATION_CATEGORIES:
            result.append(finding)
    return result


def format_annotation_report_markdown(report: AnnotationReport) -> str:
    """Format an annotation report as markdown for inclusion in security report.
    
    Args:
        report: The annotation report
        
    Returns:
        Markdown formatted string
    """
    lines = [
        "## Security Annotations",
        "",
    ]
    
    if report.annotations_added:
        lines.extend([
            "### Annotations Added",
            "",
            "The following locations have been annotated with `TODO: SECURITY CRITICAL` comments:",
            "",
        ])
        for location in report.annotations_added:
            lines.append(f"- `{location}`")
        lines.append("")
    
    if report.annotations_failed:
        lines.extend([
            "### Annotation Failures",
            "",
            "The following annotations could not be added:",
            "",
        ])
        for location, error in report.annotations_failed:
            lines.append(f"- `{location}`: {error}")
        lines.append("")
    
    if report.annotations_reverted:
        lines.extend([
            "### Annotations Reverted",
            "",
            "The following annotations were reverted due to test failures:",
            "",
        ])
        for location in report.annotations_reverted:
            lines.append(f"- `{location}`")
        lines.append("")
    
    if report.conflicts:
        lines.extend([
            "### Conflicts",
            "",
        ])
        for conflict in report.conflicts:
            lines.append(f"- {conflict}")
        lines.append("")
    
    if not any([report.annotations_added, report.annotations_failed, 
                report.annotations_reverted, report.conflicts]):
        lines.append("No annotations were added during this scan.")
        lines.append("")
    
    return "\n".join(lines)
