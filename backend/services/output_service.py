"""
Output Service

Manages document outputs (exports, reports, etc.) with Cosmos DB storage.
- Create and retrieve outputs
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


class OutputService:
    """Service for managing document outputs in Cosmos DB."""

    def __init__(self, cosmos_service: CosmosService):
        """Initialize with Cosmos DB service.
        
        Args:
            cosmos_service: Instance of CosmosService for database operations
        """
        self.cosmos_service = cosmos_service
        self.container_name = "outputs"

    async def create_output(
        self,
        conversion_id: str,
        user_email: str,
        output_data: Dict[str, Any],
        format: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new output document.
        
        Args:
            conversion_id: ID of the conversion this output is for
            user_email: Email of the user (partition key)
            output_data: The output content (document structure, data, etc.)
            format: Output format (json, csv, pdf, xml, etc.)
            metadata: Optional metadata dict (e.g., export type, settings, status)
        
        Returns:
            Dict containing the created output document
        
        Raises:
            HTTPException: 409 if output already exists, 500 on server error
        """
        try:
            output_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat() + "Z"

            output_item = {
                "id": output_id,
                "type": "output",
                "conversion_id": conversion_id,
                "user_email": user_email,
                "format": format,
                "output_data": output_data,
                "metadata": metadata or {},
                "created_at": now,
                "updated_at": now,
            }

            logger.debug(
                f"Creating output {output_id} for conversion {conversion_id}, user {user_email}, format {format}"
            )

            result = await self.cosmos_service.create_item(
                self.container_name,
                output_item,
                partition_key=user_email
            )

            logger.info(
                f"Output created: {output_id} for conversion {conversion_id}, format {format}"
            )
            return result

        except exceptions.CosmosResourceExistsError:
            logger.warning(
                f"Output already exists for conversion {conversion_id}"
            )
            raise

        except Exception as e:
            logger.error(
                f"Failed to create output for conversion {conversion_id}: {e}",
                exc_info=True
            )
            raise

    async def get_output(
        self,
        output_id: str,
        user_email: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve an output by ID.
        
        Args:
            output_id: The output ID
            user_email: Email of the user (partition key)
        
        Returns:
            Dict containing the output document, or None if not found
        
        Raises:
            HTTPException: 404 if not found, 500 on server error
        """
        try:
            logger.debug(f"Retrieving output {output_id} for user {user_email}")

            result = await self.cosmos_service.read_item(
                self.container_name,
                output_id,
                partition_key=user_email
            )

            logger.debug(f"Output retrieved: {output_id}, format {result.get('format', 'unknown')}")
            return result

        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Output not found: {output_id}")
            raise

        except Exception as e:
            logger.error(
                f"Failed to retrieve output {output_id}: {e}",
                exc_info=True
            )
            raise

    async def get_user_outputs(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all outputs for a user.
        
        Args:
            user_email: Email of the user (partition key)
        
        Returns:
            List of output documents
        
        Raises:
            HTTPException: 500 on server error
        """
        try:
            logger.debug(f"Retrieving all outputs for user {user_email}")

            query = "SELECT * FROM c WHERE c.type = 'output' ORDER BY c.created_at DESC"
            results = await self.cosmos_service.query_items(
                self.container_name,
                query,
                partition_key=user_email
            )

            logger.info(f"Retrieved {len(results)} outputs for user {user_email}")
            return results

        except Exception as e:
            logger.error(
                f"Failed to retrieve outputs for user {user_email}: {e}",
                exc_info=True
            )
            raise

    async def get_outputs_for_conversion(
        self,
        conversion_id: str,
        user_email: str
    ) -> List[Dict[str, Any]]:
        """Get all outputs for a specific conversion.
        
        Args:
            conversion_id: The conversion ID
            user_email: Email of the user (partition key)
        
        Returns:
            List of output documents for the conversion
        
        Raises:
            HTTPException: 500 on server error
        """
        try:
            logger.debug(
                f"Retrieving outputs for conversion {conversion_id}, user {user_email}"
            )

            query = (
                "SELECT * FROM c WHERE c.type = 'output' "
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
                f"Retrieved {len(results)} outputs for conversion {conversion_id}"
            )
            return results

        except Exception as e:
            logger.error(
                f"Failed to retrieve outputs for conversion {conversion_id}: {e}",
                exc_info=True
            )
            raise


# ===== Singleton Helper =====

_output_service_instance: Optional[OutputService] = None


def get_output_service() -> OutputService:
    """Get or create the singleton OutputService instance.
    
    Returns:
        OutputService instance
    """
    global _output_service_instance
    if _output_service_instance is None:
        cosmos_service = CosmosService()
        _output_service_instance = OutputService(cosmos_service)
    return _output_service_instance
