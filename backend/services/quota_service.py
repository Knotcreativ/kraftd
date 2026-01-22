"""
Quota Service

Manages user quota and usage limits with Cosmos DB storage.
- Get or create user quotas
- Increment usage counters
- Check quota limits
- Track usage by tier (free, pro, enterprise)
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from services.cosmos_service import CosmosService
from azure.cosmos import exceptions

logger = logging.getLogger(__name__)


# Default quota limits by tier
QUOTA_LIMITS = {
    "free": {
        "documents_per_month": 10,
        "exports_per_month": 20,
        "api_calls_per_day": 100,
    },
    "pro": {
        "documents_per_month": 100,
        "exports_per_month": 500,
        "api_calls_per_day": 10000,
    },
    "enterprise": {
        "documents_per_month": None,  # Unlimited
        "exports_per_month": None,
        "api_calls_per_day": None,
    },
}


class QuotaService:
    """Service for managing user quotas and usage limits in Cosmos DB."""

    def __init__(self, cosmos_service: CosmosService):
        """Initialize with Cosmos DB service.
        
        Args:
            cosmos_service: Instance of CosmosService for database operations
        """
        self.cosmos_service = cosmos_service
        self.container_name = "quota"

    async def get_or_create_quota(self, user_email: str, tier: str = "free") -> Dict[str, Any]:
        """Get existing quota or create default for user.
        
        Args:
            user_email: Email of the user (partition key)
            tier: User tier (free, pro, enterprise)
        
        Returns:
            Dict containing the quota document
        
        Raises:
            HTTPException: 500 on server error
        """
        try:
            logger.debug(f"Getting or creating quota for user {user_email}, tier {tier}")
            
            # Try to read existing quota
            quota_id = f"quota-{user_email}"
            try:
                result = await self.cosmos_service.read_item(
                    self.container_name,
                    quota_id,
                    partition_key=user_email
                )
                logger.debug(f"Existing quota found for {user_email}")
                return result
            
            except exceptions.CosmosResourceNotFoundError:
                # Create new quota if not found
                logger.debug(f"Creating new quota for {user_email}")
                now = datetime.utcnow().isoformat() + "Z"
                
                quota_item = {
                    "id": quota_id,
                    "type": "quota",
                    "user_email": user_email,
                    "tier": tier,
                    "limits": QUOTA_LIMITS.get(tier, QUOTA_LIMITS["free"]),
                    "usage": {
                        "documents_uploaded": 0,
                        "documents_processed": 0,
                        "exports_generated": 0,
                        "total_api_calls": 0,
                        "daily_api_calls": 0,
                    },
                    "last_reset": now,
                    "next_reset": self._calculate_next_reset(),
                    "created_at": now,
                    "updated_at": now,
                }
                
                result = await self.cosmos_service.create_item(
                    self.container_name,
                    quota_item,
                    partition_key=user_email
                )
                
                logger.info(f"Quota created for user {user_email}, tier {tier}")
                return result
        
        except Exception as e:
            logger.error(
                f"Failed to get or create quota for {user_email}: {e}",
                exc_info=True
            )
            raise

    async def increment_usage(
        self,
        user_email: str,
        field: str,
        amount: int = 1
    ) -> Dict[str, Any]:
        """Increment a usage counter for user.
        
        Args:
            user_email: Email of the user (partition key)
            field: Usage field name (e.g., 'documents_uploaded', 'exports_generated')
            amount: Amount to increment by (default 1)
        
        Returns:
            Dict containing updated quota document
        
        Raises:
            HTTPException: 404 if quota not found, 500 on server error
        """
        try:
            logger.debug(f"Incrementing {field} by {amount} for user {user_email}")
            
            quota_id = f"quota-{user_email}"
            
            # Read current quota
            quota = await self.cosmos_service.read_item(
                self.container_name,
                quota_id,
                partition_key=user_email
            )
            
            # Increment the field
            if "usage" not in quota:
                quota["usage"] = {}
            
            current_value = quota["usage"].get(field, 0)
            quota["usage"][field] = current_value + amount
            quota["updated_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Replace the document
            result = await self.cosmos_service.replace_item(
                self.container_name,
                quota_id,
                quota,
                partition_key=user_email
            )
            
            logger.info(f"Usage {field} incremented to {result['usage'].get(field)} for {user_email}")
            return result
        
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Quota not found for user {user_email}")
            raise
        
        except Exception as e:
            logger.error(
                f"Failed to increment usage for {user_email}: {e}",
                exc_info=True
            )
            raise

    async def check_limits(self, user_email: str, field: str) -> Dict[str, Any]:
        """Check if user has exceeded limits for a field.
        
        Args:
            user_email: Email of the user (partition key)
            field: Field to check (e.g., 'documents_per_month')
        
        Returns:
            Dict with 'exceeded' (bool) and 'remaining' (int or None if unlimited)
        
        Raises:
            HTTPException: 500 on server error
        """
        try:
            logger.debug(f"Checking limits for {field}, user {user_email}")
            
            quota = await self.get_or_create_quota(user_email)
            
            limits = quota.get("limits", {})
            usage = quota.get("usage", {})
            
            # Map usage field to limit field (e.g., 'documents_uploaded' -> 'documents_per_month')
            field_mapping = {
                "documents_uploaded": "documents_per_month",
                "exports_generated": "exports_per_month",
                "total_api_calls": "api_calls_per_day",
            }
            
            limit_field = field_mapping.get(field, field)
            limit = limits.get(limit_field)
            usage_count = usage.get(field, 0)
            
            # Unlimited if limit is None
            if limit is None:
                return {
                    "exceeded": False,
                    "remaining": None,
                    "usage": usage_count,
                    "limit": None,
                    "unlimited": True
                }
            
            exceeded = usage_count >= limit
            remaining = max(0, limit - usage_count)
            
            logger.debug(f"Limit check for {field}: usage={usage_count}, limit={limit}, exceeded={exceeded}")
            
            return {
                "exceeded": exceeded,
                "remaining": remaining,
                "usage": usage_count,
                "limit": limit,
                "unlimited": False
            }
        
        except Exception as e:
            logger.error(
                f"Failed to check limits for {user_email}: {e}",
                exc_info=True
            )
            raise

    async def get_usage(self, user_email: str) -> Dict[str, Any]:
        """Get current usage and quota status for user.
        
        Args:
            user_email: Email of the user (partition key)
        
        Returns:
            Dict with usage, limits, and quota information
        
        Raises:
            HTTPException: 500 on server error
        """
        try:
            logger.debug(f"Retrieving usage for user {user_email}")
            
            quota = await self.get_or_create_quota(user_email)
            
            usage_info = {
                "email": user_email,
                "tier": quota.get("tier", "free"),
                "usage": quota.get("usage", {}),
                "limits": quota.get("limits", {}),
                "next_reset": quota.get("next_reset"),
                "created_at": quota.get("created_at"),
            }
            
            logger.info(f"Retrieved usage for user {user_email}, tier {usage_info['tier']}")
            return usage_info
        
        except Exception as e:
            logger.error(
                f"Failed to retrieve usage for {user_email}: {e}",
                exc_info=True
            )
            raise

    async def reset_monthly_usage(self) -> int:
        """Reset monthly usage counters for all users.
        
        This should be called monthly (e.g., via scheduled task).
        
        Returns:
            Number of quotas updated
        
        Raises:
            HTTPException: 500 on server error
        """
        try:
            logger.info("Starting monthly quota reset")
            
            # Query all quota documents
            query = "SELECT * FROM c WHERE c.type = 'quota'"
            results = await self.cosmos_service.query_items(
                self.container_name,
                query,
                partition_key=None  # Query across all partitions
            )
            
            updated_count = 0
            now = datetime.utcnow().isoformat() + "Z"
            
            for quota in results:
                try:
                    # Reset monthly counters
                    quota["usage"]["documents_uploaded"] = 0
                    quota["usage"]["documents_processed"] = 0
                    quota["usage"]["exports_generated"] = 0
                    quota["usage"]["daily_api_calls"] = 0
                    quota["last_reset"] = now
                    quota["next_reset"] = self._calculate_next_reset()
                    quota["updated_at"] = now
                    
                    # Replace the document
                    await self.cosmos_service.replace_item(
                        self.container_name,
                        quota.get("id"),
                        quota,
                        partition_key=quota.get("user_email")
                    )
                    
                    updated_count += 1
                    logger.debug(f"Reset quota for {quota.get('user_email')}")
                
                except Exception as e:
                    logger.error(f"Failed to reset quota {quota.get('id')}: {e}")
                    continue
            
            logger.info(f"Monthly quota reset complete: {updated_count} quotas updated")
            return updated_count
        
        except Exception as e:
            logger.error(
                f"Failed to reset monthly usage: {e}",
                exc_info=True
            )
            raise

    @staticmethod
    def _calculate_next_reset() -> str:
        """Calculate next monthly reset date (1st of next month).
        
        Returns:
            ISO 8601 formatted datetime string
        """
        now = datetime.utcnow()
        
        # Calculate first day of next month
        if now.month == 12:
            next_reset = datetime(now.year + 1, 1, 1)
        else:
            next_reset = datetime(now.year, now.month + 1, 1)
        
        return next_reset.isoformat() + "Z"


# ===== Singleton Helper =====

_quota_service_instance: Optional[QuotaService] = None


def get_quota_service() -> QuotaService:
    """Get or create the singleton QuotaService instance.
    
    Returns:
        QuotaService instance
    """
    global _quota_service_instance
    if _quota_service_instance is None:
        cosmos_service = CosmosService()
        _quota_service_instance = QuotaService(cosmos_service)
    return _quota_service_instance
