"""
Schema Service

Business logic for document schema generation, revision, and finalization.
Handles schema creation, versioning, and state management.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import uuid

from services.cosmos_service import get_cosmos_service
from azure.cosmos import exceptions

logger = logging.getLogger(__name__)


class SchemaService:
    """
    Service for managing document schemas.
    
    A schema defines the structure and fields of extracted document data.
    Schemas support versioning and revisions before finalization.
    
    Item Types:
    - "schema": Initial schema (can be revised)
    - "schema_revision": A revision of a schema
    - "final_schema": Finalized schema (read-only for production)
    """
    
    def __init__(self):
        """Initialize the service with Cosmos DB connection."""
        self.cosmos = get_cosmos_service()
        self.container_name = "schemas"
    
    async def create_schema(
        self,
        conversion_id: str,
        user_email: str,
        schema_json: Dict[str, Any],
        document_id: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new schema from extracted document structure.
        
        Args:
            conversion_id: UUID of the conversion session
            user_email: Email of the user (partition key)
            schema_json: Schema definition with 'fields' key containing field definitions
            document_id: Optional document ID this schema was generated from
            document_type: Optional document type (e.g., 'invoice', 'contract')
        
        Returns:
            Dict with created schema metadata
        
        Raises:
            ValueError: If schema_json is missing required fields
            Exception: If database insert fails
        
        Example:
            schema = await schema_service.create_schema(
                conversion_id='conv-123',
                user_email='user@example.com',
                schema_json={
                    'fields': [
                        {'name': 'invoice_number', 'type': 'string'},
                        {'name': 'total_amount', 'type': 'number'}
                    ]
                },
                document_id='doc-456'
            )
        """
        schema_id = str(uuid.uuid4())
        
        if not isinstance(schema_json, dict) or 'fields' not in schema_json:
            raise ValueError("schema_json must contain 'fields' key")
        
        schema_record = {
            "id": schema_id,
            "schema_id": schema_id,
            "conversion_id": conversion_id,
            "user_email": user_email,  # Partition key
            "type": "schema",  # Item discriminator
            "status": "draft",  # draft | finalized
            "version": 1,
            "document_id": document_id,
            "document_type": document_type,
            "fields": schema_json.get("fields", []),
            "metadata": schema_json.get("metadata", {}),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "created_by_ip": None,
            "created_by_user_agent": None
        }
        
        try:
            result = await self.cosmos.create_item(
                container_name=self.container_name,
                item=schema_record
            )
            
            logger.info(f"Schema created: {schema_id} for conversion: {conversion_id}")
            return result
        
        except exceptions.CosmosResourceExistsError:
            logger.error(f"Schema already exists: {schema_id}")
            raise ValueError(f"Schema {schema_id} already exists")
        
        except Exception as e:
            logger.error(
                f"Error creating schema for conversion {conversion_id}: {str(e)}",
                exc_info=True
            )
            raise
    
    async def save_revision(
        self,
        schema_id: str,
        conversion_id: str,
        user_email: str,
        edits: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a revision of an existing schema.
        
        Revisions track changes to a schema before it's finalized.
        Each revision has a unique ID and maintains the parent schema reference.
        
        Args:
            schema_id: UUID of the parent schema
            conversion_id: UUID of the conversion session
            user_email: Email of the user (partition key)
            edits: Changes to apply, containing:
                - 'fields': Updated field definitions
                - 'changes_summary': Description of what changed
        
        Returns:
            Dict with created revision metadata
        
        Raises:
            ValueError: If edits format is invalid
            Exception: If database insert fails
        
        Example:
            revision = await schema_service.save_revision(
                schema_id='schema-123',
                conversion_id='conv-123',
                user_email='user@example.com',
                edits={
                    'fields': [...updated fields...],
                    'changes_summary': 'Added 3 new fields, removed deprecated field'
                }
            )
        """
        revision_id = str(uuid.uuid4())
        
        if not isinstance(edits, dict) or 'fields' not in edits:
            raise ValueError("edits must contain 'fields' key")
        
        revision_record = {
            "id": revision_id,
            "revision_id": revision_id,
            "schema_id": schema_id,  # Reference to parent schema
            "conversion_id": conversion_id,
            "user_email": user_email,  # Partition key
            "type": "schema_revision",  # Item discriminator
            "status": "pending_review",  # pending_review | approved | rejected
            "fields": edits.get("fields", []),
            "changes_summary": edits.get("changes_summary", ""),
            "metadata": edits.get("metadata", {}),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "reviewed_at": None,
            "reviewed_by": None
        }
        
        try:
            result = await self.cosmos.create_item(
                container_name=self.container_name,
                item=revision_record
            )
            
            logger.info(f"Schema revision created: {revision_id} for schema: {schema_id}")
            return result
        
        except Exception as e:
            logger.error(
                f"Error creating revision for schema {schema_id}: {str(e)}",
                exc_info=True
            )
            raise
    
    async def finalize_schema(
        self,
        schema_id: str,
        conversion_id: str,
        user_email: str,
        schema_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Finalize a schema for production use.
        
        Finalized schemas are locked and cannot be edited further.
        They represent the approved structure for data extraction.
        
        Args:
            schema_id: UUID of the schema to finalize
            conversion_id: UUID of the conversion session
            user_email: Email of the user (partition key)
            schema_json: Final schema definition with all fields and validation rules
        
        Returns:
            Dict with finalized schema metadata
        
        Raises:
            ValueError: If schema_json is invalid
            Exception: If database insert fails
        
        Example:
            final = await schema_service.finalize_schema(
                schema_id='schema-123',
                conversion_id='conv-123',
                user_email='user@example.com',
                schema_json={
                    'fields': [...],
                    'validation_rules': {...}
                }
            )
        """
        final_schema_id = str(uuid.uuid4())
        
        if not isinstance(schema_json, dict) or 'fields' not in schema_json:
            raise ValueError("schema_json must contain 'fields' key")
        
        final_record = {
            "id": final_schema_id,
            "final_schema_id": final_schema_id,
            "schema_id": schema_id,  # Reference to original schema
            "conversion_id": conversion_id,
            "user_email": user_email,  # Partition key
            "type": "final_schema",  # Item discriminator
            "status": "active",  # active | archived | deprecated
            "version": 1,
            "fields": schema_json.get("fields", []),
            "validation_rules": schema_json.get("validation_rules", {}),
            "metadata": schema_json.get("metadata", {}),
            "finalized_at": datetime.utcnow().isoformat() + "Z",
            "approved_by": None,
            "approval_notes": None,
            "archived_at": None
        }
        
        try:
            result = await self.cosmos.create_item(
                container_name=self.container_name,
                item=final_record
            )
            
            logger.info(f"Schema finalized: {final_schema_id} from schema: {schema_id}")
            return result
        
        except Exception as e:
            logger.error(
                f"Error finalizing schema {schema_id}: {str(e)}",
                exc_info=True
            )
            raise
    
    async def get_schema(
        self,
        schema_id: str,
        user_email: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a schema by ID.
        
        Returns the schema item with type='schema' and highest version.
        
        Args:
            schema_id: UUID of the schema
            user_email: Email of the user (partition key)
        
        Returns:
            Schema document or None if not found
        
        Raises:
            Exception: If database query fails
        
        Example:
            schema = await schema_service.get_schema(
                schema_id='schema-123',
                user_email='user@example.com'
            )
        """
        try:
            # Query for the schema by ID and user
            query = (
                "SELECT * FROM c WHERE c.schema_id = @schema_id "
                "AND c.user_email = @user_email AND c.type = 'schema' "
                "ORDER BY c.version DESC"
            )
            
            parameters = [
                {"name": "@schema_id", "value": schema_id},
                {"name": "@user_email", "value": user_email}
            ]
            
            items = await self.cosmos.query_items(
                container_name=self.container_name,
                query=query,
                parameters=parameters
            )
            
            if items:
                logger.debug(f"Retrieved schema: {schema_id}")
                return items[0]  # Return highest version
            else:
                logger.warning(f"Schema not found: {schema_id}")
                return None
        
        except Exception as e:
            logger.error(
                f"Error retrieving schema {schema_id}: {str(e)}",
                exc_info=True
            )
            raise
    
    async def get_user_schemas(
        self,
        user_email: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all schemas for a user.
        
        Args:
            user_email: Email of the user (partition key)
            status: Optional status filter ('draft', 'finalized', etc.)
        
        Returns:
            List of schema documents
        
        Raises:
            Exception: If database query fails
        
        Example:
            schemas = await schema_service.get_user_schemas(
                user_email='user@example.com',
                status='draft'
            )
        """
        try:
            if status:
                query = (
                    "SELECT * FROM c WHERE c.user_email = @user_email "
                    "AND c.type = 'schema' AND c.status = @status "
                    "ORDER BY c.created_at DESC"
                )
                parameters = [
                    {"name": "@user_email", "value": user_email},
                    {"name": "@status", "value": status}
                ]
            else:
                query = (
                    "SELECT * FROM c WHERE c.user_email = @user_email "
                    "AND c.type = 'schema' ORDER BY c.created_at DESC"
                )
                parameters = [
                    {"name": "@user_email", "value": user_email}
                ]
            
            items = await self.cosmos.query_items(
                container_name=self.container_name,
                query=query,
                parameters=parameters
            )
            
            logger.debug(f"Retrieved {len(items)} schemas for user: {user_email}")
            return items
        
        except Exception as e:
            logger.error(
                f"Error retrieving schemas for user {user_email}: {str(e)}",
                exc_info=True
            )
            raise
    
    async def get_schema_revisions(
        self,
        schema_id: str,
        user_email: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all revisions for a schema.
        
        Args:
            schema_id: UUID of the schema
            user_email: Email of the user (partition key)
        
        Returns:
            List of revision documents ordered by creation date
        
        Raises:
            Exception: If database query fails
        
        Example:
            revisions = await schema_service.get_schema_revisions(
                schema_id='schema-123',
                user_email='user@example.com'
            )
        """
        try:
            query = (
                "SELECT * FROM c WHERE c.schema_id = @schema_id "
                "AND c.user_email = @user_email AND c.type = 'schema_revision' "
                "ORDER BY c.created_at DESC"
            )
            
            parameters = [
                {"name": "@schema_id", "value": schema_id},
                {"name": "@user_email", "value": user_email}
            ]
            
            items = await self.cosmos.query_items(
                container_name=self.container_name,
                query=query,
                parameters=parameters
            )
            
            logger.debug(f"Retrieved {len(items)} revisions for schema: {schema_id}")
            return items
        
        except Exception as e:
            logger.error(
                f"Error retrieving revisions for schema {schema_id}: {str(e)}",
                exc_info=True
            )
            raise
    
    async def get_final_schema(
        self,
        schema_id: str,
        user_email: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve the finalized version of a schema.
        
        Args:
            schema_id: UUID of the original schema
            user_email: Email of the user (partition key)
        
        Returns:
            Final schema document or None if not yet finalized
        
        Raises:
            Exception: If database query fails
        
        Example:
            final = await schema_service.get_final_schema(
                schema_id='schema-123',
                user_email='user@example.com'
            )
        """
        try:
            query = (
                "SELECT * FROM c WHERE c.schema_id = @schema_id "
                "AND c.user_email = @user_email AND c.type = 'final_schema' "
                "ORDER BY c.finalized_at DESC"
            )
            
            parameters = [
                {"name": "@schema_id", "value": schema_id},
                {"name": "@user_email", "value": user_email}
            ]
            
            items = await self.cosmos.query_items(
                container_name=self.container_name,
                query=query,
                parameters=parameters
            )
            
            if items:
                logger.debug(f"Retrieved final schema for: {schema_id}")
                return items[0]  # Return most recent finalization
            else:
                logger.debug(f"No finalized schema found for: {schema_id}")
                return None
        
        except Exception as e:
            logger.error(
                f"Error retrieving final schema for {schema_id}: {str(e)}",
                exc_info=True
            )
            raise


# Singleton instance helper
_schema_service: Optional[SchemaService] = None


def get_schema_service() -> SchemaService:
    """Get or create global schema service instance."""
    global _schema_service
    if _schema_service is None:
        _schema_service = SchemaService()
    return _schema_service
