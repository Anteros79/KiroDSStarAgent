"""API Auditor Module for analyzing API endpoint security.

This module provides functionality to scan source files for API endpoint
definitions and analyze them for security vulnerabilities including
missing authorization, input validation issues, and injection risks.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Tuple

from src.security.models import (
    APIFinding,
    FindingCategory,
    Severity,
)


# ============================================================================
# Endpoint Detection Patterns
# ============================================================================

ENDPOINT_PATTERNS: Dict[str, List[str]] = {
    "fastapi": [
        r'@app\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']',
        r'@router\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']',
    ],
    "flask": [
        r'@app\.route\s*\(\s*["\']([^"\']+)["\'](?:.*?methods\s*=\s*\[([^\]]+)\])?',
        r'@blueprint\.route\s*\(\s*["\']([^"\']+)["\'](?:.*?methods\s*=\s*\[([^\]]+)\])?',
        r'@bp\.route\s*\(\s*["\']([^"\']+)["\'](?:.*?methods\s*=\s*\[([^\]]+)\])?',
    ],
    "express": [
        r'app\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']',
        r'router\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']',
    ],
}

# ============================================================================
# Authorization Detection Patterns
# ============================================================================

AUTHZ_INDICATORS: List[str] = [
    r'Depends\s*\(\s*get_current_user',
    r'Depends\s*\(\s*verify_token',
    r'Depends\s*\(\s*authenticate',
    r'Depends\s*\(\s*require_auth',
    r'@login_required',
    r'@jwt_required',
    r'@auth_required',
    r'@requires_auth',
    r'@token_required',
    r'@permission_required',
    r'@roles_required',
    r'authenticate\s*\(',
    r'authorization',
    r'verify_token',
    r'check_auth',
    r'isAuthenticated',
    r'requireAuth',
    r'passport\.authenticate',
    r'jwt\.verify',
    r'verifyToken',
]

# ============================================================================
# Injection Risk Patterns
# ============================================================================

INJECTION_RISK_PATTERNS: Dict[str, List[str]] = {
    "code_execution": [
        r'exec\s*\(',
        r'eval\s*\(',
        r'compile\s*\(',
    ],
    "command_injection": [
        r'subprocess\.(call|run|Popen|check_output|check_call)\s*\(',
        r'os\.system\s*\(',
        r'os\.popen\s*\(',
        r'commands\.getoutput\s*\(',
        r'child_process\.exec\s*\(',
        r'child_process\.spawn\s*\(',
    ],
    "sql_injection": [
        r'execute\s*\(\s*["\'].*%s',
        r'execute\s*\(\s*f["\']',
        r'\.format\s*\(.*\)\s*\)',
        r'cursor\.execute\s*\(\s*["\'].*\+',
    ],
    "path_traversal": [
        r'open\s*\(\s*request\.',
        r'os\.path\.join\s*\(.*request\.',
        r'send_file\s*\(\s*request\.',
    ],
}

# ============================================================================
# Unvalidated Input Patterns
# ============================================================================

UNVALIDATED_INPUT_PATTERNS: List[str] = [
    r'request\.(args|form|json|data|values|files)\s*\[',
    r'request\.(args|form|json|data|values|files)\.get\s*\(',
    r'request\.get_json\s*\(',
    r'f["\'].*\{.*request\.',
    r'\.format\s*\(.*request\.',
    r'%\s*\(.*request\.',
    r'req\.body\[',
    r'req\.query\[',
    r'req\.params\[',
]

# ============================================================================
# OWASP Top 10 Mapping
# ============================================================================

OWASP_MAPPING: Dict[str, str] = {
    "missing_auth": "A01:2021 - Broken Access Control",
    "code_execution": "A03:2021 - Injection",
    "command_injection": "A03:2021 - Injection",
    "sql_injection": "A03:2021 - Injection",
    "path_traversal": "A01:2021 - Broken Access Control",
    "unvalidated_input": "A03:2021 - Injection",
    "insecure_deserialization": "A08:2021 - Software and Data Integrity Failures",
}

# ============================================================================
# Files/directories to exclude from scanning
# ============================================================================

EXCLUDE_PATTERNS: List[str] = [
    r'\.git[/\\]',
    r'node_modules[/\\]',
    r'\.venv[/\\]',
    r'venv[/\\]',
    r'__pycache__[/\\]',
    r'\.pytest_cache[/\\]',
    r'\.hypothesis[/\\]',
    r'dist[/\\]',
    r'build[/\\]',
    r'\.egg-info[/\\]',
    r'test[s]?[/\\]',
]


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class APIEndpoint:
    """Represents a detected API endpoint."""
    file_path: str
    line_number: int
    endpoint_path: str
    http_method: str
    framework: str
    line_content: str
    function_context: str = ""


# ============================================================================
# API Auditor Class
# ============================================================================

class APIAuditor:
    """Auditor for analyzing API endpoint security vulnerabilities."""
    
    def __init__(self, root_path: str):
        """Initialize the API auditor.
        
        Args:
            root_path: Root directory path to scan
        """
        self.root_path = Path(root_path).resolve()
        self._finding_counter = 0
        self._compiled_endpoint_patterns: Dict[str, List[Pattern]] = {}
        self._compiled_authz_patterns: List[Pattern] = []
        self._compiled_injection_patterns: Dict[str, List[Pattern]] = {}
        self._compiled_input_patterns: List[Pattern] = []
        self._compiled_exclude_patterns: List[Pattern] = []
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        # Compile endpoint patterns
        for framework, patterns in ENDPOINT_PATTERNS.items():
            self._compiled_endpoint_patterns[framework] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for pattern in patterns
            ]
        
        # Compile authorization patterns
        self._compiled_authz_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in AUTHZ_INDICATORS
        ]
        
        # Compile injection risk patterns
        for risk_type, patterns in INJECTION_RISK_PATTERNS.items():
            self._compiled_injection_patterns[risk_type] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in patterns
            ]
        
        # Compile unvalidated input patterns
        self._compiled_input_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in UNVALIDATED_INPUT_PATTERNS
        ]
        
        # Compile exclude patterns
        self._compiled_exclude_patterns = [
            re.compile(pattern) for pattern in EXCLUDE_PATTERNS
        ]
    
    def _should_exclude_path(self, file_path: str) -> bool:
        """Check if a file path should be excluded from scanning.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the path should be excluded
        """
        for pattern in self._compiled_exclude_patterns:
            if pattern.search(file_path):
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
    
    def _generate_finding_id(self) -> str:
        """Generate a unique finding ID.
        
        Returns:
            Unique finding ID string
        """
        self._finding_counter += 1
        return f"API-{self._finding_counter:03d}"
    
    def _extract_function_context(self, content: str, line_number: int, window: int = 20) -> str:
        """Extract function context around an endpoint definition.
        
        Args:
            content: Full file content
            line_number: Line number of the endpoint
            window: Number of lines to include after the endpoint
            
        Returns:
            Function context string
        """
        lines = content.split('\n')
        start = max(0, line_number - 1)
        end = min(len(lines), line_number + window)
        return '\n'.join(lines[start:end])

    def find_endpoints(self, file_path: Path) -> List[APIEndpoint]:
        """Extract API endpoint definitions from a file.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            List of APIEndpoint objects for detected endpoints
        """
        endpoints: List[APIEndpoint] = []
        
        # Get relative path for reporting
        try:
            relative_path = str(file_path.relative_to(self.root_path))
        except ValueError:
            relative_path = str(file_path)
        
        # Check exclusions
        if self._should_exclude_path(relative_path):
            return endpoints
        
        # Read file content
        content = self._read_file_content(file_path)
        if content is None:
            return endpoints
        
        lines = content.split('\n')
        
        # Scan for endpoints using each framework's patterns
        for framework, patterns in self._compiled_endpoint_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(content):
                    # Calculate line number
                    line_start = content[:match.start()].count('\n') + 1
                    line_content = lines[line_start - 1] if line_start <= len(lines) else ""
                    
                    # Extract endpoint details based on framework
                    endpoint_path, http_method = self._extract_endpoint_details(
                        match, framework, pattern.pattern
                    )
                    
                    # Get function context for authorization checking
                    function_context = self._extract_function_context(content, line_start)
                    
                    endpoint = APIEndpoint(
                        file_path=relative_path,
                        line_number=line_start,
                        endpoint_path=endpoint_path,
                        http_method=http_method.upper(),
                        framework=framework,
                        line_content=line_content.strip(),
                        function_context=function_context,
                    )
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_endpoint_details(
        self, match: re.Match, framework: str, pattern: str
    ) -> Tuple[str, str]:
        """Extract endpoint path and HTTP method from a regex match.
        
        Args:
            match: The regex match object
            framework: The framework type
            pattern: The pattern that was matched
            
        Returns:
            Tuple of (endpoint_path, http_method)
        """
        groups = match.groups()
        
        if framework == "fastapi":
            # FastAPI: group 1 is method, group 2 is path
            http_method = groups[0] if groups else "GET"
            endpoint_path = groups[1] if len(groups) > 1 else "/"
        elif framework == "flask":
            # Flask: group 1 is path, group 2 is methods (optional)
            endpoint_path = groups[0] if groups else "/"
            methods_str = groups[1] if len(groups) > 1 and groups[1] else None
            if methods_str:
                # Parse methods like "'GET', 'POST'"
                methods = re.findall(r'["\'](\w+)["\']', methods_str)
                http_method = methods[0] if methods else "GET"
            else:
                http_method = "GET"
        elif framework == "express":
            # Express: group 1 is method, group 2 is path
            http_method = groups[0] if groups else "GET"
            endpoint_path = groups[1] if len(groups) > 1 else "/"
        else:
            endpoint_path = groups[0] if groups else "/"
            http_method = "GET"
        
        return endpoint_path, http_method
    
    def check_authorization(self, endpoint: APIEndpoint) -> bool:
        """Check if an endpoint has authorization controls.
        
        Args:
            endpoint: The API endpoint to check
            
        Returns:
            True if authorization is present, False otherwise
        """
        context = endpoint.function_context
        
        for pattern in self._compiled_authz_patterns:
            if pattern.search(context):
                return True
        
        return False
    
    def check_input_validation(self, endpoint: APIEndpoint) -> List[Tuple[str, int, str]]:
        """Check for unvalidated inputs that could lead to injection.
        
        Args:
            endpoint: The API endpoint to check
            
        Returns:
            List of tuples (vulnerability_type, line_offset, matched_content)
        """
        vulnerabilities: List[Tuple[str, int, str]] = []
        context_lines = endpoint.function_context.split('\n')
        
        # Check for unvalidated input access
        for i, line in enumerate(context_lines):
            for pattern in self._compiled_input_patterns:
                if pattern.search(line):
                    vulnerabilities.append(("unvalidated_input", i, line.strip()))
        
        # Check for injection risks
        for risk_type, patterns in self._compiled_injection_patterns.items():
            for i, line in enumerate(context_lines):
                for pattern in patterns:
                    if pattern.search(line):
                        vulnerabilities.append((risk_type, i, line.strip()))
        
        return vulnerabilities
    
    def classify_owasp(self, vulnerability_type: str) -> str:
        """Map vulnerability type to OWASP Top 10 category.
        
        Args:
            vulnerability_type: Type of vulnerability detected
            
        Returns:
            OWASP Top 10 category string
        """
        return OWASP_MAPPING.get(vulnerability_type, "A03:2021 - Injection")
    
    def _get_severity_for_vulnerability(self, vulnerability_type: str) -> Severity:
        """Get severity level for a vulnerability type.
        
        Args:
            vulnerability_type: Type of vulnerability
            
        Returns:
            Severity level
        """
        severity_map = {
            "missing_auth": Severity.HIGH,
            "code_execution": Severity.CRITICAL,
            "command_injection": Severity.CRITICAL,
            "sql_injection": Severity.CRITICAL,
            "path_traversal": Severity.HIGH,
            "unvalidated_input": Severity.MEDIUM,
        }
        return severity_map.get(vulnerability_type, Severity.MEDIUM)
    
    def _get_remediation(self, vulnerability_type: str) -> str:
        """Get remediation guidance for a vulnerability type.
        
        Args:
            vulnerability_type: Type of vulnerability
            
        Returns:
            Remediation guidance string
        """
        remediation_map = {
            "missing_auth": "Add authentication/authorization middleware or decorator to protect this endpoint",
            "code_execution": "Remove use of exec/eval. Use safe alternatives or strict input validation",
            "command_injection": "Use parameterized commands or subprocess with shell=False. Validate all inputs",
            "sql_injection": "Use parameterized queries or ORM. Never concatenate user input into SQL",
            "path_traversal": "Validate and sanitize file paths. Use os.path.basename() and whitelist allowed paths",
            "unvalidated_input": "Validate and sanitize all user inputs. Use schema validation libraries",
        }
        return remediation_map.get(vulnerability_type, "Review and secure this code pattern")

    def audit_endpoint(self, endpoint: APIEndpoint) -> List[APIFinding]:
        """Audit a single endpoint for security vulnerabilities.
        
        Args:
            endpoint: The API endpoint to audit
            
        Returns:
            List of APIFinding objects for detected vulnerabilities
        """
        findings: List[APIFinding] = []
        
        # Check for missing authorization
        has_auth = self.check_authorization(endpoint)
        if not has_auth:
            finding = APIFinding(
                id=self._generate_finding_id(),
                category=FindingCategory.MISSING_AUTHZ,
                severity=Severity.HIGH,
                file_path=endpoint.file_path,
                line_number=endpoint.line_number,
                description=f"Endpoint {endpoint.http_method} {endpoint.endpoint_path} lacks authorization controls",
                evidence=f"Line {endpoint.line_number}: {endpoint.line_content}",
                remediation=self._get_remediation("missing_auth"),
                owasp_category=self.classify_owasp("missing_auth"),
                endpoint_path=endpoint.endpoint_path,
                http_method=endpoint.http_method,
                vulnerability_type="missing_auth",
            )
            findings.append(finding)
        
        # Check for input validation issues and injection risks
        input_issues = self.check_input_validation(endpoint)
        for vuln_type, line_offset, matched_content in input_issues:
            actual_line = endpoint.line_number + line_offset
            
            # Determine category based on vulnerability type
            if vuln_type in ["code_execution", "command_injection", "sql_injection"]:
                category = FindingCategory.INJECTION_RISK
            else:
                category = FindingCategory.INJECTION_RISK
            
            finding = APIFinding(
                id=self._generate_finding_id(),
                category=category,
                severity=self._get_severity_for_vulnerability(vuln_type),
                file_path=endpoint.file_path,
                line_number=actual_line,
                description=f"{vuln_type.replace('_', ' ').title()} risk in endpoint {endpoint.http_method} {endpoint.endpoint_path}",
                evidence=f"Line {actual_line}: {matched_content}",
                remediation=self._get_remediation(vuln_type),
                owasp_category=self.classify_owasp(vuln_type),
                endpoint_path=endpoint.endpoint_path,
                http_method=endpoint.http_method,
                vulnerability_type=vuln_type,
            )
            findings.append(finding)
        
        return findings
    
    def audit_file(self, file_path: Path) -> List[APIFinding]:
        """Audit a single file for API security vulnerabilities.
        
        Args:
            file_path: Path to the file to audit
            
        Returns:
            List of APIFinding objects for detected vulnerabilities
        """
        findings: List[APIFinding] = []
        
        # Find all endpoints in the file
        endpoints = self.find_endpoints(file_path)
        
        # Audit each endpoint
        for endpoint in endpoints:
            endpoint_findings = self.audit_endpoint(endpoint)
            findings.extend(endpoint_findings)
        
        return findings
    
    def get_api_directories(self) -> List[Path]:
        """Get directories likely to contain API code.
        
        Returns:
            List of directory paths to scan
        """
        api_dirs: List[Path] = []
        
        # Common API directory names
        api_dir_names = ['api', 'routes', 'endpoints', 'controllers', 'views', 'handlers']
        
        for root, dirs, files in os.walk(self.root_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude_path(os.path.join(root, d) + os.sep)]
            
            root_path = Path(root)
            dir_name = root_path.name.lower()
            
            if dir_name in api_dir_names:
                api_dirs.append(root_path)
        
        # If no specific API directories found, scan src directory
        if not api_dirs:
            src_dir = self.root_path / 'src'
            if src_dir.exists():
                api_dirs.append(src_dir)
        
        return api_dirs
    
    def get_source_files(self, directories: Optional[List[Path]] = None) -> List[Path]:
        """Get all source files to scan for API endpoints.
        
        Args:
            directories: Optional list of directories to scan. If None, scans API directories.
            
        Returns:
            List of file paths to scan
        """
        source_files: List[Path] = []
        
        if directories is None:
            directories = self.get_api_directories()
        
        # If still no directories, scan from root
        if not directories:
            directories = [self.root_path]
        
        # File extensions to scan
        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx'}
        
        for directory in directories:
            if not directory.exists():
                continue
                
            for root, dirs, files in os.walk(directory):
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if not self._should_exclude_path(os.path.join(root, d) + os.sep)]
                
                for file in files:
                    file_path = Path(root) / file
                    
                    # Check extension
                    if file_path.suffix.lower() not in extensions:
                        continue
                    
                    try:
                        relative_path = str(file_path.relative_to(self.root_path))
                    except ValueError:
                        relative_path = str(file_path)
                    
                    if not self._should_exclude_path(relative_path):
                        source_files.append(file_path)
        
        return source_files
    
    def audit_all_files(self) -> List[APIFinding]:
        """Audit all API files in the repository.
        
        Returns:
            List of all APIFinding objects found
        """
        all_findings: List[APIFinding] = []
        source_files = self.get_source_files()
        
        for file_path in source_files:
            try:
                findings = self.audit_file(file_path)
                all_findings.extend(findings)
            except Exception:
                # Skip files that cause errors, continue scanning
                continue
        
        return all_findings
    
    def get_summary(self, findings: List[APIFinding]) -> Dict:
        """Generate a summary of API audit findings.
        
        Args:
            findings: List of API findings
            
        Returns:
            Dictionary containing summary statistics
        """
        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        by_endpoint: Dict[str, int] = {}
        
        for finding in findings:
            # Count by vulnerability type
            vuln_type = finding.vulnerability_type
            by_type[vuln_type] = by_type.get(vuln_type, 0) + 1
            
            # Count by severity
            severity_name = finding.severity.value
            by_severity[severity_name] = by_severity.get(severity_name, 0) + 1
            
            # Count by endpoint
            endpoint_key = f"{finding.http_method} {finding.endpoint_path}"
            by_endpoint[endpoint_key] = by_endpoint.get(endpoint_key, 0) + 1
        
        return {
            "total_findings": len(findings),
            "by_vulnerability_type": by_type,
            "by_severity": by_severity,
            "by_endpoint": by_endpoint,
            "endpoints_analyzed": len(set(f"{f.http_method} {f.endpoint_path}" for f in findings)),
        }
