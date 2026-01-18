"""Pytest configuration for KraftdIntel backend tests"""
import sys
from pathlib import Path
import pytest
import uuid

# Add backend directory to Python path so imports work
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from services.tenant_service import TenantService, TenantContext
from services.rbac_service import UserRole
from services.event_broadcaster import ClientConnection
from services.profile_service import ProfileService
from routes.user_profile import set_profile_service


@pytest.fixture(autouse=True)
def reset_tenant_context():
    """Reset tenant context before and after each test"""
    # Reset before test
    TenantService.clear_current_tenant()
    
    yield
    
    # Reset after test
    TenantService.clear_current_tenant()


@pytest.fixture(autouse=True)
def init_profile_service():
    """Initialize ProfileService for all tests"""
    # Create a mock cosmos_service that satisfies ProfileService requirements
    from unittest.mock import Mock
    
    mock_cosmos = Mock()
    mock_cosmos.is_initialized.return_value = False  # Tests don't need actual DB
    
    service = ProfileService(mock_cosmos)
    set_profile_service(service)
    yield
    # Service is stateless, no cleanup needed


def create_client_connection(websocket, user_id: str) -> ClientConnection:
    """Helper to create ClientConnection with auto-generated client_id"""
    client_id = f"test-client-{uuid.uuid4()}"
    return ClientConnection(client_id, websocket, user_id)


@pytest.fixture
def tenant_context_tenant_b():
    """Fixture providing TenantContext for tenant-b"""
    context = TenantContext(
        tenant_id="tenant-b",
        user_email="user@tenant-b.com",
        user_role=UserRole.USER
    )
    TenantService.set_current_tenant(context)
    yield context
    TenantService.clear_current_tenant()


@pytest.fixture
def tenant_context_admin():
    """Fixture providing admin TenantContext"""
    context = TenantContext(
        tenant_id="tenant-a",
        user_email="admin@tenant-a.com",
        user_role=UserRole.ADMIN
    )
    TenantService.set_current_tenant(context)
    yield context
    TenantService.clear_current_tenant()


@pytest.fixture
def mock_profile_service():
    """Mock ProfileService for tests that verify service interactions"""
    from unittest.mock import AsyncMock
    return AsyncMock()


@pytest.fixture
def tenant_context_tenant_a():
    """Fixture providing TenantContext for tenant-a"""
    context = TenantContext(
        tenant_id="tenant-a",
        user_email="user@tenant-a.com",
        user_role=UserRole.USER
    )
    TenantService.set_current_tenant(context)
    yield context
    TenantService.clear_current_tenant()


@pytest.fixture
def tenant_a_user():
    """Alias for tenant_context_tenant_a"""
    context = TenantContext(
        tenant_id="tenant-a",
        user_email="user@tenant-a.com",
        user_role=UserRole.USER
    )
    TenantService.set_current_tenant(context)
    yield context
    TenantService.clear_current_tenant()


@pytest.fixture
def tenant_a_admin():
    """Alias for tenant_context_admin"""
    context = TenantContext(
        tenant_id="tenant-a",
        user_email="admin@tenant-a.com",
        user_role=UserRole.ADMIN
    )
    TenantService.set_current_tenant(context)
    yield context
    TenantService.clear_current_tenant()


@pytest.fixture
def tenant_b_user():
    """Alias for tenant_context_tenant_b"""
    context = TenantContext(
        tenant_id="tenant-b",
        user_email="user@tenant-b.com",
        user_role=UserRole.USER
    )
    TenantService.set_current_tenant(context)
    yield context
    TenantService.clear_current_tenant()
