"""
Unit Tests for Repository Layer

Tests DocumentRepository and UserRepository implementations
including async operations, error handling, and fallback scenarios.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional, Dict, Any

from repositories.document_repository import DocumentRepository, DocumentStatus
from repositories.user_repository import UserRepository


class TestDocumentRepository:
    """Test DocumentRepository methods."""
    
    @pytest.fixture
    def repo(self):
        """Create repository instance for testing."""
        return DocumentRepository()
    
    @pytest.mark.asyncio
    async def test_create_document_success(self, repo):
        """Test successful document creation."""
        # Mock the cosmos service
        with patch.object(repo, 'container', new_callable=AsyncMock) as mock_container:
            mock_container.create_item = AsyncMock(return_value={
                'id': 'doc-123',
                'owner_email': 'user@example.com',
                'filename': 'test.pdf',
                'document_type': 'INVOICE'
            })
            
            result = await repo.create_document(
                document_id='doc-123',
                owner_email='user@example.com',
                filename='test.pdf',
                document_type='INVOICE'
            )
            
            assert result is not None
            assert result['id'] == 'doc-123'
            assert result['owner_email'] == 'user@example.com'
    
    @pytest.mark.asyncio
    async def test_get_document_success(self, repo):
        """Test successful document retrieval."""
        with patch.object(repo, 'container', new_callable=AsyncMock) as mock_container:
            mock_container.read_item = AsyncMock(return_value={
                'id': 'doc-123',
                'owner_email': 'user@example.com',
                'filename': 'test.pdf'
            })
            
            result = await repo.get_document('doc-123', 'user@example.com')
            
            assert result is not None
            assert result['id'] == 'doc-123'
    
    @pytest.mark.asyncio
    async def test_get_document_not_found(self, repo):
        """Test document retrieval when not found."""
        with patch.object(repo, 'container', new_callable=AsyncMock) as mock_container:
            mock_container.read_item = AsyncMock(side_effect=Exception('404'))
            
            result = await repo.get_document('nonexistent', 'user@example.com')
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_document_success(self, repo):
        """Test successful document update."""
        with patch.object(repo, 'container', new_callable=AsyncMock) as mock_container:
            mock_container.replace_item = AsyncMock(return_value={
                'id': 'doc-123',
                'owner_email': 'user@example.com',
                'status': 'COMPLETED'
            })
            
            result = await repo.update_document(
                'doc-123',
                'user@example.com',
                {'status': 'COMPLETED'}
            )
            
            assert result is not None
            assert result['status'] == 'COMPLETED'
    
    @pytest.mark.asyncio
    async def test_update_document_status_success(self, repo):
        """Test document status update."""
        with patch.object(repo, 'container', new_callable=AsyncMock) as mock_container:
            mock_container.read_item = AsyncMock(return_value={
                'id': 'doc-123',
                'owner_email': 'user@example.com',
                'status': 'PENDING'
            })
            mock_container.replace_item = AsyncMock(return_value={
                'id': 'doc-123',
                'status': DocumentStatus.PROCESSING
            })
            
            result = await repo.update_document_status(
                'doc-123',
                'user@example.com',
                DocumentStatus.PROCESSING
            )
            
            assert result['status'] == DocumentStatus.PROCESSING
    
    @pytest.mark.asyncio
    async def test_document_exists_true(self, repo):
        """Test document existence check - exists."""
        with patch.object(repo, 'container', new_callable=AsyncMock) as mock_container:
            mock_container.read_item = AsyncMock(return_value={'id': 'doc-123'})
            
            result = await repo.exists('doc-123', 'user@example.com')
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_document_exists_false(self, repo):
        """Test document existence check - not exists."""
        with patch.object(repo, 'container', new_callable=AsyncMock) as mock_container:
            mock_container.read_item = AsyncMock(side_effect=Exception('404'))
            
            result = await repo.exists('nonexistent', 'user@example.com')
            
            assert result is False


class TestUserRepository:
    """Test UserRepository methods."""
    
    @pytest.fixture
    def repo(self):
        """Create user repository instance for testing."""
        return UserRepository()
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, repo):
        """Test successful user creation."""
        with patch.object(repo, 'container', new_callable=AsyncMock) as mock_container:
            mock_container.create_item = AsyncMock(return_value={
                'id': 'user-123',
                'email': 'test@example.com',
                'name': 'Test User'
            })
            
            result = await repo.create_user(
                user_id='user-123',
                email='test@example.com',
                name='Test User'
            )
            
            assert result is not None
            assert result['email'] == 'test@example.com'
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, repo):
        """Test successful user retrieval by email."""
        with patch.object(repo, 'container', new_callable=AsyncMock) as mock_container:
            mock_container.query_items = AsyncMock(return_value=[{
                'id': 'user-123',
                'email': 'test@example.com'
            }])
            
            result = await repo.get_user_by_email('test@example.com')
            
            assert result is not None
            assert result['email'] == 'test@example.com'
    
    @pytest.mark.asyncio
    async def test_user_exists_true(self, repo):
        """Test user existence check - exists."""
        with patch.object(repo, 'container', new_callable=AsyncMock) as mock_container:
            mock_container.query_items = AsyncMock(return_value=[{'id': 'user-123'}])
            
            result = await repo.exists('user-123')
            
            assert result is True


class TestDocumentStatusEnum:
    """Test DocumentStatus enum."""
    
    def test_all_status_values_present(self):
        """Verify all required status values exist."""
        required_statuses = [
            'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'ARCHIVED',
            'REVIEW_PENDING', 'ESTIMATION_IN_PROGRESS', 'QUOTES_NORMALIZED',
            'COMPARISON_DONE', 'PROPOSAL_GENERATED', 'PO_GENERATED'
        ]
        
        for status in required_statuses:
            assert hasattr(DocumentStatus, status), f"Status {status} not found"
    
    def test_status_value_format(self):
        """Verify status values are strings."""
        assert isinstance(DocumentStatus.PENDING.value, str)
        assert isinstance(DocumentStatus.REVIEW_PENDING.value, str)


class TestRepositoryErrorHandling:
    """Test error handling in repositories."""
    
    @pytest.mark.asyncio
    async def test_cosmos_service_unavailable(self):
        """Test fallback when Cosmos service unavailable."""
        repo = DocumentRepository()
        
        # Mock container to return None (simulating unavailable service)
        with patch.object(repo, 'container', return_value=None):
            result = await repo.get_document('doc-123', 'user@example.com')
            assert result is None
    
    @pytest.mark.asyncio
    async def test_invalid_partition_key(self):
        """Test handling of invalid partition key."""
        repo = DocumentRepository()
        
        with patch.object(repo, 'container', new_callable=AsyncMock) as mock_container:
            mock_container.read_item = AsyncMock(side_effect=ValueError('Invalid partition key'))
            
            with pytest.raises(ValueError):
                await repo.get_document('doc-123', 'invalid-key')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])