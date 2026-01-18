"""Configuration for Kraftd Docs Backend."""
import os
from typing import Optional

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
SERVER_WORKERS = int(os.getenv("SERVER_WORKERS", "4"))

# Timeout Configuration (in seconds)
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))  # Max 30s per request
DOCUMENT_PROCESSING_TIMEOUT = float(os.getenv("DOCUMENT_PROCESSING_TIMEOUT", "25"))  # Max 25s for processing
FILE_PARSE_TIMEOUT = float(os.getenv("FILE_PARSE_TIMEOUT", "20"))  # Max 20s for file parsing

# Retry Configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_BACKOFF_FACTOR = float(os.getenv("RETRY_BACKOFF_FACTOR", "0.5"))  # exponential backoff
RETRY_MAX_WAIT = float(os.getenv("RETRY_MAX_WAIT", "10"))  # Max wait between retries

# Rate Limiting Configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
RATE_LIMIT_REQUESTS_PER_HOUR = int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "1000"))

# Monitoring Configuration
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
METRICS_EXPORT_INTERVAL = int(os.getenv("METRICS_EXPORT_INTERVAL", "60"))  # seconds

# Azure Configuration
AZURE_ENDPOINT = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT")
AZURE_API_KEY = os.getenv("DOCUMENTINTELLIGENCE_API_KEY")

# Connection Pool Configuration
CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "10"))
CONNECTION_POOL_TIMEOUT = float(os.getenv("CONNECTION_POOL_TIMEOUT", "30"))

# Storage Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/kraftd_uploads")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))  # Per MASTER INPUT SPECIFICATION

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "backend.log")

# Cosmos DB Configuration (Task 8 Phase 5)
COSMOS_DB_ENDPOINT = os.getenv("COSMOS_DB_ENDPOINT")  # https://<account>.documents.azure.com:443/
COSMOS_DB_KEY = os.getenv("COSMOS_DB_KEY")  # Primary key
COSMOS_DB_NAME = os.getenv("COSMOS_DB_NAME", "kraftd_audit")  # Database name
COSMOS_DB_AUDIT_CONTAINER = os.getenv("COSMOS_DB_AUDIT_CONTAINER", "audit_events")  # Collection name
COSMOS_DB_THROUGHPUT = int(os.getenv("COSMOS_DB_THROUGHPUT", "400"))  # RU/s for container
COSMOS_DB_TTL_DAYS = int(os.getenv("COSMOS_DB_TTL_DAYS", "2555"))  # 7 years default

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

def validate_config() -> bool:
    """Validate critical configuration (Azure credentials are optional for local dev)."""
    errors = []
    
    # Azure credentials are OPTIONAL for local development
    # Only warn if they're partially set
    has_endpoint = bool(AZURE_ENDPOINT)
    has_api_key = bool(AZURE_API_KEY)
    
    if has_endpoint != has_api_key:
        # One is set but not the other
        errors.append("Both DOCUMENTINTELLIGENCE_ENDPOINT and DOCUMENTINTELLIGENCE_API_KEY must be set together or both unset")
    
    # Timeout validation (required)
    if REQUEST_TIMEOUT <= 0:
        errors.append("REQUEST_TIMEOUT must be positive")
    if DOCUMENT_PROCESSING_TIMEOUT >= REQUEST_TIMEOUT:
        errors.append("DOCUMENT_PROCESSING_TIMEOUT must be less than REQUEST_TIMEOUT")
    
    # Retry configuration validation (required)
    if MAX_RETRIES < 0:
        errors.append("MAX_RETRIES must be non-negative")
    if RETRY_BACKOFF_FACTOR <= 0:
        errors.append("RETRY_BACKOFF_FACTOR must be positive")
    
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True

# Display configuration on load
if __name__ == "__main__":
    print("Current Configuration:")
    print(f"  Environment: {ENVIRONMENT}")
    print(f"  Request Timeout: {REQUEST_TIMEOUT}s")
    print(f"  Document Processing Timeout: {DOCUMENT_PROCESSING_TIMEOUT}s")
    print(f"  Max Retries: {MAX_RETRIES}")
    print(f"  Rate Limiting: {'Enabled' if RATE_LIMIT_ENABLED else 'Disabled'}")
    print(f"  Metrics: {'Enabled' if METRICS_ENABLED else 'Disabled'}")
    print(f"  Is Valid: {validate_config()}")
