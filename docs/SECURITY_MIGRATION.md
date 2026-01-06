# Security Migration Guide

This document provides comprehensive guidance for migrating the DS-Star Multi-Agent System from global state management to session-isolated, request-scoped architecture, and for integrating with enterprise identity providers (Azure AD and AWS IAM).

## Table of Contents

1. [Overview](#overview)
2. [Migration from Global State to Sessions](#migration-from-global-state-to-sessions)
3. [Azure AD Integration](#azure-ad-integration)
4. [AWS IAM Integration](#aws-iam-integration)
5. [Testing Procedures](#testing-procedures)
6. [Troubleshooting](#troubleshooting)

---

## Overview

### Security Architecture

The DS-Star security architecture consists of four main components:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Web Browser  │  │   WebSocket  │  │   API Client │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Security Layer                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Session Manager                         │  │
│  │  • Creates isolated session contexts                      │  │
│  │  • Generates cryptographically secure tokens              │  │
│  │  • Manages session lifecycle (TTL, invalidation)          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               Identity Provider Adapter                   │  │
│  │  • Local/Demo (default)                                   │  │
│  │  • Azure AD (enterprise SSO)                              │  │
│  │  • AWS IAM (AWS-native auth)                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Row-Level Security Engine                    │  │
│  │  • Permission policy enforcement                          │  │
│  │  • Data scope filtering (station/region/company)          │  │
│  │  • Audit logging                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Session Context** | Request-scoped container holding user identity, session ID, and permissions |
| **Session Token** | Cryptographically secure identifier (256-bit entropy) for a user session |
| **Open Access Mode** | Default mode where all users have full access to all data |
| **Data Scope** | Boundary of data visibility: station, region, or company-wide |
| **Permission Policy** | Configurable rule set defining what data a user or role can access |

---

## Migration from Global State to Sessions

### What Changed

The previous implementation used global variables for state management:

```python
# OLD: Global state (REMOVED)
_current_identity_id: Optional[str] = None
_techops_investigations: Dict[str, Dict] = {}
```

The new implementation uses request-scoped session contexts:

```python
# NEW: Session-isolated state
_session_manager: SessionManager
_investigation_store: InvestigationStore
```

### Migration Steps

#### Step 1: Update Server Initialization

The server now initializes security infrastructure at startup:

```python
# src/api/server.py - startup_event()

# Initialize security infrastructure
_identity_provider = LocalIdentityProvider(_demo_identities)
_session_manager = SessionManager(
    identity_provider=_identity_provider,
    session_ttl_hours=24,
    open_access_mode=True  # Default to open access
)
_rls_engine = RowLevelSecurityEngine(open_access_mode=True)
_investigation_store = InvestigationStore(rls_engine=_rls_engine)
```

#### Step 2: Use FastAPI Dependencies

Replace direct global variable access with dependency injection:

```python
# OLD: Direct global access
@app.get("/api/me")
async def get_me():
    identity = _demo_identities_by_id.get(_current_identity_id)
    return identity

# NEW: Dependency injection
@app.get("/api/me")
async def get_me(session: SessionContext = Depends(get_session_context)):
    return SessionResponse(
        identity=DemoIdentity(**session.identity),
        session_id=session.session_id
    )
```

#### Step 3: Update WebSocket Handlers

Create request-scoped stream handlers for each WebSocket connection:

```python
# OLD: Shared stream handler
orchestrator.stream_handler = global_stream_handler

# NEW: Request-scoped stream handler
stream_handler = StreamHandlerFactory.create_websocket_handler(
    websocket=websocket,
    session_context=session
)
await orchestrator.process(query, stream_handler=stream_handler)
```

#### Step 4: Update Investigation Storage

Use the InvestigationStore with session context:

```python
# OLD: Global dictionary
_techops_investigations[investigation_id] = record

# NEW: Session-aware store
investigation_store.create(
    investigation_id=investigation_id,
    data=record,
    context=session
)
```

### Session Header Protocol

Clients should include the session ID in requests:

```http
GET /api/techops/investigations HTTP/1.1
X-Session-ID: <session_token>
```

If no session ID is provided, a new session is created automatically.

---

## Azure AD Integration

### Prerequisites

1. Azure AD tenant with appropriate permissions
2. Application registration in Azure AD portal
3. Client credentials (client ID and secret)

### Step 1: Register Application in Azure AD

1. Navigate to Azure Portal → Azure Active Directory → App registrations
2. Click "New registration"
3. Configure:
   - Name: `DS-Star Multi-Agent System`
   - Supported account types: Single tenant (or as needed)
   - Redirect URI: `https://your-domain.com/auth/callback`
4. Note the **Application (client) ID** and **Directory (tenant) ID**

### Step 2: Configure Client Secret

1. In your app registration, go to "Certificates & secrets"
2. Click "New client secret"
3. Set description and expiration
4. **Copy the secret value immediately** (it won't be shown again)

### Step 3: Create Azure AD Groups

Create groups that map to DS-Star permission levels:

| Azure AD Group | DS-Star Permission | Data Scope |
|----------------|-------------------|------------|
| `DS-Star-Admins` | Full access | Company |
| `DS-Star-RegionalManagers` | Regional data | Region |
| `DS-Star-StationManagers` | Station data | Station |
| `DS-Star-Analysts` | Read-only | Station |

### Step 4: Configure Custom Claims (Optional)

For station/region assignments, add custom claims:

1. Go to "Token configuration" in your app registration
2. Add optional claims for `extension_Station` and `extension_Region`
3. Or use Azure AD extension attributes

### Step 5: Update Configuration

Update `config/security.yaml`:

```yaml
security:
  open_access_mode: false  # Enable RLS
  identity_provider: azure_ad

azure_ad:
  tenant_id: "${AZURE_AD_TENANT_ID}"
  client_id: "${AZURE_AD_CLIENT_ID}"
  client_secret: "${AZURE_AD_CLIENT_SECRET}"
  authority: "https://login.microsoftonline.com/${AZURE_AD_TENANT_ID}"
  
  group_mappings:
    - group: "DS-Star-Admins"
      permission_policy: "full_access"
      data_scope: "company"
    - group: "DS-Star-RegionalManagers"
      permission_policy: "regional_access"
      data_scope: "region"
    - group: "DS-Star-StationManagers"
      permission_policy: "station_access"
      data_scope: "station"
    - group: "DS-Star-Analysts"
      permission_policy: "read_only"
      data_scope: "station"
```

### Step 6: Set Environment Variables

```bash
export AZURE_AD_TENANT_ID="your-tenant-id"
export AZURE_AD_CLIENT_ID="your-client-id"
export AZURE_AD_CLIENT_SECRET="your-client-secret"
```

### Step 7: Implement Azure AD Provider

The `AzureADProvider` class stub is ready for implementation. Key integration points:

```python
# src/security/identity_provider.py

class AzureADProvider(IdentityProviderAdapter):
    def __init__(self, config: Dict[str, str]):
        # Initialize MSAL client
        self._app = msal.ConfidentialClientApplication(
            config["AZURE_AD_CLIENT_ID"],
            authority=config["AZURE_AD_AUTHORITY"],
            client_credential=config["AZURE_AD_CLIENT_SECRET"]
        )
    
    def validate_token(self, token: str) -> Optional[UserAttributes]:
        # Validate JWT using MSAL
        # Extract claims and map to UserAttributes
        pass
    
    def get_permissions(self, user_id: str) -> Dict[str, Any]:
        # Map Azure AD groups to permission policies
        pass
```

### Azure AD Token Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│ Azure AD │────▶│ DS-Star  │────▶│   RLS    │
│          │     │          │     │  Server  │     │  Engine  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
     │  1. Login      │                │                │
     │───────────────▶│                │                │
     │                │                │                │
     │  2. JWT Token  │                │                │
     │◀───────────────│                │                │
     │                │                │                │
     │  3. API Request + Token         │                │
     │────────────────────────────────▶│                │
     │                │                │                │
     │                │  4. Validate   │                │
     │                │◀───────────────│                │
     │                │                │                │
     │                │  5. Claims     │                │
     │                │───────────────▶│                │
     │                │                │                │
     │                │                │  6. Filter     │
     │                │                │───────────────▶│
     │                │                │                │
     │  7. Filtered Response           │                │
     │◀────────────────────────────────│                │
```

---

## AWS IAM Integration

### Prerequisites

1. AWS account with IAM permissions
2. IAM roles configured for DS-Star users
3. (Optional) Cognito identity pool for federated identities

### Step 1: Create IAM Roles

Create IAM roles that map to DS-Star permission levels:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:saml-provider/PROVIDER"
      },
      "Action": "sts:AssumeRoleWithSAML",
      "Condition": {
        "StringEquals": {
          "SAML:aud": "https://signin.aws.amazon.com/saml"
        }
      }
    }
  ]
}
```

| IAM Role | DS-Star Permission | Data Scope |
|----------|-------------------|------------|
| `DSStarAdmin` | Full access | Company |
| `DSStarRegionalManager` | Regional data | Region |
| `DSStarStationManager` | Station data | Station |
| `DSStarAnalyst` | Read-only | Station |

### Step 2: Add Resource Tags

Use IAM resource tags for station/region assignments:

```bash
aws iam tag-role --role-name DSStarStationManager \
  --tags Key=ds-star:station,Value=LAX Key=ds-star:region,Value=West
```

### Step 3: Configure Cognito (Optional)

For web/mobile clients, set up Cognito identity pool:

1. Create identity pool in AWS Console
2. Configure authentication providers
3. Map authenticated roles to DS-Star IAM roles

### Step 4: Update Configuration

Update `config/security.yaml`:

```yaml
security:
  open_access_mode: false  # Enable RLS
  identity_provider: aws_iam

aws_iam:
  region: "${AWS_REGION}"
  role_arn: "${AWS_ROLE_ARN}"
  identity_pool_id: "${AWS_COGNITO_IDENTITY_POOL_ID}"
  
  role_mappings:
    - role: "DSStarAdmin"
      permission_policy: "full_access"
      data_scope: "company"
    - role: "DSStarRegionalManager"
      permission_policy: "regional_access"
      data_scope: "region"
    - role: "DSStarStationManager"
      permission_policy: "station_access"
      data_scope: "station"
    - role: "DSStarAnalyst"
      permission_policy: "read_only"
      data_scope: "station"
  
  tag_mappings:
    station_tag: "ds-star:station"
    region_tag: "ds-star:region"
```

### Step 5: Set Environment Variables

```bash
export AWS_REGION="us-west-2"
export AWS_ROLE_ARN="arn:aws:iam::123456789012:role/DSStarValidation"
export AWS_COGNITO_IDENTITY_POOL_ID="us-west-2:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### Step 6: Implement AWS IAM Provider

The `AWSIAMProvider` class stub is ready for implementation:

```python
# src/security/identity_provider.py

class AWSIAMProvider(IdentityProviderAdapter):
    def __init__(self, config: Dict[str, str]):
        # Initialize boto3 STS client
        self._sts_client = boto3.client(
            'sts',
            region_name=config["AWS_REGION"]
        )
    
    def validate_token(self, token: str) -> Optional[UserAttributes]:
        # Validate STS token
        # Extract identity and role information
        pass
    
    def get_permissions(self, user_id: str) -> Dict[str, Any]:
        # Map IAM roles to permission policies
        pass
```

---

## Testing Procedures

### Unit Tests

Run the security unit tests:

```bash
# Run all security tests
pytest tests/test_session_security.py -v

# Run specific test classes
pytest tests/test_session_security.py::TestSessionManager -v
pytest tests/test_session_security.py::TestRowLevelSecurityEngine -v
pytest tests/test_session_security.py::TestLocalIdentityProvider -v
```

### Property-Based Tests

The security module includes property-based tests using Hypothesis:

```bash
# Run property-based tests with verbose output
pytest tests/test_session_security.py -v -k "Properties"

# Run with more examples for thorough testing
pytest tests/test_session_security.py --hypothesis-seed=0 -v
```

Key properties tested:

| Property | Description | Requirements |
|----------|-------------|--------------|
| Session Token Uniqueness | All tokens are unique with 256-bit entropy | 1.1 |
| Session Isolation | Modifying session A doesn't affect session B | 1.2, 1.3, 1.4 |
| Invalid Token Rejection | Invalid/expired tokens return None | 1.5 |
| Open Access Mode | All users see all data in open mode | 3.5, 6.2, 6.3 |
| Permission Policy Application | RLS filters based on user scope | 4.2, 4.4, 4.6 |
| Audit Logging Completeness | All access decisions are logged | 4.5 |

### Integration Tests

Test the full stack with session isolation:

```bash
# Start the server
python -m src.main

# In another terminal, run integration tests
pytest tests/test_session_security.py::TestServerIntegration -v
```

### Manual Testing Checklist

#### Session Isolation

1. Open two browser windows/tabs
2. In Window 1: Select identity "jmartinez"
3. In Window 2: Select identity "schen"
4. Verify each window shows its own identity
5. Create an investigation in Window 1
6. Verify Window 2 cannot see Window 1's investigation (when RLS enabled)

#### Open Access Mode

1. Ensure `open_access_mode: true` in config
2. Create investigations as different users
3. Verify all users can see all investigations
4. Verify session contexts are still separate

#### Row-Level Security

1. Set `open_access_mode: false` in config
2. Create investigation as station-level user
3. Verify company-level user can see it
4. Verify other station-level users cannot see it

### Load Testing

For concurrent request safety testing:

```bash
# Install locust
pip install locust

# Run load test (create locustfile.py first)
locust -f tests/locustfile.py --host=http://localhost:8000
```

Example locustfile.py:

```python
from locust import HttpUser, task, between

class DSStarUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Get session
        response = self.client.get("/api/me")
        self.session_id = response.json().get("session_id")
    
    @task
    def get_dashboard(self):
        self.client.get(
            "/api/techops/dashboard/weekly?station=DAL",
            headers={"X-Session-ID": self.session_id}
        )
    
    @task
    def create_investigation(self):
        self.client.post(
            "/api/techops/investigations",
            json={"kpi_id": "d0", "station": "DAL", "window": "weekly"},
            headers={"X-Session-ID": self.session_id}
        )
```

---

## Troubleshooting

### Common Issues

#### Session Not Persisting

**Symptom**: Each request creates a new session

**Solution**: Ensure the client sends the `X-Session-ID` header:

```javascript
// Frontend example
fetch('/api/techops/investigations', {
  headers: {
    'X-Session-ID': sessionStorage.getItem('sessionId')
  }
});
```

#### 401 Unauthorized Errors

**Symptom**: Valid users getting 401 errors

**Possible Causes**:
1. Session expired (check `session_ttl_hours` config)
2. Invalid session token format
3. Session manager not initialized

**Solution**: Check server logs for specific error messages

#### RLS Filtering Too Restrictive

**Symptom**: Users can't see data they should access

**Solution**: 
1. Verify user's `data_scope` is correct
2. Check permission policy configuration
3. Verify `open_access_mode` setting

#### Azure AD Token Validation Fails

**Symptom**: Azure AD tokens rejected

**Possible Causes**:
1. Incorrect tenant ID or client ID
2. Token expired
3. Missing required claims

**Solution**: 
1. Verify Azure AD configuration
2. Check token expiration
3. Validate token at https://jwt.ms

#### AWS IAM Role Assumption Fails

**Symptom**: AWS STS token validation fails

**Possible Causes**:
1. Incorrect role ARN
2. Missing trust relationship
3. Insufficient permissions

**Solution**:
1. Verify IAM role configuration
2. Check CloudTrail for detailed errors
3. Validate trust policy

### Debug Logging

Enable debug logging for security components:

```python
# In your startup code
import logging
logging.getLogger('src.security').setLevel(logging.DEBUG)
```

### Audit Log Analysis

Query the audit log for access patterns:

```python
from src.security.rls_engine import RowLevelSecurityEngine

engine = get_rls_engine()
for entry in engine.audit_log:
    print(f"{entry.timestamp} | {entry.user_id} | {entry.entity_type} | {entry.decision.value}")
```

---

## Appendix: Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DS_STAR_OPEN_ACCESS_MODE` | Enable open access mode | `true` |
| `DS_STAR_SESSION_TTL_HOURS` | Session lifetime in hours | `24` |
| `DS_STAR_IDENTITY_PROVIDER` | Identity provider type | `local` |
| `DS_STAR_ENABLE_AUDIT_LOGGING` | Enable audit logging | `true` |
| `AZURE_AD_TENANT_ID` | Azure AD tenant ID | - |
| `AZURE_AD_CLIENT_ID` | Azure AD client ID | - |
| `AZURE_AD_CLIENT_SECRET` | Azure AD client secret | - |
| `AWS_REGION` | AWS region | - |
| `AWS_ROLE_ARN` | AWS IAM role ARN | - |
| `AWS_COGNITO_IDENTITY_POOL_ID` | Cognito identity pool ID | - |

### Permission Policies

| Policy | Description | Scopes | Create | Update | Delete |
|--------|-------------|--------|--------|--------|--------|
| `full_access` | Company-wide access | All | ✓ | ✓ | ✓ |
| `regional_access` | Regional data access | Region, Station | ✓ | ✓ | ✗ |
| `station_access` | Station data access | Station | ✓ | ✓ | ✗ |
| `read_only` | Read-only access | Station | ✗ | ✗ | ✗ |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-06 | Initial release with session isolation and RLS framework |

