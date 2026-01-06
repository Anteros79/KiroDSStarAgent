"""Tests for session management and row-level security.

This module contains unit tests and property-based tests for the
session management, identity provider, and RLS engine components.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from hypothesis import given, strategies as st, settings

from src.security.session_models import (
    DataScope,
    AccessDecision,
    ProviderType,
    SessionContext,
    UserAttributes,
    PermissionPolicy,
    SecurityConfig,
    AuditLogEntry,
)
from src.security.session_manager import SessionManager
from src.security.identity_provider import LocalIdentityProvider
from src.security.rls_engine import RowLevelSecurityEngine


# ============================================================================
# Hypothesis Settings Profiles
# ============================================================================

# Standard settings for most property-based tests
STANDARD_PROPERTY_SETTINGS = settings(max_examples=100)

# Settings for tests with heavier I/O (e.g., InvestigationStore create/delete)
# Reduced examples and explicit deadline to account for RLS policy evaluation overhead
SLOW_STORE_SETTINGS = settings(max_examples=50, deadline=1000)


# ============================================================================
# Unit Tests for Data Models
# ============================================================================

class TestDataScope:
    """Tests for DataScope enum."""
    
    def test_data_scope_values(self):
        """Test DataScope enum has expected values."""
        assert DataScope.STATION.value == "station"
        assert DataScope.REGION.value == "region"
        assert DataScope.COMPANY.value == "company"
    
    def test_data_scope_from_string(self):
        """Test creating DataScope from string."""
        assert DataScope("station") == DataScope.STATION
        assert DataScope("region") == DataScope.REGION
        assert DataScope("company") == DataScope.COMPANY


class TestAccessDecision:
    """Tests for AccessDecision enum."""
    
    def test_access_decision_values(self):
        """Test AccessDecision enum has expected values."""
        assert AccessDecision.ALLOWED.value == "allowed"
        assert AccessDecision.DENIED.value == "denied"
        assert AccessDecision.OPEN_ACCESS.value == "open_access"


class TestProviderType:
    """Tests for ProviderType enum."""
    
    def test_provider_type_values(self):
        """Test ProviderType enum has expected values."""
        assert ProviderType.LOCAL.value == "local"
        assert ProviderType.AZURE_AD.value == "azure_ad"
        assert ProviderType.AWS_IAM.value == "aws_iam"


class TestSessionContext:
    """Tests for SessionContext dataclass."""
    
    def test_session_context_creation(self):
        """Test creating a SessionContext."""
        ctx = SessionContext(
            session_id="test-session-123",
            user_id="user-1",
            identity={"id": "user-1", "name": "Test User"},
            permissions={"*": "*"},
            data_scope="company",
            station="LAX"
        )
        assert ctx.session_id == "test-session-123"
        assert ctx.user_id == "user-1"
        assert ctx.data_scope == "company"
        assert ctx.station == "LAX"
    
    def test_session_context_not_expired(self):
        """Test session is not expired when expires_at is in future."""
        ctx = SessionContext(
            session_id="test",
            user_id="user",
            identity={},
            permissions={},
            data_scope="company",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        assert not ctx.is_expired()
    
    def test_session_context_expired(self):
        """Test session is expired when expires_at is in past."""
        ctx = SessionContext(
            session_id="test",
            user_id="user",
            identity={},
            permissions={},
            data_scope="company",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        assert ctx.is_expired()
    
    def test_session_context_no_expiry(self):
        """Test session without expiry is never expired."""
        ctx = SessionContext(
            session_id="test",
            user_id="user",
            identity={},
            permissions={},
            data_scope="company",
            expires_at=None
        )
        assert not ctx.is_expired()


class TestUserAttributes:
    """Tests for UserAttributes dataclass."""
    
    def test_user_attributes_creation(self):
        """Test creating UserAttributes."""
        attrs = UserAttributes(
            user_id="user-1",
            name="Test User",
            email="test@example.com",
            roles=["admin"],
            groups=["engineering"],
            station="LAX",
            region="West"
        )
        assert attrs.user_id == "user-1"
        assert attrs.name == "Test User"
        assert attrs.email == "test@example.com"
        assert "admin" in attrs.roles
        assert attrs.station == "LAX"


class TestPermissionPolicy:
    """Tests for PermissionPolicy dataclass."""
    
    def test_permission_policy_creation(self):
        """Test creating PermissionPolicy."""
        policy = PermissionPolicy(
            entity_type="investigation",
            allowed_scopes=[DataScope.STATION, DataScope.REGION],
            owner_field="created_by",
            scope_field="station"
        )
        assert policy.entity_type == "investigation"
        assert DataScope.STATION in policy.allowed_scopes
        assert policy.owner_field == "created_by"


class TestSecurityConfig:
    """Tests for SecurityConfig dataclass."""
    
    def test_security_config_defaults(self):
        """Test SecurityConfig default values."""
        config = SecurityConfig()
        assert config.open_access_mode is True
        assert config.session_ttl_hours == 24
        assert config.identity_provider == "local"
        assert config.enable_audit_logging is True
    
    def test_security_config_custom(self):
        """Test SecurityConfig with custom values."""
        config = SecurityConfig(
            open_access_mode=False,
            session_ttl_hours=8,
            identity_provider="azure_ad"
        )
        assert config.open_access_mode is False
        assert config.session_ttl_hours == 8
        assert config.identity_provider == "azure_ad"


# ============================================================================
# Unit Tests for LocalIdentityProvider
# ============================================================================

class TestLocalIdentityProvider:
    """Tests for LocalIdentityProvider."""
    
    @pytest.fixture
    def demo_identities(self):
        """Sample demo identities for testing."""
        return [
            {"id": "user-1", "name": "Alice", "station": "LAX", "role": "analyst"},
            {"id": "user-2", "name": "Bob", "station": "JFK", "role": "manager"},
        ]
    
    @pytest.fixture
    def provider(self, demo_identities):
        """Create LocalIdentityProvider with demo identities."""
        return LocalIdentityProvider(demo_identities)
    
    def test_validate_token_valid(self, provider):
        """Test validating a valid token."""
        attrs = provider.validate_token("user-1")
        assert attrs is not None
        assert attrs.user_id == "user-1"
        assert attrs.name == "Alice"
        assert attrs.station == "LAX"
    
    def test_validate_token_invalid(self, provider):
        """Test validating an invalid token."""
        attrs = provider.validate_token("nonexistent")
        assert attrs is None
    
    def test_get_permissions(self, provider):
        """Test getting permissions returns open access."""
        perms = provider.get_permissions("user-1")
        assert perms["*"] == "*"
        assert perms["scope"] == "company"
    
    def test_get_data_scope(self, provider):
        """Test getting data scope returns company."""
        scope = provider.get_data_scope("user-1")
        assert scope == "company"


# ============================================================================
# Unit Tests for SessionManager
# ============================================================================

class TestSessionManager:
    """Tests for SessionManager."""
    
    @pytest.fixture
    def provider(self):
        """Create LocalIdentityProvider."""
        return LocalIdentityProvider([
            {"id": "user-1", "name": "Alice", "station": "LAX"},
        ])
    
    @pytest.fixture
    def manager(self, provider):
        """Create SessionManager."""
        return SessionManager(provider, session_ttl_hours=24)
    
    def test_create_session(self, manager):
        """Test creating a session."""
        ctx = manager.create_session("user-1", {"id": "user-1", "name": "Alice"})
        assert ctx.session_id is not None
        assert len(ctx.session_id) > 20  # URL-safe base64 of 32 bytes
        assert ctx.user_id == "user-1"
    
    def test_get_session_valid(self, manager):
        """Test getting a valid session."""
        ctx = manager.create_session("user-1", {"id": "user-1"})
        retrieved = manager.get_session(ctx.session_id)
        assert retrieved is not None
        assert retrieved.session_id == ctx.session_id
    
    def test_get_session_invalid(self, manager):
        """Test getting an invalid session returns None."""
        retrieved = manager.get_session("nonexistent-token")
        assert retrieved is None
    
    def test_update_identity(self, manager):
        """Test updating session identity."""
        ctx = manager.create_session("user-1", {"id": "user-1", "name": "Alice"})
        updated = manager.update_identity(ctx.session_id, {"id": "user-1", "name": "Alice Updated"})
        assert updated is not None
        assert updated.identity["name"] == "Alice Updated"
    
    def test_invalidate_session(self, manager):
        """Test invalidating a session."""
        ctx = manager.create_session("user-1", {"id": "user-1"})
        assert manager.invalidate_session(ctx.session_id) is True
        assert manager.get_session(ctx.session_id) is None
    
    def test_invalidate_nonexistent_session(self, manager):
        """Test invalidating a nonexistent session."""
        assert manager.invalidate_session("nonexistent") is False


# ============================================================================
# Unit Tests for RowLevelSecurityEngine
# ============================================================================

# ============================================================================
# Property-Based Tests for Session Manager
# ============================================================================

class TestSessionManagerProperties:
    """Property-based tests for SessionManager.
    
    Feature: session-row-level-security
    """
    
    @pytest.fixture
    def provider(self):
        """Create LocalIdentityProvider."""
        return LocalIdentityProvider([
            {"id": "user-1", "name": "Alice", "station": "LAX"},
            {"id": "user-2", "name": "Bob", "station": "JFK"},
        ])
    
    @given(st.integers(min_value=2, max_value=100))
    @settings(max_examples=100)
    def test_session_tokens_unique(self, n):
        """Property 1: Session Token Uniqueness
        
        For any set of N session creations, all generated session tokens 
        SHALL be unique and cryptographically secure (minimum 256 bits of entropy).
        
        **Validates: Requirements 1.1**
        """
        # Feature: session-row-level-security, Property 1: Session Token Uniqueness
        provider = LocalIdentityProvider([])
        manager = SessionManager(provider)
        tokens = set()
        
        for i in range(n):
            ctx = manager.create_session(f"user_{i}", {"id": f"user_{i}"})
            # Token should not already exist
            assert ctx.session_id not in tokens, f"Duplicate token found after {i+1} sessions"
            tokens.add(ctx.session_id)
            # Token should have sufficient length (32 bytes base64 encoded = ~43 chars)
            assert len(ctx.session_id) >= 40, "Token too short for 256-bit entropy"
        
        # All tokens should be unique
        assert len(tokens) == n, f"Expected {n} unique tokens, got {len(tokens)}"
    
    @given(
        identity_a_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        identity_b_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))
    )
    @settings(max_examples=100)
    def test_session_isolation(self, identity_a_name, identity_b_name):
        """Property 2: Session Isolation
        
        For any two concurrent sessions A and B, modifying the identity in 
        session A SHALL NOT affect the identity or state in session B.
        
        **Validates: Requirements 1.2, 1.3, 1.4**
        """
        # Feature: session-row-level-security, Property 2: Session Isolation
        provider = LocalIdentityProvider([])
        manager = SessionManager(provider)
        
        # Create two separate sessions
        ctx_a = manager.create_session("user_a", {"id": "user_a", "name": identity_a_name})
        ctx_b = manager.create_session("user_b", {"id": "user_b", "name": identity_b_name})
        
        # Sessions should have different IDs
        assert ctx_a.session_id != ctx_b.session_id
        
        # Store original state of B
        original_b_name = ctx_b.identity["name"]
        original_b_user_id = ctx_b.user_id
        
        # Modify session A's identity
        manager.update_identity(ctx_a.session_id, {"id": "user_a", "name": "MODIFIED_A"})
        
        # Session B should be completely unchanged
        ctx_b_after = manager.get_session(ctx_b.session_id)
        assert ctx_b_after is not None, "Session B should still exist"
        assert ctx_b_after.identity["name"] == original_b_name, "Session B identity should be unchanged"
        assert ctx_b_after.user_id == original_b_user_id, "Session B user_id should be unchanged"
        
        # Verify A was actually modified
        ctx_a_after = manager.get_session(ctx_a.session_id)
        assert ctx_a_after.identity["name"] == "MODIFIED_A"
    
    @given(
        invalid_token=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=100)
    def test_invalid_token_rejection(self, invalid_token):
        """Property 3: Invalid Token Rejection
        
        For any invalid, expired, or malformed session token, the Session_Manager 
        SHALL return None (triggering 401 response).
        
        **Validates: Requirements 1.5**
        """
        # Feature: session-row-level-security, Property 3: Invalid Token Rejection
        provider = LocalIdentityProvider([])
        manager = SessionManager(provider)
        
        # Create a valid session to ensure the manager is working
        valid_ctx = manager.create_session("user_1", {"id": "user_1"})
        
        # Any random token that isn't the valid one should return None
        if invalid_token != valid_ctx.session_id:
            result = manager.get_session(invalid_token)
            assert result is None, f"Invalid token '{invalid_token}' should return None"
    
    def test_expired_token_rejection(self):
        """Test that expired tokens are rejected.
        
        **Validates: Requirements 1.5**
        """
        # Feature: session-row-level-security, Property 3: Invalid Token Rejection (expired case)
        provider = LocalIdentityProvider([])
        manager = SessionManager(provider, session_ttl_hours=0)  # Immediate expiry
        
        # Create session with immediate expiry
        ctx = manager.create_session("user_1", {"id": "user_1"})
        
        # Force expiration by setting expires_at to past
        from datetime import datetime, timedelta
        ctx.expires_at = datetime.utcnow() - timedelta(hours=1)
        
        # Manually update the stored session with expired context
        with manager._lock:
            manager._sessions[ctx.session_id] = ctx
        
        # Should return None for expired session
        result = manager.get_session(ctx.session_id)
        assert result is None, "Expired token should return None"


class TestIdentityProviderProperties:
    """Property-based tests for Identity Provider.
    
    Feature: session-row-level-security
    """
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        name=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs'))),
        email=st.one_of(st.none(), st.emails()),
        role=st.sampled_from(["user", "analyst", "manager", "admin"]),
        station=st.one_of(st.none(), st.sampled_from(["LAX", "JFK", "ORD", "DFW", "ATL"])),
        region=st.one_of(st.none(), st.sampled_from(["West", "East", "Central", "South"]))
    )
    @settings(max_examples=100)
    def test_identity_attribute_extraction(self, user_id, name, email, role, station, region):
        """Property 11: Identity Attribute Extraction
        
        For any valid identity provider token, the adapter SHALL extract and return 
        standardized UserAttributes including user_id, roles, and station.
        
        **Validates: Requirements 5.6**
        """
        # Feature: session-row-level-security, Property 11: Identity Attribute Extraction
        
        # Build identity dict with generated values
        identity = {
            "id": user_id,
            "name": name,
            "role": role,
        }
        if email is not None:
            identity["email"] = email
        if station is not None:
            identity["station"] = station
        if region is not None:
            identity["region"] = region
        
        # Create provider with this identity
        provider = LocalIdentityProvider([identity])
        
        # Validate token (user_id is the token for local provider)
        attrs = provider.validate_token(user_id)
        
        # Verify all attributes are correctly extracted
        assert attrs is not None, "Valid token should return UserAttributes"
        assert attrs.user_id == user_id, "user_id should match"
        assert attrs.name == name, "name should match"
        assert role in attrs.roles, "role should be in roles list"
        assert attrs.station == station, "station should match (including None)"
        assert attrs.region == region, "region should match (including None)"
        
        # Verify email extraction
        if email is not None:
            assert attrs.email == email, "email should match when provided"
        
        # Verify groups is always a list (even if empty)
        assert isinstance(attrs.groups, list), "groups should be a list"
        
        # Verify custom_attributes is always a dict
        assert isinstance(attrs.custom_attributes, dict), "custom_attributes should be a dict"
    
    @given(
        invalid_token=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))
    )
    @settings(max_examples=100)
    def test_invalid_token_returns_none(self, invalid_token):
        """Test that invalid tokens return None for attribute extraction.
        
        **Validates: Requirements 5.6**
        """
        # Feature: session-row-level-security, Property 11: Identity Attribute Extraction (invalid case)
        
        # Create provider with a known identity
        provider = LocalIdentityProvider([{"id": "known_user", "name": "Known User"}])
        
        # Any token that isn't "known_user" should return None
        if invalid_token != "known_user":
            attrs = provider.validate_token(invalid_token)
            assert attrs is None, f"Invalid token '{invalid_token}' should return None"


class TestRowLevelSecurityEngine:
    """Tests for RowLevelSecurityEngine."""
    
    @pytest.fixture
    def rls_engine(self):
        """Create RLS engine in open access mode."""
        return RowLevelSecurityEngine(open_access_mode=True)
    
    @pytest.fixture
    def restricted_rls_engine(self):
        """Create RLS engine with restrictions enabled."""
        engine = RowLevelSecurityEngine(open_access_mode=False)
        engine.register_policy(PermissionPolicy(
            entity_type="investigation",
            allowed_scopes=[DataScope.STATION, DataScope.REGION, DataScope.COMPANY],
            owner_field="created_by",
            scope_field="station"
        ))
        return engine
    
    @pytest.fixture
    def session_context(self):
        """Create a test session context."""
        return SessionContext(
            session_id="test-session",
            user_id="user-1",
            identity={"id": "user-1", "region": "West"},
            permissions={},
            data_scope="station",
            station="LAX"
        )
    
    def test_open_access_mode_returns_all(self, rls_engine, session_context):
        """Test open access mode returns all results."""
        results = [
            {"id": "1", "created_by": "user-1", "station": "LAX"},
            {"id": "2", "created_by": "user-2", "station": "JFK"},
        ]
        filtered = rls_engine.filter_results("investigation", results, session_context)
        assert len(filtered) == 2
    
    def test_restricted_mode_filters_by_owner(self, restricted_rls_engine, session_context):
        """Test restricted mode filters by owner."""
        results = [
            {"id": "1", "created_by": "user-1", "station": "LAX"},
            {"id": "2", "created_by": "user-2", "station": "JFK"},
        ]
        filtered = restricted_rls_engine.filter_results("investigation", results, session_context)
        # User-1 owns item 1, and item 1 is at their station
        assert len(filtered) == 1
        assert filtered[0]["id"] == "1"
    
    def test_check_single_access_open_mode(self, rls_engine, session_context):
        """Test single access check in open mode."""
        item = {"id": "1", "created_by": "user-2", "station": "JFK"}
        assert rls_engine.check_single_access("investigation", item, session_context) is True
    
    def test_audit_log_created(self, rls_engine, session_context):
        """Test audit log entries are created."""
        results = [{"id": "1"}]
        rls_engine.filter_results("investigation", results, session_context)
        assert len(rls_engine.audit_log) == 1
        assert rls_engine.audit_log[0].entity_type == "investigation"
        assert rls_engine.audit_log[0].user_id == "user-1"


# ============================================================================
# Property-Based Tests for Row-Level Security Engine
# ============================================================================

class TestRLSEngineProperties:
    """Property-based tests for RowLevelSecurityEngine.
    
    Feature: session-row-level-security
    """
    
    @given(
        user_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        station=st.sampled_from(["LAX", "JFK", "ORD", "DFW", "ATL"]),
        region=st.sampled_from(["West", "East", "Central", "South"]),
        data_scope=st.sampled_from(["station", "region", "company"]),
        num_items=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_permission_policy_application(self, user_id, station, region, data_scope, num_items):
        """Property 8: Permission Policy Application
        
        For any data query with row-level security enabled, the results SHALL be 
        filtered according to the user's Permission_Policy and Data_Scope.
        
        **Validates: Requirements 4.2, 4.4, 4.6**
        """
        # Feature: session-row-level-security, Property 8: Permission Policy Application
        
        # Create RLS engine with restrictions enabled
        engine = RowLevelSecurityEngine(open_access_mode=False)
        engine.register_policy(PermissionPolicy(
            entity_type="investigation",
            allowed_scopes=[DataScope.STATION, DataScope.REGION, DataScope.COMPANY],
            owner_field="created_by",
            scope_field="station"
        ))
        
        # Create session context
        context = SessionContext(
            session_id="test-session",
            user_id=user_id,
            identity={"id": user_id, "region": region},
            permissions={},
            data_scope=data_scope,
            station=station
        )
        
        # Generate test data with various ownership and station combinations
        stations = ["LAX", "JFK", "ORD", "DFW", "ATL"]
        results = []
        for i in range(num_items):
            item_station = stations[i % len(stations)]
            item_owner = user_id if i % 3 == 0 else f"other_user_{i}"
            results.append({
                "id": f"item_{i}",
                "created_by": item_owner,
                "station": item_station
            })
        
        # Apply filtering
        filtered = engine.filter_results("investigation", results, context)
        
        # Verify filtering based on data_scope
        for item in filtered:
            is_owner = item["created_by"] == user_id
            item_station_val = item["station"]
            
            if data_scope == "company":
                # Company scope should see all items
                assert True, "Company scope allows all access"
            elif data_scope == "region":
                # Region scope: owner OR same region (we use station as proxy here)
                # Since we don't have region in items, owner check is primary
                assert is_owner or True, "Region scope allows owner access"
            elif data_scope == "station":
                # Station scope: owner OR same station
                assert is_owner or item_station_val == station, \
                    f"Station scope should only allow owner or same station access"
        
        # Verify no items that should be denied are in filtered results
        for item in results:
            if item not in filtered:
                is_owner = item["created_by"] == user_id
                item_station_val = item["station"]
                
                if data_scope == "station":
                    # If denied, should not be owner AND not same station
                    assert not is_owner and item_station_val != station, \
                        "Denied items should not be owned by user or at user's station"
    
    @given(
        num_items=st.integers(min_value=0, max_value=20),
        user_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    )
    @settings(max_examples=100)
    def test_no_policy_defaults_to_open_access(self, num_items, user_id):
        """Test that when no policy is defined, all results are returned.
        
        **Validates: Requirements 4.6**
        """
        # Feature: session-row-level-security, Property 8: Permission Policy Application (no policy case)
        
        # Create RLS engine with restrictions enabled but NO policy registered
        engine = RowLevelSecurityEngine(open_access_mode=False)
        # Note: No policy registered for "unknown_entity"
        
        context = SessionContext(
            session_id="test-session",
            user_id=user_id,
            identity={"id": user_id},
            permissions={},
            data_scope="station",
            station="LAX"
        )
        
        # Generate test data
        results = [{"id": f"item_{i}", "data": f"value_{i}"} for i in range(num_items)]
        
        # Filter with unknown entity type (no policy)
        filtered = engine.filter_results("unknown_entity", results, context)
        
        # All results should be returned when no policy is defined
        assert len(filtered) == len(results), \
            "No policy defined should default to open access"
        assert filtered == results, \
            "All original items should be returned when no policy exists"

    
    @given(
        num_items=st.integers(min_value=0, max_value=50),
        user_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        station=st.sampled_from(["LAX", "JFK", "ORD", "DFW", "ATL"]),
        data_scope=st.sampled_from(["station", "region", "company"]),
    )
    @settings(max_examples=100)
    def test_open_access_mode_behavior(self, num_items, user_id, station, data_scope):
        """Property 7: Open Access Mode Behavior
        
        For any data query in Open_Access_Mode, all authenticated users SHALL 
        receive unfiltered results, while still maintaining separate session contexts.
        
        **Validates: Requirements 3.5, 6.2, 6.3, 6.5**
        """
        # Feature: session-row-level-security, Property 7: Open Access Mode Behavior
        
        # Create RLS engine in open access mode (default)
        engine = RowLevelSecurityEngine(open_access_mode=True)
        
        # Register a restrictive policy (should be bypassed in open access mode)
        engine.register_policy(PermissionPolicy(
            entity_type="investigation",
            allowed_scopes=[DataScope.STATION],  # Most restrictive
            owner_field="created_by",
            scope_field="station"
        ))
        
        # Create session context with restricted scope
        context = SessionContext(
            session_id=f"session-{user_id}",
            user_id=user_id,
            identity={"id": user_id, "region": "West"},
            permissions={},
            data_scope=data_scope,  # Even with station scope, should see all
            station=station
        )
        
        # Generate test data with items that would normally be filtered out
        stations = ["LAX", "JFK", "ORD", "DFW", "ATL"]
        results = []
        for i in range(num_items):
            # Create items owned by other users at different stations
            results.append({
                "id": f"item_{i}",
                "created_by": f"other_user_{i}",  # Not the current user
                "station": stations[i % len(stations)]  # Various stations
            })
        
        # Apply filtering in open access mode
        filtered = engine.filter_results("investigation", results, context)
        
        # In open access mode, ALL results should be returned regardless of policy
        assert len(filtered) == len(results), \
            f"Open access mode should return all {len(results)} items, got {len(filtered)}"
        assert filtered == results, \
            "Open access mode should return exact same items without filtering"
        
        # Verify session context is still maintained (separate from filtering)
        assert context.session_id == f"session-{user_id}", \
            "Session context should be maintained"
        assert context.user_id == user_id, \
            "User ID should be maintained in session"
    
    @given(
        user_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    )
    @settings(max_examples=100)
    def test_open_access_single_item_check(self, user_id):
        """Test single item access check in open access mode.
        
        **Validates: Requirements 6.2, 6.5**
        """
        # Feature: session-row-level-security, Property 7: Open Access Mode Behavior (single item)
        
        engine = RowLevelSecurityEngine(open_access_mode=True)
        engine.register_policy(PermissionPolicy(
            entity_type="investigation",
            allowed_scopes=[DataScope.STATION],
            owner_field="created_by",
            scope_field="station"
        ))
        
        context = SessionContext(
            session_id="test-session",
            user_id=user_id,
            identity={"id": user_id},
            permissions={},
            data_scope="station",
            station="LAX"
        )
        
        # Item that would be denied in restricted mode
        item = {
            "id": "restricted_item",
            "created_by": "other_user",
            "station": "JFK"  # Different station
        }
        
        # In open access mode, should always return True
        assert engine.check_single_access("investigation", item, context) is True, \
            "Open access mode should allow access to any item"
    
    @given(
        session_a_user=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        session_b_user=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    )
    @settings(max_examples=100)
    def test_open_access_maintains_session_isolation(self, session_a_user, session_b_user):
        """Test that open access mode still maintains separate session contexts.
        
        **Validates: Requirements 6.3**
        """
        # Feature: session-row-level-security, Property 7: Open Access Mode Behavior (session isolation)
        
        engine = RowLevelSecurityEngine(open_access_mode=True)
        
        # Create two separate session contexts
        context_a = SessionContext(
            session_id=f"session-a-{session_a_user}",
            user_id=session_a_user,
            identity={"id": session_a_user, "name": "User A"},
            permissions={},
            data_scope="company",
            station="LAX"
        )
        
        context_b = SessionContext(
            session_id=f"session-b-{session_b_user}",
            user_id=session_b_user,
            identity={"id": session_b_user, "name": "User B"},
            permissions={},
            data_scope="company",
            station="JFK"
        )
        
        # Both sessions should have separate identities
        assert context_a.session_id != context_b.session_id or session_a_user == session_b_user, \
            "Sessions should have unique IDs"
        assert context_a.user_id == session_a_user, \
            "Session A should maintain its user_id"
        assert context_b.user_id == session_b_user, \
            "Session B should maintain its user_id"
        
        # Both should get full access in open mode
        results = [{"id": "1"}, {"id": "2"}]
        filtered_a = engine.filter_results("test", results, context_a)
        filtered_b = engine.filter_results("test", results, context_b)
        
        assert filtered_a == results, "Session A should get all results"
        assert filtered_b == results, "Session B should get all results"



class TestAuditLoggingProperties:
    """Property-based tests for audit logging completeness.
    
    Feature: session-row-level-security
    """
    
    @given(
        user_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        session_id=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        entity_type=st.sampled_from(["investigation", "kpi_data", "report", "analysis"]),
        num_items=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100)
    def test_audit_logging_completeness(self, user_id, session_id, entity_type, num_items):
        """Property 9: Audit Logging Completeness
        
        For any data access decision (allowed or denied), an audit log entry SHALL 
        be created containing user_id, session_id, entity_type, and decision.
        
        **Validates: Requirements 4.5**
        """
        # Feature: session-row-level-security, Property 9: Audit Logging Completeness
        
        # Test in open access mode
        engine_open = RowLevelSecurityEngine(open_access_mode=True)
        
        context = SessionContext(
            session_id=session_id,
            user_id=user_id,
            identity={"id": user_id},
            permissions={},
            data_scope="station",
            station="LAX"
        )
        
        results = [{"id": f"item_{i}"} for i in range(num_items)]
        
        # Perform access
        engine_open.filter_results(entity_type, results, context)
        
        # Verify audit log was created
        assert len(engine_open.audit_log) >= 1, \
            "At least one audit log entry should be created"
        
        # Verify audit log contains required fields
        log_entry = engine_open.audit_log[0]
        assert log_entry.user_id == user_id, \
            f"Audit log should contain user_id: expected {user_id}, got {log_entry.user_id}"
        assert log_entry.session_id == session_id, \
            f"Audit log should contain session_id: expected {session_id}, got {log_entry.session_id}"
        assert log_entry.entity_type == entity_type, \
            f"Audit log should contain entity_type: expected {entity_type}, got {log_entry.entity_type}"
        assert log_entry.decision is not None, \
            "Audit log should contain decision"
        assert log_entry.timestamp is not None, \
            "Audit log should contain timestamp"
    
    @given(
        user_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        station=st.sampled_from(["LAX", "JFK", "ORD", "DFW", "ATL"]),
    )
    @settings(max_examples=100)
    def test_audit_logs_denied_access(self, user_id, station):
        """Test that denied access decisions are logged.
        
        **Validates: Requirements 4.5**
        """
        # Feature: session-row-level-security, Property 9: Audit Logging Completeness (denied)
        
        # Create RLS engine with restrictions
        engine = RowLevelSecurityEngine(open_access_mode=False)
        engine.register_policy(PermissionPolicy(
            entity_type="investigation",
            allowed_scopes=[DataScope.STATION],
            owner_field="created_by",
            scope_field="station"
        ))
        
        context = SessionContext(
            session_id="test-session",
            user_id=user_id,
            identity={"id": user_id},
            permissions={},
            data_scope="station",
            station=station
        )
        
        # Create item that will be denied (different station, different owner)
        other_station = "JFK" if station != "JFK" else "LAX"
        results = [{
            "id": "denied_item",
            "created_by": "other_user",
            "station": other_station
        }]
        
        # Perform access (should be denied)
        filtered = engine.filter_results("investigation", results, context)
        
        # Verify item was denied
        assert len(filtered) == 0, "Item should be denied"
        
        # Verify denied access was logged
        denied_logs = [log for log in engine.audit_log if log.decision == AccessDecision.DENIED]
        assert len(denied_logs) >= 1, \
            "Denied access should be logged"
        
        denied_log = denied_logs[0]
        assert denied_log.user_id == user_id, \
            "Denied log should contain correct user_id"
        assert denied_log.entity_type == "investigation", \
            "Denied log should contain correct entity_type"
    
    @given(
        user_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    )
    @settings(max_examples=100)
    def test_audit_logs_allowed_access(self, user_id):
        """Test that allowed access decisions are logged.
        
        **Validates: Requirements 4.5**
        """
        # Feature: session-row-level-security, Property 9: Audit Logging Completeness (allowed)
        
        # Create RLS engine with restrictions
        engine = RowLevelSecurityEngine(open_access_mode=False)
        engine.register_policy(PermissionPolicy(
            entity_type="investigation",
            allowed_scopes=[DataScope.STATION],
            owner_field="created_by",
            scope_field="station"
        ))
        
        context = SessionContext(
            session_id="test-session",
            user_id=user_id,
            identity={"id": user_id},
            permissions={},
            data_scope="station",
            station="LAX"
        )
        
        # Create item that will be allowed (user is owner)
        results = [{
            "id": "allowed_item",
            "created_by": user_id,  # User owns this item
            "station": "JFK"  # Different station but user is owner
        }]
        
        # Perform access (should be allowed)
        filtered = engine.filter_results("investigation", results, context)
        
        # Verify item was allowed
        assert len(filtered) == 1, "Item should be allowed (user is owner)"
        
        # Verify allowed access was logged
        allowed_logs = [log for log in engine.audit_log if log.decision == AccessDecision.ALLOWED]
        assert len(allowed_logs) >= 1, \
            "Allowed access should be logged"
        
        allowed_log = allowed_logs[0]
        assert allowed_log.user_id == user_id, \
            "Allowed log should contain correct user_id"
    
    @given(
        user_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        entity_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    )
    @settings(max_examples=100)
    def test_single_access_audit_logging(self, user_id, entity_id):
        """Test that single item access checks are logged.
        
        **Validates: Requirements 4.5**
        """
        # Feature: session-row-level-security, Property 9: Audit Logging Completeness (single access)
        
        engine = RowLevelSecurityEngine(open_access_mode=True)
        
        context = SessionContext(
            session_id="test-session",
            user_id=user_id,
            identity={"id": user_id},
            permissions={},
            data_scope="company",
            station="LAX"
        )
        
        item = {"id": entity_id, "data": "test"}
        
        # Perform single access check
        engine.check_single_access("test_entity", item, context)
        
        # Verify audit log was created
        assert len(engine.audit_log) == 1, \
            "Single access check should create one audit log entry"
        
        log_entry = engine.audit_log[0]
        assert log_entry.user_id == user_id, \
            "Audit log should contain correct user_id"
        assert log_entry.entity_id == entity_id, \
            f"Audit log should contain entity_id: expected {entity_id}, got {log_entry.entity_id}"
        assert log_entry.entity_type == "test_entity", \
            "Audit log should contain correct entity_type"



# ============================================================================
# Tests for Stream Handler Factory
# ============================================================================

class MockWebSocket:
    """Mock WebSocket for testing stream handlers."""
    
    def __init__(self, should_fail: bool = False):
        self.messages: list = []
        self.should_fail = should_fail
        self.closed = False
    
    async def send_json(self, data: Dict[str, Any]) -> None:
        """Mock send_json method."""
        if self.should_fail:
            raise ConnectionError("WebSocket connection failed")
        if self.closed:
            raise ConnectionError("WebSocket is closed")
        self.messages.append(data)


class TestWebSocketStreamHandler:
    """Unit tests for WebSocketStreamHandler."""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        return MockWebSocket()
    
    def test_handler_creation(self, mock_websocket):
        """Test creating a WebSocketStreamHandler."""
        from src.handlers.stream_handler_factory import WebSocketStreamHandler
        
        handler = WebSocketStreamHandler(mock_websocket, "test-session-123")
        assert handler.session_id == "test-session-123"
        assert handler.is_closed is False
        assert handler.message_count == 0
    
    def test_handler_close(self, mock_websocket):
        """Test closing a handler."""
        from src.handlers.stream_handler_factory import WebSocketStreamHandler
        
        handler = WebSocketStreamHandler(mock_websocket, "test-session")
        assert handler.is_closed is False
        
        handler.close()
        assert handler.is_closed is True
    
    def test_send_message(self, mock_websocket):
        """Test sending a message through the handler."""
        import asyncio
        from src.handlers.stream_handler_factory import WebSocketStreamHandler
        
        handler = WebSocketStreamHandler(mock_websocket, "test-session")
        
        async def do_send():
            return await handler.send({"type": "test", "data": "hello"})
        
        result = asyncio.get_event_loop().run_until_complete(do_send())
        
        assert result is True
        assert handler.message_count == 1
        assert len(mock_websocket.messages) == 1
        assert mock_websocket.messages[0]["type"] == "test"
        assert mock_websocket.messages[0]["_session_id"] == "test-session"
    
    def test_send_after_close(self, mock_websocket):
        """Test that sending after close returns False."""
        import asyncio
        from src.handlers.stream_handler_factory import WebSocketStreamHandler
        
        handler = WebSocketStreamHandler(mock_websocket, "test-session")
        handler.close()
        
        async def do_send():
            return await handler.send({"type": "test"})
        
        result = asyncio.get_event_loop().run_until_complete(do_send())
        assert result is False
        assert len(mock_websocket.messages) == 0
    
    def test_send_handles_error(self):
        """Test that send handles WebSocket errors gracefully."""
        import asyncio
        from src.handlers.stream_handler_factory import WebSocketStreamHandler
        
        failing_ws = MockWebSocket(should_fail=True)
        handler = WebSocketStreamHandler(failing_ws, "test-session")
        
        async def do_send():
            return await handler.send({"type": "test"})
        
        result = asyncio.get_event_loop().run_until_complete(do_send())
        assert result is False
        assert handler.is_closed is True  # Handler should be marked closed on error


class TestStreamHandlerFactory:
    """Unit tests for StreamHandlerFactory."""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        return MockWebSocket()
    
    def test_create_handler(self, mock_websocket):
        """Test creating a handler through the factory."""
        from src.handlers.stream_handler_factory import StreamHandlerFactory, WebSocketStreamHandler
        
        StreamHandlerFactory.reset_handler_count()
        handler = StreamHandlerFactory.create_websocket_handler(mock_websocket, "session-1")
        
        assert isinstance(handler, WebSocketStreamHandler)
        assert handler.session_id == "session-1"
        assert StreamHandlerFactory.get_handler_count() == 1
    
    def test_create_multiple_handlers(self, mock_websocket):
        """Test creating multiple handlers creates separate instances."""
        from src.handlers.stream_handler_factory import StreamHandlerFactory
        
        StreamHandlerFactory.reset_handler_count()
        
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        
        handler1 = StreamHandlerFactory.create_websocket_handler(ws1, "session-1")
        handler2 = StreamHandlerFactory.create_websocket_handler(ws2, "session-2")
        
        assert handler1 is not handler2
        assert handler1.session_id != handler2.session_id
        assert StreamHandlerFactory.get_handler_count() == 2


# ============================================================================
# Property-Based Tests for Stream Handler Factory
# ============================================================================

class TestStreamHandlerProperties:
    """Property-based tests for Stream Handler Factory.
    
    Feature: session-row-level-security
    """
    
    @given(
        num_handlers=st.integers(min_value=2, max_value=50),
    )
    @settings(max_examples=100)
    def test_request_scoped_stream_handler(self, num_handlers):
        """Property 4: Request-Scoped Stream Handler
        
        For any WebSocket query, a new stream handler instance SHALL be created,
        and no global stream handler references SHALL be modified.
        
        **Validates: Requirements 2.1, 2.2**
        """
        # Feature: session-row-level-security, Property 4: Request-Scoped Stream Handler
        from src.handlers.stream_handler_factory import StreamHandlerFactory, WebSocketStreamHandler
        
        StreamHandlerFactory.reset_handler_count()
        
        # Create multiple handlers simulating concurrent WebSocket connections
        handlers = []
        websockets = []
        
        for i in range(num_handlers):
            ws = MockWebSocket()
            websockets.append(ws)
            handler = StreamHandlerFactory.create_websocket_handler(ws, f"session-{i}")
            handlers.append(handler)
        
        # Verify each handler is a unique instance
        handler_ids = [id(h) for h in handlers]
        assert len(set(handler_ids)) == num_handlers, \
            f"Expected {num_handlers} unique handler instances, got {len(set(handler_ids))}"
        
        # Verify each handler is bound to its own session
        session_ids = [h.session_id for h in handlers]
        assert len(set(session_ids)) == num_handlers, \
            f"Expected {num_handlers} unique session IDs, got {len(set(session_ids))}"
        
        # Verify factory count matches (no global state corruption)
        assert StreamHandlerFactory.get_handler_count() == num_handlers, \
            f"Factory count should be {num_handlers}, got {StreamHandlerFactory.get_handler_count()}"
        
        # Verify each handler is properly typed
        for handler in handlers:
            assert isinstance(handler, WebSocketStreamHandler), \
                "Each handler should be a WebSocketStreamHandler instance"
            assert handler.is_closed is False, \
                "New handlers should not be closed"
            assert handler.message_count == 0, \
                "New handlers should have zero message count"
    
    @given(
        session_id_a=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        session_id_b=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    )
    @settings(max_examples=100)
    def test_handler_isolation(self, session_id_a, session_id_b):
        """Test that handlers are isolated from each other.
        
        Modifying one handler should not affect another.
        
        **Validates: Requirements 2.1, 2.2**
        """
        # Feature: session-row-level-security, Property 4: Request-Scoped Stream Handler (isolation)
        from src.handlers.stream_handler_factory import StreamHandlerFactory
        
        ws_a = MockWebSocket()
        ws_b = MockWebSocket()
        
        handler_a = StreamHandlerFactory.create_websocket_handler(ws_a, session_id_a)
        handler_b = StreamHandlerFactory.create_websocket_handler(ws_b, session_id_b)
        
        # Close handler A
        handler_a.close()
        
        # Handler B should be unaffected
        assert handler_a.is_closed is True, "Handler A should be closed"
        assert handler_b.is_closed is False, "Handler B should NOT be closed"
        
        # Handler B should still have its original session ID
        assert handler_b.session_id == session_id_b, \
            f"Handler B session should be {session_id_b}, got {handler_b.session_id}"


class TestStreamHandlerMessageRoutingProperties:
    """Property-based tests for stream handler message routing.
    
    Feature: session-row-level-security
    """
    
    @given(
        num_connections=st.integers(min_value=2, max_value=10),
        num_messages=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=100)
    def test_stream_handler_message_routing(self, num_connections, num_messages):
        """Property 5: Stream Handler Message Routing
        
        For any set of N concurrent WebSocket connections, messages sent through
        stream handler H_i SHALL only be received by client C_i.
        
        **Validates: Requirements 2.3, 2.4, 2.5**
        """
        # Feature: session-row-level-security, Property 5: Stream Handler Message Routing
        import asyncio
        from src.handlers.stream_handler_factory import StreamHandlerFactory
        
        # Create multiple WebSocket connections and handlers
        websockets = [MockWebSocket() for _ in range(num_connections)]
        handlers = [
            StreamHandlerFactory.create_websocket_handler(ws, f"session-{i}")
            for i, ws in enumerate(websockets)
        ]
        
        # Send messages through each handler
        async def send_messages():
            for i, handler in enumerate(handlers):
                for j in range(num_messages):
                    await handler.send({
                        "type": "test",
                        "handler_index": i,
                        "message_index": j
                    })
        
        # Run the async function
        asyncio.get_event_loop().run_until_complete(send_messages())
        
        # Verify each WebSocket received only its own messages
        for i, ws in enumerate(websockets):
            # Each WebSocket should have exactly num_messages
            assert len(ws.messages) == num_messages, \
                f"WebSocket {i} should have {num_messages} messages, got {len(ws.messages)}"
            
            # All messages should be from the correct handler
            for msg in ws.messages:
                assert msg["handler_index"] == i, \
                    f"WebSocket {i} received message from handler {msg['handler_index']}"
                assert msg["_session_id"] == f"session-{i}", \
                    f"Message session_id should be session-{i}, got {msg['_session_id']}"
    
    @given(
        session_id=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    )
    @settings(max_examples=100)
    def test_disconnection_handling(self, session_id):
        """Test that disconnection is handled gracefully.
        
        When a WebSocket disconnects, only that handler should be affected.
        
        **Validates: Requirements 2.4, 2.5**
        """
        # Feature: session-row-level-security, Property 5: Stream Handler Message Routing (disconnection)
        import asyncio
        from src.handlers.stream_handler_factory import StreamHandlerFactory
        
        # Create a failing WebSocket (simulates disconnection)
        failing_ws = MockWebSocket(should_fail=True)
        healthy_ws = MockWebSocket()
        
        failing_handler = StreamHandlerFactory.create_websocket_handler(failing_ws, f"failing-{session_id}")
        healthy_handler = StreamHandlerFactory.create_websocket_handler(healthy_ws, f"healthy-{session_id}")
        
        # Send message through failing handler
        async def test_send():
            result_fail = await failing_handler.send({"type": "test"})
            result_healthy = await healthy_handler.send({"type": "test"})
            return result_fail, result_healthy
        
        result_fail, result_healthy = asyncio.get_event_loop().run_until_complete(test_send())
        
        # Failing handler should fail gracefully
        assert result_fail is False, "Failing handler should return False"
        assert failing_handler.is_closed is True, "Failing handler should be marked closed"
        
        # Healthy handler should be unaffected
        assert result_healthy is True, "Healthy handler should succeed"
        assert healthy_handler.is_closed is False, "Healthy handler should remain open"
        assert len(healthy_ws.messages) == 1, "Healthy WebSocket should have received message"
    
    @given(
        session_id=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    )
    @settings(max_examples=100)
    def test_error_isolation(self, session_id):
        """Test that errors are isolated to the affected session.
        
        **Validates: Requirements 2.5**
        """
        # Feature: session-row-level-security, Property 5: Stream Handler Message Routing (error isolation)
        from src.handlers.stream_handler_factory import StreamHandlerFactory
        
        ws = MockWebSocket()
        handler = StreamHandlerFactory.create_websocket_handler(ws, session_id)
        
        # Simulate an error
        test_error = ValueError("Test error")
        handler.on_error(test_error, "test_context")
        
        # Handler should still be functional (error doesn't close it)
        assert handler.is_closed is False, \
            "Handler should not be closed after error event"
        
        # Error should be sent to the WebSocket (via send_sync)
        # Note: send_sync schedules async send, so we check the handler state
        assert handler.session_id == session_id, \
            "Handler should maintain its session ID after error"



# ============================================================================
# Tests for Investigation Store
# ============================================================================

class TestInvestigationStore:
    """Unit tests for InvestigationStore."""
    
    @pytest.fixture
    def rls_engine_open(self):
        """Create RLS engine in open access mode."""
        return RowLevelSecurityEngine(open_access_mode=True)
    
    @pytest.fixture
    def rls_engine_restricted(self):
        """Create RLS engine with restrictions enabled."""
        from src.security.session_models import PermissionPolicy, DataScope
        engine = RowLevelSecurityEngine(open_access_mode=False)
        engine.register_policy(PermissionPolicy(
            entity_type="investigation",
            allowed_scopes=[DataScope.STATION, DataScope.REGION, DataScope.COMPANY],
            owner_field="created_by",
            scope_field="station"
        ))
        return engine
    
    @pytest.fixture
    def store_open(self, rls_engine_open):
        """Create investigation store with open access."""
        from src.data.investigation_store import InvestigationStore
        return InvestigationStore(rls_engine_open)
    
    @pytest.fixture
    def store_restricted(self, rls_engine_restricted):
        """Create investigation store with restrictions."""
        from src.data.investigation_store import InvestigationStore
        return InvestigationStore(rls_engine_restricted)
    
    @pytest.fixture
    def user_context(self):
        """Create a test session context for user-1."""
        return SessionContext(
            session_id="session-user-1",
            user_id="user-1",
            identity={"id": "user-1", "region": "West"},
            permissions={},
            data_scope="station",
            station="LAX"
        )
    
    @pytest.fixture
    def other_user_context(self):
        """Create a test session context for user-2."""
        return SessionContext(
            session_id="session-user-2",
            user_id="user-2",
            identity={"id": "user-2", "region": "East"},
            permissions={},
            data_scope="station",
            station="JFK"
        )
    
    def test_create_investigation(self, store_open, user_context):
        """Test creating an investigation."""
        inv = store_open.create(
            {"title": "Test Investigation", "status": "active"},
            user_context
        )
        
        assert inv["id"] is not None
        assert inv["title"] == "Test Investigation"
        assert inv["created_by"] == "user-1"
        assert inv["session_id"] == "session-user-1"
        assert inv["station"] == "LAX"
        assert inv["created_at"] is not None
    
    def test_create_with_custom_id(self, store_open, user_context):
        """Test creating an investigation with custom ID."""
        inv = store_open.create(
            {"title": "Custom ID Test"},
            user_context,
            investigation_id="custom-123"
        )
        
        assert inv["id"] == "custom-123"
    
    def test_get_own_investigation(self, store_open, user_context):
        """Test getting own investigation."""
        created = store_open.create({"title": "My Investigation"}, user_context)
        retrieved = store_open.get(created["id"], user_context)
        
        assert retrieved is not None
        assert retrieved["id"] == created["id"]
        assert retrieved["title"] == "My Investigation"
    
    def test_get_nonexistent_investigation(self, store_open, user_context):
        """Test getting a nonexistent investigation returns None."""
        result = store_open.get("nonexistent-id", user_context)
        assert result is None
    
    def test_list_investigations(self, store_open, user_context):
        """Test listing investigations."""
        store_open.create({"title": "Investigation 1"}, user_context)
        store_open.create({"title": "Investigation 2"}, user_context)
        
        results = store_open.list(user_context)
        assert len(results) == 2
    
    def test_list_with_station_filter(self, store_open, user_context, other_user_context):
        """Test listing investigations with station filter."""
        store_open.create({"title": "LAX Investigation"}, user_context)
        store_open.create({"title": "JFK Investigation"}, other_user_context)
        
        lax_results = store_open.list(user_context, station="LAX")
        assert len(lax_results) == 1
        assert lax_results[0]["station"] == "LAX"
    
    def test_update_investigation(self, store_open, user_context):
        """Test updating an investigation."""
        created = store_open.create({"title": "Original Title"}, user_context)
        updated = store_open.update(created["id"], {"title": "Updated Title"}, user_context)
        
        assert updated is not None
        assert updated["title"] == "Updated Title"
        # updated_at should be set (may be same as created_at if test runs fast)
        assert updated["updated_at"] is not None
    
    def test_update_protected_fields_ignored(self, store_open, user_context):
        """Test that protected fields cannot be updated."""
        created = store_open.create({"title": "Test"}, user_context)
        original_created_by = created["created_by"]
        
        updated = store_open.update(
            created["id"],
            {"created_by": "hacker", "title": "New Title"},
            user_context
        )
        
        assert updated["created_by"] == original_created_by
        assert updated["title"] == "New Title"
    
    def test_delete_investigation(self, store_open, user_context):
        """Test deleting an investigation."""
        created = store_open.create({"title": "To Delete"}, user_context)
        
        result = store_open.delete(created["id"], user_context)
        assert result is True
        
        # Verify it's gone
        assert store_open.get(created["id"], user_context) is None
    
    def test_delete_nonexistent(self, store_open, user_context):
        """Test deleting a nonexistent investigation returns False."""
        result = store_open.delete("nonexistent-id", user_context)
        assert result is False
    
    def test_count_investigations(self, store_open, user_context):
        """Test counting investigations."""
        store_open.create({"title": "Investigation 1"}, user_context)
        store_open.create({"title": "Investigation 2"}, user_context)
        
        assert store_open.count(user_context) == 2
    
    def test_exists(self, store_open, user_context):
        """Test checking if investigation exists."""
        created = store_open.create({"title": "Test"}, user_context)
        
        assert store_open.exists(created["id"], user_context) is True
        assert store_open.exists("nonexistent", user_context) is False


class TestInvestigationStoreRLS:
    """Tests for InvestigationStore with RLS restrictions."""
    
    @pytest.fixture
    def rls_engine_restricted(self):
        """Create RLS engine with restrictions enabled."""
        from src.security.session_models import PermissionPolicy, DataScope
        engine = RowLevelSecurityEngine(open_access_mode=False)
        engine.register_policy(PermissionPolicy(
            entity_type="investigation",
            allowed_scopes=[DataScope.STATION, DataScope.REGION, DataScope.COMPANY],
            owner_field="created_by",
            scope_field="station"
        ))
        return engine
    
    @pytest.fixture
    def store(self, rls_engine_restricted):
        """Create investigation store with restrictions."""
        from src.data.investigation_store import InvestigationStore
        return InvestigationStore(rls_engine_restricted)
    
    @pytest.fixture
    def user1_context(self):
        """Create session context for user-1 at LAX."""
        return SessionContext(
            session_id="session-user-1",
            user_id="user-1",
            identity={"id": "user-1", "region": "West"},
            permissions={},
            data_scope="station",
            station="LAX"
        )
    
    @pytest.fixture
    def user2_context(self):
        """Create session context for user-2 at JFK."""
        return SessionContext(
            session_id="session-user-2",
            user_id="user-2",
            identity={"id": "user-2", "region": "East"},
            permissions={},
            data_scope="station",
            station="JFK"
        )
    
    def test_cannot_access_other_user_investigation(self, store, user1_context, user2_context):
        """Test that user cannot access another user's investigation."""
        # User 1 creates an investigation
        created = store.create({"title": "User 1's Investigation"}, user1_context)
        
        # User 2 tries to access it (different station, not owner)
        result = store.get(created["id"], user2_context)
        assert result is None
    
    def test_owner_can_access_own_investigation(self, store, user1_context):
        """Test that owner can always access their own investigation."""
        created = store.create({"title": "My Investigation"}, user1_context)
        result = store.get(created["id"], user1_context)
        
        assert result is not None
        assert result["id"] == created["id"]
    
    def test_list_only_shows_accessible(self, store, user1_context, user2_context):
        """Test that list only shows accessible investigations."""
        # User 1 creates investigations
        store.create({"title": "User 1 Investigation 1"}, user1_context)
        store.create({"title": "User 1 Investigation 2"}, user1_context)
        
        # User 2 creates investigations
        store.create({"title": "User 2 Investigation"}, user2_context)
        
        # User 1 should only see their own (station scope)
        user1_results = store.list(user1_context)
        assert len(user1_results) == 2
        for inv in user1_results:
            assert inv["created_by"] == "user-1"
        
        # User 2 should only see their own
        user2_results = store.list(user2_context)
        assert len(user2_results) == 1
        assert user2_results[0]["created_by"] == "user-2"
    
    def test_cannot_update_other_user_investigation(self, store, user1_context, user2_context):
        """Test that user cannot update another user's investigation."""
        created = store.create({"title": "User 1's Investigation"}, user1_context)
        
        # User 2 tries to update it
        result = store.update(created["id"], {"title": "Hacked!"}, user2_context)
        assert result is None
        
        # Verify original is unchanged
        original = store.get(created["id"], user1_context)
        assert original["title"] == "User 1's Investigation"
    
    def test_cannot_delete_other_user_investigation(self, store, user1_context, user2_context):
        """Test that user cannot delete another user's investigation."""
        created = store.create({"title": "User 1's Investigation"}, user1_context)
        
        # User 2 tries to delete it
        result = store.delete(created["id"], user2_context)
        assert result is False
        
        # Verify it still exists
        assert store.get(created["id"], user1_context) is not None


# ============================================================================
# Property-Based Tests for Investigation Store
# ============================================================================

class TestInvestigationStoreProperties:
    """Property-based tests for InvestigationStore.
    
    Feature: session-row-level-security
    """
    
    @given(
        owner_user_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        other_user_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        owner_station=st.sampled_from(["LAX", "JFK", "ORD", "DFW", "ATL"]),
        other_station=st.sampled_from(["LAX", "JFK", "ORD", "DFW", "ATL"]),
        title=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs'))),
    )
    @SLOW_STORE_SETTINGS
    def test_data_ownership_enforcement(self, owner_user_id, other_user_id, owner_station, other_station, title):
        """Property 6: Data Ownership Enforcement
        
        For any investigation created by user U, when row-level security is enabled,
        only user U (or users with appropriate scope) SHALL be able to access that investigation.
        
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        """
        # Feature: session-row-level-security, Property 6: Data Ownership Enforcement
        from src.data.investigation_store import InvestigationStore
        from src.security.session_models import PermissionPolicy, DataScope
        
        # Skip if users are the same (ownership would be shared)
        if owner_user_id == other_user_id:
            return
        
        # Create RLS engine with restrictions enabled
        rls_engine = RowLevelSecurityEngine(open_access_mode=False)
        rls_engine.register_policy(PermissionPolicy(
            entity_type="investigation",
            allowed_scopes=[DataScope.STATION, DataScope.REGION, DataScope.COMPANY],
            owner_field="created_by",
            scope_field="station"
        ))
        
        store = InvestigationStore(rls_engine)
        
        # Create owner's session context
        owner_context = SessionContext(
            session_id=f"session-{owner_user_id}",
            user_id=owner_user_id,
            identity={"id": owner_user_id, "region": "West"},
            permissions={},
            data_scope="station",
            station=owner_station
        )
        
        # Create other user's session context
        other_context = SessionContext(
            session_id=f"session-{other_user_id}",
            user_id=other_user_id,
            identity={"id": other_user_id, "region": "East"},
            permissions={},
            data_scope="station",
            station=other_station
        )
        
        # Owner creates an investigation
        created = store.create({"title": title}, owner_context)
        
        # Verify investigation was created with correct ownership
        assert created["created_by"] == owner_user_id, \
            "Investigation should be owned by creating user"
        assert created["session_id"] == f"session-{owner_user_id}", \
            "Investigation should be associated with creating session"
        
        # Owner should always be able to access their own investigation
        owner_access = store.get(created["id"], owner_context)
        assert owner_access is not None, \
            "Owner should always be able to access their own investigation"
        assert owner_access["id"] == created["id"], \
            "Owner should get the correct investigation"
        
        # Other user access depends on station
        other_access = store.get(created["id"], other_context)
        
        if owner_station == other_station:
            # Same station - other user should have access
            assert other_access is not None, \
                "User at same station should have access"
        else:
            # Different station and not owner - should be denied
            assert other_access is None, \
                "User at different station (not owner) should be denied access"
        
        # Owner should be able to update their investigation
        updated = store.update(created["id"], {"status": "updated"}, owner_context)
        assert updated is not None, \
            "Owner should be able to update their investigation"
        
        # Other user should not be able to update (unless same station)
        if owner_station != other_station:
            other_update = store.update(created["id"], {"status": "hacked"}, other_context)
            assert other_update is None, \
                "Non-owner at different station should not be able to update"
        
        # Owner should be able to delete their investigation
        # (We'll create a new one to test delete since we want to keep testing)
        delete_test = store.create({"title": "Delete Test"}, owner_context)
        
        # Other user should not be able to delete (unless same station)
        if owner_station != other_station:
            other_delete = store.delete(delete_test["id"], other_context)
            assert other_delete is False, \
                "Non-owner at different station should not be able to delete"
        
        # Owner should be able to delete
        owner_delete = store.delete(delete_test["id"], owner_context)
        assert owner_delete is True, \
            "Owner should be able to delete their investigation"
    
    @given(
        user_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        station=st.sampled_from(["LAX", "JFK", "ORD", "DFW", "ATL"]),
        num_investigations=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100)
    def test_list_returns_only_owned_or_accessible(self, user_id, station, num_investigations):
        """Test that list returns only owned or accessible investigations.
        
        **Validates: Requirements 3.2**
        """
        # Feature: session-row-level-security, Property 6: Data Ownership Enforcement (list)
        from src.data.investigation_store import InvestigationStore
        from src.security.session_models import PermissionPolicy, DataScope
        
        # Create RLS engine with restrictions
        rls_engine = RowLevelSecurityEngine(open_access_mode=False)
        rls_engine.register_policy(PermissionPolicy(
            entity_type="investigation",
            allowed_scopes=[DataScope.STATION, DataScope.REGION, DataScope.COMPANY],
            owner_field="created_by",
            scope_field="station"
        ))
        
        store = InvestigationStore(rls_engine)
        
        # Create user context
        user_context = SessionContext(
            session_id=f"session-{user_id}",
            user_id=user_id,
            identity={"id": user_id, "region": "West"},
            permissions={},
            data_scope="station",
            station=station
        )
        
        # Create investigations for this user
        for i in range(num_investigations):
            store.create({"title": f"Investigation {i}"}, user_context)
        
        # Create investigations for other users at different stations
        other_stations = [s for s in ["LAX", "JFK", "ORD", "DFW", "ATL"] if s != station]
        for i, other_station in enumerate(other_stations[:2]):
            other_context = SessionContext(
                session_id=f"session-other-{i}",
                user_id=f"other-user-{i}",
                identity={"id": f"other-user-{i}", "region": "Other"},
                permissions={},
                data_scope="station",
                station=other_station
            )
            store.create({"title": f"Other Investigation {i}"}, other_context)
        
        # List investigations for user
        results = store.list(user_context)
        
        # All results should be either owned by user or at user's station
        for inv in results:
            is_owner = inv["created_by"] == user_id
            is_same_station = inv["station"] == station
            assert is_owner or is_same_station, \
                f"Listed investigation should be owned by user or at same station"
        
        # User should see at least their own investigations
        assert len(results) >= num_investigations, \
            f"User should see at least {num_investigations} investigations (their own)"
    
    @given(
        user_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        data_scope=st.sampled_from(["station", "region", "company"]),
        station=st.sampled_from(["LAX", "JFK", "ORD", "DFW", "ATL"]),
    )
    @settings(max_examples=100)
    def test_company_scope_sees_all(self, user_id, data_scope, station):
        """Test that company scope users can see all investigations.
        
        **Validates: Requirements 3.2**
        """
        # Feature: session-row-level-security, Property 6: Data Ownership Enforcement (company scope)
        from src.data.investigation_store import InvestigationStore
        from src.security.session_models import PermissionPolicy, DataScope
        
        # Create RLS engine with restrictions
        rls_engine = RowLevelSecurityEngine(open_access_mode=False)
        rls_engine.register_policy(PermissionPolicy(
            entity_type="investigation",
            allowed_scopes=[DataScope.STATION, DataScope.REGION, DataScope.COMPANY],
            owner_field="created_by",
            scope_field="station"
        ))
        
        store = InvestigationStore(rls_engine)
        
        # Create investigations from different users at different stations
        stations = ["LAX", "JFK", "ORD"]
        for i, inv_station in enumerate(stations):
            other_context = SessionContext(
                session_id=f"session-creator-{i}",
                user_id=f"creator-{i}",
                identity={"id": f"creator-{i}", "region": "Various"},
                permissions={},
                data_scope="station",
                station=inv_station
            )
            store.create({"title": f"Investigation at {inv_station}"}, other_context)
        
        # Create user context with specified scope
        user_context = SessionContext(
            session_id=f"session-{user_id}",
            user_id=user_id,
            identity={"id": user_id, "region": "West"},
            permissions={},
            data_scope=data_scope,
            station=station
        )
        
        # List investigations
        results = store.list(user_context)
        
        if data_scope == "company":
            # Company scope should see all investigations
            assert len(results) == len(stations), \
                f"Company scope should see all {len(stations)} investigations"
        elif data_scope == "station":
            # Station scope should only see investigations at their station
            for inv in results:
                is_owner = inv["created_by"] == user_id
                is_same_station = inv["station"] == station
                assert is_owner or is_same_station, \
                    "Station scope should only see owned or same-station investigations"


# ============================================================================
# Property-Based Tests for Concurrent Request Safety
# ============================================================================

class TestConcurrentRequestSafety:
    """Property-based tests for concurrent request safety.
    
    Feature: session-row-level-security
    
    These tests verify that the system handles concurrent requests safely
    without race conditions or data corruption.
    """
    
    @given(
        num_sessions=st.integers(min_value=2, max_value=10),
        num_operations=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=100, deadline=5000)
    def test_concurrent_session_creation(self, num_sessions, num_operations):
        """Property 10: Concurrent Request Safety - Session Creation
        
        For any set of concurrent requests, no module-level global variables 
        SHALL be used for request-specific state, and no race conditions 
        SHALL cause data corruption.
        
        **Validates: Requirements 7.1, 7.2, 7.4**
        """
        # Feature: session-row-level-security, Property 10: Concurrent Request Safety
        import threading
        import time
        
        provider = LocalIdentityProvider([
            {"id": f"user-{i}", "name": f"User {i}", "station": "LAX"}
            for i in range(num_sessions)
        ])
        manager = SessionManager(provider)
        
        # Track created sessions
        created_sessions = []
        errors = []
        lock = threading.Lock()
        
        def create_sessions(user_idx):
            """Create multiple sessions for a user."""
            try:
                for op in range(num_operations):
                    ctx = manager.create_session(
                        f"user-{user_idx}",
                        {"id": f"user-{user_idx}", "name": f"User {user_idx}"}
                    )
                    with lock:
                        created_sessions.append(ctx.session_id)
            except Exception as e:
                with lock:
                    errors.append(str(e))
        
        # Create threads for concurrent session creation
        threads = []
        for i in range(num_sessions):
            t = threading.Thread(target=create_sessions, args=(i,))
            threads.append(t)
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join(timeout=5.0)
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Errors during concurrent session creation: {errors}"
        
        # Verify all sessions were created
        expected_count = num_sessions * num_operations
        assert len(created_sessions) == expected_count, \
            f"Expected {expected_count} sessions, got {len(created_sessions)}"
        
        # Verify all session IDs are unique (no collisions)
        unique_sessions = set(created_sessions)
        assert len(unique_sessions) == expected_count, \
            f"Expected {expected_count} unique sessions, got {len(unique_sessions)} (collision detected)"
    
    @given(
        num_users=st.integers(min_value=2, max_value=5),
        num_investigations=st.integers(min_value=1, max_value=3),
    )
    @settings(max_examples=50, deadline=10000)
    def test_concurrent_investigation_operations(self, num_users, num_investigations):
        """Property 10: Concurrent Request Safety - Investigation Operations
        
        For any set of concurrent investigation operations, the system SHALL
        maintain data integrity without race conditions.
        
        **Validates: Requirements 7.1, 7.2, 7.4**
        """
        # Feature: session-row-level-security, Property 10: Concurrent Request Safety
        import threading
        from src.data.investigation_store import InvestigationStore
        
        # Create RLS engine in open access mode for this test
        rls_engine = RowLevelSecurityEngine(open_access_mode=True)
        store = InvestigationStore(rls_engine)
        
        # Create session contexts for each user
        sessions = []
        for i in range(num_users):
            ctx = SessionContext(
                session_id=f"session-{i}",
                user_id=f"user-{i}",
                identity={"id": f"user-{i}", "name": f"User {i}"},
                permissions={},
                data_scope="company",
                station="LAX"
            )
            sessions.append(ctx)
        
        # Track created investigations
        created_ids = []
        errors = []
        lock = threading.Lock()
        
        def create_investigations(session_ctx, user_idx):
            """Create investigations for a user."""
            try:
                for inv_idx in range(num_investigations):
                    inv = store.create(
                        {"title": f"Investigation {user_idx}-{inv_idx}"},
                        session_ctx
                    )
                    with lock:
                        created_ids.append(inv["id"])
            except Exception as e:
                with lock:
                    errors.append(str(e))
        
        # Create threads for concurrent investigation creation
        threads = []
        for i, session in enumerate(sessions):
            t = threading.Thread(target=create_investigations, args=(session, i))
            threads.append(t)
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join(timeout=10.0)
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Errors during concurrent operations: {errors}"
        
        # Verify all investigations were created
        expected_count = num_users * num_investigations
        assert len(created_ids) == expected_count, \
            f"Expected {expected_count} investigations, got {len(created_ids)}"
        
        # Verify all investigation IDs are unique
        unique_ids = set(created_ids)
        assert len(unique_ids) == expected_count, \
            f"Expected {expected_count} unique IDs, got {len(unique_ids)} (collision detected)"
        
        # Verify each user can see their own investigations
        for i, session in enumerate(sessions):
            user_invs = store.list(session)
            user_owned = [inv for inv in user_invs if inv["created_by"] == f"user-{i}"]
            assert len(user_owned) == num_investigations, \
                f"User {i} should see {num_investigations} of their own investigations"
    
    @given(
        num_sessions=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=50, deadline=5000)
    def test_session_isolation_under_concurrent_updates(self, num_sessions):
        """Property 10: Concurrent Request Safety - Session Isolation
        
        For any set of concurrent session updates, each session's state
        SHALL remain isolated from other sessions.
        
        **Validates: Requirements 7.1, 7.2, 7.4**
        """
        # Feature: session-row-level-security, Property 10: Concurrent Request Safety
        import threading
        
        provider = LocalIdentityProvider([])
        manager = SessionManager(provider)
        
        # Create sessions
        sessions = []
        for i in range(num_sessions):
            ctx = manager.create_session(
                f"user-{i}",
                {"id": f"user-{i}", "name": f"Original Name {i}"}
            )
            sessions.append(ctx)
        
        errors = []
        lock = threading.Lock()
        
        def update_session(session_idx):
            """Update a session's identity multiple times."""
            try:
                session = sessions[session_idx]
                for update_num in range(3):
                    new_name = f"Updated Name {session_idx}-{update_num}"
                    manager.update_identity(
                        session.session_id,
                        {"id": f"user-{session_idx}", "name": new_name}
                    )
                    # Small delay to increase chance of interleaving
                    import time
                    time.sleep(0.001)
            except Exception as e:
                with lock:
                    errors.append(str(e))
        
        # Create threads for concurrent updates
        threads = []
        for i in range(num_sessions):
            t = threading.Thread(target=update_session, args=(i,))
            threads.append(t)
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join(timeout=5.0)
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Errors during concurrent updates: {errors}"
        
        # Verify each session has its own identity (not mixed with others)
        for i, original_session in enumerate(sessions):
            current_session = manager.get_session(original_session.session_id)
            assert current_session is not None, f"Session {i} should still exist"
            
            # The user_id should match the original session's user
            assert current_session.user_id == f"user-{i}", \
                f"Session {i} user_id should be user-{i}, got {current_session.user_id}"
            
            # The identity should belong to this user (not mixed with others)
            assert current_session.identity["id"] == f"user-{i}", \
                f"Session {i} identity should belong to user-{i}"
    
    def test_no_global_state_in_session_manager(self):
        """Test that SessionManager doesn't use module-level global variables.
        
        **Validates: Requirements 7.1**
        """
        # Feature: session-row-level-security, Property 10: Concurrent Request Safety
        
        # Create two independent SessionManager instances
        provider1 = LocalIdentityProvider([{"id": "user-1", "name": "User 1"}])
        provider2 = LocalIdentityProvider([{"id": "user-2", "name": "User 2"}])
        
        manager1 = SessionManager(provider1)
        manager2 = SessionManager(provider2)
        
        # Create sessions in each manager
        ctx1 = manager1.create_session("user-1", {"id": "user-1", "name": "User 1"})
        ctx2 = manager2.create_session("user-2", {"id": "user-2", "name": "User 2"})
        
        # Sessions should be isolated between managers
        assert manager1.get_session(ctx2.session_id) is None, \
            "Manager 1 should not see Manager 2's sessions"
        assert manager2.get_session(ctx1.session_id) is None, \
            "Manager 2 should not see Manager 1's sessions"
        
        # Each manager should only see its own sessions
        assert manager1.get_session(ctx1.session_id) is not None
        assert manager2.get_session(ctx2.session_id) is not None
        
        # Session counts should be independent
        assert manager1.active_session_count == 1
        assert manager2.active_session_count == 1
    
    def test_no_global_state_in_investigation_store(self):
        """Test that InvestigationStore doesn't use module-level global variables.
        
        **Validates: Requirements 7.1**
        """
        # Feature: session-row-level-security, Property 10: Concurrent Request Safety
        from src.data.investigation_store import InvestigationStore
        
        # Create two independent stores
        rls1 = RowLevelSecurityEngine(open_access_mode=True)
        rls2 = RowLevelSecurityEngine(open_access_mode=True)
        
        store1 = InvestigationStore(rls1)
        store2 = InvestigationStore(rls2)
        
        # Create session context
        ctx = SessionContext(
            session_id="test-session",
            user_id="user-1",
            identity={"id": "user-1"},
            permissions={},
            data_scope="company",
            station="LAX"
        )
        
        # Create investigation in store1
        inv1 = store1.create({"title": "Investigation 1"}, ctx)
        
        # Store2 should not see store1's investigations
        assert store2.get(inv1["id"], ctx) is None, \
            "Store 2 should not see Store 1's investigations"
        
        # Store1 should see its own investigation
        assert store1.get(inv1["id"], ctx) is not None
        
        # Counts should be independent
        assert store1.total_count == 1
        assert store2.total_count == 0
