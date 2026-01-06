# Implementation Plan: Session Individualization & Row-Level Security

## Overview

This implementation plan transforms the DS-Star Multi-Agent System from global state management to session-isolated, request-scoped architecture. The approach builds incrementally: security models first, then session management, followed by RLS engine, and finally server integration.

## Tasks

- [x] 1. Set up security module structure and data models
  - Create `src/security/` directory structure (session_manager.py, identity_provider.py, rls_engine.py)
  - Define data models (SessionContext, UserAttributes, PermissionPolicy, SecurityConfig)
  - Define enums (DataScope, AccessDecision, ProviderType)
  - Set up testing framework with hypothesis
  - _Requirements: 1.1, 4.1, 5.1_

- [x] 2. Implement Session Manager
  - [x] 2.1 Create session token generation
    - Implement cryptographically secure token generation using secrets module
    - Ensure minimum 256 bits of entropy
    - _Requirements: 1.1_

  - [x] 2.2 Write property test for session token uniqueness
    - **Property 1: Session Token Uniqueness**
    - **Validates: Requirements 1.1**

  - [x] 2.3 Implement session context management
    - Create SessionContext dataclass with user_id, identity, permissions, data_scope
    - Implement create_session, get_session, update_identity, invalidate_session methods
    - Use thread-safe dictionary for session storage
    - _Requirements: 1.2, 1.3, 1.4_

  - [x] 2.4 Write property test for session isolation
    - **Property 2: Session Isolation**
    - **Validates: Requirements 1.2, 1.3, 1.4**

  - [x] 2.5 Implement session expiration and validation
    - Add expires_at field to SessionContext
    - Implement is_expired() check
    - Return None for invalid/expired tokens
    - _Requirements: 1.5_

  - [x] 2.6 Write property test for invalid token rejection
    - **Property 3: Invalid Token Rejection**
    - **Validates: Requirements 1.5**

- [x] 3. Checkpoint - Ensure session manager tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Identity Provider Adapter
  - [x] 4.1 Create abstract IdentityProviderAdapter interface
    - Define validate_token, get_permissions, get_data_scope abstract methods
    - Define UserAttributes dataclass for standardized attributes
    - _Requirements: 5.1_

  - [x] 4.2 Implement LocalIdentityProvider
    - Support demo identities list
    - Return open permissions by default
    - Extract user attributes from identity dict
    - _Requirements: 5.2, 6.1_

  - [x] 4.3 Create Azure AD provider stub with documentation
    - Document OIDC/OAuth2 integration points
    - Document group-to-permission mapping
    - Document configuration requirements
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 4.4 Create AWS IAM provider stub with documentation
    - Document STS token validation integration points
    - Document role-to-permission mapping
    - Document configuration requirements
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 4.5 Write property test for identity attribute extraction
    - **Property 11: Identity Attribute Extraction**
    - **Validates: Requirements 5.6**

- [x] 5. Checkpoint - Ensure identity provider tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement Row-Level Security Engine
  - [x] 6.1 Create PermissionPolicy and DataScope models
    - Define PermissionPolicy dataclass with entity_type, allowed_scopes, owner_field, scope_field
    - Define DataScope enum (STATION, REGION, COMPANY)
    - _Requirements: 4.1, 4.3_

  - [x] 6.2 Implement RLS filter logic
    - Implement filter_results method with policy application
    - Implement check_single_access for individual items
    - Support custom filter functions
    - _Requirements: 4.2_

  - [x] 6.3 Implement open access mode bypass
    - Add open_access_mode flag to RLS engine
    - Bypass all filtering when enabled
    - Default to open access when no policy defined
    - _Requirements: 4.4, 4.6, 6.2, 6.5_

  - [x] 6.4 Implement audit logging
    - Log all access decisions with timestamp, user_id, session_id, entity_type
    - Log both allowed and denied decisions
    - _Requirements: 4.5_

  - [x] 6.5 Write property test for permission policy application
    - **Property 8: Permission Policy Application**
    - **Validates: Requirements 4.2, 4.4, 4.6**

  - [x] 6.6 Write property test for open access mode behavior
    - **Property 7: Open Access Mode Behavior**
    - **Validates: Requirements 3.5, 6.2, 6.3, 6.5**

  - [x] 6.7 Write property test for audit logging completeness
    - **Property 9: Audit Logging Completeness**
    - **Validates: Requirements 4.5**

- [x] 7. Checkpoint - Ensure RLS engine tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement Stream Handler Factory
  - [x] 8.1 Create WebSocketStreamHandler class
    - Extend InvestigationStreamHandler
    - Bind to specific WebSocket and session_id
    - Implement send method for single connection
    - _Requirements: 2.1, 2.3_

  - [x] 8.2 Create StreamHandlerFactory
    - Implement create_websocket_handler factory method
    - Ensure no global state modification
    - _Requirements: 2.2_

  - [x] 8.3 Implement handler cleanup
    - Add close method to mark handler as closed
    - Handle disconnection gracefully
    - _Requirements: 2.4, 2.5_

  - [x] 8.4 Write property test for request-scoped stream handler
    - **Property 4: Request-Scoped Stream Handler**
    - **Validates: Requirements 2.1, 2.2**

  - [x] 8.5 Write property test for stream handler message routing
    - **Property 5: Stream Handler Message Routing**
    - **Validates: Requirements 2.3, 2.4, 2.5**

- [x] 9. Checkpoint - Ensure stream handler tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement Session-Isolated Investigation Store
  - [x] 10.1 Create InvestigationStore class
    - Implement thread-safe storage with RLock
    - Associate investigations with session context
    - _Requirements: 3.1_

  - [x] 10.2 Implement CRUD operations with RLS
    - Implement create with session association
    - Implement get with access check
    - Implement list with RLS filtering
    - Implement update with access check
    - _Requirements: 3.2, 3.3, 3.4_

  - [x] 10.3 Write property test for data ownership enforcement
    - **Property 6: Data Ownership Enforcement**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

- [x] 11. Checkpoint - Ensure investigation store tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Integrate with FastAPI Server
  - [x] 12.1 Remove global state variables
    - Remove `_current_identity_id` global variable
    - Remove global `_techops_investigations` dictionary
    - Remove global orchestrator stream handler assignment
    - _Requirements: 7.1_

  - [x] 12.2 Create FastAPI dependencies for session context
    - Create `get_session_context` dependency
    - Create `get_current_user` dependency
    - Inject session context into all protected endpoints
    - _Requirements: 7.3_

  - [x] 12.3 Update identity endpoints
    - Update GET /api/me to use session context
    - Update POST /api/me/select to update only requesting session
    - _Requirements: 1.4_

  - [x] 12.4 Update investigation endpoints
    - Update POST /api/techops/investigations to use InvestigationStore
    - Update GET /api/techops/investigations to filter by session
    - Update GET /api/techops/investigations/{id} with access check
    - Update POST /api/techops/investigations/{id}/finalize with access check
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 12.5 Update WebSocket handlers
    - Create request-scoped stream handler per connection
    - Associate WebSocket with session context
    - Pass stream handler to orchestrator.process() method
    - _Requirements: 1.6, 2.1, 2.2, 2.3_

  - [x] 12.6 Write property test for concurrent request safety
    - **Property 10: Concurrent Request Safety**
    - **Validates: Requirements 7.1, 7.2, 7.4**

- [x] 13. Checkpoint - Ensure server integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Update Orchestrator for Request-Scoped Handlers
  - [x] 14.1 Modify OrchestratorAgent.process signature
    - Add optional stream_handler parameter
    - Use passed handler instead of instance attribute
    - _Requirements: 2.1, 2.2_

  - [x] 14.2 Update all stream handler calls
    - Replace self.stream_handler with local handler variable
    - Ensure no global state modification
    - _Requirements: 2.2, 7.1_

- [x] 15. Create Security Configuration
  - [x] 15.1 Add security config to src/config.py
    - Add OPEN_ACCESS_MODE flag (default: True)
    - Add SESSION_TTL_HOURS setting
    - Add IDENTITY_PROVIDER setting
    - Add ENABLE_AUDIT_LOGGING flag
    - _Requirements: 6.1, 6.4_

  - [x] 15.2 Create config/security.yaml template
    - Document all configuration options
    - Include Azure AD configuration template
    - Include AWS IAM configuration template
    - _Requirements: 8.5, 9.5_

- [x] 16. Create Migration Documentation
  - [x] 16.1 Create docs/SECURITY_MIGRATION.md
    - Document migration from global state to sessions
    - Document Azure AD integration steps
    - Document AWS IAM integration steps
    - Document testing procedures
    - _Requirements: 8.5, 9.5_

- [x] 17. Final checkpoint - Run full test suite
  - Ensure all tests pass, ask the user if questions arise.
  - Verify no global state usage in server.py
  - Verify session isolation with concurrent requests
  - Verify open access mode works correctly

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation uses Python with pytest and hypothesis for testing
- Open Access Mode is enabled by default - no breaking changes to existing functionality
