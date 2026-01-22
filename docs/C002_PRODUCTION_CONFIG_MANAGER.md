# C-002: Production Configuration Manager Implementation

**Status**: NOT STARTED  
**Effort**: 4 hours  
**Priority**: HIGH - Infrastructure  

## Objective
Create centralized configuration management system with environment-specific settings, externalize hardcoded values, and support environment variable overrides.

## Current State Analysis

### 🔴 Issues Found
- Configuration values spread across multiple files
- Limited environment-specific configuration
- No clear separation between dev/staging/prod settings
- Some hardcoded values in code

### ✅ Current Config System
- `backend/config.py` - Main configuration file
- Environment variables support via `os.getenv()`
- Validation framework in place

## Implementation Plan

### Step 1: Centralized Config Manager
**File**: `backend/config_manager.py`

```python
"""
Centralized Configuration Manager
Handles environment-specific settings with validation
"""
```

Features:
- Load configuration from multiple sources (env vars, files, Key Vault)
- Validate settings on startup
- Support environment-specific overrides
- Type-safe configuration objects
- Easy unit testing with fixtures

### Step 2: Environment-Specific Configuration Files

Create configuration hierarchy:
```
backend/config/
├── base.py              # Shared defaults
├── development.py       # Dev overrides
├── staging.py          # Staging overrides
├── production.py       # Prod requirements
└── __init__.py
```

### Step 3: Configuration Templates

**Development** (local development):
```python
DEBUG = True
LOG_LEVEL = 'DEBUG'
CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
RATE_LIMIT = False
```

**Staging** (Azure staging environment):
```python
DEBUG = False
LOG_LEVEL = 'INFO'
CORS_ORIGINS = ['https://staging.kraftdintel.com']
RATE_LIMIT = True
RATE_LIMIT_REQUESTS_PER_MINUTE = 60
```

**Production** (Azure production):
```python
DEBUG = False
LOG_LEVEL = 'WARNING'
CORS_ORIGINS = ['https://kraftdintel.com']
RATE_LIMIT = True
RATE_LIMIT_REQUESTS_PER_MINUTE = 30
HTTPS_REQUIRED = True
```

### Step 4: Configuration Validation

Implement validation for:
- Required variables presence
- Type checking
- Value range validation
- Database connectivity
- Service availability

### Step 5: Externalize Hardcoded Values

Audit and move these to config:
- API timeouts
- Retry policies
- Cache settings
- Log configurations
- File upload paths
- Feature flags

### Step 6: Integration with Startup

Update `backend/main.py`:
```python
from config_manager import ConfigManager

# Load and validate config
config = ConfigManager.from_environment()
config.validate()

# Use throughout application
app = FastAPI(
    title=config.app_name,
    debug=config.debug,
    ...
)
```

## Files to Create/Modify

### New Files:
1. `backend/config_manager.py` - Core configuration system
2. `backend/config/__init__.py` - Configuration package
3. `backend/config/base.py` - Shared configuration
4. `backend/config/development.py` - Dev settings
5. `backend/config/staging.py` - Staging settings
6. `backend/config/production.py` - Prod settings
7. `backend/tests/test_config_manager.py` - Config tests

### Modified Files:
1. `backend/main.py` - Integrate ConfigManager
2. `backend/config.py` - Delegate to ConfigManager
3. `.env.example` - Template for environment variables
4. `docker-compose.yml` - Pass config to containers
5. `Dockerfile` - Inject environment

## Configuration Options Reference

### Application Settings
- `APP_NAME`: Application name
- `ENVIRONMENT`: dev|staging|production
- `DEBUG`: Enable debug mode
- `LOG_LEVEL`: DEBUG|INFO|WARNING|ERROR
- `WORKERS`: Number of worker processes

### API Settings
- `HOST`: API host address
- `PORT`: API port
- `API_TIMEOUT`: Request timeout seconds
- `DOCUMENT_PROCESSING_TIMEOUT`: Doc processing timeout
- `MAX_RETRIES`: Retry attempts
- `RETRY_BACKOFF_FACTOR`: Backoff multiplier

### Security
- `JWT_SECRET_KEY`: Token signing key
- `JWT_EXPIRATION`: Token lifetime minutes
- `CORS_ORIGINS`: Allowed CORS origins
- `RATE_LIMIT_ENABLED`: Enable rate limiting
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: RPM limit
- `HTTPS_REQUIRED`: Enforce HTTPS

### Database
- `COSMOS_ENDPOINT`: Cosmos DB endpoint
- `COSMOS_KEY`: Cosmos DB key
- `COSMOS_DATABASE`: Database name
- `COSMOS_TIMEOUT`: Query timeout

### Services
- `SENDGRID_API_KEY`: Email service key
- `OPENAI_API_KEY`: GPT-4o mini key
- `DOCUMENT_INTELLIGENCE_ENDPOINT`: OCR endpoint
- `DOCUMENTINTELLIGENCE_API_KEY`: OCR key

## Testing Strategy

1. Unit tests for ConfigManager
2. Integration tests with environment variables
3. Validation tests for each environment
4. Startup tests to verify config loads correctly

## Deployment Impact

- **Zero Downtime**: Configuration can be updated without restart
- **Version Control**: Config structure versioned in git
- **Audit Trail**: All configuration changes logged
- **Easy Rollback**: Can revert to previous config versions

## Success Criteria

✅ Single source of truth for all configuration  
✅ Environment-specific settings properly isolated  
✅ All hardcoded values externalized  
✅ Comprehensive validation on startup  
✅ Clear documentation for ops team  
✅ Zero breaking changes to existing code  

## Timeline

1. **Hour 1**: Create ConfigManager base class and structure
2. **Hour 1.5**: Implement environment-specific configurations
3. **Hour 1**: Audit and externalize hardcoded values
4. **Hour 0.5**: Add validation and testing

Total: 4 hours
