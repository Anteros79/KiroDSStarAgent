"""Main Security Scanner Orchestrator.

This module provides the main orchestrator class that coordinates all security
scanning phases: secret detection, dependency analysis, API auditing, and
report generation.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from src.security.models import (
    AuditReport,
    SecurityFinding,
    Severity,
)
from src.security.secret_scanner import SecretScanner
from src.security.dependency_analyzer import DependencyAnalyzer
from src.security.api_auditor import APIAuditor
from src.security.report_generator import ReportGenerator
from src.security.annotation_injector import (
    AnnotationInjector,
    AnnotationReport,
    format_annotation_report_markdown,
)


# Configure logging
logger = logging.getLogger(__name__)


class SecurityScanner:
    """Main orchestrator for security audit operations.
    
    Coordinates all scanning phases:
    - Secret detection in source files
    - Dependency vulnerability analysis
    - API endpoint security auditing
    - Report generation
    - Security annotation injection
    """

    def __init__(self, root_path: str, dry_run: bool = False):
        """Initialize the security scanner.
        
        Args:
            root_path: Root directory path of the repository to scan
            dry_run: If True, don't modify files (no annotations)
        """
        self.root_path = Path(root_path).resolve()
        self.dry_run = dry_run
        
        # Initialize component scanners
        self.secret_scanner = SecretScanner(str(self.root_path))
        self.dependency_analyzer = DependencyAnalyzer(str(self.root_path))
        self.api_auditor = APIAuditor(str(self.root_path))
        self.report_generator = ReportGenerator()
        self.annotation_injector = AnnotationInjector(str(self.root_path), dry_run=dry_run)
        
        # Store findings and report
        self._findings: List[SecurityFinding] = []
        self._audit_report: Optional[AuditReport] = None
        self._annotation_report: Optional[AnnotationReport] = None
        self._warnings: List[str] = []

    def scan_secrets(self) -> List[SecurityFinding]:
        """Scan for hardcoded secrets in source files.
        
        Returns:
            List of SecretFinding objects for detected secrets
        """
        logger.info("Starting secret scan...")
        findings = self.secret_scanner.scan_all_files()
        logger.info(f"Secret scan complete. Found {len(findings)} potential secrets.")
        return findings

    def analyze_dependencies(self) -> List[SecurityFinding]:
        """Analyze dependencies for known vulnerabilities.
        
        Returns:
            List of DependencyFinding objects for vulnerable packages
        """
        logger.info("Starting dependency analysis...")
        dependencies, findings = self.dependency_analyzer.analyze_all()
        
        # Collect warnings from dependency analyzer
        self._warnings.extend(self.dependency_analyzer.warnings)
        
        logger.info(f"Dependency analysis complete. Found {len(findings)} vulnerabilities in {len(dependencies)} dependencies.")
        return findings

    def audit_api_endpoints(self) -> List[SecurityFinding]:
        """Audit API endpoints for security vulnerabilities.
        
        Returns:
            List of APIFinding objects for detected vulnerabilities
        """
        logger.info("Starting API endpoint audit...")
        findings = self.api_auditor.audit_all_files()
        logger.info(f"API audit complete. Found {len(findings)} issues.")
        return findings

    def aggregate_findings(
        self,
        secret_findings: List[SecurityFinding],
        dependency_findings: List[SecurityFinding],
        api_findings: List[SecurityFinding],
    ) -> AuditReport:
        """Aggregate findings from all scanners into an AuditReport.
        
        Args:
            secret_findings: Findings from secret scanner
            dependency_findings: Findings from dependency analyzer
            api_findings: Findings from API auditor
            
        Returns:
            AuditReport containing all findings
        """
        report = AuditReport(
            scan_timestamp=datetime.utcnow().isoformat(),
        )
        
        # Add all findings
        for finding in secret_findings:
            report.add_finding(finding)
        
        for finding in dependency_findings:
            report.add_finding(finding)
        
        for finding in api_findings:
            report.add_finding(finding)
        
        return report

    def inject_annotations(
        self,
        findings: List[SecurityFinding],
        verify_tests: bool = True,
        test_command: Optional[str] = None,
    ) -> AnnotationReport:
        """Inject security annotations for critical findings.
        
        Args:
            findings: List of security findings
            verify_tests: If True, run tests and rollback on failure
            test_command: Optional custom test command
            
        Returns:
            AnnotationReport with operation results
        """
        if self.dry_run:
            logger.info("Dry run mode - skipping annotation injection")
            return AnnotationReport()
        
        logger.info("Injecting security annotations...")
        annotation_report = self.annotation_injector.inject_annotations_for_findings(findings)
        
        if verify_tests and annotation_report.annotations_added:
            logger.info("Verifying tests after annotation...")
            tests_passed, annotation_report = self.annotation_injector.verify_and_rollback_on_failure(
                test_command
            )
            if not tests_passed:
                logger.warning("Tests failed after annotation - annotations reverted")
        
        logger.info(f"Annotation complete. Added {len(annotation_report.annotations_added)} annotations.")
        return annotation_report

    def generate_report(
        self,
        findings: List[SecurityFinding],
        annotation_report: Optional[AnnotationReport] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """Generate the security audit report.
        
        Args:
            findings: List of all security findings
            annotation_report: Optional annotation report to include
            output_path: Optional custom output path for the report
            
        Returns:
            Path to the generated report file
        """
        logger.info("Generating security audit report...")
        
        if output_path is None:
            output_path = str(self.root_path / "SECURITY_AUDIT.md")
        
        # Generate main report
        report_content = self.report_generator.generate_full_report(findings)
        
        # Append annotation report if available
        if annotation_report:
            annotation_section = format_annotation_report_markdown(annotation_report)
            report_content += "\n" + annotation_section
        
        # Append warnings if any
        if self._warnings:
            warnings_section = self._format_warnings_section()
            report_content += "\n" + warnings_section
        
        # Write report
        output_file = Path(output_path)
        output_file.write_text(report_content, encoding="utf-8")
        
        logger.info(f"Report generated: {output_path}")
        return str(output_file.absolute())

    def _format_warnings_section(self) -> str:
        """Format warnings as a markdown section.
        
        Returns:
            Markdown formatted warnings section
        """
        if not self._warnings:
            return ""
        
        lines = [
            "## Warnings",
            "",
            "The following warnings were encountered during the scan:",
            "",
        ]
        for warning in self._warnings:
            lines.append(f"- {warning}")
        lines.append("")
        
        return "\n".join(lines)

    def run_full_audit(
        self,
        inject_annotations: bool = True,
        verify_tests: bool = True,
        test_command: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> Tuple[AuditReport, str]:
        """Execute a complete security audit.
        
        This method coordinates all scanning phases:
        1. Scan for hardcoded secrets
        2. Analyze dependencies for CVEs
        3. Audit API endpoints
        4. Aggregate findings
        5. Inject annotations (if enabled)
        6. Generate report
        
        Args:
            inject_annotations: If True, inject security annotations
            verify_tests: If True, verify tests pass after annotation
            test_command: Optional custom test command
            output_path: Optional custom output path for report
            
        Returns:
            Tuple of (AuditReport, report_file_path)
        """
        logger.info(f"Starting full security audit of {self.root_path}")
        
        # Phase 1: Scan for secrets
        secret_findings = self.scan_secrets()
        
        # Phase 2: Analyze dependencies
        dependency_findings = self.analyze_dependencies()
        
        # Phase 3: Audit API endpoints
        api_findings = self.audit_api_endpoints()
        
        # Phase 4: Aggregate findings
        self._audit_report = self.aggregate_findings(
            secret_findings,
            dependency_findings,
            api_findings,
        )
        self._findings = self._audit_report.findings
        
        # Phase 5: Inject annotations (if enabled and not dry run)
        annotation_report = None
        if inject_annotations and not self.dry_run:
            annotation_report = self.inject_annotations(
                self._findings,
                verify_tests=verify_tests,
                test_command=test_command,
            )
            self._annotation_report = annotation_report
            
            # Update audit report with annotation info
            self._audit_report.annotations_added = annotation_report.annotations_added
        
        # Phase 6: Generate report
        report_path = self.generate_report(
            self._findings,
            annotation_report=annotation_report,
            output_path=output_path,
        )
        
        logger.info(f"Security audit complete. Total findings: {self._audit_report.total_findings}")
        
        return self._audit_report, report_path

    def get_findings(self) -> List[SecurityFinding]:
        """Get all findings from the last audit.
        
        Returns:
            List of all security findings
        """
        return self._findings

    def get_audit_report(self) -> Optional[AuditReport]:
        """Get the audit report from the last audit.
        
        Returns:
            AuditReport or None if no audit has been run
        """
        return self._audit_report

    def get_summary(self) -> dict:
        """Get a summary of the last audit.
        
        Returns:
            Dictionary containing audit summary statistics
        """
        if not self._audit_report:
            return {
                "status": "No audit has been run",
                "total_findings": 0,
            }
        
        return {
            "scan_timestamp": self._audit_report.scan_timestamp,
            "total_findings": self._audit_report.total_findings,
            "critical_count": self._audit_report.critical_count,
            "high_count": self._audit_report.high_count,
            "medium_count": self._audit_report.medium_count,
            "low_count": self._audit_report.low_count,
            "annotations_added": len(self._audit_report.annotations_added),
            "warnings": len(self._warnings),
        }

    def print_summary(self) -> None:
        """Print a summary of the audit to console."""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("SECURITY AUDIT SUMMARY")
        print("=" * 60)
        
        if summary.get("status") == "No audit has been run":
            print("No audit has been run yet.")
            return
        
        print(f"Scan Time: {summary['scan_timestamp']}")
        print(f"\nTotal Findings: {summary['total_findings']}")
        print(f"  - Critical: {summary['critical_count']}")
        print(f"  - High: {summary['high_count']}")
        print(f"  - Medium: {summary['medium_count']}")
        print(f"  - Low: {summary['low_count']}")
        
        if summary['annotations_added'] > 0:
            print(f"\nAnnotations Added: {summary['annotations_added']}")
        
        if summary['warnings'] > 0:
            print(f"\nWarnings: {summary['warnings']}")
        
        # Risk assessment
        if summary['critical_count'] > 0:
            risk = "CRITICAL"
        elif summary['high_count'] >= 3:
            risk = "HIGH"
        elif summary['high_count'] > 0 or summary['medium_count'] >= 5:
            risk = "MEDIUM"
        elif summary['medium_count'] > 0:
            risk = "LOW"
        else:
            risk = "MINIMAL"
        
        print(f"\nOverall Risk: {risk}")
        print("=" * 60 + "\n")
