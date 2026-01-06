"""Tests for the API Auditor module.

This module tests the API endpoint detection, authorization checking,
and input validation analysis functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.security.api_auditor import (
    APIAuditor,
    APIEndpoint,
    ENDPOINT_PATTERNS,
    AUTHZ_INDICATORS,
    INJECTION_RISK_PATTERNS,
    OWASP_MAPPING,
)
from src.security.models import (
    APIFinding,
    FindingCategory,
    Severity,
)


class TestEndpointDetection:
    """Tests for API endpoint detection across different frameworks."""
    
    def test_fastapi_endpoint_detection(self, tmp_path):
        """Test detection of FastAPI endpoints."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    return []

@app.post("/users")
def create_user():
    return {}

@router.delete("/users/{id}")
def delete_user(id: int):
    return {}
''')
        
        auditor = APIAuditor(str(tmp_path))
        endpoints = auditor.find_endpoints(test_file)
        
        # Should find endpoints (may match multiple frameworks due to similar patterns)
        assert len(endpoints) >= 3
        
        # Check that we found the expected paths
        paths = [e.endpoint_path for e in endpoints]
        assert "/users" in paths
        assert "/users/{id}" in paths
        
        # Check that FastAPI framework was detected
        fastapi_endpoints = [e for e in endpoints if e.framework == "fastapi"]
        assert len(fastapi_endpoints) >= 3
    
    def test_flask_endpoint_detection(self, tmp_path):
        """Test detection of Flask endpoints."""
        test_file = tmp_path / "routes.py"
        test_file.write_text('''
from flask import Flask, Blueprint

app = Flask(__name__)
bp = Blueprint('api', __name__)

@app.route("/health")
def health():
    return "OK"

@app.route("/users", methods=['GET', 'POST'])
def users():
    return []

@bp.route("/items")
def items():
    return []
''')
        
        auditor = APIAuditor(str(tmp_path))
        endpoints = auditor.find_endpoints(test_file)
        
        assert len(endpoints) >= 2
        
        # Check health endpoint
        health_endpoint = next((e for e in endpoints if "/health" in e.endpoint_path), None)
        assert health_endpoint is not None
        assert health_endpoint.framework == "flask"
    
    def test_express_endpoint_detection(self, tmp_path):
        """Test detection of Express.js endpoints."""
        test_file = tmp_path / "routes.js"
        test_file.write_text('''
const express = require('express');
const app = express();
const router = express.Router();

app.get('/api/users', (req, res) => {
    res.json([]);
});

router.post('/api/items', (req, res) => {
    res.json({});
});

app.delete('/api/users/:id', (req, res) => {
    res.status(204).send();
});
''')
        
        auditor = APIAuditor(str(tmp_path))
        endpoints = auditor.find_endpoints(test_file)
        
        assert len(endpoints) == 3
        
        # Check GET endpoint
        get_endpoint = next(e for e in endpoints if e.http_method == "GET")
        assert get_endpoint.endpoint_path == "/api/users"
        assert get_endpoint.framework == "express"


class TestAuthorizationChecker:
    """Tests for authorization detection."""
    
    def test_detects_fastapi_depends_auth(self, tmp_path):
        """Test detection of FastAPI Depends authentication."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/protected")
def protected_route(user = Depends(get_current_user)):
    return {"user": user}
''')
        
        auditor = APIAuditor(str(tmp_path))
        endpoints = auditor.find_endpoints(test_file)
        
        assert len(endpoints) >= 1
        # All detected endpoints should have auth (since they all share the same context)
        for endpoint in endpoints:
            assert auditor.check_authorization(endpoint) is True
    
    def test_detects_flask_login_required(self, tmp_path):
        """Test detection of Flask login_required decorator."""
        test_file = tmp_path / "routes.py"
        test_file.write_text('''
from flask import Flask
from flask_login import login_required

app = Flask(__name__)

@app.route("/dashboard")
@login_required
def dashboard():
    return "Dashboard"
''')
        
        auditor = APIAuditor(str(tmp_path))
        endpoints = auditor.find_endpoints(test_file)
        
        assert len(endpoints) >= 1
        # All detected endpoints should have auth
        for endpoint in endpoints:
            assert auditor.check_authorization(endpoint) is True
    
    def test_detects_missing_auth(self, tmp_path):
        """Test detection of endpoints without authorization."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.get("/public")
def public_route():
    return {"status": "ok"}
''')
        
        auditor = APIAuditor(str(tmp_path))
        endpoints = auditor.find_endpoints(test_file)
        
        assert len(endpoints) >= 1
        # All detected endpoints should NOT have auth
        for endpoint in endpoints:
            assert auditor.check_authorization(endpoint) is False


class TestInputValidationChecker:
    """Tests for input validation and injection risk detection."""
    
    def test_detects_unvalidated_request_data(self, tmp_path):
        """Test detection of unvalidated request data access."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/users")
async def create_user(request: Request):
    data = await request.json()
    name = request.args["name"]
    return {"name": name}
''')
        
        auditor = APIAuditor(str(tmp_path))
        endpoints = auditor.find_endpoints(test_file)
        
        assert len(endpoints) >= 1
        
        # Check that at least one endpoint has unvalidated input issues
        all_issues = []
        for endpoint in endpoints:
            issues = auditor.check_input_validation(endpoint)
            all_issues.extend(issues)
        
        # Should detect request.args access
        assert len(all_issues) >= 1
        assert any(vuln_type == "unvalidated_input" for vuln_type, _, _ in all_issues)
    
    def test_detects_code_execution_risk(self, tmp_path):
        """Test detection of code execution risks (eval, exec)."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.post("/execute")
def execute_code(code: str):
    result = eval(code)
    return {"result": result}
''')
        
        auditor = APIAuditor(str(tmp_path))
        endpoints = auditor.find_endpoints(test_file)
        
        assert len(endpoints) >= 1
        
        # Check that at least one endpoint has code execution issues
        all_issues = []
        for endpoint in endpoints:
            issues = auditor.check_input_validation(endpoint)
            all_issues.extend(issues)
        
        # Should detect eval usage
        assert len(all_issues) >= 1
        assert any(vuln_type == "code_execution" for vuln_type, _, _ in all_issues)
    
    def test_detects_command_injection_risk(self, tmp_path):
        """Test detection of command injection risks."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
from fastapi import FastAPI
import subprocess
import os

app = FastAPI()

@app.post("/run")
def run_command(cmd: str):
    result = subprocess.run(cmd, shell=True)
    os.system(cmd)
    return {"status": "done"}
''')
        
        auditor = APIAuditor(str(tmp_path))
        endpoints = auditor.find_endpoints(test_file)
        
        assert len(endpoints) >= 1
        
        # Check that at least one endpoint has command injection issues
        all_issues = []
        for endpoint in endpoints:
            issues = auditor.check_input_validation(endpoint)
            all_issues.extend(issues)
        
        # Should detect subprocess and os.system usage
        assert len(all_issues) >= 2
        assert any(vuln_type == "command_injection" for vuln_type, _, _ in all_issues)


class TestOWASPClassification:
    """Tests for OWASP Top 10 classification."""
    
    def test_owasp_mapping_completeness(self):
        """Test that all vulnerability types have OWASP mappings."""
        auditor = APIAuditor(".")
        
        vuln_types = [
            "missing_auth",
            "code_execution",
            "command_injection",
            "sql_injection",
            "path_traversal",
            "unvalidated_input",
        ]
        
        for vuln_type in vuln_types:
            owasp = auditor.classify_owasp(vuln_type)
            assert owasp is not None
            assert "A0" in owasp  # OWASP categories start with A0X
    
    def test_injection_risks_map_to_a03(self):
        """Test that injection risks map to A03:2021."""
        auditor = APIAuditor(".")
        
        injection_types = ["code_execution", "command_injection", "sql_injection"]
        
        for vuln_type in injection_types:
            owasp = auditor.classify_owasp(vuln_type)
            assert "A03:2021" in owasp


class TestFullAudit:
    """Tests for full API audit functionality."""
    
    def test_audit_generates_findings(self, tmp_path):
        """Test that audit generates appropriate findings."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    return []

@app.post("/execute")
def execute(code: str):
    return eval(code)
''')
        
        auditor = APIAuditor(str(tmp_path))
        findings = auditor.audit_file(test_file)
        
        # Should have findings for missing auth and code execution
        assert len(findings) >= 2
        
        # Check finding structure
        for finding in findings:
            assert isinstance(finding, APIFinding)
            assert finding.id.startswith("API-")
            assert finding.endpoint_path is not None
            assert finding.http_method is not None
            assert finding.owasp_category is not None
    
    def test_audit_summary(self, tmp_path):
        """Test audit summary generation."""
        test_file = tmp_path / "api.py"
        test_file.write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.get("/a")
def a():
    return []

@app.get("/b")
def b():
    return []
''')
        
        auditor = APIAuditor(str(tmp_path))
        findings = auditor.audit_file(test_file)
        summary = auditor.get_summary(findings)
        
        assert "total_findings" in summary
        assert "by_vulnerability_type" in summary
        assert "by_severity" in summary
        assert summary["total_findings"] == len(findings)


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_file(self, tmp_path):
        """Test handling of empty files."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")
        
        auditor = APIAuditor(str(tmp_path))
        endpoints = auditor.find_endpoints(test_file)
        
        assert endpoints == []
    
    def test_non_api_file(self, tmp_path):
        """Test handling of files without API endpoints."""
        test_file = tmp_path / "utils.py"
        test_file.write_text('''
def helper_function():
    return "helper"

class UtilityClass:
    pass
''')
        
        auditor = APIAuditor(str(tmp_path))
        endpoints = auditor.find_endpoints(test_file)
        
        assert endpoints == []
    
    def test_excluded_directories(self, tmp_path):
        """Test that excluded directories are skipped."""
        # Create a test directory in node_modules
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        test_file = node_modules / "api.js"
        test_file.write_text('''
app.get('/test', (req, res) => {
    res.json({});
});
''')
        
        auditor = APIAuditor(str(tmp_path))
        source_files = auditor.get_source_files([tmp_path])
        
        # node_modules should be excluded
        assert not any("node_modules" in str(f) for f in source_files)
