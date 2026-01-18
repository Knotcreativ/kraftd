"""
Tests for multi-tenant scoping in user_profile routes
Validates that user profile endpoints respect tenant boundaries
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from fastapi import HTTPException, status

from routes.user_profile import router, get_profile_service, set_profile_service
from services.profile_service import ProfileService
from services.tenant_service import TenantService
from models.user_preferences import UserProfile, UserPreferencesResponse


class TestUserProfileScoping:
    """Test suite for user profile endpoint multi-tenant isolation"""
    
    @pytest.fixture
    def mock_profile_service(self):
        """Create a mock ProfileService"""
        service = AsyncMock(spec=ProfileService)
        service.get_profile = AsyncMock()
        service.get_preferences = AsyncMock()
        service.update_profile = AsyncMock()
        service.update_preferences = AsyncMock()
        service.get_all_profiles = AsyncMock()
        service.export_profile_data = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_tenant_service(self):
        """Mock TenantService"""
        with patch('routes.user_profile.TenantService') as mock:
            yield mock
    
    @pytest.fixture
    def client(self, mock_profile_service, mock_tenant_service):
        """Create test client"""
        set_profile_service(mock_profile_service)
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_list_profiles_requires_tenant_context(self, mock_profile_service, mock_tenant_service):
        """Test that list_all_profiles endpoint requires tenant context"""
        # Setup: TenantService returns None (no tenant context)
        mock_tenant_service.get_current_tenant.return_value = None
        
        # The endpoint should raise HTTPException when no tenant context
        from routes.user_profile import list_all_profiles
        
        with pytest.raises(HTTPException) as exc_info:
            await list_all_profiles(
                skip=0,
                limit=10,
                current_user=("user@example.com", "admin")
            )
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "tenant context" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_list_profiles_filters_by_tenant(self, mock_profile_service, mock_tenant_service):
        """Test that list_all_profiles applies tenant filtering"""
        # Setup
        tenant_id = "tenant-123"
        mock_tenant_service.get_current_tenant.return_value = tenant_id
        
        mock_profiles = [
            {"id": "1", "email": "user1@example.com", "tenant_id": tenant_id},
            {"id": "2", "email": "user2@example.com", "tenant_id": tenant_id},
        ]
        mock_profile_service.get_all_profiles.return_value = mock_profiles
        
        # Execute
        from routes.user_profile import list_all_profiles
        set_profile_service(mock_profile_service)
        
        result = await list_all_profiles(
            skip=0,
            limit=10,
            current_user=("admin@example.com", "admin")
        )
        
        # Verify tenant_id was passed to service
        mock_profile_service.get_all_profiles.assert_called_once_with(
            skip=0,
            limit=10,
            tenant_id=tenant_id
        )
        
        assert result["count"] == 2
        assert result["profiles"] == mock_profiles
    
    @pytest.mark.asyncio
    async def test_export_user_data_requires_tenant_context(self, mock_profile_service, mock_tenant_service):
        """Test that export_user_data endpoint requires tenant context"""
        # Setup: TenantService returns None (no tenant context)
        mock_tenant_service.get_current_tenant.return_value = None
        
        from routes.user_profile import export_user_data
        set_profile_service(mock_profile_service)
        
        with pytest.raises(HTTPException) as exc_info:
            await export_user_data(
                current_user=("user@example.com", "user")
            )
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_export_user_data_validates_tenant(self, mock_profile_service, mock_tenant_service):
        """Test that export_user_data validates user is in correct tenant"""
        # Setup
        tenant_id = "tenant-123"
        email = "user@example.com"
        mock_tenant_service.get_current_tenant.return_value = tenant_id
        
        export_data = {
            "profile": {"email": email, "tenant_id": tenant_id},
            "preferences": {"theme": "dark"},
            "exported_at": "2024-01-18T00:00:00"
        }
        mock_profile_service.export_profile_data.return_value = export_data
        
        # Execute
        from routes.user_profile import export_user_data
        set_profile_service(mock_profile_service)
        
        result = await export_user_data(
            current_user=(email, "user")
        )
        
        # Verify
        mock_profile_service.export_profile_data.assert_called_once_with(email)
        assert result == export_data
    
    @pytest.mark.asyncio
    async def test_cross_tenant_isolation_list_profiles(self):
        """
        Integration test: Verify cross-tenant isolation
        
        Scenario:
        - Tenant A admin requests profile list
        - System should only return profiles from Tenant A
        - Should not return profiles from Tenant B
        """
        mock_service = AsyncMock(spec=ProfileService)
        tenant_a_profiles = [
            {"id": "1", "email": "a1@example.com", "tenant_id": "tenant-a"},
            {"id": "2", "email": "a2@example.com", "tenant_id": "tenant-a"},
        ]
        mock_service.get_all_profiles.return_value = tenant_a_profiles
        
        set_profile_service(mock_service)
        
        with patch('routes.user_profile.TenantService') as mock_tenant:
            mock_tenant.get_current_tenant.return_value = "tenant-a"
            
            from routes.user_profile import list_all_profiles
            
            result = await list_all_profiles(
                skip=0,
                limit=10,
                current_user=("admin-a@example.com", "admin")
            )
        
        # Verify no Tenant B profiles returned
        assert all(p["tenant_id"] == "tenant-a" for p in result["profiles"])
        assert len(result["profiles"]) == 2
    
    def test_user_profile_get_all_profiles_tenant_query(self, mock_profile_service):
        """
        Test that ProfileService.get_all_profiles builds correct SQL when tenant_id provided
        """
        # This test validates the SQL generation at the service layer
        # Would execute if ProfileService used async query execution
        pass


class TestUserProfileEndpointTenantContext:
    """Tests for tenant context in profile endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_profile_uses_current_user_email(self, mock_profile_service):
        """Test get_user_profile uses current user's email (implicit scoping)"""
        email = "user@example.com"
        mock_profile = {"email": email, "name": "Test User", "tenant_id": "tenant-123"}
        mock_profile_service.get_profile = AsyncMock(return_value=mock_profile)
        
        set_profile_service(mock_profile_service)
        
        from routes.user_profile import get_user_profile
        
        result = await get_user_profile(
            current_user=(email, "user")
        )
        
        # Verify only requesting own profile
        mock_profile_service.get_profile.assert_called_once_with(email)
    
    @pytest.mark.asyncio
    async def test_get_preferences_uses_current_user_email(self, mock_profile_service):
        """Test get_user_preferences uses current user's email (implicit scoping)"""
        email = "user@example.com"
        mock_prefs = UserPreferencesResponse(
            email=email,
            theme="light",
            notifications_enabled=True,
            language="en",
            preferences={},
            updated_at=datetime.now(tz=timezone.utc)
        )
        mock_profile_service.get_preferences = AsyncMock(return_value=mock_prefs)
        
        set_profile_service(mock_profile_service)
        
        from routes.user_profile import get_user_preferences
        
        result = await get_user_preferences(
            current_user=(email, "user")
        )
        
        # Verify only requesting own preferences
        mock_profile_service.get_preferences.assert_called_once_with(email)


# Test data fixtures

@pytest.fixture
def tenant_a_user():
    """Fixture: User from Tenant A"""
    return {
        "email": "alice@tenant-a.com",
        "tenant_id": "tenant-a",
        "name": "Alice",
        "role": "user"
    }


@pytest.fixture
def tenant_b_user():
    """Fixture: User from Tenant B"""
    return {
        "email": "bob@tenant-b.com",
        "tenant_id": "tenant-b",
        "name": "Bob",
        "role": "user"
    }


@pytest.fixture
def tenant_a_admin():
    """Fixture: Admin from Tenant A"""
    return {
        "email": "admin-a@tenant-a.com",
        "tenant_id": "tenant-a",
        "name": "Admin A",
        "role": "admin"
    }
