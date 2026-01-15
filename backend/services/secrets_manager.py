"""
Azure Key Vault Secrets Manager

Provides secure secret retrieval from Azure Key Vault with fallback to environment variables.
Follows Microsoft security best practices: https://learn.microsoft.com/en-us/azure/developer/python/walkthrough-tutorial-authentication-01
"""

import os
import logging
from typing import Optional
from functools import lru_cache

try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    logging.warning("Azure SDK not available. Falling back to environment variables only.")

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Manage secrets securely using Azure Key Vault with local development fallback.
    
    Behavior:
    - Production: Fetches from Azure Key Vault using managed identity
    - Development: Falls back to environment variables or defaults
    """
    
    def __init__(self, vault_url: Optional[str] = None):
        """
        Initialize secrets manager.
        
        Args:
            vault_url: Azure Key Vault URL (e.g., https://my-vault.vault.azure.net/)
                      If None, will use AZURE_KEYVAULT_URL environment variable
        """
        self.vault_url = vault_url or os.getenv("AZURE_KEYVAULT_URL")
        self._client = None
        self._is_dev_mode = not self.vault_url or os.getenv("ENVIRONMENT") == "development"
        
        if self._is_dev_mode:
            logger.info("Running in development mode - using environment variables for secrets")
        elif not AZURE_SDK_AVAILABLE:
            logger.warning("Azure SDK not available. Running in dev mode fallback.")
            self._is_dev_mode = True
        else:
            logger.info(f"Connecting to Key Vault: {self.vault_url}")
            try:
                self._initialize_client()
                logger.info("Key Vault client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Key Vault client: {e}. Falling back to environment variables.")
                self._is_dev_mode = True
    
    def _initialize_client(self):
        """Initialize Azure Key Vault client using managed identity."""
        if AZURE_SDK_AVAILABLE and self.vault_url:
            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=self.vault_url, credential=credential)
    
    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> str:
        """
        Retrieve a secret from Key Vault or environment variables.
        
        Args:
            secret_name: Name of the secret (e.g., 'jwt-secret-key')
            default: Default value if secret not found (not recommended for production)
        
        Returns:
            The secret value
            
        Raises:
            ValueError: If secret not found and no default provided
        """
        # Try Key Vault first (production)
        if self._client:
            try:
                secret = self._client.get_secret(secret_name)
                logger.debug(f"Retrieved secret '{secret_name}' from Key Vault")
                return secret.value
            except Exception as e:
                logger.warning(f"Failed to retrieve secret '{secret_name}' from Key Vault: {e}")
        
        # Fall back to environment variables (development)
        env_var_name = secret_name.upper().replace("-", "_")
        env_value = os.getenv(env_var_name)
        
        if env_value:
            logger.debug(f"Retrieved secret '{secret_name}' from environment variable '{env_var_name}'")
            return env_value
        
        # Use default if provided
        if default:
            logger.warning(f"Using default value for secret '{secret_name}' (not recommended for production)")
            return default
        
        # No secret found
        raise ValueError(
            f"Secret '{secret_name}' not found in Key Vault or environment variables. "
            f"Set {env_var_name} environment variable or configure AZURE_KEYVAULT_URL."
        )
    
    def get_jwt_secret(self) -> str:
        """
        Get JWT secret key.
        
        Production: Retrieves from Key Vault secret named 'jwt-secret-key'
        Development: Uses JWT_SECRET_KEY environment variable
        
        Returns:
            The JWT secret key (must be at least 32 characters for security)
            
        Raises:
            ValueError: If secret not found
        """
        try:
            secret = self.get_secret("jwt-secret-key")
            if len(secret) < 32:
                logger.warning("JWT secret is less than 32 characters - consider using a stronger secret")
            return secret
        except ValueError:
            if self._is_dev_mode:
                # Dev mode: generate a temporary warning secret
                logger.warning(
                    "⚠️  No JWT secret configured. Using temporary insecure default. "
                    "Set JWT_SECRET_KEY environment variable or configure Azure Key Vault."
                )
                return "development-secret-key-not-for-production-12345"
            raise
    
    def get_cosmos_endpoint(self) -> str:
        """
        Get Azure Cosmos DB endpoint URL.
        
        Production: Retrieves from Key Vault secret named 'cosmos-endpoint'
        Development: Uses COSMOS_ENDPOINT environment variable
        
        Returns:
            The Cosmos DB endpoint URL
        """
        return self.get_secret("cosmos-endpoint", os.getenv("COSMOS_ENDPOINT"))
    
    def get_cosmos_key(self) -> str:
        """
        Get Azure Cosmos DB connection key.
        
        Production: Retrieves from Key Vault secret named 'cosmos-key'
        Development: Uses COSMOS_KEY environment variable
        
        Returns:
            The Cosmos DB primary key
        """
        return self.get_secret("cosmos-key", os.getenv("COSMOS_KEY"))


# Global instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get or create the global secrets manager instance (singleton)."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def initialize_secrets(vault_url: Optional[str] = None) -> SecretsManager:
    """
    Initialize the global secrets manager.
    
    Call this during application startup.
    
    Args:
        vault_url: Optional Azure Key Vault URL
        
    Returns:
        The initialized SecretsManager instance
    """
    global _secrets_manager
    _secrets_manager = SecretsManager(vault_url)
    return _secrets_manager
