"""Secret Scanner Module for detecting hardcoded secrets in source code.

This module provides functionality to scan source files for hardcoded secrets
such as API keys, AWS credentials, passwords, tokens, private keys, JWTs,
and connection strings using regex pattern matching.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Set, Tuple

from src.security.models import (
    FindingCategory,
    SecretFinding,
    Severity,
)


# ============================================================================
# Secret Detection Patterns
# ============================================================================

SECRET_PATTERNS: Dict[str, List[str]] = {
    "api_key": [
        r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        r'(?i)x-api-key\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    ],
    "aws_credentials": [
        r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[=:]\s*["\']?(AKIA[A-Z0-9]{16})["\']?',
        r'(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*[=:]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?',
    ],
    "generic_secret": [
        r'(?i)(password|passwd|pwd|secret|token)\s*[=:]\s*["\']?([^\s"\']{8,})["\']?',
    ],
    "private_key": [
        r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
        r'-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----',
        r'-----BEGIN\s+EC\s+PRIVATE\s+KEY-----',
        r'-----BEGIN\s+DSA\s+PRIVATE\s+KEY-----',
    ],
    "jwt_token": [
        r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
    ],
    "connection_string": [
        r'(?i)(mongodb|postgres|mysql|redis|postgresql)://[^\s"\']+',
        r'(?i)Data\s+Source=[^;]+;.*Password=[^;]+',
    ],
}

# Severity mapping for secret types
SECRET_SEVERITY: Dict[str, Severity] = {
    "api_key": Severity.HIGH,
    "aws_credentials": Severity.CRITICAL,
    "generic_secret": Severity.MEDIUM,
    "private_key": Severity.CRITICAL,
    "jwt_token": Severity.HIGH,
    "connection_string": Severity.CRITICAL,
}

# Files and directories to exclude from scanning
EXCLUDE_PATTERNS: List[str] = [
    r'\.git[/\\]',
    r'node_modules[/\\]',
    r'\.venv[/\\]',
    r'venv[/\\]',
    r'__pycache__[/\\]',
    r'\.env\.example$',
    r'\.md$',
    r'\.lock$',
    r'\.pyc$',
    r'\.pyo$',
    r'\.so$',
    r'\.dll$',
    r'\.exe$',
    r'\.bin$',
    r'\.png$',
    r'\.jpg$',
    r'\.jpeg$',
    r'\.gif$',
    r'\.ico$',
    r'\.svg$',
    r'\.woff$',
    r'\.woff2$',
    r'\.ttf$',
    r'\.eot$',
    r'\.pdf$',
    r'\.zip$',
    r'\.tar$',
    r'\.gz$',
    r'\.rar$',
    r'dist[/\\]',
    r'build[/\\]',
    r'\.egg-info[/\\]',
    r'\.pytest_cache[/\\]',
    r'\.hypothesis[/\\]',
]

# Compiled exclude patterns for performance
_COMPILED_EXCLUDE_PATTERNS: List[Pattern] = [
    re.compile(pattern) for pattern in EXCLUDE_PATTERNS
]


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class SecretMatch:
    """Represents a matched secret in source code."""
    secret_type: str
    matched_value: str
    line_number: int
    line_content: str
    pattern_used: str


# ============================================================================
# Secret Scanner Class
# ============================================================================

class SecretScanner:
    """Scanner for detecting hardcoded secrets in source code files."""
    
    def __init__(self, root_path: str):
        """Initialize the secret scanner.
        
        Args:
            root_path: Root directory path to scan
        """
        self.root_path = Path(root_path).resolve()
        self._finding_counter = 0
        self._compiled_patterns: Dict[str, List[Pattern]] = {}
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        for secret_type, patterns in SECRET_PATTERNS.items():
            self._compiled_patterns[secret_type] = [
                re.compile(pattern) for pattern in patterns
            ]
    
    def _should_exclude_path(self, file_path: str) -> bool:
        """Check if a file path should be excluded from scanning.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the path should be excluded
        """
        for pattern in _COMPILED_EXCLUDE_PATTERNS:
            if pattern.search(file_path):
                return True
        return False
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if a file is binary by reading first bytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file appears to be binary
        """
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(8192)
                # Check for null bytes which indicate binary content
                if b'\x00' in chunk:
                    return True
                return False
        except (IOError, OSError):
            return True
    
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
    
    def mask_secret(self, secret: str) -> str:
        """Mask a secret value for safe logging.
        
        Shows first 4 and last 2 characters for secrets longer than 8 chars.
        For shorter secrets, returns asterisks.
        
        Args:
            secret: The secret value to mask
            
        Returns:
            Masked secret string
        """
        if not secret:
            return "****"
        
        if len(secret) <= 8:
            return "*" * len(secret)
        
        return f"{secret[:4]}...{secret[-2:]}"
    
    def _extract_secret_value(self, match: re.Match, pattern: str) -> str:
        """Extract the actual secret value from a regex match.
        
        Args:
            match: The regex match object
            pattern: The pattern that was matched
            
        Returns:
            The extracted secret value
        """
        groups = match.groups()
        if groups:
            # Return the last non-None group (usually the secret value)
            for group in reversed(groups):
                if group:
                    return group
        return match.group(0)
    
    def _generate_finding_id(self) -> str:
        """Generate a unique finding ID.
        
        Returns:
            Unique finding ID string
        """
        self._finding_counter += 1
        return f"SEC-{self._finding_counter:03d}"
    
    def scan_file(self, file_path: Path) -> List[SecretFinding]:
        """Scan a single file for hardcoded secrets.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            List of SecretFinding objects for detected secrets
        """
        findings: List[SecretFinding] = []
        
        # Get relative path for reporting
        try:
            relative_path = str(file_path.relative_to(self.root_path))
        except ValueError:
            relative_path = str(file_path)
        
        # Check exclusions
        if self._should_exclude_path(relative_path):
            return findings
        
        # Skip binary files
        if self._is_binary_file(file_path):
            return findings
        
        # Read file content
        content = self._read_file_content(file_path)
        if content is None:
            return findings
        
        # Split into lines for line number tracking
        lines = content.split('\n')
        
        # Scan each line for secrets
        for line_num, line in enumerate(lines, start=1):
            for secret_type, patterns in self._compiled_patterns.items():
                for pattern in patterns:
                    for match in pattern.finditer(line):
                        secret_value = self._extract_secret_value(match, pattern.pattern)
                        masked_value = self.mask_secret(secret_value)
                        
                        finding = SecretFinding(
                            id=self._generate_finding_id(),
                            category=FindingCategory.HARDCODED_SECRET,
                            severity=SECRET_SEVERITY.get(secret_type, Severity.MEDIUM),
                            file_path=relative_path,
                            line_number=line_num,
                            description=f"Hardcoded {secret_type.replace('_', ' ')} detected",
                            evidence=f"Line {line_num}: {self._mask_line(line, secret_value)}",
                            remediation=self._get_remediation(secret_type),
                            secret_type=secret_type,
                            masked_value=masked_value,
                        )
                        findings.append(finding)
        
        return findings
    
    def _mask_line(self, line: str, secret: str) -> str:
        """Mask the secret value within a line of code.
        
        Args:
            line: The full line of code
            secret: The secret value to mask
            
        Returns:
            Line with secret masked
        """
        if not secret or secret not in line:
            return line.strip()
        
        masked = self.mask_secret(secret)
        return line.replace(secret, masked).strip()
    
    def _get_remediation(self, secret_type: str) -> str:
        """Get remediation guidance for a secret type.
        
        Args:
            secret_type: Type of secret detected
            
        Returns:
            Remediation guidance string
        """
        remediation_map = {
            "api_key": "Move API key to environment variable or secrets manager",
            "aws_credentials": "Use AWS IAM roles, environment variables, or AWS Secrets Manager",
            "generic_secret": "Move secret to environment variable or secure vault",
            "private_key": "Store private key in secure key management system, never commit to repository",
            "jwt_token": "Generate tokens dynamically, never hardcode JWT tokens",
            "connection_string": "Use environment variables or secrets manager for database credentials",
        }
        return remediation_map.get(secret_type, "Remove hardcoded secret and use secure storage")
    
    def get_source_files(self) -> List[Path]:
        """Get all source files in the repository for scanning.
        
        Returns:
            List of file paths to scan
        """
        source_files: List[Path] = []
        
        for root, dirs, files in os.walk(self.root_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude_path(os.path.join(root, d) + os.sep)]
            
            for file in files:
                file_path = Path(root) / file
                relative_path = str(file_path.relative_to(self.root_path))
                
                if not self._should_exclude_path(relative_path):
                    source_files.append(file_path)
        
        return source_files


    def scan_all_files(self) -> List[SecretFinding]:
        """Scan all source files in the repository for secrets.
        
        Returns:
            List of all SecretFinding objects found
        """
        all_findings: List[SecretFinding] = []
        source_files = self.get_source_files()
        
        for file_path in source_files:
            try:
                findings = self.scan_file(file_path)
                all_findings.extend(findings)
            except Exception:
                # Skip files that cause errors, continue scanning
                continue
        
        return all_findings
    
    def get_summary_by_type(self, findings: List[SecretFinding]) -> Dict[str, int]:
        """Get summary counts of findings by secret type.
        
        Args:
            findings: List of secret findings
            
        Returns:
            Dictionary mapping secret type to count
        """
        summary: Dict[str, int] = {}
        for finding in findings:
            secret_type = finding.secret_type
            summary[secret_type] = summary.get(secret_type, 0) + 1
        return summary
    
    def get_summary_by_severity(self, findings: List[SecretFinding]) -> Dict[str, int]:
        """Get summary counts of findings by severity.
        
        Args:
            findings: List of secret findings
            
        Returns:
            Dictionary mapping severity name to count
        """
        summary: Dict[str, int] = {}
        for finding in findings:
            severity_name = finding.severity.value
            summary[severity_name] = summary.get(severity_name, 0) + 1
        return summary
    
    def generate_scan_summary(self, findings: List[SecretFinding]) -> Dict:
        """Generate a complete scan summary.
        
        Args:
            findings: List of secret findings
            
        Returns:
            Dictionary containing summary statistics
        """
        return {
            "total_findings": len(findings),
            "by_type": self.get_summary_by_type(findings),
            "by_severity": self.get_summary_by_severity(findings),
            "files_with_secrets": len(set(f.file_path for f in findings)),
        }
