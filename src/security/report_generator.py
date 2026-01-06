"""Report Generator for Security Audit.

This module generates comprehensive SECURITY_AUDIT.md reports containing:
- Executive summary with risk assessment and key metrics
- Critical findings table sorted by severity
- Prioritized remediation plan with effort estimates
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter

from src.security.models import (
    AuditReport,
    SecurityFinding,
    Severity,
    FindingCategory,
)


# Effort estimates for different finding categories (in hours)
REMEDIATION_EFFORT = {
    FindingCategory.HARDCODED_SECRET: {
        Severity.CRITICAL: "1-2 hours",
        Severity.HIGH: "1-2 hours",
        Severity.MEDIUM: "30 minutes",
        Severity.LOW: "15 minutes",
        Severity.INFO: "15 minutes",
    },
    FindingCategory.VULNERABLE_DEPENDENCY: {
        Severity.CRITICAL: "2-4 hours",
        Severity.HIGH: "1-2 hours",
        Severity.MEDIUM: "1 hour",
        Severity.LOW: "30 minutes",
        Severity.INFO: "15 minutes",
    },
    FindingCategory.MISSING_AUTHZ: {
        Severity.CRITICAL: "4-8 hours",
        Severity.HIGH: "2-4 hours",
        Severity.MEDIUM: "1-2 hours",
        Severity.LOW: "1 hour",
        Severity.INFO: "30 minutes",
    },
    FindingCategory.INJECTION_RISK: {
        Severity.CRITICAL: "4-8 hours",
        Severity.HIGH: "2-4 hours",
        Severity.MEDIUM: "1-2 hours",
        Severity.LOW: "1 hour",
        Severity.INFO: "30 minutes",
    },
    FindingCategory.INSECURE_CONFIG: {
        Severity.CRITICAL: "2-4 hours",
        Severity.HIGH: "1-2 hours",
        Severity.MEDIUM: "1 hour",
        Severity.LOW: "30 minutes",
        Severity.INFO: "15 minutes",
    },
}


class ReportGenerator:
    """Generates security audit reports in Markdown format."""

    def __init__(self, report: Optional[AuditReport] = None):
        """Initialize the report generator.
        
        Args:
            report: Optional AuditReport to generate from
        """
        self.report = report or AuditReport()

    def calculate_risk_assessment(self, findings: List[SecurityFinding]) -> str:
        """Calculate overall risk assessment based on findings.
        
        Args:
            findings: List of security findings
            
        Returns:
            Risk level string: "CRITICAL", "HIGH", "MEDIUM", "LOW", or "MINIMAL"
        """
        if not findings:
            return "MINIMAL"
        
        critical_count = sum(1 for f in findings if f.severity == Severity.CRITICAL)
        high_count = sum(1 for f in findings if f.severity == Severity.HIGH)
        medium_count = sum(1 for f in findings if f.severity == Severity.MEDIUM)
        
        if critical_count > 0:
            return "CRITICAL"
        elif high_count >= 3:
            return "HIGH"
        elif high_count > 0 or medium_count >= 5:
            return "MEDIUM"
        elif medium_count > 0:
            return "LOW"
        else:
            return "MINIMAL"

    def generate_executive_summary(self, findings: List[SecurityFinding]) -> str:
        """Generate executive summary with risk assessment and key metrics.
        
        Args:
            findings: List of security findings
            
        Returns:
            Markdown formatted executive summary
        """
        risk_level = self.calculate_risk_assessment(findings)
        
        # Count by severity
        severity_counts = Counter(f.severity for f in findings)
        critical = severity_counts.get(Severity.CRITICAL, 0)
        high = severity_counts.get(Severity.HIGH, 0)
        medium = severity_counts.get(Severity.MEDIUM, 0)
        low = severity_counts.get(Severity.LOW, 0)
        info = severity_counts.get(Severity.INFO, 0)
        
        # Count by category
        category_counts = Counter(f.category for f in findings)
        
        # Build summary
        lines = [
            "## Executive Summary",
            "",
            f"**Scan Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            f"**Overall Risk Assessment:** {risk_level}",
            "",
            "### Key Metrics",
            "",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Total Findings | {len(findings)} |",
            f"| Critical | {critical} |",
            f"| High | {high} |",
            f"| Medium | {medium} |",
            f"| Low | {low} |",
            f"| Informational | {info} |",
            "",
        ]
        
        # Add category breakdown if there are findings
        if category_counts:
            lines.extend([
                "### Findings by Category",
                "",
                "| Category | Count |",
                "|----------|-------|",
            ])
            for category in FindingCategory:
                count = category_counts.get(category, 0)
                if count > 0:
                    lines.append(f"| {category.value} | {count} |")
            lines.append("")
        
        return "\n".join(lines)

    def sort_findings_by_severity(
        self, findings: List[SecurityFinding]
    ) -> List[SecurityFinding]:
        """Sort findings by severity (Critical > High > Medium > Low > Info).
        
        Args:
            findings: List of security findings
            
        Returns:
            Sorted list with Critical findings first
        """
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        return sorted(findings, key=lambda f: severity_order.get(f.severity, 5))

    def _escape_markdown(self, text: str) -> str:
        """Escape special markdown characters in text.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text safe for markdown tables
        """
        # Replace pipe characters and newlines for table compatibility
        return text.replace("|", "\\|").replace("\n", " ")

    def _format_location(self, finding: SecurityFinding) -> str:
        """Format the location string for a finding.
        
        Args:
            finding: Security finding
            
        Returns:
            Formatted location string (file:line or just file)
        """
        if finding.line_number:
            return f"`{finding.file_path}:{finding.line_number}`"
        return f"`{finding.file_path}`"

    def generate_findings_table(self, findings: List[SecurityFinding]) -> str:
        """Generate markdown table of findings sorted by severity.
        
        Args:
            findings: List of security findings
            
        Returns:
            Markdown formatted findings table
        """
        if not findings:
            return "## Critical Findings\n\nNo security findings detected.\n"
        
        sorted_findings = self.sort_findings_by_severity(findings)
        
        lines = [
            "## Critical Findings",
            "",
            "| ID | Category | Severity | Location | Description |",
            "|----|----------|----------|----------|-------------|",
        ]
        
        for finding in sorted_findings:
            location = self._format_location(finding)
            description = self._escape_markdown(finding.description)
            # Truncate long descriptions
            if len(description) > 80:
                description = description[:77] + "..."
            
            lines.append(
                f"| {finding.id} | {finding.category.value} | "
                f"{finding.severity.value} | {location} | {description} |"
            )
        
        lines.append("")
        return "\n".join(lines)

    def _get_effort_estimate(self, finding: SecurityFinding) -> str:
        """Get effort estimate for remediating a finding.
        
        Args:
            finding: Security finding
            
        Returns:
            Effort estimate string
        """
        category_efforts = REMEDIATION_EFFORT.get(finding.category, {})
        return category_efforts.get(finding.severity, "1-2 hours")

    def _get_priority(self, finding: SecurityFinding) -> int:
        """Get priority number for a finding (1 = highest priority).
        
        Args:
            finding: Security finding
            
        Returns:
            Priority number (1-5)
        """
        severity_priority = {
            Severity.CRITICAL: 1,
            Severity.HIGH: 2,
            Severity.MEDIUM: 3,
            Severity.LOW: 4,
            Severity.INFO: 5,
        }
        return severity_priority.get(finding.severity, 5)

    def generate_remediation_plan(self, findings: List[SecurityFinding]) -> str:
        """Generate prioritized remediation plan with effort estimates.
        
        Args:
            findings: List of security findings
            
        Returns:
            Markdown formatted remediation plan
        """
        if not findings:
            return "## Remediation Plan\n\nNo remediation actions required.\n"
        
        sorted_findings = self.sort_findings_by_severity(findings)
        
        lines = [
            "## Remediation Plan",
            "",
            "The following actions are prioritized by severity. "
            "Address Critical and High severity items first.",
            "",
            "| Priority | ID | Action | Estimated Effort |",
            "|----------|-----|--------|------------------|",
        ]
        
        for finding in sorted_findings:
            priority = self._get_priority(finding)
            effort = self._get_effort_estimate(finding)
            action = self._escape_markdown(finding.remediation)
            # Truncate long actions
            if len(action) > 60:
                action = action[:57] + "..."
            
            lines.append(f"| P{priority} | {finding.id} | {action} | {effort} |")
        
        lines.append("")
        
        # Add detailed remediation guidance by category
        lines.extend(self._generate_remediation_guidance(sorted_findings))
        
        return "\n".join(lines)

    def _generate_remediation_guidance(
        self, findings: List[SecurityFinding]
    ) -> List[str]:
        """Generate detailed remediation guidance grouped by category.
        
        Args:
            findings: List of security findings (already sorted)
            
        Returns:
            List of markdown lines with detailed guidance
        """
        lines = [
            "### Detailed Remediation Guidance",
            "",
        ]
        
        # Group findings by category
        categories_seen = set()
        for finding in findings:
            if finding.category not in categories_seen:
                categories_seen.add(finding.category)
                lines.extend(self._get_category_guidance(finding.category))
        
        return lines

    def _get_category_guidance(self, category: FindingCategory) -> List[str]:
        """Get remediation guidance for a specific category.
        
        Args:
            category: Finding category
            
        Returns:
            List of markdown lines with guidance
        """
        guidance = {
            FindingCategory.HARDCODED_SECRET: [
                "#### Hardcoded Secrets",
                "",
                "1. Remove all hardcoded secrets from source code",
                "2. Use environment variables or a secrets manager (AWS Secrets Manager, HashiCorp Vault)",
                "3. Rotate any exposed credentials immediately",
                "4. Add secret patterns to `.gitignore` and pre-commit hooks",
                "",
            ],
            FindingCategory.VULNERABLE_DEPENDENCY: [
                "#### Vulnerable Dependencies",
                "",
                "1. Update vulnerable packages to the recommended safe versions",
                "2. Run `pip-audit` or `npm audit` regularly",
                "3. Consider using Dependabot or Snyk for automated updates",
                "4. Review changelogs for breaking changes before updating",
                "",
            ],
            FindingCategory.MISSING_AUTHZ: [
                "#### Missing Authorization",
                "",
                "1. Add authentication middleware to all protected endpoints",
                "2. Implement role-based access control (RBAC) where appropriate",
                "3. Use framework-specific auth decorators (e.g., `@login_required`, `Depends()`)",
                "4. Audit all endpoints for proper authorization checks",
                "",
            ],
            FindingCategory.INJECTION_RISK: [
                "#### Injection Risks",
                "",
                "1. Use parameterized queries for all database operations",
                "2. Validate and sanitize all user inputs",
                "3. Avoid using `eval()`, `exec()`, or dynamic code execution",
                "4. Use allowlists for command execution when necessary",
                "",
            ],
            FindingCategory.INSECURE_CONFIG: [
                "#### Insecure Configuration",
                "",
                "1. Review and harden security configurations",
                "2. Disable debug mode in production",
                "3. Use secure defaults for all settings",
                "4. Implement proper CORS and CSP policies",
                "",
            ],
        }
        return guidance.get(category, [f"#### {category.value}", "", "Review and address findings.", ""])

    def generate_full_report(self, findings: List[SecurityFinding]) -> str:
        """Generate the complete security audit report.
        
        Args:
            findings: List of security findings
            
        Returns:
            Complete markdown report content
        """
        sections = [
            "# Security Audit Report",
            "",
            self.generate_executive_summary(findings),
            self.generate_findings_table(findings),
            self.generate_remediation_plan(findings),
            self._generate_footer(),
        ]
        return "\n".join(sections)

    def _generate_footer(self) -> str:
        """Generate report footer with metadata.
        
        Returns:
            Markdown formatted footer
        """
        return "\n".join([
            "---",
            "",
            "*This report was automatically generated by the Security Audit Scanner.*",
            "",
            f"*Report generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*",
            "",
        ])

    def write_report(
        self,
        findings: List[SecurityFinding],
        output_path: Optional[str] = None,
    ) -> str:
        """Write the complete SECURITY_AUDIT.md file.
        
        Args:
            findings: List of security findings
            output_path: Optional path for the report file. 
                        Defaults to SECURITY_AUDIT.md in current directory.
            
        Returns:
            Path to the written report file
        """
        if output_path is None:
            output_path = "SECURITY_AUDIT.md"
        
        report_content = self.generate_full_report(findings)
        
        output_file = Path(output_path)
        output_file.write_text(report_content, encoding="utf-8")
        
        return str(output_file.absolute())

    def write_report_to_root(
        self,
        findings: List[SecurityFinding],
        root_path: str,
    ) -> str:
        """Write the SECURITY_AUDIT.md file to the repository root.
        
        Args:
            findings: List of security findings
            root_path: Path to the repository root directory
            
        Returns:
            Path to the written report file
        """
        output_path = Path(root_path) / "SECURITY_AUDIT.md"
        return self.write_report(findings, str(output_path))
