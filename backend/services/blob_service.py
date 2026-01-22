"""
Azure Blob Storage Service

Handles file uploads and downloads to/from Azure Blob Storage.
"""

import logging
from typing import Optional
from azure.storage.blob import BlobServiceClient, BlobClient
import os

logger = logging.getLogger(__name__)

# Get Blob Storage connection string from environment
BLOB_CONNECTION_STRING = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING",
    "DefaultEndpointsProtocol=https;AccountName=kraftdblob;AccountKey=<key>;EndpointSuffix=core.windows.net"
)

BLOB_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "kraftdblob")


def get_blob_client() -> BlobServiceClient:
    """
    Get Azure Blob Service client for file operations.
    
    Returns:
        BlobServiceClient instance
    """
    try:
        client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
        logger.debug("Blob service client initialized")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Blob service client: {e}")
        raise


def upload_file_to_blob(
    container_name: str,
    blob_name: str,
    file_content: bytes,
    content_type: str = "application/octet-stream",
    overwrite: bool = True
) -> str:
    """
    Upload a file to Azure Blob Storage.
    
    Args:
        container_name: Blob container name
        blob_name: Full path/name of the blob
        file_content: File content bytes
        content_type: MIME type
        overwrite: Whether to overwrite if exists
    
    Returns:
        Full blob URI
    
    Raises:
        Exception: If upload fails
    """
    try:
        client = get_blob_client()
        blob_client = client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        blob_client.upload_blob(
            data=file_content,
            overwrite=overwrite,
            content_settings={"content_type": content_type}
        )
        
        blob_uri = blob_client.url
        logger.info(f"File uploaded to blob: {blob_uri}")
        return blob_uri
        
    except Exception as e:
        logger.error(f"Blob upload failed: {e}")
        raise


def download_file_from_blob(
    container_name: str,
    blob_name: str
) -> bytes:
    """
    Download a file from Azure Blob Storage.
    
    Args:
        container_name: Blob container name
        blob_name: Full path/name of the blob
    
    Returns:
        File content bytes
    
    Raises:
        Exception: If download fails
    """
    try:
        client = get_blob_client()
        blob_client = client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        download_stream = blob_client.download_blob()
        content = download_stream.readall()
        
        logger.info(f"File downloaded from blob: {blob_name}")
        return content
        
    except Exception as e:
        logger.error(f"Blob download failed: {e}")
        raise


def delete_blob(
    container_name: str,
    blob_name: str
) -> bool:
    """
    Delete a blob from Azure Blob Storage.
    
    Args:
        container_name: Blob container name
        blob_name: Full path/name of the blob
    
    Returns:
        True if deleted, False if not found
    
    Raises:
        Exception: If deletion fails
    """
    try:
        client = get_blob_client()
        blob_client = client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        blob_client.delete_blob()
        
        logger.info(f"Blob deleted: {blob_name}")
        return True
        
    except Exception as e:
        if "BlobNotFound" in str(e):
            logger.warning(f"Blob not found: {blob_name}")
            return False
        logger.error(f"Blob deletion failed: {e}")
        raise


def get_blob_uri(
    container_name: str,
    blob_name: str
) -> str:
    """
    Get the URI for a blob.
    
    Args:
        container_name: Blob container name
        blob_name: Full path/name of the blob
    
    Returns:
        Full blob URI
    """
    return f"https://{BLOB_ACCOUNT_NAME}.blob.core.windows.net/{container_name}/{blob_name}"


def list_blobs(
    container_name: str,
    prefix: Optional[str] = None
) -> list:
    """
    List blobs in a container.
    
    Args:
        container_name: Blob container name
        prefix: Optional blob name prefix to filter
    
    Returns:
        List of blob names
    """
    try:
        client = get_blob_client()
        container_client = client.get_container_client(container=container_name)
        
        blobs = []
        for blob in container_client.list_blobs(name_starts_with=prefix):
            blobs.append(blob.name)
        
        logger.debug(f"Listed {len(blobs)} blobs in {container_name}")
        return blobs
        
    except Exception as e:
        logger.error(f"Blob listing failed: {e}")
        raise
