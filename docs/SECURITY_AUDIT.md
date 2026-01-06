# Security Audit Report

## Executive Summary

**Scan Date:** 2026-01-06 05:45:15 UTC

**Overall Risk Assessment:** CRITICAL

### Key Metrics

| Metric | Count |
|--------|-------|
| Total Findings | 67 |
| Critical | 3 |
| High | 52 |
| Medium | 12 |
| Low | 0 |
| Informational | 0 |

### Findings by Category

| Category | Count |
|----------|-------|
| Hardcoded Secret | 33 |
| Missing Authorization | 32 |
| Injection Risk | 2 |

## Critical Findings

| ID | Category | Severity | Location | Description |
|----|----------|----------|----------|-------------|
| SEC-020 | Hardcoded Secret | Critical | `tests\test_secret_scanner.py:117` | Hardcoded aws credentials detected |
| SEC-023 | Hardcoded Secret | Critical | `tests\test_secret_scanner.py:155` | Hardcoded private key detected |
| SEC-024 | Hardcoded Secret | Critical | `tests\test_secret_scanner.py:167` | Hardcoded connection string detected |
| SEC-002 | Hardcoded Secret | High | `tests\test_annotation_injector.py:189` | Hardcoded api key detected |
| SEC-003 | Hardcoded Secret | High | `tests\test_annotation_injector.py:216` | Hardcoded api key detected |
| SEC-005 | Hardcoded Secret | High | `tests\test_annotation_injector.py:300` | Hardcoded api key detected |
| SEC-006 | Hardcoded Secret | High | `tests\test_annotation_injector.py:328` | Hardcoded api key detected |
| SEC-007 | Hardcoded Secret | High | `tests\test_annotation_injector.py:358` | Hardcoded api key detected |
| SEC-009 | Hardcoded Secret | High | `tests\test_annotation_injector.py:406` | Hardcoded api key detected |
| SEC-010 | Hardcoded Secret | High | `tests\test_annotation_injector.py:566` | Hardcoded api key detected |
| SEC-011 | Hardcoded Secret | High | `tests\test_annotation_injector.py:596` | Hardcoded api key detected |
| SEC-012 | Hardcoded Secret | High | `tests\test_annotation_injector.py:633` | Hardcoded api key detected |
| SEC-013 | Hardcoded Secret | High | `tests\test_annotation_injector.py:661` | Hardcoded api key detected |
| SEC-015 | Hardcoded Secret | High | `tests\test_annotation_injector.py:716` | Hardcoded api key detected |
| SEC-016 | Hardcoded Secret | High | `tests\test_annotation_injector.py:771` | Hardcoded api key detected |
| SEC-018 | Hardcoded Secret | High | `tests\test_annotation_injector.py:822` | Hardcoded api key detected |
| SEC-019 | Hardcoded Secret | High | `tests\test_secret_scanner.py:105` | Hardcoded api key detected |
| SEC-022 | Hardcoded Secret | High | `tests\test_secret_scanner.py:142` | Hardcoded jwt token detected |
| SEC-025 | Hardcoded Secret | High | `tests\test_secret_scanner.py:194` | Hardcoded api key detected |
| SEC-027 | Hardcoded Secret | High | `tests\test_secret_scanner.py:238` | Hardcoded api key detected |
| SEC-029 | Hardcoded Secret | High | `tests\test_secret_scanner.py:250` | Hardcoded api key detected |
| SEC-031 | Hardcoded Secret | High | `tests\test_secret_scanner.py:263` | Hardcoded api key detected |
| SEC-033 | Hardcoded Secret | High | `tests\test_secret_scanner.py:276` | Hardcoded api key detected |
| API-001 | Missing Authorization | High | `src\api\server.py:1099` | Endpoint GET /health lacks authorization controls |
| API-002 | Missing Authorization | High | `src\api\server.py:1105` | Endpoint GET / lacks authorization controls |
| API-003 | Missing Authorization | High | `src\api\server.py:1125` | Endpoint GET /api/status lacks authorization controls |
| API-004 | Missing Authorization | High | `src\api\server.py:1167` | Endpoint GET /api/me lacks authorization controls |
| API-005 | Missing Authorization | High | `src\api\server.py:1174` | Endpoint POST /api/me/select lacks authorization controls |
| API-006 | Missing Authorization | High | `src\api\server.py:1185` | Endpoint GET /api/techops/kpis lacks authorization controls |
| API-007 | Missing Authorization | High | `src\api\server.py:1232` | Endpoint GET /api/techops/dashboard/weekly lacks authorization controls |
| API-008 | Missing Authorization | High | `src\api\server.py:1243` | Endpoint GET /api/techops/dashboard/daily lacks authorization controls |
| API-009 | Missing Authorization | High | `src\api\server.py:1254` | Endpoint GET /api/techops/signals/active lacks authorization controls |
| API-010 | Missing Authorization | High | `src\api\server.py:1277` | Endpoint POST /api/techops/investigations lacks authorization controls |
| API-011 | Missing Authorization | High | `src\api\server.py:1390` | Endpoint GET /api/techops/investigations lacks authorization controls |
| API-012 | Missing Authorization | High | `src\api\server.py:1402` | Endpoint GET /api/techops/investigations/{investigation_id} lacks authorizati... |
| API-013 | Missing Authorization | High | `src\api\server.py:1410` | Endpoint POST /api/techops/investigations/{investigation_id}/finalize lacks a... |
| API-014 | Missing Authorization | High | `src\api\server.py:1425` | Endpoint POST /api/query lacks authorization controls |
| API-016 | Missing Authorization | High | `src\api\server.py:2043` | Endpoint GET /api/history lacks authorization controls |
| API-017 | Missing Authorization | High | `src\api\server.py:2052` | Endpoint DELETE /api/history lacks authorization controls |
| API-018 | Missing Authorization | High | `src\api\server.py:1099` | Endpoint GET /health lacks authorization controls |
| API-019 | Missing Authorization | High | `src\api\server.py:1105` | Endpoint GET / lacks authorization controls |
| API-020 | Missing Authorization | High | `src\api\server.py:1125` | Endpoint GET /api/status lacks authorization controls |
| API-021 | Missing Authorization | High | `src\api\server.py:1167` | Endpoint GET /api/me lacks authorization controls |
| API-022 | Missing Authorization | High | `src\api\server.py:1174` | Endpoint POST /api/me/select lacks authorization controls |
| API-023 | Missing Authorization | High | `src\api\server.py:1185` | Endpoint GET /api/techops/kpis lacks authorization controls |
| API-024 | Missing Authorization | High | `src\api\server.py:1232` | Endpoint GET /api/techops/dashboard/weekly lacks authorization controls |
| API-025 | Missing Authorization | High | `src\api\server.py:1243` | Endpoint GET /api/techops/dashboard/daily lacks authorization controls |
| API-026 | Missing Authorization | High | `src\api\server.py:1254` | Endpoint GET /api/techops/signals/active lacks authorization controls |
| API-027 | Missing Authorization | High | `src\api\server.py:1277` | Endpoint POST /api/techops/investigations lacks authorization controls |
| API-028 | Missing Authorization | High | `src\api\server.py:1390` | Endpoint GET /api/techops/investigations lacks authorization controls |
| API-029 | Missing Authorization | High | `src\api\server.py:1402` | Endpoint GET /api/techops/investigations/{investigation_id} lacks authorizati... |
| API-030 | Missing Authorization | High | `src\api\server.py:1410` | Endpoint POST /api/techops/investigations/{investigation_id}/finalize lacks a... |
| API-031 | Missing Authorization | High | `src\api\server.py:1425` | Endpoint POST /api/query lacks authorization controls |
| API-033 | Missing Authorization | High | `src\api\server.py:2043` | Endpoint GET /api/history lacks authorization controls |
| API-034 | Missing Authorization | High | `src\api\server.py:2052` | Endpoint DELETE /api/history lacks authorization controls |
| SEC-001 | Hardcoded Secret | Medium | `src\security\models.py:33` | Hardcoded generic secret detected |
| SEC-004 | Hardcoded Secret | Medium | `tests\test_annotation_injector.py:222` | Hardcoded generic secret detected |
| SEC-008 | Hardcoded Secret | Medium | `tests\test_annotation_injector.py:358` | Hardcoded generic secret detected |
| SEC-014 | Hardcoded Secret | Medium | `tests\test_annotation_injector.py:662` | Hardcoded generic secret detected |
| SEC-017 | Hardcoded Secret | Medium | `tests\test_annotation_injector.py:815` | Hardcoded generic secret detected |
| SEC-021 | Hardcoded Secret | Medium | `tests\test_secret_scanner.py:129` | Hardcoded generic secret detected |
| SEC-026 | Hardcoded Secret | Medium | `tests\test_secret_scanner.py:217` | Hardcoded generic secret detected |
| SEC-028 | Hardcoded Secret | Medium | `tests\test_secret_scanner.py:240` | Hardcoded generic secret detected |
| SEC-030 | Hardcoded Secret | Medium | `tests\test_secret_scanner.py:251` | Hardcoded generic secret detected |
| SEC-032 | Hardcoded Secret | Medium | `tests\test_secret_scanner.py:264` | Hardcoded generic secret detected |
| API-015 | Injection Risk | Medium | `src\api\server.py:1432` | Unvalidated Input risk in endpoint POST /api/query |
| API-032 | Injection Risk | Medium | `src\api\server.py:1432` | Unvalidated Input risk in endpoint POST /api/query |

## Remediation Plan

The following actions are prioritized by severity. Address Critical and High severity items first.

| Priority | ID | Action | Estimated Effort |
|----------|-----|--------|------------------|
| P1 | SEC-020 | Use AWS IAM roles, environment variables, or AWS Secrets ... | 1-2 hours |
| P1 | SEC-023 | Store private key in secure key management system, never ... | 1-2 hours |
| P1 | SEC-024 | Use environment variables or secrets manager for database... | 1-2 hours |
| P2 | SEC-002 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-003 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-005 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-006 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-007 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-009 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-010 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-011 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-012 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-013 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-015 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-016 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-018 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-019 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-022 | Generate tokens dynamically, never hardcode JWT tokens | 1-2 hours |
| P2 | SEC-025 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-027 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-029 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-031 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | SEC-033 | Move API key to environment variable or secrets manager | 1-2 hours |
| P2 | API-001 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-002 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-003 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-004 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-005 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-006 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-007 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-008 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-009 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-010 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-011 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-012 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-013 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-014 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-016 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-017 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-018 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-019 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-020 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-021 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-022 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-023 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-024 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-025 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-026 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-027 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-028 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-029 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-030 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-031 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-033 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P2 | API-034 | Add authentication/authorization middleware or decorator ... | 2-4 hours |
| P3 | SEC-001 | Move secret to environment variable or secure vault | 30 minutes |
| P3 | SEC-004 | Move secret to environment variable or secure vault | 30 minutes |
| P3 | SEC-008 | Move secret to environment variable or secure vault | 30 minutes |
| P3 | SEC-014 | Move secret to environment variable or secure vault | 30 minutes |
| P3 | SEC-017 | Move secret to environment variable or secure vault | 30 minutes |
| P3 | SEC-021 | Move secret to environment variable or secure vault | 30 minutes |
| P3 | SEC-026 | Move secret to environment variable or secure vault | 30 minutes |
| P3 | SEC-028 | Move secret to environment variable or secure vault | 30 minutes |
| P3 | SEC-030 | Move secret to environment variable or secure vault | 30 minutes |
| P3 | SEC-032 | Move secret to environment variable or secure vault | 30 minutes |
| P3 | API-015 | Validate and sanitize all user inputs. Use schema validat... | 1-2 hours |
| P3 | API-032 | Validate and sanitize all user inputs. Use schema validat... | 1-2 hours |

### Detailed Remediation Guidance

#### Hardcoded Secrets

1. Remove all hardcoded secrets from source code
2. Use environment variables or a secrets manager (AWS Secrets Manager, HashiCorp Vault)
3. Rotate any exposed credentials immediately
4. Add secret patterns to `.gitignore` and pre-commit hooks

#### Missing Authorization

1. Add authentication middleware to all protected endpoints
2. Implement role-based access control (RBAC) where appropriate
3. Use framework-specific auth decorators (e.g., `@login_required`, `Depends()`)
4. Audit all endpoints for proper authorization checks

#### Injection Risks

1. Use parameterized queries for all database operations
2. Validate and sanitize all user inputs
3. Avoid using `eval()`, `exec()`, or dynamic code execution
4. Use allowlists for command execution when necessary

---

*This report was automatically generated by the Security Audit Scanner.*

*Report generated: 2026-01-06 05:45:15 UTC*

## Warnings

The following warnings were encountered during the scan:

- pip-audit not installed. Install with: pip install pip-audit
- npm not installed. Install Node.js to use npm audit.
