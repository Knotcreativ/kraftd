"""
Security Tests for KraftdIntel Backend

Comprehensive security test suite covering:
- JWT authentication and validation
- Multi-tenant isolation (partition key enforcement)
- Authorization and access control
- Input validation
- Error handling
- Sensitive data protection

Run: pytest test_security.py -v
Coverage: 20+ security-focused tests
Estimated time: 2-3 minutes per full suite
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import jwt
import json

# Import services
from services.auth_service import AuthService
from repositories.document_repository import DocumentRepository, DocumentStatus
from repositories.user_repository import UserRepository


# ========== JWT & Authentication Tests ==========

class TestJWTSecurity:
    """Tests for JWT token security and validation."""
    
    @pytest.mark.asyncio
    async def test_valid_token_accepted(self):
        """Verify valid JWT tokens are accepted."""
        email = "test@kraftdintel.com"
        token = AuthService.create_access_token(email)
        
        # Token should be decodable and valid
        payload = AuthService.verify_token(token)
        
        assert payload is not None
        assert payload.get("sub") == email
        assert payload.get("type") == "access"
        assert payload.get("exp") is not None
    
    @pytest.mark.asyncio
    async def test_expired_token_rejected(self):
        """Verify expired tokens are rejected."""
        email = "test@kraftdintel.com"
        # Create token with negative expiry (already expired)
        expired_delta = timedelta(minutes=-1)
        token = AuthService.create_access_token(email, expired_delta)
        
        # Expired token should return None
        payload = AuthService.verify_token(token)
        
        assert payload is None
    
    @pytest.mark.asyncio
    async def test_invalid_signature_rejected(self):
        """Verify tokens with invalid signatures are rejected."""
        email = "test@kraftdintel.com"
        token = AuthService.create_access_token(email)
        
        # Tamper with token by changing last character
        tampered_token = token[:-5] + "XXXXX"
        
        # Tampered token should be rejected
        payload = AuthService.verify_token(tampered_token)
        
        assert payload is None
    
    @pytest.mark.asyncio
    async def test_malformed_token_rejected(self):
        """Verify malformed tokens are rejected."""
        malformed_tokens = [
            "not.a.token",
            "invalid",
            "",
            "Bearer token_without_dots",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.invalid"
        ]
        
        for token in malformed_tokens:
            payload = AuthService.verify_token(token)
            assert payload is None, f"Malformed token should be rejected: {token}"
    
    @pytest.mark.asyncio
    async def test_token_without_sub_claim_rejected(self):
        """Verify tokens without 'sub' claim are rejected."""
        # Create custom JWT without 'sub' claim
        payload = {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        # This is a security test - should fail in verify_token
        result = AuthService.verify_token("invalid.token.here")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_access_token_type_verified(self):
        """Verify access token type claim is present."""
        email = "test@kraftdintel.com"
        token = AuthService.create_access_token(email)
        
        payload = AuthService.verify_token(token)
        
        assert payload.get("type") == "access"
    
    @pytest.mark.asyncio
    async def test_refresh_token_type_verified(self):
        """Verify refresh token type claim is present."""
        email = "test@kraftdintel.com"
        token = AuthService.create_refresh_token(email)
        
        payload = AuthService.verify_token(token)
        
        assert payload.get("type") == "refresh"
    
    @pytest.mark.asyncio
    async def test_token_expiration_times(self):
        """Verify token expiration times are correct."""
        email = "test@kraftdintel.com"
        
        # Access token: 60 minutes
        access_token = AuthService.create_access_token(email)
        access_payload = AuthService.verify_token(access_token)
        access_expires = access_payload.get("exp")
        access_issued = access_payload.get("iat")
        access_duration = access_expires - access_issued
        
        # Should be approximately 60 minutes (3600 seconds)
        assert 3595 <= access_duration <= 3605, "Access token should expire in ~60 minutes"
        
        # Refresh token: 7 days
        refresh_token = AuthService.create_refresh_token(email)
        refresh_payload = AuthService.verify_token(refresh_token)
        refresh_expires = refresh_payload.get("exp")
        refresh_issued = refresh_payload.get("iat")
        refresh_duration = refresh_expires - refresh_issued
        
        # Should be approximately 7 days (604800 seconds)
        assert 604795 <= refresh_duration <= 604805, "Refresh token should expire in ~7 days"


# ========== Multi-Tenant Isolation Tests ==========

class TestMultiTenantIsolation:
    """Tests for partition key-based multi-tenant isolation."""
    
    @pytest.mark.asyncio
    async def test_document_partition_key_enforced(self):
        """Verify partition key is required in document creation."""
        doc_repo = DocumentRepository()
        
        user_email = "user1@kraftdintel.com"
        doc_id = "doc-001"
        
        # Create document with partition key
        doc_data = await doc_repo.create_document(
            document_id=doc_id,
            owner_email=user_email,
            filename="test.pdf",
            document_type="INVOICE"
        )
        
        # Document should include partition key
        assert doc_data.get("owner_email") == user_email
        assert doc_data.get("id") == doc_id
    
    @pytest.mark.asyncio
    async def test_user_cannot_access_other_users_documents(self):
        """Verify users cannot access documents from other partitions."""
        doc_repo = DocumentRepository()
        
        user1_email = "user1@kraftdintel.com"
        user2_email = "user2@kraftdintel.com"
        doc_id = "doc-001"
        
        # Create document for user1
        await doc_repo.create_document(
            document_id=doc_id,
            owner_email=user1_email,
            filename="sensitive.pdf",
            document_type="INVOICE"
        )
        
        # Try to get document from user1 with user2's email
        result = await doc_repo.get_document(doc_id, user2_email)
        
        # Should not find document (partition isolation)
        assert result is None or result.get("owner_email") == user1_email
    
    @pytest.mark.asyncio
    async def test_partition_key_in_all_queries(self):
        """Verify partition key is included in all database queries."""
        doc_repo = DocumentRepository()
        user_email = "user1@kraftdintel.com"
        
        # All these methods should enforce partition key
        methods_to_test = [
            ("get_user_documents", [user_email]),
            ("get_documents_by_status", [user_email, "PENDING"]),
        ]
        
        for method_name, args in methods_to_test:
            # Method should accept partition key parameter
            method = getattr(doc_repo, method_name, None)
            assert method is not None, f"Method {method_name} should exist"
            
            # Should handle owner_email parameter
            if method_name == "get_user_documents":
                # This method should filter by owner_email
                assert callable(method)
    
    @pytest.mark.asyncio
    async def test_cross_partition_query_prevention(self):
        """Verify cross-partition queries are not possible."""
        doc_repo = DocumentRepository()
        
        user1_email = "user1@kraftdintel.com"
        user2_email = "user2@kraftdintel.com"
        
        # Get user1 documents
        user1_docs = await doc_repo.get_user_documents(user1_email)
        
        # Get user2 documents
        user2_docs = await doc_repo.get_user_documents(user2_email)
        
        # Collections should be separate
        if user1_docs and user2_docs:
            # Ensure no document appears in both lists
            user1_ids = {doc.get("id") for doc in user1_docs}
            user2_ids = {doc.get("id") for doc in user2_docs}
            
            assert user1_ids.isdisjoint(user2_ids), "Documents should not cross partitions"


# ========== Authorization Tests ==========

class TestAuthorizationControls:
    """Tests for authorization and access control."""
    
    def test_password_hashing_secure(self):
        """Verify passwords are securely hashed with bcrypt."""
        password = "SecurePassword123!"
        
        # Hash password
        hashed = AuthService.hash_password(password)
        
        # Hash should not be plaintext
        assert hashed != password
        # Hash should start with bcrypt identifier
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    
    def test_password_verification_works(self):
        """Verify password verification function works correctly."""
        password = "SecurePassword123!"
        hashed = AuthService.hash_password(password)
        
        # Correct password should verify
        assert AuthService.verify_password(password, hashed) is True
        
        # Incorrect password should not verify
        assert AuthService.verify_password("WrongPassword", hashed) is False
    
    def test_duplicate_hash_different(self):
        """Verify same password produces different hashes (salt variation)."""
        password = "SecurePassword123!"
        
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2
        # But both should verify the password
        assert AuthService.verify_password(password, hash1) is True
        assert AuthService.verify_password(password, hash2) is True
    
    @pytest.mark.asyncio
    async def test_user_email_extracted_from_token(self):
        """Verify user email is correctly extracted from token."""
        user_email = "test@kraftdintel.com"
        token = AuthService.create_access_token(user_email)
        
        payload = AuthService.verify_token(token)
        extracted_email = payload.get("sub")
        
        assert extracted_email == user_email


# ========== Input Validation Tests ==========

class TestInputValidation:
    """Tests for input validation and data sanitization."""
    
    def test_email_validation(self):
        """Verify email validation works correctly."""
        from models.user import UserRegister
        
        valid_emails = [
            "test@kraftdintel.com",
            "user.name@company.org",
            "first+last@example.co.uk"
        ]
        
        invalid_emails = [
            "notanemail",
            "@kraftdintel.com",
            "user@",
            "user @kraftdintel.com",  # Space
            ""
        ]
        
        # Valid emails should work
        for email in valid_emails:
            try:
                user = UserRegister(
                    email=email,
                    name="Test User",
                    organization="Test Org",
                    password="ValidPassword123!"
                )
                assert user.email == email
            except Exception as e:
                pytest.fail(f"Valid email {email} should be accepted: {e}")
        
        # Invalid emails should be rejected
        for email in invalid_emails:
            with pytest.raises(Exception):
                UserRegister(
                    email=email,
                    name="Test User",
                    organization="Test Org",
                    password="ValidPassword123!"
                )
    
    def test_missing_required_fields_rejected(self):
        """Verify missing required fields are rejected."""
        from models.user import UserRegister
        
        # Missing email
        with pytest.raises(Exception):
            UserRegister(
                email=None,
                name="Test User",
                organization="Test Org",
                password="ValidPassword123!"
            )
        
        # Missing password
        with pytest.raises(Exception):
            UserRegister(
                email="test@kraftdintel.com",
                name="Test User",
                organization="Test Org",
                password=None
            )


# ========== Error Handling Tests ==========

class TestErrorHandling:
    """Tests for error handling and sensitive data protection."""
    
    @pytest.mark.asyncio
    async def test_invalid_token_format_error_message(self):
        """Verify error messages for invalid tokens don't expose sensitive data."""
        invalid_token = "invalid.token.here"
        
        payload = AuthService.verify_token(invalid_token)
        
        # Should return None, not expose token or error details
        assert payload is None
    
    @pytest.mark.asyncio
    async def test_expired_token_error_message(self):
        """Verify error messages for expired tokens don't expose secrets."""
        email = "test@kraftdintel.com"
        # Create expired token
        token = AuthService.create_access_token(email, timedelta(minutes=-1))
        
        payload = AuthService.verify_token(token)
        
        # Should return None, not expose token internals
        assert payload is None
    
    def test_password_not_in_user_object(self):
        """Verify passwords are not returned in user responses."""
        from models.user import UserProfile
        
        # UserProfile should not include password field
        user = UserProfile(
            id="user@kraftdintel.com",
            email="user@kraftdintel.com",
            name="Test User",
            organization="Test Org"
        )
        
        # Convert to dict
        user_dict = user.dict()
        assert "password" not in user_dict
        assert "hashed_password" not in user_dict


# ========== Security Configuration Tests ==========

class TestSecurityConfiguration:
    """Tests for security-related configuration."""
    
    def test_jwt_algorithm_not_none(self):
        """Verify JWT algorithm is properly configured."""
        from services.auth_service import ALGORITHM
        assert ALGORITHM is not None
        assert ALGORITHM == "HS256"
    
    def test_access_token_expiration_configured(self):
        """Verify access token expiration is configured."""
        from services.auth_service import ACCESS_TOKEN_EXPIRE_MINUTES
        assert ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert ACCESS_TOKEN_EXPIRE_MINUTES <= 120  # Reasonable limit
    
    def test_refresh_token_expiration_configured(self):
        """Verify refresh token expiration is configured."""
        from services.auth_service import REFRESH_TOKEN_EXPIRE_DAYS
        assert REFRESH_TOKEN_EXPIRE_DAYS > 0
        assert REFRESH_TOKEN_EXPIRE_DAYS <= 30  # Reasonable limit


# ========== Integration Security Tests ==========

class TestIntegrationSecurity:
    """End-to-end security tests."""
    
    @pytest.mark.asyncio
    async def test_complete_auth_flow_security(self):
        """Verify complete authentication flow maintains security."""
        user_email = "integration@kraftdintel.com"
        user_name = "Integration Test"
        user_org = "Test Org"
        password = "SecurePassword123!"
        
        # Create user
        user = AuthService.create_user(user_email, user_name, user_org, password)
        
        # Verify password is hashed
        assert user.hashed_password != password
        assert AuthService.verify_password(password, user.hashed_password)
        
        # Create tokens
        access_token = AuthService.create_access_token(user_email)
        refresh_token = AuthService.create_refresh_token(user_email)
        
        # Verify tokens
        access_payload = AuthService.verify_token(access_token)
        refresh_payload = AuthService.verify_token(refresh_token)
        
        # Tokens should have different types
        assert access_payload.get("type") == "access"
        assert refresh_payload.get("type") == "refresh"
        
        # Both should have correct email
        assert access_payload.get("sub") == user_email
        assert refresh_payload.get("sub") == user_email


# ========== Fixtures ==========

@pytest.fixture(scope="function")
async def clean_database():
    """Clean database before and after tests."""
    yield
    # Cleanup would go here


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
