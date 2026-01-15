"""
STEP 5 DESIGN DOCUMENT: Cosmos DB Repository Pattern

This document outlines the repository architecture for integrating Azure Cosmos DB
with async/await patterns, following Microsoft best practices.

Reference: https://learn.microsoft.com/en-us/azure/cosmos-db/best-practice-python
"""

# ============================================================================
# ARCHITECTURE OVERVIEW
# ============================================================================

REPOSITORY_ARCHITECTURE = """
PROPOSED DIRECTORY STRUCTURE:
────────────────────────────────────────────────────────────────────────────

backend/
├── repositories/                    # NEW
│   ├── __init__.py                  # Export main classes
│   ├── base.py                      # BaseRepository abstract class
│   ├── user_repository.py           # UserRepository concrete class
│   ├── document_repository.py       # DocumentRepository concrete class
│   └── models.py                    # Repository models (different from Pydantic models)
│
├── services/
│   ├── cosmos_service.py            # NEW - Cosmos DB client management
│   ├── secrets_manager.py           # ✓ EXISTING - Key Vault integration
│   └── auth_service.py              # ✓ EXISTING - JWT handling
│
└── main.py                          # ✓ MODIFIED - routes now use repositories


KEY DESIGN PATTERNS:
1. Repository Pattern: Abstraction layer for data access
2. Singleton Pattern: Single CosmosClient instance per application
3. Async/Await: All I/O operations are async
4. Dependency Injection: FastAPI Depends() for repository access
5. Error Handling: Proper exception types for different failure modes
"""

# ============================================================================
# COSMOS DB CONFIGURATION
# ============================================================================

COSMOS_DB_SETUP = """
REQUIRED COSMOS DB SETUP (To be done before implementation):

1. Create Cosmos DB Account:
   - Location: UAE North (uaenorth)
   - Capacity: Autoscale (1000-4000 RU/s)
   - API: SQL (Core)

2. Create Database:
   - Name: "kraftdintel"
   - Throughput: Autoscale

3. Create Containers:
   a) Container "users"
      - Partition Key: /email
      - TTL: Disabled (users don't expire)
      - Indexing: All properties (default)
      
   b) Container "documents"
      - Partition Key: /owner_email (enables per-user queries)
      - TTL: 7776000 seconds (90 days) for auto-cleanup
      - Indexing: All properties
      - Unique constraints: /id

EXAMPLE DOCUMENTS:

users container:
{
    "id": "user-001",
    "email": "alice@company.com",
    "name": "Alice Chen",
    "organization": "ACME Corp",
    "hashed_password": "$2b$12$...",
    "created_at": "2026-01-15T12:00:00Z",
    "is_active": true,
    "subscription_tier": "enterprise",
    "_ts": 1737974400
}

documents container:
{
    "id": "doc-001",
    "owner_email": "alice@company.com",
    "filename": "invoice-2025-01.pdf",
    "document_type": "INVOICE",
    "status": "PROCESSING",
    "created_at": "2026-01-15T12:00:00Z",
    "updated_at": "2026-01-15T12:05:00Z",
    "extraction_result": {...},
    "workflow_data": {...},
    "_ts": 1737974400
}
"""

# ============================================================================
# COSMOS CLIENT SINGLETON
# ============================================================================

COSMOS_CLIENT_PATTERN = """
SINGLETON COSMOS CLIENT PATTERN:
────────────────────────────────────────────────────────────────────────────

Purpose:
- Reuse single CosmosClient connection across entire application
- Avoid creating new clients for each request (expensive)
- Proper lifecycle management with application lifespan

Location: services/cosmos_service.py

Key Features:
✓ Lazy initialization (client created on first use)
✓ Singleton pattern (only one instance per app lifetime)
✓ Proper cleanup on shutdown (lifespan context manager)
✓ Configurable endpoint and key from Key Vault
✓ Fallback to environment variables for development

Usage Pattern:
```python
# In main.py lifespan handler
async with lifespan(...):
    cosmos = CosmosService()
    await cosmos.initialize()  # Setup client and containers
    
    # Client available throughout app lifetime
    # Access via: cosmos.get_client()
    
    yield  # App runs here
    
    # Cleanup on shutdown
    await cosmos.close()
```

Performance Considerations:
- Single client handles thousands of concurrent requests
- Connection pooling managed internally by SDK
- No overhead from connection reuse
"""

# ============================================================================
# REPOSITORY INTERFACE
# ============================================================================

REPOSITORY_INTERFACE = """
BASE REPOSITORY INTERFACE:
────────────────────────────────────────────────────────────────────────────

class BaseRepository(ABC):
    '''Abstract base class for all repositories'''
    
    async def create(self, item: dict) -> dict:
        '''Create new item and return with id and timestamp'''
        
    async def read(self, item_id: str, partition_key: str) -> dict:
        '''Retrieve single item by id'''
        
    async def read_by_query(self, query: str, params: list) -> List[dict]:
        '''Execute SQL query and return results'''
        
    async def update(self, item_id: str, partition_key: str, data: dict) -> dict:
        '''Update item and return updated version'''
        
    async def delete(self, item_id: str, partition_key: str) -> bool:
        '''Delete item by id'''

    async def exists(self, item_id: str, partition_key: str) -> bool:
        '''Check if item exists (optimized query)'''


USER REPOSITORY INTERFACE:
────────────────────────────────────────────────────────────────────────────

class UserRepository(BaseRepository):
    '''Repository for user management'''
    
    async def create_user(self, email: str, name: str, organization: str,
                         hashed_password: str) -> UserDocument:
        '''Create new user and return created document'''
        
    async def get_user_by_email(self, email: str) -> UserDocument:
        '''Retrieve user by email (partition key)'''
        
    async def update_user(self, email: str, updates: dict) -> UserDocument:
        '''Update user and return updated document'''
        
    async def user_exists(self, email: str) -> bool:
        '''Check if user exists by email'''


DOCUMENT REPOSITORY INTERFACE:
────────────────────────────────────────────────────────────────────────────

class DocumentRepository(BaseRepository):
    '''Repository for document management'''
    
    async def create_document(self, document_data: dict) -> DocumentDocument:
        '''Create new document'''
        
    async def get_document(self, document_id: str, owner_email: str) -> DocumentDocument:
        '''Retrieve document (owner_email is partition key)'''
        
    async def get_user_documents(self, owner_email: str) -> List[DocumentDocument]:
        '''Get all documents for specific user (partition query)'''
        
    async def update_document_status(self, document_id: str, owner_email: str,
                                    status: str) -> DocumentDocument:
        '''Update document status'''
        
    async def get_documents_by_type(self, owner_email: str,
                                   document_type: str) -> List[DocumentDocument]:
        '''Query documents by type within partition'''
"""

# ============================================================================
# ERROR HANDLING STRATEGY
# ============================================================================

ERROR_HANDLING = """
COSMOS DB ERROR HANDLING:
────────────────────────────────────────────────────────────────────────────

Error Type                  HTTP Code   Action
─────────────────────────────────────────────────────────────────────────────
ItemAlreadyExists           409         Return conflict response
ItemNotFound                404         Return not found response
CosmosHttpResponseError(429) 429        Implement exponential backoff retry
CosmosHttpResponseError(500) 500        Retry with backoff
CosmosHttpResponseError(503) 503        Retry with backoff
NetworkException            500         Retry with backoff
Timeout                     500         Return timeout error
Other exceptions            500         Log and return internal error

RETRY STRATEGY:
- Max retries: 3
- Initial delay: 100ms
- Max delay: 5000ms
- Backoff multiplier: 2.0 (exponential)
- Retry on: 429 (RU throttled), 500, 503 (transient errors)

LOGGING:
- DEBUG: Each operation (create, read, update, delete)
- INFO: Success with timing
- WARNING: Retries and recoverable errors
- ERROR: Failures after retries
"""

# ============================================================================
# VALIDATION CRITERIA
# ============================================================================

VALIDATION_CRITERIA = {
    "Async/Await Correctness": {
        "criteria": [
            "✓ All I/O operations use async (no blocking calls)",
            "✓ No .sync_client() calls (always use async client)",
            "✓ Proper async context managers for connections",
            "✓ await keyword on all async function calls",
        ],
        "test_approach": "Verify no blocking operations in repository methods"
    },
    
    "Cosmos DB SDK Best Practices": {
        "criteria": [
            "✓ Single CosmosClient instance (singleton)",
            "✓ Reuse client across requests",
            "✓ Proper connection configuration (regions, retries)",
            "✓ Partition key used in all queries",
            "✓ Point reads for single item (preferred over queries)",
        ],
        "test_approach": "Verify singleton pattern and query patterns"
    },
    
    "Repository Pattern": {
        "criteria": [
            "✓ Abstract BaseRepository class",
            "✓ Concrete implementations: UserRepository, DocumentRepository",
            "✓ Consistent CRUD interface across repositories",
            "✓ No direct Cosmos imports in routes",
            "✓ Repositories injected via FastAPI Depends()",
        ],
        "test_approach": "Check inheritance and dependency injection"
    },
    
    "Error Handling": {
        "criteria": [
            "✓ Proper exception type mapping (Cosmos → HTTP)",
            "✓ Retry logic for transient failures",
            "✓ Meaningful error messages to clients",
            "✓ Logging of all error conditions",
            "✓ No credentials exposed in error messages",
        ],
        "test_approach": "Simulate errors and verify responses"
    },
    
    "Security & Data": {
        "criteria": [
            "✓ Partition key filtering (no cross-user data leaks)",
            "✓ No sensitive data in logs",
            "✓ Connection string from Key Vault (not hardcoded)",
            "✓ Proper access control per user",
            "✓ TTL configured for auto-cleanup",
        ],
        "test_approach": "Verify partition keys in queries"
    },
}

# ============================================================================
# TESTING STRATEGY
# ============================================================================

TESTING_STRATEGY = """
UNIT TESTS:

1. Test UserRepository:
   ✓ create_user() creates user and returns with id
   ✓ get_user_by_email() retrieves created user
   ✓ user_exists() returns True/False correctly
   ✓ update_user() modifies and returns updated user
   ✓ Duplicate email raises 409 Conflict
   ✓ Non-existent user raises 404 NotFound

2. Test DocumentRepository:
   ✓ create_document() creates document with owner_email partition key
   ✓ get_document() retrieves document with proper partition key
   ✓ get_user_documents() returns only user's documents
   ✓ update_document_status() changes status correctly
   ✓ Cross-partition query properly filtered

3. Test Error Handling:
   ✓ Network error triggers retry
   ✓ 429 (throttle) triggers exponential backoff
   ✓ Persistent error after retries returns 500
   ✓ Duplicate email returns 409
   ✓ Non-existent item returns 404

INTEGRATION TESTS:

1. Auth Flow:
   ✓ Register user → Create in Cosmos DB
   ✓ Login user → Query from Cosmos DB
   ✓ Get profile → Retrieve from Cosmos DB
   
2. Document Flow:
   ✓ Upload document → Create in Cosmos DB
   ✓ Get document → Retrieve from Cosmos DB
   ✓ Users can only see their own documents

MANUAL VERIFICATION:

1. In Azure Portal:
   ✓ Verify users container has created users
   ✓ Verify documents container has created documents
   ✓ Check RU consumption is reasonable (<100 RU per op)

2. In Application:
   ✓ Health check returns 200
   ✓ Register new user works
   ✓ Login returns JWT token
   ✓ Profile endpoint returns user data
"""

# ============================================================================
# IMPLEMENTATION CHECKLIST
# ============================================================================

IMPLEMENTATION_CHECKLIST = {
    "Pre-Implementation": [
        "✓ Review Cosmos DB setup (database, containers, partition keys)",
        "✓ Set JWT_SECRET_KEY and COSMOS_* environment variables",
        "✓ Understand repository pattern and async/await patterns",
        "✓ Review Microsoft Cosmos DB best practices",
    ],
    
    "Implementation": [
        "✓ Create repositories/__init__.py",
        "✓ Create repositories/base.py (BaseRepository abstract class)",
        "✓ Create repositories/user_repository.py (UserRepository implementation)",
        "✓ Create repositories/document_repository.py (DocumentRepository implementation)",
        "✓ Create services/cosmos_service.py (CosmosClient singleton)",
        "✓ Update main.py lifespan handler to initialize Cosmos",
        "✓ Update main.py to inject repositories in routes",
    ],
    
    "Code Quality": [
        "✓ Type hints on all methods",
        "✓ Docstrings on all public methods",
        "✓ Proper logging (DEBUG, INFO, ERROR levels)",
        "✓ PEP 8 compliant code",
        "✓ No hardcoded strings or credentials",
    ],
    
    "Testing": [
        "✓ All unit tests pass",
        "✓ All integration tests pass",
        "✓ Manual verification in Azure Portal",
        "✓ Error scenarios tested",
        "✓ Performance verified (sub-100ms per operation)",
    ],
    
    "Documentation": [
        "✓ Docstrings explain each repository method",
        "✓ Error handling documented",
        "✓ Configuration documented",
        "✓ Usage examples provided",
    ],
}

# ============================================================================
# PRINT VALIDATION SUMMARY
# ============================================================================

def print_design_summary():
    """Print Step 5 design validation summary."""
    
    print("\n" + "="*80)
    print("STEP 5 DESIGN VALIDATION: Cosmos DB Repository Pattern")
    print("="*80)
    
    print("\n" + REPOSITORY_ARCHITECTURE)
    
    print("\n📊 COSMOS DB CONFIGURATION:")
    print(COSMOS_DB_SETUP)
    
    print("\n🔧 COSMOS CLIENT PATTERN:")
    print(COSMOS_CLIENT_PATTERN)
    
    print("\n📋 REPOSITORY INTERFACE:")
    print(REPOSITORY_INTERFACE)
    
    print("\n⚠️ ERROR HANDLING:")
    print(ERROR_HANDLING)
    
    print("\n✅ VALIDATION CRITERIA:")
    for category, details in VALIDATION_CRITERIA.items():
        print(f"\n{category}:")
        for criterion in details["criteria"]:
            print(f"  {criterion}")
    
    print("\n🧪 TESTING STRATEGY:")
    print(TESTING_STRATEGY)
    
    print("\n📝 IMPLEMENTATION CHECKLIST:")
    for phase, items in IMPLEMENTATION_CHECKLIST.items():
        print(f"\n{phase}:")
        for item in items:
            print(f"  {item}")
    
    print("\n" + "="*80)
    print("STATUS: Ready for implementation")
    print("="*80 + "\n")


if __name__ == "__main__":
    print("Step 5 Design Document Created Successfully!")
    print("Key points:")
    print("  - Repository pattern with async/await")
    print("  - Single Cosmos DB client (singleton)")
    print("  - User and Document repositories")
    print("  - Proper error handling and retries")
    print("  - Partition key strategy for data isolation")
