"""
Test suite for ProfileService - Database Integration Tests
"""

import pytest
import asyncio
from datetime import datetime
from typing import Optional

from services.profile_service import ProfileService
from models.user_preferences import ProfileUpdate, Preferences, UserProfile


class MockCosmosService:
    """Mock CosmosService for testing"""
    
    def __init__(self):
        self._initialized = True
        self._containers = {}
    
    def is_initialized(self):
        return self._initialized
    
    async def get_container(self, database_id: str, container_id: str):
        key = f"{database_id}/{container_id}"
        if key not in self._containers:
            self._containers[key] = MockContainer()
        return self._containers[key]


class MockContainer:
    """Mock Cosmos DB Container"""
    
    def __init__(self):
        self._items = {}
    
    def read_item(self, item: str, partition_key: str):
        if item not in self._items:
            raise Exception(f"Item not found: {item}")
        return self._items[item].copy()
    
    def create_item(self, body: dict):
        item_id = body.get("id")
        if item_id in self._items:
            raise Exception(f"Item already exists: {item_id}")
        self._items[item_id] = body.copy()
    
    def replace_item(self, item: str, body: dict):
        if item not in self._items:
            raise Exception(f"Item not found: {item}")
        self._items[item] = body.copy()
    
    def delete_item(self, item: str, partition_key: str):
        if item not in self._items:
            raise Exception(f"Item not found: {item}")
        del self._items[item]


class TestProfileService:
    """Test cases for ProfileService"""
    
    @pytest.fixture
    async def profile_service(self):
        """Create ProfileService with mock Cosmos DB"""
        cosmos = MockCosmosService()
        service = ProfileService(cosmos)
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_create_profile(self, profile_service):
        """Test creating a new profile"""
        email = "test@example.com"
        
        profile = await profile_service.create_profile(
            email=email,
            first_name="John",
            last_name="Doe"
        )
        
        assert profile is not None
        assert profile.email == email
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
    
    @pytest.mark.asyncio
    async def test_get_profile(self, profile_service):
        """Test retrieving a profile"""
        email = "test@example.com"
        
        # Create profile
        await profile_service.create_profile(email, "John", "Doe")
        
        # Get profile
        profile = await profile_service.get_profile(email)
        
        assert profile is not None
        assert profile.email == email
        assert profile.first_name == "John"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_profile(self, profile_service):
        """Test retrieving non-existent profile returns None"""
        profile = await profile_service.get_profile("nonexistent@example.com")
        assert profile is None
    
    @pytest.mark.asyncio
    async def test_update_profile(self, profile_service):
        """Test updating a profile"""
        email = "test@example.com"
        
        # Create profile
        await profile_service.create_profile(email, "John", "Doe")
        
        # Update profile
        update_data = ProfileUpdate(
            first_name="Jane",
            company="TechCorp"
        )
        updated = await profile_service.update_profile(email, update_data)
        
        assert updated.first_name == "Jane"
        assert updated.company == "TechCorp"
        assert updated.last_name == "Doe"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_create_preferences(self, profile_service):
        """Test creating default preferences"""
        email = "test@example.com"
        
        prefs = await profile_service.create_preferences(email)
        
        assert prefs is not None
        assert prefs.email == email
        assert prefs.preferences.theme.value == "light"
    
    @pytest.mark.asyncio
    async def test_update_preferences(self, profile_service):
        """Test updating preferences"""
        email = "test@example.com"
        
        new_prefs = Preferences(theme="dark", language="es")
        updated = await profile_service.update_preferences(email, new_prefs)
        
        assert updated.email == email
        assert updated.preferences.theme.value == "dark"
        assert updated.preferences.language.value == "es"
    
    @pytest.mark.asyncio
    async def test_get_preferences_defaults(self, profile_service):
        """Test getting preferences returns defaults if not created"""
        email = "test@example.com"
        
        prefs = await profile_service.get_preferences(email)
        
        assert prefs is not None
        assert prefs.email == email
        assert prefs.preferences.theme.value == "light"
    
    @pytest.mark.asyncio
    async def test_export_profile_data(self, profile_service):
        """Test exporting user data (GDPR)"""
        email = "test@example.com"
        
        # Create profile and preferences
        await profile_service.create_profile(email, "John", "Doe")
        new_prefs = Preferences(theme="dark")
        await profile_service.update_preferences(email, new_prefs)
        
        # Export data
        exported = await profile_service.export_profile_data(email)
        
        assert exported["profile"] is not None
        assert exported["profile"]["email"] == email
        assert exported["preferences"] is not None
        assert "exported_at" in exported
    
    @pytest.mark.asyncio
    async def test_delete_profile(self, profile_service):
        """Test deleting a profile"""
        email = "test@example.com"
        
        # Create profile
        await profile_service.create_profile(email)
        
        # Delete profile
        success = await profile_service.delete_profile(email)
        assert success
        
        # Verify deleted
        profile = await profile_service.get_profile(email)
        assert profile is None


# Run tests with: pytest backend/tests/test_profile_service.py -v
