"""
Summary Service

Manages document summaries with Cosmos DB storage.
- Create and retrieve summaries
- Query by user or conversion
- Timestamp tracking
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from services.cosmos_service import CosmosService
from azure.cosmos import exceptions

logger = logging.getLogger(__name__)


class SummaryService:
    """Service for managing document summaries in Cosmos DB."""

    def __init__(self, cosmos_service: CosmosService):
        """Initialize with Cosmos DB service.
        
        Args:
            cosmos_service: Instance of CosmosService for database operations
        """
        self.cosmos_service = cosmos_service
        self.container_name = "summaries"

    async def create_summary(
        self,
        conversion_id: str,
        user_email: str,
        summary_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new summary document.
        
        Args:
            conversion_id: ID of the conversion this summary is for
            user_email: Email of the user (partition key)
            summary_text: The summary text content
            metadata: Optional metadata dict (e.g., extraction quality, key points)
        
        Returns:
            Dict containing the created summary document
        
        Raises:
            HTTPException: 409 if summary already exists, 500 on server error
        """
        try:
            summary_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat() + "Z"

            summary_item = {
                "id": summary_id,
                "type": "summary",
                "conversion_id": conversion_id,
                "user_email": user_email,
                "summary_text": summary_text,
                "metadata": metadata or {},
                "created_at": now,
                "updated_at": now,
            }

            logger.debug(
                f"Creating summary {summary_id} for conversion {conversion_id}, user {user_email}"
            )

            result = await self.cosmos_service.create_item(
                self.container_name,
                summary_item,
                partition_key=user_email
            )

            logger.info(
                f"Summary created: {summary_id} for conversion {conversion_id}"
            )
            return result

        except exceptions.CosmosResourceExistsError:
            logger.warning(
                f"Summary already exists for conversion {conversion_id}"
            )
            raise

        except Exception as e:
            logger.error(
                f"Failed to create summary for conversion {conversion_id}: {e}",
                exc_info=True
            )
            raise

    async def get_summary(
        self,
        summary_id: str,
        user_email: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a summary by ID.
        
        Args:
            summary_id: The summary ID
            user_email: Email of the user (partition key)
        
        Returns:
            Dict containing the summary document, or None if not found
        
        Raises:
            HTTPException: 404 if not found, 500 on server error
        """
        try:
            logger.debug(f"Retrieving summary {summary_id} for user {user_email}")

            result = await self.cosmos_service.read_item(
                self.container_name,
                summary_id,
                partition_key=user_email
            )

            logger.debug(f"Summary retrieved: {summary_id}")
            return result

        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Summary not found: {summary_id}")
            raise

        except Exception as e:
            logger.error(
                f"Failed to retrieve summary {summary_id}: {e}",
                exc_info=True
            )
            raise

    async def get_user_summaries(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all summaries for a user.
        
        Args:
            user_email: Email of the user (partition key)
        
        Returns:
            List of summary documents
        
        Raises:
            HTTPException: 500 on server error
        """
        try:
            logger.debug(f"Retrieving all summaries for user {user_email}")

            query = "SELECT * FROM c WHERE c.type = 'summary' ORDER BY c.created_at DESC"
            results = await self.cosmos_service.query_items(
                self.container_name,
                query,
                partition_key=user_email
            )

            logger.info(f"Retrieved {len(results)} summaries for user {user_email}")
            return results

        except Exception as e:
            logger.error(
                f"Failed to retrieve summaries for user {user_email}: {e}",
                exc_info=True
            )
            raise

    async def get_summaries_for_conversion(
        self,
        conversion_id: str,
        user_email: str
    ) -> List[Dict[str, Any]]:
        """Get all summaries for a specific conversion.
        
        Args:
            conversion_id: The conversion ID
            user_email: Email of the user (partition key)
        
        Returns:
            List of summary documents for the conversion
        
        Raises:
            HTTPException: 500 on server error
        """
        try:
            logger.debug(
                f"Retrieving summaries for conversion {conversion_id}, user {user_email}"
            )

            query = (
                "SELECT * FROM c WHERE c.type = 'summary' "
                "AND c.conversion_id = @conversion_id "
                "ORDER BY c.created_at DESC"
            )
            parameters = [{"name": "@conversion_id", "value": conversion_id}]

            results = await self.cosmos_service.query_items(
                self.container_name,
                query,
                partition_key=user_email,
                parameters=parameters
            )

            logger.info(
                f"Retrieved {len(results)} summaries for conversion {conversion_id}"
            )
            return results

        except Exception as e:
            logger.error(
                f"Failed to retrieve summaries for conversion {conversion_id}: {e}",
                exc_info=True
            )
            raise


# ===== Singleton Helper =====

_summary_service_instance: Optional[SummaryService] = None


def get_summary_service() -> SummaryService:
    """Get or create the singleton SummaryService instance.
    
    Returns:
        SummaryService instance
    """
    global _summary_service_instance
    if _summary_service_instance is None:
        cosmos_service = CosmosService()
        _summary_service_instance = SummaryService(cosmos_service)
    return _summary_service_instance
