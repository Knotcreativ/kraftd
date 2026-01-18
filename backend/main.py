from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import uuid
from datetime import datetime
import os
import time
import logging
import asyncio
import sys
import json

# Setup logging
logger = logging.getLogger(__name__)

from document_processing import (
    PDFProcessor, WordProcessor, ExcelProcessor, ImageProcessor,
    DocumentExtractor, DocumentType, KraftdDocument, DocumentStatus,
    ProcessingMetadata, ExtractionMethod, DataQuality
)
from document_processing.azure_service import get_azure_service, is_azure_configured
from document_processing.orchestrator import ExtractionPipeline

# Import AI Agent (GPT-4o mini)
try:
    from agent.kraft_agent import KraftdAIAgent
    AGENT_AVAILABLE = True
except Exception as e:
    logger.warning(f"Agent module not available: {e}")
    AGENT_AVAILABLE = False

# Import configuration and monitoring
from config import (
    REQUEST_TIMEOUT, DOCUMENT_PROCESSING_TIMEOUT, FILE_PARSE_TIMEOUT,
    MAX_RETRIES, RETRY_BACKOFF_FACTOR, RETRY_MAX_WAIT,
    RATE_LIMIT_ENABLED, RATE_LIMIT_REQUESTS_PER_MINUTE, RATE_LIMIT_REQUESTS_PER_HOUR,
    METRICS_ENABLED, UPLOAD_DIR, validate_config
)
from metrics import metrics_collector
from rate_limit import RateLimitMiddleware

# Import Cosmos DB services
from services.cosmos_service import initialize_cosmos, get_cosmos_service
from services.secrets_manager import get_secrets_manager

# Import repositories
from repositories import UserRepository, DocumentRepository
from repositories.document_repository import DocumentStatus as RepoDocumentStatus

# Import Agent Routes
try:
    from routes.agent import router as agent_router
    AGENT_ROUTES_AVAILABLE = True
except Exception as e:
    logger.warning(f"Agent routes not available: {e}")
    AGENT_ROUTES_AVAILABLE = False

# Export Tracking Service (Three-stage recording)
from services.export_tracking_service import (
    initialize_export_tracking, get_export_tracking_service, ExportStage
)

# ===== Helper Functions =====
async def get_document_repository() -> DocumentRepository:
    """
    Get DocumentRepository instance.
    Mirrors pattern used in Step 5 (auth endpoints).
    
    Returns:
        DocumentRepository instance
        
    Raises:
        HTTPException: If repository cannot be initialized
    """
    try:
        cosmos_service = get_cosmos_service()
        if not cosmos_service or not cosmos_service.is_initialized():
            logger.debug("Cosmos service not initialized, using fallback mode")
            return None  # Fallback to in-memory documents_db
        
        repo = DocumentRepository()
        return repo
    except Exception as e:
        logger.error(f"Failed to get DocumentRepository: {e}")
        return None  # Fallback to in-memory documents_db


async def get_document_record(document_id: str, owner_email: str = "default@kraftdintel.com"):
    """
    Retrieve document record from Cosmos DB or fallback to in-memory.
    
    Args:
        document_id: Document ID to retrieve
        owner_email: Owner email for partition key
        
    Returns:
        Document record dict or None if not found
    """
    repo = await get_document_repository()
    if repo:
        try:
            doc = await repo.get_document(document_id, owner_email)
            if doc:
                return doc
        except Exception as e:
            logger.warning(f"Failed to get document from Cosmos DB: {e}")
    
    # Fallback to in-memory
    if document_id in documents_db:
        return documents_db[document_id]
    return None


async def update_document_record(document_id: str, updates: dict, owner_email: str = "default@kraftdintel.com"):
    """
    Update document record in Cosmos DB or fallback to in-memory.
    
    Args:
        document_id: Document ID to update
        updates: Dictionary of fields to update
        owner_email: Owner email for partition key
        
    Returns:
        True if successful
    """
    repo = await get_document_repository()
    if repo:
        try:
            await repo.update_document(document_id, owner_email, updates)
            logger.info(f"Document {document_id} updated in Cosmos DB")
            return True
        except Exception as e:
            logger.warning(f"Failed to update document in Cosmos DB: {e}")
    
    # Fallback to in-memory
    if document_id in documents_db:
        documents_db[document_id].update(updates)
        logger.info(f"Document {document_id} updated in fallback storage")
        return True
    return False

# ===== Logging Configuration =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backend.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ===== Lifespan Handler (FastAPI 0.93+) =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    # Startup code
    logger.info("=" * 60)
    logger.info("Starting Kraftd Docs Backend")
    logger.info("=" * 60)
    
    cosmos_service = None
    try:
        # Validate configuration
        if not validate_config():
            raise RuntimeError("Configuration validation failed")
        
        logger.info(f"Configuration valid - Timeout: {REQUEST_TIMEOUT}s, Retries: {MAX_RETRIES}")
        
        # Initialize Cosmos DB
        logger.info("Initializing Azure Cosmos DB...")
        try:
            secrets_mgr = get_secrets_manager()
            endpoint = secrets_mgr.get_cosmos_endpoint()
            key = secrets_mgr.get_cosmos_key()
            
            if endpoint and key:
                await initialize_cosmos(endpoint, key)
                cosmos_service = get_cosmos_service()
                logger.info("[OK] Azure Cosmos DB initialized successfully")
            else:
                logger.warning("[WARN] Cosmos DB credentials not configured")
                logger.warning("      Set COSMOS_ENDPOINT and COSMOS_KEY in environment or Azure Key Vault")
                logger.info("      Continuing with fallback mode (in-memory storage)")
        except Exception as e:
            logger.warning(f"[WARN] Could not initialize Cosmos DB: {str(e)}")
            logger.info("      Continuing with fallback mode (in-memory storage)")
        
        # Check Azure configuration
        if is_azure_configured():
            logger.info("[OK] Azure Document Intelligence is configured")
            service = get_azure_service()
            logger.info(f"[OK] Azure service initialized")
        else:
            logger.warning("[WARN] Azure Document Intelligence is NOT configured")
            logger.warning("      Set DOCUMENTINTELLIGENCE_ENDPOINT and DOCUMENTINTELLIGENCE_API_KEY")
        
        # Check upload directory
        if os.path.exists(UPLOAD_DIR):
            logger.info(f"[OK] Upload directory exists: {UPLOAD_DIR}")
        else:
            logger.info(f"Creating upload directory: {UPLOAD_DIR}")
            os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Check file permissions
        if os.access(UPLOAD_DIR, os.W_OK):
            logger.info(f"[OK] Upload directory is writable")
        else:
            logger.error(f"[ERROR] Upload directory is NOT writable: {UPLOAD_DIR}")
            raise PermissionError(f"Cannot write to {UPLOAD_DIR}")
        
        # Validate pipeline
        try:
            pipeline = ExtractionPipeline()
            logger.info(f"[OK] ExtractionPipeline initialized and ready")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize ExtractionPipeline: {str(e)}")
            raise
        
        # Initialize Export Tracking Service (Three-stage recording)
        if cosmos_service and cosmos_service.is_initialized():
            try:
                await initialize_export_tracking(cosmos_service, "KraftdIntel")
                logger.info("[OK] Export tracking service initialized")
            except Exception as e:
                logger.warning(f"[WARN] Export tracking initialization failed: {str(e)}")
                logger.info("      Export recording will not be persisted to Cosmos DB")
        else:
            logger.info("[INFO] Cosmos DB not initialized, export tracking in fallback mode")
        
        logger.info("=" * 60)
        logger.info("Startup Configuration:")
        logger.info(f"  Request Timeout: {REQUEST_TIMEOUT}s")
        logger.info(f"  Document Processing Timeout: {DOCUMENT_PROCESSING_TIMEOUT}s")
        logger.info(f"  Max Retries: {MAX_RETRIES}")
        logger.info(f"  Rate Limiting: {'Enabled' if RATE_LIMIT_ENABLED else 'Disabled'}")
        logger.info(f"  Metrics: {'Enabled' if METRICS_ENABLED else 'Disabled'}")
        logger.info(f"  Cosmos DB: {'Connected' if cosmos_service and cosmos_service.is_initialized() else 'Fallback mode'}")
        logger.info("=" * 60)
        logger.info("Startup completed successfully")
        logger.info("=" * 60)
        
        yield
    except Exception as e:
        logger.error(f"[ERROR] Startup failed: {str(e)}", exc_info=True)
        raise
    finally:
        # Shutdown code
        logger.info("=" * 60)
        logger.info("Shutting down Kraftd Docs Backend")
        logger.info("=" * 60)
        
        # Close Cosmos DB connection
        if cosmos_service and cosmos_service.is_initialized():
            try:
                await cosmos_service.close()
                logger.info("[OK] Cosmos DB connection closed")
            except Exception as e:
                logger.error(f"[ERROR] Failed to close Cosmos DB: {str(e)}")
        
        # Export metrics on shutdown if enabled
        if METRICS_ENABLED:
            metrics_collector.export_metrics("metrics_export.json")
            logger.info("[OK] Metrics exported successfully")

app = FastAPI(title="Kraftd Docs MVP Backend", lifespan=lifespan)

# ===== CORS Configuration =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MVP (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Auth System (JWT + User Management) =====
from services.auth_service import AuthService
from models.user import UserRegister, UserLogin, UserProfile, TokenResponse

# In-memory user store (for MVP - will move to Cosmos DB later)
users_db = {}

# ===== Repository Helper Functions =====
async def get_user_repository() -> Optional[UserRepository]:
    """Get UserRepository instance if Cosmos DB is initialized, else None for fallback."""
    try:
        cosmos_service = get_cosmos_service()
        if cosmos_service and cosmos_service.is_initialized():
            return UserRepository()
        return None
    except Exception as e:
        logger.warning(f"Could not get UserRepository: {str(e)}")
        return None

# ===== Add Rate Limiting Middleware =====
if RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=RATE_LIMIT_REQUESTS_PER_MINUTE,
        requests_per_hour=RATE_LIMIT_REQUESTS_PER_HOUR
    )
    logger.info(f"Rate limiting enabled: {RATE_LIMIT_REQUESTS_PER_MINUTE} req/min")

# ===== JSON Encoder Helper =====
def json_serialize(obj):
    """Encode JSON with support for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def create_json_response(data, status_code=200):
    """Create a JSON response with proper encoding."""
    json_str = json.dumps(data, default=json_serialize)
    return JSONResponse(content=json.loads(json_str), status_code=status_code)

# ===== Startup Handler =====
@app.on_event("startup")
async def startup_event():
    """Validate configuration and initialize services on startup."""
    logger.info("=" * 60)
    logger.info("Starting Kraftd Docs Backend")
    logger.info("=" * 60)
    
    try:
        # Validate configuration
        if not validate_config():
            raise RuntimeError("Configuration validation failed")
        
        logger.info(f"Configuration valid - Timeout: {REQUEST_TIMEOUT}s, Retries: {MAX_RETRIES}")
        
        # Check Azure configuration
        if is_azure_configured():
            logger.info("[OK] Azure Document Intelligence is configured")
            service = get_azure_service()
            logger.info(f"[OK] Azure service initialized")
        else:
            logger.warning("[WARN] Azure Document Intelligence is NOT configured")
            logger.warning("      Set DOCUMENTINTELLIGENCE_ENDPOINT and DOCUMENTINTELLIGENCE_API_KEY")
        
        # Check upload directory
        if os.path.exists(UPLOAD_DIR):
            logger.info(f"[OK] Upload directory exists: {UPLOAD_DIR}")
        else:
            logger.info(f"Creating upload directory: {UPLOAD_DIR}")
            os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Check file permissions
        if os.access(UPLOAD_DIR, os.W_OK):
            logger.info(f"[OK] Upload directory is writable")
        else:
            logger.error(f"[ERROR] Upload directory is NOT writable: {UPLOAD_DIR}")
            raise PermissionError(f"Cannot write to {UPLOAD_DIR}")
        
        # Validate pipeline
        try:
            pipeline = ExtractionPipeline()
            logger.info(f"[OK] ExtractionPipeline initialized and ready")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize ExtractionPipeline: {str(e)}")
            raise
        
        logger.info("=" * 60)
        logger.info("Startup Configuration:")
        logger.info(f"  Request Timeout: {REQUEST_TIMEOUT}s")
        logger.info(f"  Document Processing Timeout: {DOCUMENT_PROCESSING_TIMEOUT}s")
        logger.info(f"  Max Retries: {MAX_RETRIES}")
        logger.info(f"  Rate Limiting: {'Enabled' if RATE_LIMIT_ENABLED else 'Disabled'}")
        logger.info(f"  Metrics: {'Enabled' if METRICS_ENABLED else 'Disabled'}")
        logger.info("=" * 60)
        logger.info("Startup completed successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"[ERROR] Startup failed: {str(e)}", exc_info=True)
        raise

# ===== Pydantic Models =====
class ChatRequest(BaseModel):
    """Request model for agent chat."""
    message: str
    conversation_id: Optional[str] = None
    document_context: Optional[dict] = None

class ChatResponse(BaseModel):
    """Response model for agent chat."""
    conversation_id: str
    response: str
    reasoning: Optional[str] = None
    metadata: Optional[dict] = None

documents_db = {}
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize global agent instance
agent_instance = None

async def get_or_init_agent():
    """Get or initialize the KraftdAI agent."""
    global agent_instance
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI Agent is not available")
    
    if agent_instance is None:
        try:
            logger.info("Initializing KraftdAI Agent...")
            agent_instance = await KraftdAIAgent.create()
            logger.info("KraftdAI Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise HTTPException(status_code=500, detail=f"Agent initialization failed: {str(e)}")
    
    return agent_instance

# ===== Authentication Endpoints =====

def get_current_user_email(authorization: str = None) -> str:
    """Extract and validate current user from JWT token (for protected endpoints)."""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )
    
    token = parts[1]
    payload = AuthService.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    
    return email

@app.post("/api/v1/auth/register", status_code=201, response_model=TokenResponse)
async def register(user_data: UserRegister):
    """
    Register a new user.
    
    Implements KRAFTD Registration Flow Specification:
    - Validates all required fields
    - Checks legal acceptance (terms & privacy)
    - Hashes password with bcrypt
    - Creates user in database
    - Sets status to pending_verification
    - Returns success message (no tokens until verified)
    
    Frontend must handle email verification flow after this.
    """
    try:
        # ===== BACKEND VALIDATION RULES =====
        
        # 1. Validate email
        if not user_data.email or len(user_data.email) > 255:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "EMAIL_INVALID",
                    "message": "Invalid email format."
                }
            )
        
        # 2. Validate password strength
        if len(user_data.password) < 8 or len(user_data.password) > 128:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "PASSWORD_TOO_WEAK",
                    "message": "Password must be 8-128 characters."
                }
            )
        
        if " " in user_data.password:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "PASSWORD_TOO_WEAK",
                    "message": "Password cannot contain spaces."
                }
            )
        
        if user_data.email.lower() in user_data.password.lower():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "PASSWORD_TOO_WEAK",
                    "message": "Password must not contain email address."
                }
            )
        
        # 3. Validate legal acceptance
        if not user_data.acceptTerms:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "TERMS_NOT_ACCEPTED",
                    "message": "You must agree to the Terms of Service."
                }
            )
        
        if not user_data.acceptPrivacy:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "PRIVACY_NOT_ACCEPTED",
                    "message": "You must agree to the Privacy Policy."
                }
            )
        
        # 4. Check if email already exists
        user_repo = await get_user_repository()
        
        if user_repo:
            try:
                if await user_repo.user_exists(user_data.email):
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": "EMAIL_ALREADY_EXISTS",
                            "message": "This email is already registered."
                        }
                    )
            except Exception as e:
                logger.warning(f"Could not check user existence in DB: {e}")
                # Fall back to in-memory
                if user_data.email in users_db:
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": "EMAIL_ALREADY_EXISTS",
                            "message": "This email is already registered."
                        }
                    )
        else:
            # In-memory fallback
            if user_data.email in users_db:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "EMAIL_ALREADY_EXISTS",
                        "message": "This email is already registered."
                    }
                )
        
        # ===== USER CREATION LOGIC =====
        
        # Hash password with bcrypt
        from bcrypt import hashpw, gensalt
        salt = gensalt()
        hashed_password = hashpw(user_data.password.encode(), salt).decode()
        
        now = datetime.now()
        user_id = str(uuid.uuid4())
        
        # Create user record matching specification
        user_record = {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "hashed_password": hashed_password,
            "email_verified": True,
            "marketing_opt_in": user_data.marketingOptIn,
            "accepted_terms_at": now.isoformat(),
            "accepted_privacy_at": now.isoformat(),
            "terms_version": "v1.0",
            "privacy_version": "v1.0",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "status": "active",
            "is_active": True,
            "owner_email": user_data.email  # For Cosmos DB partition
        }
        
        # Store in database
        if user_repo:
            try:
                # Create user in Cosmos DB
                await user_repo.create_user_from_dict(user_record)
                logger.info(f"User registered in Cosmos DB: {user_data.email}")
            except Exception as e:
                logger.error(f"Failed to persist user to Cosmos DB: {str(e)}")
                # Fall back to in-memory
                users_db[user_data.email] = user_record
                logger.warning(f"Falling back to in-memory storage for: {user_data.email}")
        else:
            # In-memory fallback
            logger.warning("Cosmos DB not available, using in-memory storage")
            users_db[user_data.email] = user_record
        
        # ===== SUCCESS RESPONSE =====
        # Generate tokens for immediate login after registration
        # NOTE: Email verification temporarily skipped for MVP
        
        try:
            access_token = AuthService.create_access_token(user_data.email)
            refresh_token = AuthService.create_refresh_token(user_data.email)
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=3600
            )
        except Exception as token_err:
            logger.error(f"Error creating tokens: {str(token_err)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "TOKEN_ERROR",
                    "message": "Failed to generate authentication tokens"
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Something went wrong. Please try again."
            }
        )

# ===== EMAIL VERIFICATION ENDPOINT =====
@app.get("/api/v1/auth/verify")
async def verify_email(token: str):
    """
    Verify user email via token.
    
    Implements KRAFTD Email Verification Specification:
    - Validates token
    - Checks expiry
    - Sets emailVerified = true
    - Sets status = "active"
    """
    try:
        # TODO: Implement token verification logic
        # For MVP, accept all tokens and set verified = true
        
        # Decode token to get email
        # Check if token is valid and not expired
        # Find user by email
        # Set email_verified = true
        # Set status = "active"
        
        logger.info(f"Email verification endpoint called with token: {token[:20]}...")
        
        return {
            "status": "success",
            "message": "Email verified successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "TOKEN_INVALID",
                "message": "This verification link is invalid."
            }
        )

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """
    Login user and return JWT tokens.
    
    Per KRAFTD specification:
    - Check if email is verified
    - If not verified, reject login and suggest verification
    """
    try:
        # Try to use Cosmos DB repository first
        user_repo = await get_user_repository()
        user = None
        
        if user_repo:
            try:
                user = await user_repo.get_user_by_email(user_data.email)
            except Exception as e:
                logger.warning(f"Error fetching user from Cosmos DB: {str(e)}")
                # Fall back to in-memory
                user = users_db.get(user_data.email)
                logger.warning(f"Falling back to in-memory lookup for: {user_data.email}")
        else:
            # Cosmos DB not available, use in-memory fallback
            logger.warning("Cosmos DB not available, using in-memory storage for login")
            user = users_db.get(user_data.email)
        
        # Validate user exists
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not AuthService.verify_password(user_data.password, user.get("hashed_password")):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # ===== KRAFTD SPEC: CHECK EMAIL VERIFICATION =====
        # NOTE: Email verification temporarily skipped for MVP
        # Will be re-enabled after email service is configured
        # if isinstance(user, dict):
        #     email_verified = user.get("email_verified", False)
        # else:
        #     email_verified = getattr(user, "email_verified", False)
        # 
        # if not email_verified:
        #     raise HTTPException(
        #         status_code=403,
        #         detail={
        #             "error": "EMAIL_NOT_VERIFIED",
        #             "message": "Please verify your email before logging in."
        #         }
        #     )
        
        # Check if active
        if isinstance(user, dict):
            is_active = user.get("is_active", True)
        else:
            is_active = getattr(user, "is_active", True)
        
        if not is_active:
            raise HTTPException(
                status_code=403,
                detail="User account is disabled"
            )
        
        # Generate tokens
        user_email = user.get("email") if isinstance(user, dict) else user.email
        access_token = AuthService.create_access_token(user_email)
        refresh_token = AuthService.create_refresh_token(user_email)
        
        logger.info(f"User logged in: {user_email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Login failed"
        )

@app.post("/api/v1/auth/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        payload = AuthService.verify_token(refresh_token)
        
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired refresh token"
            )
        
        email = payload.get("sub")
        
        # Try to use Cosmos DB repository first
        user_repo = await get_user_repository()
        user = None
        
        if user_repo:
            try:
                user = await user_repo.get_user_by_email(email)
            except Exception as e:
                logger.warning(f"Error fetching user from Cosmos DB: {str(e)}")
                # Fall back to in-memory
                user = users_db.get(email)
                logger.warning(f"Falling back to in-memory lookup for: {email}")
        else:
            # Cosmos DB not available, use in-memory fallback
            logger.warning("Cosmos DB not available, using in-memory storage for refresh")
            user = users_db.get(email)
        
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="User not found or inactive"
            )
        
        # Generate new access token
        access_token = AuthService.create_access_token(email)
        new_refresh_token = AuthService.create_refresh_token(email)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=3600
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Token refresh failed"
        )

@app.get("/api/v1/auth/profile", response_model=UserProfile)
async def get_profile(authorization: str = None):
    """Get current user profile."""
    try:
        email = get_current_user_email(authorization)
        
        # Try to use Cosmos DB repository first
        user_repo = await get_user_repository()
        user = None
        
        if user_repo:
            try:
                user = await user_repo.get_user_by_email(email)
            except Exception as e:
                logger.warning(f"Error fetching user from Cosmos DB: {str(e)}")
                # Fall back to in-memory
                user = users_db.get(email)
                logger.warning(f"Falling back to in-memory lookup for: {email}")
        else:
            # Cosmos DB not available, use in-memory fallback
            logger.warning("Cosmos DB not available, using in-memory storage for profile")
            user = users_db.get(email)
        
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        return UserProfile(
            email=user.email,
            name=user.name,
            organization=user.organization,
            created_at=user.created_at,
            is_active=user.is_active
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch profile"
        )

@app.get("/api/v1/auth/validate")
async def validate_token(authorization: str = None):
    """Validate current token."""
    try:
        email = get_current_user_email(authorization)
        
        # Try to use Cosmos DB repository first
        user_repo = await get_user_repository()
        user_exists = False
        
        if user_repo:
            try:
                user_exists = await user_repo.user_exists(email)
            except Exception as e:
                logger.warning(f"Error checking user in Cosmos DB: {str(e)}")
                # Fall back to in-memory
                user_exists = email in users_db
                logger.warning(f"Falling back to in-memory check for: {email}")
        else:
            # Cosmos DB not available, use in-memory fallback
            logger.warning("Cosmos DB not available, using in-memory storage for validation")
            user_exists = email in users_db
        
        if not user_exists:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
        
        return {
            "email": email,
            "valid": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Token validation failed"
        )

# ===== Agent API Routes =====
if AGENT_ROUTES_AVAILABLE:
    app.include_router(agent_router, prefix="/api/v1")
    logger.info("[OK] Agent API routes registered at /api/v1/agent")
else:
    logger.warning("[WARN] Agent API routes not available - agent functionality disabled")

# ===== Health Check Endpoint =====
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - datetime.fromisoformat(metrics_collector.start_time.isoformat())).total_seconds() if hasattr(metrics_collector, 'start_time') else 0
    }

# ===== Metrics Endpoint =====
@app.get("/api/v1/metrics")
async def get_metrics():
    """Get current metrics and statistics."""
    if not METRICS_ENABLED:
        raise HTTPException(status_code=403, detail="Metrics are disabled")
    
    return metrics_collector.get_stats()

# ===== Root Endpoint =====
@app.get("/api/v1/")
async def root():
    logger.debug("Root endpoint called")
    return {
        "message": "Kraftd Docs Backend is running.",
        "version": "1.0.0-MVP",
        "endpoints": {
            "document_ingestion": "/docs/upload",
            "document_intelligence": "/extract",
            "workflow": "/workflow",
            "output": "/generate-output",
            "health": "/health",
            "metrics": "/metrics"
        }
    }

# ===== Document Ingestion Endpoints =====
@app.post("/api/v1/docs/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a document (PDF, Excel, Word, image, scanned).
    
    Supported formats: PDF, DOCX, XLSX, XLS, JPG, PNG, JPEG, GIF
    Max file size: 25MB (per MASTER INPUT SPECIFICATION)
    """
    try:
        logger.info(f"Uploading document: {file.filename}")
        doc_id = str(uuid.uuid4())
        file_ext = file.filename.split(".")[-1].lower()
        file_path = os.path.join(UPLOAD_DIR, f"{doc_id}.{file_ext}")
        
        # Save uploaded file
        contents = await file.read()
        
        # Validate file size (25MB limit per specification)
        max_size_bytes = 25 * 1024 * 1024  # 25MB
        if len(contents) > max_size_bytes:
            logger.warning(f"File too large: {file.filename} ({len(contents)} bytes > {max_size_bytes} bytes)")
            raise HTTPException(status_code=413, detail=f"File size exceeds 25MB limit. File size: {len(contents) / (1024*1024):.2f}MB")
        
        # Validate file type
        allowed_extensions = {'pdf', 'docx', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'gif'}
        if file_ext not in allowed_extensions:
            logger.warning(f"Unsupported file type: {file_ext}")
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}")
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"Document saved: {doc_id}, size: {len(contents)} bytes, type: {file_ext}")
        
        # Create initial document record
        kraftd_doc = KraftdDocument(
            document_id=doc_id,
            metadata={
                "document_type": DocumentType.BOQ,  # Will be detected during extraction
                "document_number": f"DOC-{doc_id[:8]}",
                "issue_date": datetime.now().date()
            },
            parties={},
            status=DocumentStatus.UPLOADED,
            processing_metadata=ProcessingMetadata(
                extraction_method=ExtractionMethod.DIRECT_PARSE,
                processing_duration_ms=0,
                source_file_size_bytes=len(contents)
            )
        )
        
        # Try to persist to Cosmos DB (with fallback to in-memory)
        repo = await get_document_repository()
        if repo:
            try:
                # Get owner email from context (for now use default)
                owner_email = "default@kraftdintel.com"
                await repo.create_document(
                    document_id=doc_id,
                    owner_email=owner_email,
                    filename=file.filename,
                    document_type=str(DocumentType.BOQ),
                    file_path=file_path,
                    file_type=file_ext,
                    document=kraftd_doc.dict()
                )
                logger.info(f"Document persisted to Cosmos DB: {doc_id}")
            except Exception as e:
                logger.warning(f"Failed to persist to Cosmos DB, using fallback: {e}")
                documents_db[doc_id] = {
                    "file_path": file_path,
                    "file_type": file_ext,
                    "document": kraftd_doc.dict()
                }
        else:
            # Fallback to in-memory storage
            documents_db[doc_id] = {
                "file_path": file_path,
                "file_type": file_ext,
                "document": kraftd_doc.dict()
            }
            logger.info(f"Using fallback in-memory storage for: {doc_id}")
        
        logger.info(f"Document registered: {doc_id}")
        return JSONResponse({
            "document_id": doc_id,
            "filename": file.filename,
            "status": "uploaded",
            "file_size_bytes": len(contents),
            "message": "Document uploaded successfully. Ready for extraction and intelligence."
        })
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

# ===== Document Conversion Endpoints =====
@app.post("/api/v1/docs/convert")
async def convert_document(document_id: str, target_format: str = "structured_data"):
    """Convert document to target format.
    
    Supported target formats:
    - structured_data: Extracted structured JSON data
    - excel: Excel workbook with extracted data
    - pdf: PDF report with extracted information
    - json: Raw JSON export of extracted fields
    - summary: Summary report of document
    
    Returns converted data in requested format.
    """
    logger.info(f"Converting document {document_id} to {target_format}")
    
    # Get document from Cosmos DB or fallback
    doc_record = await get_document_record(document_id)
    if not doc_record:
        logger.warning(f"Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = doc_record["file_path"]
    
    try:
        # Parse based on file type
        file_ext = doc_record["file_type"]
        parsed_data = None
        
        if file_ext == "pdf":
            processor = PDFProcessor(file_path)
        elif file_ext == "docx":
            processor = WordProcessor(file_path)
        elif file_ext in ["xlsx", "xls"]:
            processor = ExcelProcessor(file_path)
        elif file_ext in ["jpg", "jpeg", "png", "gif"]:
            processor = ImageProcessor(file_path)
        else:
            logger.error(f"Unsupported file type: {file_ext}")
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")
        
        # Run parsing in thread pool to avoid blocking
        parsed_data = await asyncio.to_thread(processor.parse)
        logger.info(f"Document {document_id} converted successfully")
        
        return JSONResponse({
            "document_id": document_id,
            "source_format": file_ext,
            "target_format": target_format,
            "status": "converted",
            "parsed_data": parsed_data,
            "message": f"Converted {doc_record['file_path']} to {target_format}"
        })
    except Exception as e:
        logger.error(f"Conversion failed for {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

# ===== Document Intelligence Endpoints =====
@app.post("/api/v1/docs/extract")
async def extract_intelligence(document_id: str):
    """Extract intelligence using the new orchestrator pipeline.
    
    Pipeline stages:
    1. Classifier - Identify document type
    2. Mapper - Extract structured fields
    3. Inferencer - Apply business logic rules
    4. Validator - Score completeness and quality
    
    Max timeout: 30 seconds per request
    """
    logger.info(f"Extracting intelligence for document: {document_id}")
    
    # Get document from Cosmos DB or fallback
    doc_record = await get_document_record(document_id)
    if not doc_record:
        logger.warning(f"Document not found: {document_id}")
        if METRICS_ENABLED:
            metrics_collector.record_error("/extract", "Document not found", document_id)
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = doc_record["file_path"]
    file_ext = doc_record["file_type"]
    
    try:
        start_time = time.time()
        
        # Validate file type
        supported_types = ["pdf", "docx", "xlsx", "xls", "jpg", "jpeg", "png", "gif"]
        if file_ext not in supported_types:
            logger.error(f"Unsupported file type: {file_ext}")
            if METRICS_ENABLED:
                metrics_collector.record_error("/extract", f"Unsupported file type: {file_ext}", document_id)
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")
        
        logger.info(f"Processing {file_ext} document")
        
        # Parse document using appropriate processor (in thread pool to avoid blocking)
        if file_ext == "pdf":
            processor = PDFProcessor(file_path)
        elif file_ext == "docx":
            processor = WordProcessor(file_path)
        elif file_ext in ["xlsx", "xls"]:
            processor = ExcelProcessor(file_path)
        else:  # jpg, jpeg, png, gif
            processor = ImageProcessor(file_path)
        
        logger.debug(f"Parser instantiated: {processor.__class__.__name__}")
        
        # Extract text from document (run in thread pool to avoid blocking, with timeout)
        try:
            parsed_data = await asyncio.wait_for(
                asyncio.to_thread(processor.parse),
                timeout=FILE_PARSE_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"File parsing timeout for document {document_id} after {FILE_PARSE_TIMEOUT}s")
            if METRICS_ENABLED:
                metrics_collector.record_error("/extract", f"Parsing timeout after {FILE_PARSE_TIMEOUT}s", document_id)
            raise HTTPException(status_code=408, detail=f"File parsing timeout (>{FILE_PARSE_TIMEOUT}s)")
        
        text = parsed_data if isinstance(parsed_data, str) else str(parsed_data)
        logger.debug(f"Text extracted, length: {len(text)} characters")
        
        # Process through full pipeline (run in thread pool to avoid blocking, with timeout)
        logger.info("Starting extraction pipeline...")
        try:
            pipeline = ExtractionPipeline()
            pipeline_result = await asyncio.wait_for(
                asyncio.to_thread(pipeline.process_document, text, doc_record["file_path"]),
                timeout=DOCUMENT_PROCESSING_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"Document processing timeout for {document_id} after {DOCUMENT_PROCESSING_TIMEOUT}s")
            if METRICS_ENABLED:
                metrics_collector.record_error("/extract", f"Processing timeout after {DOCUMENT_PROCESSING_TIMEOUT}s", document_id)
            raise HTTPException(status_code=408, detail=f"Processing timeout (>{DOCUMENT_PROCESSING_TIMEOUT}s)")
        
        if not pipeline_result.success:
            logger.error(f"Pipeline failed: {pipeline_result.error}")
            if METRICS_ENABLED:
                metrics_collector.record_error("/extract", f"Pipeline failed: {pipeline_result.error}", document_id)
            raise HTTPException(status_code=500, detail=f"Pipeline failed: {pipeline_result.error}")
        
        logger.info("Pipeline completed successfully")
        
        # Get the extracted document
        kraftd_document = pipeline_result.document
        kraftd_document.document_id = document_id
        
        # Update document with extraction results
        processing_duration = int((time.time() - start_time) * 1000)
        kraftd_document.status = DocumentStatus.EXTRACTED
        kraftd_document.processing_metadata = ProcessingMetadata(
            extraction_method=ExtractionMethod.DIRECT_PARSE,
            processing_duration_ms=processing_duration,
            source_file_size_bytes=os.path.getsize(file_path)
        )
        
        # Use validation results from pipeline
        if pipeline_result.validation_result:
            kraftd_document.data_quality = DataQuality(
                completeness_percentage=pipeline_result.validation_result.completeness_score,
                accuracy_score=pipeline_result.validation_result.data_quality_score / 100,
                requires_manual_review=pipeline_result.needs_manual_review
            )
        
        # Prepare validation data
        validation_data = {
            "completeness_score": pipeline_result.validation_result.completeness_score if pipeline_result.validation_result else 0,
            "quality_score": pipeline_result.validation_result.data_quality_score if pipeline_result.validation_result else 0,
            "ready_for_processing": pipeline_result.is_ready_for_processing,
            "requires_manual_review": pipeline_result.needs_manual_review
        }
        
        # Update database using helper (Cosmos DB or fallback)
        await update_document_record(document_id, {
            "document": kraftd_document.dict(),
            "validation": validation_data
        })
        
        logger.info(f"Document {document_id} extraction complete in {processing_duration}ms")
        logger.info(f"  - Type: {kraftd_document.metadata.document_type.value if kraftd_document.metadata else 'UNKNOWN'}")
        logger.info(f"  - Completeness: {pipeline_result.validation_result.completeness_score if pipeline_result.validation_result else 0}%")
        logger.info(f"  - Quality: {pipeline_result.validation_result.data_quality_score if pipeline_result.validation_result else 0}%")
        
        # Record metrics if enabled
        if METRICS_ENABLED:
            metrics_collector.record_extraction(
                document_id=document_id,
                status_code=200,
                duration_ms=processing_duration,
                completeness=pipeline_result.validation_result.completeness_score if pipeline_result.validation_result else 0,
                quality=pipeline_result.validation_result.data_quality_score if pipeline_result.validation_result else 0,
                doc_type=kraftd_document.metadata.document_type.value if kraftd_document.metadata else "UNKNOWN"
            )
        
        # Prepare response data with proper JSON serialization
        response_data = {
            "document_id": document_id,
            "status": "extracted",
            "document_type": kraftd_document.metadata.document_type.value if kraftd_document.metadata else "UNKNOWN",
            "processing_time_ms": processing_duration,
            "extraction_metrics": {
                "fields_mapped": pipeline_result.mapping_signals,
                "inferences_made": pipeline_result.inference_signals,
                "line_items": len(kraftd_document.line_items) if kraftd_document.line_items else 0,
                "parties_found": len(kraftd_document.parties) if kraftd_document.parties else 0
            },
            "validation": {
                "completeness_score": pipeline_result.validation_result.completeness_score if pipeline_result.validation_result else 0,
                "quality_score": pipeline_result.validation_result.data_quality_score if pipeline_result.validation_result else 0,
                "overall_score": pipeline_result.validation_result.overall_score if pipeline_result.validation_result else 0,
                "ready_for_processing": pipeline_result.is_ready_for_processing,
                "requires_manual_review": pipeline_result.needs_manual_review
            },
            "document": json.loads(json.dumps(kraftd_document.dict(), default=json_serialize))
        }
        
        # Return extraction summary using custom JSON serialization
        return create_json_response(response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction failed for {document_id}: {str(e)}", exc_info=True)
        if METRICS_ENABLED:
            metrics_collector.record_error("/extract", str(e), document_id)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

# ===== Workflow Orchestration Endpoints =====
@app.post("/api/v1/workflow/inquiry")
async def create_inquiry(document_id: str):
    """Step 1: Review received inquiry and dissect scope."""
    logger.info(f"Workflow inquiry step for document: {document_id}")
    
    # Get document from Cosmos DB or fallback
    doc_record = await get_document_record(document_id)
    if not doc_record:
        logger.warning(f"Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update status to REVIEW_PENDING in repository
    await update_document_record(document_id, {
        "status": RepoDocumentStatus.REVIEW_PENDING
    })
    
    logger.info(f"Document {document_id} status updated to REVIEW_PENDING")
    
    return JSONResponse({
        "document_id": document_id,
        "step": "inquiry",
        "status": RepoDocumentStatus.REVIEW_PENDING,
        "timestamp": datetime.now().isoformat(),
        "message": "Inquiry reviewed and scope dissected."
    })

@app.post("/api/v1/workflow/estimation")
async def create_estimation(document_id: str):
    """Step 2-4: Convert to estimation sheet and prepare RFQ."""
    logger.info(f"Workflow estimation step for document: {document_id}")
    
    # Get document from Cosmos DB or fallback
    doc_record = await get_document_record(document_id)
    if not doc_record:
        logger.warning(f"Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update status to ESTIMATION_IN_PROGRESS
    await update_document_record(document_id, {
        "status": RepoDocumentStatus.ESTIMATION_IN_PROGRESS
    })
    
    logger.info(f"Document {document_id} estimation sheet created")
    
    return JSONResponse({
        "document_id": document_id,
        "step": "estimation",
        "status": RepoDocumentStatus.ESTIMATION_IN_PROGRESS,
        "timestamp": datetime.now().isoformat()
    })

@app.post("/api/v1/workflow/normalize-quotes")
async def normalize_supplier_quotes(document_id: str, supplier_quotes: Optional[List[dict]] = None):
    """Step 5-6: Receive and normalize supplier quotes."""
    logger.info(f"Normalizing supplier quotes for document: {document_id}")
    
    # Get document from Cosmos DB or fallback
    doc_record = await get_document_record(document_id)
    if not doc_record:
        logger.warning(f"Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    normalized_quotes = [
        {
            "supplier": quote.get("supplier", "Unknown"),
            "normalized_price": quote.get("price", 0),
            "currency": "SAR"
        }
        for quote in (supplier_quotes or [])
    ]
    
    # Update status and quotes
    await update_document_record(document_id, {
        "status": RepoDocumentStatus.QUOTES_NORMALIZED,
        "normalized_quotes": normalized_quotes
    })
    
    logger.info(f"Normalized {len(normalized_quotes)} quotes for document {document_id}")
    
    return JSONResponse({
        "document_id": document_id,
        "step": "normalize_quotes",
        "normalized_quotes": normalized_quotes,
        "timestamp": datetime.now().isoformat()
    })

@app.post("/api/v1/workflow/comparison")
async def compare_quotations(document_id: str):
    """Step 7: Perform comparative analysis of quotations."""
    logger.info(f"Comparing quotations for document: {document_id}")
    
    # Get document from Cosmos DB or fallback
    doc_record = await get_document_record(document_id)
    if not doc_record:
        logger.warning(f"Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    analysis = {
        "lowest_price_supplier": "Supplier A",
        "best_value_supplier": "Supplier B",
        "savings_potential": "15%"
    }
    
    # Update status and comparison analysis
    await update_document_record(document_id, {
        "status": RepoDocumentStatus.COMPARISON_DONE,
        "comparison_analysis": analysis
    })
    
    logger.info(f"Quotation comparison complete for document {document_id}")
    
    return JSONResponse({
        "document_id": document_id,
        "step": "comparison",
        "analysis": analysis,
        "timestamp": datetime.now().isoformat()
    })

@app.post("/api/v1/workflow/proposal")
async def generate_proposal(document_id: str):
    """Step 8-9: Merge estimation and quotes, generate proposal."""
    logger.info(f"Generating proposal for document: {document_id}")
    
    # Get document from Cosmos DB or fallback
    doc_record = await get_document_record(document_id)
    if not doc_record:
        logger.warning(f"Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    proposal_id = str(uuid.uuid4())
    
    # Update status and proposal info
    await update_document_record(document_id, {
        "status": RepoDocumentStatus.PROPOSAL_GENERATED,
        "proposal_id": proposal_id
    })
    
    logger.info(f"Proposal generated for document {document_id}, proposal_id: {proposal_id}")
    
    return JSONResponse({
        "document_id": document_id,
        "step": "proposal",
        "proposal_id": proposal_id,
        "status": RepoDocumentStatus.PROPOSAL_GENERATED,
        "timestamp": datetime.now().isoformat()
    })

@app.post("/api/v1/workflow/po")
async def generate_purchase_order(document_id: str, supplier_id: Optional[str] = None):
    """Step 10: Generate purchase order."""
    logger.info(f"Generating PO for document: {document_id}")
    
    # Get document from Cosmos DB or fallback
    doc_record = await get_document_record(document_id)
    if not doc_record:
        logger.warning(f"Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    po_id = str(uuid.uuid4())
    
    # Update status and PO info
    await update_document_record(document_id, {
        "status": RepoDocumentStatus.PO_GENERATED,
        "po_id": po_id,
        "supplier_id": supplier_id or "Unknown"
    })
    
    logger.info(f"PO generated for document {document_id}, po_id: {po_id}")
    
    return JSONResponse({
        "document_id": document_id,
        "step": "po",
        "po_id": po_id,
        "supplier_id": supplier_id or "Unknown",
        "status": RepoDocumentStatus.PO_GENERATED,
        "timestamp": datetime.now().isoformat()
    })

@app.post("/api/v1/workflow/proforma-invoice")
async def generate_proforma_invoice(document_id: str):
    """Step 11: Generate proforma invoice."""
    logger.info(f"Generating proforma invoice for document: {document_id}")
    
    # Get document from Cosmos DB or fallback
    doc_record = await get_document_record(document_id)
    if not doc_record:
        logger.warning(f"Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    invoice_id = str(uuid.uuid4())
    
    # Update record with invoice info
    await update_document_record(document_id, {
        "proforma_invoice_id": invoice_id,
        "invoice_type": "proforma"
    })
    
    logger.info(f"Proforma invoice generated for document {document_id}, invoice_id: {invoice_id}")
    
    return JSONResponse({
        "document_id": document_id,
        "step": "proforma_invoice",
        "invoice_id": invoice_id,
        "invoice_type": "proforma",
        "status": "invoice_generated",
        "timestamp": datetime.now().isoformat()
    })

# ===== Output Generation Endpoints =====
@app.get("/api/v1/documents/{document_id}/output")
async def generate_output(document_id: str, format: str = "excel"):
    """Generate output in Excel, PDF, or Word format."""
    logger.info(f"Generating output for document {document_id} in format: {format}")
    
    # Get document from Cosmos DB or fallback
    doc_record = await get_document_record(document_id)
    if not doc_record:
        logger.warning(f"Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    supported_formats = ["excel", "pdf", "word"]
    if format.lower() not in supported_formats:
        logger.error(f"Unsupported output format: {format}")
        raise HTTPException(status_code=400, detail=f"Unsupported format. Use: {supported_formats}")
    
    doc = KraftdDocument(**doc_record["document"])
    
    return JSONResponse({
        "document_id": document_id,
        "format": format,
        "status": "generated",
        "download_url": f"/download/{document_id}.{format}",
        "line_items_count": len(doc.line_items) if doc.line_items else 0,
        "message": f"Output generated in {format} format."
    })

# ===== Utility Endpoints =====
@app.get("/api/v1/documents/{document_id}")
async def get_document_details(document_id: str):
    """Retrieve document details and extracted data."""
    logger.info(f"Retrieving document details for: {document_id}")
    
    # Get document from Cosmos DB or fallback
    doc_record = await get_document_record(document_id)
    if not doc_record:
        logger.warning(f"Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = KraftdDocument(**doc_record["document"])
    
    # Serialize document with proper JSON handling
    return create_json_response(json.loads(json.dumps(doc.dict(), default=json_serialize)))

@app.get("/api/v1/documents/{document_id}/status")
async def get_document_status(document_id: str):
    """Get document processing status and quality metrics."""
    logger.info(f"Getting status for document: {document_id}")
    
    # Get document from Cosmos DB or fallback
    doc_record = await get_document_record(document_id)
    if not doc_record:
        logger.warning(f"Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = KraftdDocument(**doc_record["document"])
    
    logger.debug(f"Document status: {doc.status}, Quality: {doc.data_quality}")
    
    return JSONResponse({
        "document_id": document_id,
        "status": doc.status,
        "file_type": doc_record["file_type"],
        "extraction_confidence": doc.extraction_confidence.dict() if doc.extraction_confidence else None,
        "data_quality": doc.data_quality.dict() if doc.data_quality else None,
        "line_items_count": len(doc.line_items) if doc.line_items else 0,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
    })
# ===== AI Agent Endpoints =====
@app.post("/api/v1/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """Chat with the KraftdAI agent for document intelligence and procurement insights."""
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI Agent is not available. OpenAI credentials not configured.")
    
    try:
        logger.info(f"Agent chat request: {request.message[:100]}...")
        agent = await get_or_init_agent()
        
        # Generate unique conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Process message with agent
        response = await agent.process_message(
            message=request.message,
            conversation_id=conversation_id,
            document_context=request.document_context
        )
        
        logger.info(f"Agent response generated for conversation: {conversation_id}")
        
        return ChatResponse(
            conversation_id=conversation_id,
            response=response.get("response", ""),
            reasoning=response.get("reasoning"),
            metadata=response.get("metadata")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@app.get("/api/v1/agent/status")
async def agent_status():
    """Get AI Agent status."""
    if not AGENT_AVAILABLE:
        return {
            "status": "unavailable",
            "reason": "Agent module not loaded",
            "openai_configured": False
        }
    
    try:
        agent = await get_or_init_agent()
        return {
            "status": "ready",
            "model": "gpt-4o-mini",
            "openai_configured": True,
            "initialized": agent_instance is not None
        }
    except Exception as e:
        return {
            "status": "error",
            "reason": str(e),
            "openai_configured": False
        }


@app.get("/api/v1/agent/learning")
async def agent_learning_insights():
    """Get AI Agent learning insights and patterns."""
    if not AGENT_AVAILABLE:
        return {
            "status": "unavailable",
            "reason": "Agent module not loaded"
        }
    
    try:
        agent = await get_or_init_agent()
        insights = await agent.get_learning_insights()
        
        # Sync patterns to Cosmos DB
        await agent._sync_learning_patterns()
        
        return {
            "status": "success",
            "insights": insights,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get learning insights: {e}")
        return {
            "status": "error",
            "reason": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/api/v1/agent/check-di-decision")
async def check_di_decision(request: dict = None):
    """
    Check if a document should use Azure Document Intelligence or learned patterns.
    
    Request body:
    {
        "supplier_name": "Supplier A",
        "document_type": "quotation",
        "confidence_threshold": 0.85
    }
    
    Returns cost optimization recommendation and decision reason.
    """
    if not AGENT_AVAILABLE:
        return {
            "status": "unavailable",
            "reason": "Agent module not loaded"
        }
    
    try:
        supplier_name = request.get("supplier_name") if request else None
        document_type = request.get("document_type") if request else None
        confidence_threshold = float(request.get("confidence_threshold", 0.85)) if request else 0.85
        
        agent = await get_or_init_agent()
        decision = await agent.should_use_document_intelligence(
            supplier_name=supplier_name,
            document_type=document_type,
            confidence_threshold=confidence_threshold
        )
        
        # Estimate cost savings
        di_cost_per_page = 0.003  # $0.003 per page for Document Intelligence (approximate)
        estimated_pages = request.get("estimated_pages", 1) if request else 1
        
        cost_data = {
            "di_cost_if_used": f"${di_cost_per_page * estimated_pages:.4f}",
            "cost_saved_with_learned": f"${di_cost_per_page * estimated_pages:.4f}" if not decision["use_di"] else "$0.00"
        }
        
        return {
            "status": "success",
            "decision": decision,
            "estimated_cost_impact": cost_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to check DI decision: {e}")
        return {
            "status": "error",
            "reason": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ==================== EXPORT FEEDBACK ENDPOINT ====================

class FeedbackRequest(BaseModel):
    """User feedback on export"""
    feedback_text: str
    satisfaction_rating: int = 5
    download_successful: bool = True


@app.post("/api/v1/exports/{export_workflow_id}/feedback")
async def submit_export_feedback(
    export_workflow_id: str,
    feedback_request: FeedbackRequest,
    authorization: str = None
):
    """
    Submit user feedback after export completion.
    
    This endpoint:
    1. Records feedback to Cosmos DB (Stage 4)
    2. Sends feedback to AI model for learning
    3. Updates workflow with feedback status
    
    Args:
        export_workflow_id: Export workflow ID (from Stage 1)
        feedback_request: User's feedback and rating
        authorization: Bearer token for authentication
        
    Returns:
        Confirmation with feedback ID and learning status
    """
    try:
        # Get current user email from authorization header
        owner_email = get_current_user_email(authorization) if authorization else "unknown@example.com"
        
        # Validate rating
        if not 1 <= feedback_request.satisfaction_rating <= 5:
            raise HTTPException(
                status_code=400,
                detail="Satisfaction rating must be between 1 and 5"
            )
        
        # Get export tracking service
        from services.export_tracking_service import get_export_tracking_service
        tracking_service = get_export_tracking_service()
        
        # Prepare learning data for AI model
        ai_learning_data = {
            "feedback_sentiment": _analyze_sentiment(feedback_request.feedback_text),
            "improvement_areas": _extract_improvement_areas(feedback_request.feedback_text),
            "positive_aspects": _extract_positive_aspects(feedback_request.feedback_text),
            "learning_enabled": True,
            "rating_context": feedback_request.satisfaction_rating
        }
        
        # Record feedback to Cosmos DB (Stage 4)
        feedback_recorded = False
        if tracking_service:
            feedback_recorded = await tracking_service.record_stage_4_user_feedback(
                export_workflow_id=export_workflow_id,
                document_id="unknown",  # Could be retrieved from Stage 1 if needed
                owner_email=owner_email,
                feedback_text=feedback_request.feedback_text,
                satisfaction_rating=feedback_request.satisfaction_rating,
                download_successful=feedback_request.download_successful,
                ai_model_learning_data=ai_learning_data
            )
        
        # Send feedback to AI model for learning (if agent available)
        learning_processed = False
        if AGENT_AVAILABLE:
            try:
                agent = KraftdAIAgent()
                
                # Call agent's learning function with feedback
                learning_result = await agent._learn_from_document_intelligence_tool(
                    pattern_type="user_feedback",
                    pattern_data={
                        "export_workflow_id": export_workflow_id,
                        "feedback_text": feedback_request.feedback_text,
                        "satisfaction_rating": feedback_request.satisfaction_rating,
                        "sentiment": ai_learning_data["feedback_sentiment"],
                        "improvements_needed": ai_learning_data["improvement_areas"],
                        "strengths": ai_learning_data["positive_aspects"],
                        "source": "user_export_feedback"
                    }
                )
                
                learning_processed = learning_result.get("success", False)
                logger.info(f"AI learning processed for feedback: {export_workflow_id}")
            except Exception as e:
                logger.warning(f"Could not process AI learning from feedback: {e}")
                learning_processed = False
        
        # Return confirmation
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "export_workflow_id": export_workflow_id,
            "feedback_recorded": feedback_recorded,
            "ai_learning_processed": learning_processed,
            "rating": feedback_request.satisfaction_rating,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting export feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to submit feedback"
        )


def _analyze_sentiment(text: str) -> str:
    """
    Simple sentiment analysis of feedback text.
    
    Returns: positive, neutral, or negative
    """
    positive_words = ["excellent", "great", "good", "perfect", "amazing", "wonderful", "love", "very good"]
    negative_words = ["bad", "poor", "terrible", "awful", "hate", "useless", "broken", "disappointing"]
    
    text_lower = text.lower()
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"


def _extract_improvement_areas(text: str) -> List[str]:
    """Extract improvement areas from feedback text."""
    improvements = []
    
    keywords = {
        "speed": ["faster", "slow", "speed", "quick"],
        "accuracy": ["accurate", "correct", "wrong", "inaccurate"],
        "format": ["format", "layout", "design", "style"],
        "features": ["feature", "option", "button", "field"],
        "documentation": ["docs", "help", "tutorial", "guide"]
    }
    
    text_lower = text.lower()
    for category, words in keywords.items():
        if any(word in text_lower for word in words):
            improvements.append(category)
    
    return improvements


def _extract_positive_aspects(text: str) -> List[str]:
    """Extract positive aspects from feedback text."""
    positives = []
    
    keywords = {
        "ease_of_use": ["easy", "simple", "straightforward", "intuitive"],
        "accuracy": ["accurate", "correct", "precise", "detailed"],
        "speed": ["fast", "quick", "instant", "responsive"],
        "quality": ["quality", "professional", "clean", "clear"],
        "features": ["feature", "option", "flexible", "customizable"]
    }
    
    text_lower = text.lower()
    for aspect, words in keywords.items():
        if any(word in text_lower for word in words):
            positives.append(aspect)
    
    return positives
