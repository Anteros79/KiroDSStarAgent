"""Dependency Analyzer Module for detecting vulnerable dependencies.

This module provides functionality to parse dependency files (requirements.txt,
package.json) and cross-reference packages against CVE databases using
pip-audit and npm-audit.
"""

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.security.models import (
    DependencyFinding,
    FindingCategory,
    Severity,
)


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Dependency:
    """Represents a parsed dependency with name and version."""
    name: str
    version: str
    source_file: str
    
    def __str__(self) -> str:
        return f"{self.name}=={self.version}" if self.version else self.name


@dataclass
class CVERecord:
    """Represents a CVE vulnerability record."""
    cve_id: str
    severity: str
    description: str
    safe_version: Optional[str] = None
    cvss_score: Optional[float] = None


# ============================================================================
# Severity Mapping
# ============================================================================

def cvss_to_severity(cvss_score: Optional[float]) -> Severity:
    """Convert CVSS score to Severity enum.
    
    Args:
        cvss_score: CVSS score (0.0-10.0)
        
    Returns:
        Corresponding Severity level
    """
    if cvss_score is None:
        return Severity.MEDIUM
    
    if cvss_score >= 9.0:
        return Severity.CRITICAL
    elif cvss_score >= 7.0:
        return Severity.HIGH
    elif cvss_score >= 4.0:
        return Severity.MEDIUM
    elif cvss_score >= 0.1:
        return Severity.LOW
    else:
        return Severity.INFO


def severity_string_to_enum(severity_str: str) -> Severity:
    """Convert severity string to Severity enum.
    
    Args:
        severity_str: Severity string (e.g., "critical", "high")
        
    Returns:
        Corresponding Severity level
    """
    severity_map = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "moderate": Severity.MEDIUM,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
        "info": Severity.INFO,
    }
    return severity_map.get(severity_str.lower(), Severity.MEDIUM)


# ============================================================================
# Dependency Analyzer Class
# ============================================================================

class DependencyAnalyzer:
    """Analyzer for detecting vulnerable dependencies in project files."""
    
    def __init__(self, root_path: str):
        """Initialize the dependency analyzer.
        
        Args:
            root_path: Root directory path to scan for dependency files
        """
        self.root_path = Path(root_path).resolve()
        self._finding_counter = 0
        self.warnings: List[str] = []
    
    def _generate_finding_id(self) -> str:
        """Generate a unique finding ID.
        
        Returns:
            Unique finding ID string
        """
        self._finding_counter += 1
        return f"DEP-{self._finding_counter:03d}"
    
    # ========================================================================
    # Requirements.txt Parser
    # ========================================================================
    
    def parse_requirements_txt(self, file_path: Optional[Path] = None) -> List[Dependency]:
        """Parse Python requirements.txt file to extract dependencies.
        
        Args:
            file_path: Path to requirements.txt (defaults to root_path/requirements.txt)
            
        Returns:
            List of Dependency objects
        """
        if file_path is None:
            file_path = self.root_path / "requirements.txt"
        
        dependencies: List[Dependency] = []
        
        if not file_path.exists():
            self.warnings.append(f"Requirements file not found: {file_path}")
            logger.warning(f"Requirements file not found: {file_path}")
            return dependencies
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, OSError) as e:
            self.warnings.append(f"Error reading requirements file: {e}")
            logger.error(f"Error reading requirements file: {e}")
            return dependencies
        
        # Parse each line
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Skip -r (recursive includes), -e (editable), and other flags
            if line.startswith('-'):
                continue
            
            # Parse dependency line
            dep = self._parse_requirements_line(line, str(file_path))
            if dep:
                dependencies.append(dep)
        
        return dependencies
    
    def _parse_requirements_line(self, line: str, source_file: str) -> Optional[Dependency]:
        """Parse a single line from requirements.txt.
        
        Handles formats:
        - package==1.0.0
        - package>=1.0.0
        - package~=1.0.0
        - package[extra]==1.0.0
        - package (no version)
        
        Args:
            line: Single line from requirements.txt
            source_file: Source file path for reference
            
        Returns:
            Dependency object or None if parsing fails
        """
        # Remove inline comments
        if '#' in line:
            line = line.split('#')[0].strip()
        
        if not line:
            return None
        
        # Pattern to match package name with optional extras and version specifier
        # Matches: package, package[extra], package==1.0, package>=1.0, etc.
        pattern = r'^([a-zA-Z0-9_-]+)(?:\[([^\]]+)\])?(?:([<>=!~]+)(.+))?$'
        match = re.match(pattern, line)
        
        if match:
            name = match.group(1)
            # extras = match.group(2)  # Not used currently
            # operator = match.group(3)  # Not used currently
            version = match.group(4) or ""
            
            return Dependency(
                name=name,
                version=version.strip(),
                source_file=source_file
            )
        
        # Fallback: just use the line as package name
        return Dependency(
            name=line,
            version="",
            source_file=source_file
        )
    
    # ========================================================================
    # Package.json Parser
    # ========================================================================
    
    def parse_package_json(self, file_path: Optional[Path] = None) -> List[Dependency]:
        """Parse Node.js package.json file to extract dependencies.
        
        Args:
            file_path: Path to package.json (defaults to root_path/package.json)
            
        Returns:
            List of Dependency objects
        """
        if file_path is None:
            file_path = self.root_path / "package.json"
        
        dependencies: List[Dependency] = []
        
        if not file_path.exists():
            self.warnings.append(f"Package.json not found: {file_path}")
            logger.warning(f"Package.json not found: {file_path}")
            return dependencies
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.warnings.append(f"Malformed package.json: {e}")
            logger.error(f"Malformed package.json at {file_path}: {e}")
            return dependencies
        except (IOError, OSError) as e:
            self.warnings.append(f"Error reading package.json: {e}")
            logger.error(f"Error reading package.json: {e}")
            return dependencies
        
        source_file = str(file_path)
        
        # Parse dependencies
        if "dependencies" in data:
            for name, version in data["dependencies"].items():
                dep = self._parse_npm_version(name, version, source_file)
                dependencies.append(dep)
        
        # Parse devDependencies
        if "devDependencies" in data:
            for name, version in data["devDependencies"].items():
                dep = self._parse_npm_version(name, version, source_file)
                dependencies.append(dep)
        
        return dependencies
    
    def _parse_npm_version(self, name: str, version_spec: str, source_file: str) -> Dependency:
        """Parse npm version specifier to extract version.
        
        Handles formats:
        - ^1.0.0 (caret range)
        - ~1.0.0 (tilde range)
        - >=1.0.0 (range)
        - 1.0.0 (exact)
        - * (any)
        
        Args:
            name: Package name
            version_spec: Version specifier string
            source_file: Source file path for reference
            
        Returns:
            Dependency object
        """
        # Remove common prefixes to get base version
        version = version_spec.strip()
        
        # Remove ^, ~, >=, <=, >, <, = prefixes
        version = re.sub(r'^[\^~>=<]+', '', version)
        
        # Handle * or latest
        if version in ('*', 'latest', ''):
            version = "latest"
        
        return Dependency(
            name=name,
            version=version,
            source_file=source_file
        )
    
    # ========================================================================
    # Find All Dependency Files
    # ========================================================================
    
    def find_dependency_files(self) -> Dict[str, List[Path]]:
        """Find all dependency files in the repository.
        
        Returns:
            Dictionary mapping file type to list of file paths
        """
        files: Dict[str, List[Path]] = {
            "requirements.txt": [],
            "package.json": [],
        }
        
        for root, dirs, filenames in os.walk(self.root_path):
            # Skip common non-project directories
            dirs[:] = [d for d in dirs if d not in {
                '.git', 'node_modules', '.venv', 'venv', '__pycache__',
                'dist', 'build', '.pytest_cache', '.hypothesis'
            }]
            
            for filename in filenames:
                if filename == "requirements.txt":
                    files["requirements.txt"].append(Path(root) / filename)
                elif filename == "package.json":
                    files["package.json"].append(Path(root) / filename)
        
        return files
    
    def parse_all_dependencies(self) -> List[Dependency]:
        """Parse all dependency files in the repository.
        
        Returns:
            List of all dependencies found
        """
        all_dependencies: List[Dependency] = []
        dep_files = self.find_dependency_files()
        
        # Parse all requirements.txt files
        for req_file in dep_files["requirements.txt"]:
            deps = self.parse_requirements_txt(req_file)
            all_dependencies.extend(deps)
        
        # Parse all package.json files
        for pkg_file in dep_files["package.json"]:
            deps = self.parse_package_json(pkg_file)
            all_dependencies.extend(deps)
        
        if not all_dependencies:
            self.warnings.append("No dependency files found in repository")
            logger.warning("No dependency files found in repository")
        
        return all_dependencies

    
    # ========================================================================
    # CVE Lookup Integration
    # ========================================================================
    
    def check_python_cves(self, dependencies: List[Dependency]) -> List[DependencyFinding]:
        """Check Python dependencies for CVEs using pip-audit.
        
        Args:
            dependencies: List of Python dependencies to check
            
        Returns:
            List of DependencyFinding objects for vulnerable packages
        """
        findings: List[DependencyFinding] = []
        
        if not dependencies:
            return findings
        
        # Try to run pip-audit
        try:
            result = subprocess.run(
                ["pip-audit", "--format", "json", "--progress-spinner", "off"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.root_path)
            )
            
            if result.returncode == 0 or result.stdout:
                findings.extend(self._parse_pip_audit_output(result.stdout, dependencies))
            elif result.stderr:
                logger.warning(f"pip-audit warning: {result.stderr}")
                
        except FileNotFoundError:
            self.warnings.append("pip-audit not installed. Install with: pip install pip-audit")
            logger.warning("pip-audit not found. Skipping Python CVE check.")
        except subprocess.TimeoutExpired:
            self.warnings.append("pip-audit timed out")
            logger.warning("pip-audit timed out")
        except Exception as e:
            self.warnings.append(f"Error running pip-audit: {e}")
            logger.error(f"Error running pip-audit: {e}")
        
        return findings
    
    def _parse_pip_audit_output(self, output: str, dependencies: List[Dependency]) -> List[DependencyFinding]:
        """Parse pip-audit JSON output into findings.
        
        Args:
            output: JSON output from pip-audit
            dependencies: Original list of dependencies for reference
            
        Returns:
            List of DependencyFinding objects
        """
        findings: List[DependencyFinding] = []
        
        if not output.strip():
            return findings
        
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            logger.warning("Failed to parse pip-audit output")
            return findings
        
        # pip-audit returns a list of vulnerabilities
        vulnerabilities = data if isinstance(data, list) else data.get("vulnerabilities", [])
        
        # Create a map of package names to source files
        dep_source_map = {dep.name.lower(): dep.source_file for dep in dependencies}
        
        for vuln in vulnerabilities:
            package_name = vuln.get("name", "")
            current_version = vuln.get("version", "")
            
            # Get vulnerabilities for this package
            vulns = vuln.get("vulns", [])
            
            for v in vulns:
                cve_id = v.get("id", "UNKNOWN")
                description = v.get("description", "No description available")
                fix_versions = v.get("fix_versions", [])
                safe_version = fix_versions[0] if fix_versions else None
                
                # Determine severity from aliases or default to HIGH
                severity = Severity.HIGH
                aliases = v.get("aliases", [])
                for alias in aliases:
                    if "CRITICAL" in alias.upper():
                        severity = Severity.CRITICAL
                        break
                
                source_file = dep_source_map.get(package_name.lower(), "requirements.txt")
                
                finding = DependencyFinding(
                    id=self._generate_finding_id(),
                    category=FindingCategory.VULNERABLE_DEPENDENCY,
                    severity=severity,
                    file_path=source_file,
                    description=f"Vulnerable dependency: {package_name}=={current_version}",
                    evidence=f"CVE: {cve_id} - {description[:200]}",
                    remediation=f"Upgrade {package_name} to version {safe_version}" if safe_version else f"Review and update {package_name}",
                    cve_id=cve_id,
                    package_name=package_name,
                    current_version=current_version,
                    safe_version=safe_version,
                )
                findings.append(finding)
        
        return findings
    
    def check_npm_cves(self, dependencies: List[Dependency]) -> List[DependencyFinding]:
        """Check Node.js dependencies for CVEs using npm-audit.
        
        Args:
            dependencies: List of Node.js dependencies to check
            
        Returns:
            List of DependencyFinding objects for vulnerable packages
        """
        findings: List[DependencyFinding] = []
        
        if not dependencies:
            return findings
        
        # Find package.json directories
        dep_files = self.find_dependency_files()
        
        for pkg_json_path in dep_files["package.json"]:
            pkg_dir = pkg_json_path.parent
            
            # Check if node_modules exists (npm audit requires it)
            if not (pkg_dir / "node_modules").exists():
                self.warnings.append(f"node_modules not found in {pkg_dir}. Run 'npm install' first.")
                continue
            
            try:
                result = subprocess.run(
                    ["npm", "audit", "--json"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=str(pkg_dir)
                )
                
                # npm audit returns non-zero if vulnerabilities found
                if result.stdout:
                    findings.extend(self._parse_npm_audit_output(
                        result.stdout, 
                        dependencies,
                        str(pkg_json_path)
                    ))
                    
            except FileNotFoundError:
                self.warnings.append("npm not installed. Install Node.js to use npm audit.")
                logger.warning("npm not found. Skipping Node.js CVE check.")
            except subprocess.TimeoutExpired:
                self.warnings.append("npm audit timed out")
                logger.warning("npm audit timed out")
            except Exception as e:
                self.warnings.append(f"Error running npm audit: {e}")
                logger.error(f"Error running npm audit: {e}")
        
        return findings
    
    def _parse_npm_audit_output(
        self, 
        output: str, 
        dependencies: List[Dependency],
        source_file: str
    ) -> List[DependencyFinding]:
        """Parse npm audit JSON output into findings.
        
        Args:
            output: JSON output from npm audit
            dependencies: Original list of dependencies for reference
            source_file: Source package.json file path
            
        Returns:
            List of DependencyFinding objects
        """
        findings: List[DependencyFinding] = []
        
        if not output.strip():
            return findings
        
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            logger.warning("Failed to parse npm audit output")
            return findings
        
        # npm audit v7+ format
        vulnerabilities = data.get("vulnerabilities", {})
        
        for package_name, vuln_info in vulnerabilities.items():
            severity_str = vuln_info.get("severity", "moderate")
            severity = severity_string_to_enum(severity_str)
            
            # Get via information for affected versions
            via = vuln_info.get("via", [])
            
            # Get fix information
            fix_available = vuln_info.get("fixAvailable", False)
            
            # Extract CVE IDs and descriptions from via
            cve_ids = []
            descriptions = []
            
            for v in via:
                if isinstance(v, dict):
                    if "url" in v:
                        # Extract CVE from URL if present
                        url = v.get("url", "")
                        cve_match = re.search(r'(CVE-\d{4}-\d+)', url)
                        if cve_match:
                            cve_ids.append(cve_match.group(1))
                    
                    title = v.get("title", "")
                    if title:
                        descriptions.append(title)
                elif isinstance(v, str):
                    # Reference to another vulnerable package
                    descriptions.append(f"Depends on vulnerable {v}")
            
            cve_id = cve_ids[0] if cve_ids else "NPM-ADVISORY"
            description = "; ".join(descriptions) if descriptions else "Vulnerability detected"
            
            # Get current version from range
            current_version = vuln_info.get("range", "unknown")
            
            # Determine safe version
            safe_version = None
            if fix_available:
                if isinstance(fix_available, dict):
                    safe_version = fix_available.get("version")
                else:
                    safe_version = "latest"
            
            finding = DependencyFinding(
                id=self._generate_finding_id(),
                category=FindingCategory.VULNERABLE_DEPENDENCY,
                severity=severity,
                file_path=source_file,
                description=f"Vulnerable dependency: {package_name}",
                evidence=f"{cve_id}: {description[:200]}",
                remediation=f"Upgrade {package_name} to version {safe_version}" if safe_version else f"Review and update {package_name}",
                cve_id=cve_id,
                package_name=package_name,
                current_version=current_version,
                safe_version=safe_version,
            )
            findings.append(finding)
        
        return findings
    
    # ========================================================================
    # Main Analysis Method
    # ========================================================================
    
    def analyze_all(self) -> Tuple[List[Dependency], List[DependencyFinding]]:
        """Run complete dependency analysis.
        
        Parses all dependency files and checks for CVEs.
        
        Returns:
            Tuple of (all dependencies, all findings)
        """
        # Parse all dependencies
        all_dependencies = self.parse_all_dependencies()
        
        # Separate Python and Node.js dependencies
        python_deps = [d for d in all_dependencies if d.source_file.endswith('.txt')]
        node_deps = [d for d in all_dependencies if d.source_file.endswith('.json')]
        
        # Check for CVEs
        findings: List[DependencyFinding] = []
        
        if python_deps:
            python_findings = self.check_python_cves(python_deps)
            findings.extend(python_findings)
        
        if node_deps:
            node_findings = self.check_npm_cves(node_deps)
            findings.extend(node_findings)
        
        return all_dependencies, findings
    
    def get_summary(
        self, 
        dependencies: List[Dependency], 
        findings: List[DependencyFinding]
    ) -> Dict:
        """Generate a summary of the dependency analysis.
        
        Args:
            dependencies: List of all parsed dependencies
            findings: List of vulnerability findings
            
        Returns:
            Dictionary containing summary statistics
        """
        severity_counts = {}
        for finding in findings:
            severity_name = finding.severity.value
            severity_counts[severity_name] = severity_counts.get(severity_name, 0) + 1
        
        return {
            "total_dependencies": len(dependencies),
            "total_vulnerabilities": len(findings),
            "by_severity": severity_counts,
            "python_dependencies": len([d for d in dependencies if d.source_file.endswith('.txt')]),
            "node_dependencies": len([d for d in dependencies if d.source_file.endswith('.json')]),
            "warnings": self.warnings,
        }
