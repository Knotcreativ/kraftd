"""
Feedback Service

Manages user feedback with Cosmos DB storage.
- Create and retrieve feedback
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


class FeedbackService:
    """Service for managing feedback in Cosmos DB."""

    def __init__(self, cosmos_service: CosmosService):
        """Initialize with Cosmos DB service.
        
        Args:
            cosmos_service: Instance of CosmosService for database operations
        """
        self.cosmos_service = cosmos_service
        self.container_name = "feedback"

    async def create_feedback(
        self,
        conversion_id: str,
        user_email: str,
        target: str,
        target_id: str,
        rating: int,
        comments: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new feedback document.
        
        Args:
            conversion_id: ID of the conversion related to this feedback
            user_email: Email of the user providing feedback (partition key)
            target: Feedback target type (export, extraction, schema, summary, etc.)
            target_id: ID of the target entity (export_id, document_id, etc.)
            rating: Numeric rating (typically 1-5)
            comments: Optional text comments on quality, accuracy, issues
            metadata: Optional metadata dict (e.g., feedback type, issues list)
        
        Returns:
            Dict containing the created feedback document
        
        Raises:
            HTTPException: 409 if feedback already exists, 500 on server error
        """
        try:
            feedback_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat() + "Z"

            feedback_item = {
                "id": feedback_id,
                "type": "feedback",
                "conversion_id": conversion_id,
                "user_email": user_email,
                "target": target,
                "target_id": target_id,
                "rating": rating,
                "comments": comments or "",
                "metadata": metadata or {},
                "created_at": now,
                "updated_at": now,
            }

            logger.debug(
                f"Creating feedback {feedback_id} for target {target} {target_id}, user {user_email}, rating {rating}"
            )

            result = await self.cosmos_service.create_item(
                self.container_name,
                feedback_item,
                partition_key=user_email
            )

            logger.info(
                f"Feedback created: {feedback_id} for target {target} {target_id}, rating {rating}"
            )
            return result

        except exceptions.CosmosResourceExistsError:
            logger.warning(
                f"Feedback already exists for target {target} {target_id}"
            )
            raise

        except Exception as e:
            logger.error(
                f"Failed to create feedback for target {target} {target_id}: {e}",
                exc_info=True
            )
            raise

    async def get_feedback(
        self,
        feedback_id: str,
        user_email: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a feedback by ID.
        
        Args:
            feedback_id: The feedback ID
            user_email: Email of the user (partition key)
        
        Returns:
            Dict containing the feedback document, or None if not found
        
        Raises:
            HTTPException: 404 if not found, 500 on server error
        """
        try:
            logger.debug(f"Retrieving feedback {feedback_id} for user {user_email}")

            result = await self.cosmos_service.read_item(
                self.container_name,
                feedback_id,
                partition_key=user_email
            )

            logger.debug(f"Feedback retrieved: {feedback_id}, rating {result.get('rating', 'unknown')}")
            return result

        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Feedback not found: {feedback_id}")
            raise

        except Exception as e:
            logger.error(
                f"Failed to retrieve feedback {feedback_id}: {e}",
                exc_info=True
            )
            raise

    async def get_user_feedback(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all feedback submitted by a user.
        
        Args:
            user_email: Email of the user (partition key)
        
        Returns:
            List of feedback documents
        
        Raises:
            HTTPException: 500 on server error
        """
        try:
            logger.debug(f"Retrieving all feedback for user {user_email}")

            query = "SELECT * FROM c WHERE c.type = 'feedback' ORDER BY c.created_at DESC"
            results = await self.cosmos_service.query_items(
                self.container_name,
                query,
                partition_key=user_email
            )

            logger.info(f"Retrieved {len(results)} feedback items for user {user_email}")
            return results

        except Exception as e:
            logger.error(
                f"Failed to retrieve feedback for user {user_email}: {e}",
                exc_info=True
            )
            raise

    async def get_feedback_for_conversion(
        self,
        conversion_id: str,
        user_email: str
    ) -> List[Dict[str, Any]]:
        """Get all feedback for a specific conversion.
        
        Args:
            conversion_id: The conversion ID
            user_email: Email of the user (partition key)
        
        Returns:
            List of feedback documents for the conversion
        
        Raises:
            HTTPException: 500 on server error
        """
        try:
            logger.debug(
                f"Retrieving feedback for conversion {conversion_id}, user {user_email}"
            )

            query = (
                "SELECT * FROM c WHERE c.type = 'feedback' "
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
                f"Retrieved {len(results)} feedback items for conversion {conversion_id}"
            )
            return results

        except Exception as e:
            logger.error(
                f"Failed to retrieve feedback for conversion {conversion_id}: {e}",
                exc_info=True
            )
            raise


# ===== Singleton Helper =====

_feedback_service_instance: Optional[FeedbackService] = None


def get_feedback_service() -> FeedbackService:
    """Get or create the singleton FeedbackService instance.
    
    Returns:
        FeedbackService instance
    """
    global _feedback_service_instance
    if _feedback_service_instance is None:
        cosmos_service = CosmosService()
        _feedback_service_instance = FeedbackService(cosmos_service)
    return _feedback_service_instance
