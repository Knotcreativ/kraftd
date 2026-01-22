# 🔧 Backend Structure Remediation Plan

**Status:** INSPECTION COMPLETE  
**Priority Issues:** 6  
**Estimated Effort:** 36-40 hours  
**Target Completion:** 3-5 days with focused work  

---

## EXECUTIVE ACTION ITEMS

### Priority 1: CRITICAL (Must Fix Before Staging)

**Issue:** Backend Server Stability
- **Status:** 🔴 BLOCKING
- **Impact:** Cannot test API, cannot deploy
- **Effort:** 2-4 hours
- **Action:** See [Debug Investigation Plan](#debug-plan)

---

### Priority 2: HIGH (Must Fix Before Staging)

#### Action Item 1: Reorganize Test Files
**Effort:** 3-4 hours  
**Complexity:** Low  
**Impact:** Maintainability, CI/CD readiness

**Current State:**
```
backend/
├── test_api.py              ❌ In root
├── test_auth.py             ❌ In root
├── test_classifier.py       ❌ In root
├── tests/
│   └── __init__.py          (empty directory)
```

**Target State:**
```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py          ✅ NEW: Shared fixtures
│   ├── pytest.ini           ✅ NEW: Configuration
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_auth.py             (moved)
│   │   ├── test_classifier.py       (moved)
│   │   ├── test_extractor.py        (moved)
│   │   ├── test_validator.py        (moved)
│   │   ├── test_mapper.py           (moved)
│   │   ├── test_orchestrator.py     (moved)
│   │   ├── test_inferencer.py       (moved)
│   │   └── test_repositories.py     (moved)
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api_endpoints.py    (moved from test_endpoints.py)
│   │   ├── test_api.py              (moved)
│   │   ├── test_security.py         (moved)
│   │   ├── test_templates.py        (moved)
│   │   ├── test_workflows.py        (moved)
│   │   ├── test_export_tracking.py  (moved)
│   │   └── test_export_feedback_stage4.py (moved)
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── conftest.py              (fixture definitions)
│   │   ├── mock_data.py             ✅ NEW: Mock data generators
│   │   ├── sample_documents/        (sample test files)
│   │   │   └── test_document.pdf    (moved)
│   │   └── db_fixtures.py           ✅ NEW: Database fixtures
│   └── test_real_documents.py       (can stay in integration)
```

**Implementation Steps:**

1. Create directory structure:
```powershell
mkdir backend/tests/unit
mkdir backend/tests/integration  
mkdir backend/tests/fixtures
mkdir backend/tests/fixtures/sample_documents
```

2. Create `conftest.py`:
```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app

@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)

@pytest.fixture
def auth_token():
    """Sample JWT token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

@pytest.fixture
def sample_user():
    """Sample user object for testing."""
    return {
        "user_id": "test-user-001",
        "email": "test@example.com",
        "role": "admin"
    }

@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "document_id": "doc-001",
        "filename": "invoice.pdf",
        "document_type": "INVOICE",
        "status": "COMPLETED"
    }
```

3. Create `pytest.ini`:
```ini
# backend/tests/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=backend
    --cov-report=html
    --cov-report=term-missing:skip-covered
    --cov-report=xml

markers =
    unit: Unit tests (no external dependencies)
    integration: Integration tests (with services)
    slow: Slow running tests
    security: Security-related tests
    
console_output_style = progress
```

4. Move test files:
```powershell
# Unit tests
mv backend/test_auth.py backend/tests/unit/
mv backend/test_classifier.py backend/tests/unit/
mv backend/test_extractor.py backend/tests/unit/
mv backend/test_validator.py backend/tests/unit/
mv backend/test_mapper.py backend/tests/unit/
mv backend/test_orchestrator.py backend/tests/unit/
mv backend/test_inferencer.py backend/tests/unit/
mv backend/test_repositories.py backend/tests/unit/

# Integration tests
mv backend/test_endpoints.py backend/tests/integration/test_api_endpoints.py
mv backend/test_api.py backend/tests/integration/
mv backend/test_security.py backend/tests/integration/
mv backend/test_templates.py backend/tests/integration/
mv backend/test_workflows.py backend/tests/integration/
mv backend/test_export_tracking.py backend/tests/integration/
mv backend/test_export_feedback_stage4.py backend/tests/integration/
mv backend/test_real_documents.py backend/tests/integration/

# Sample documents
mv backend/test_documents/test_document.pdf backend/tests/fixtures/sample_documents/
```

5. Update imports in moved test files (example):
```python
# backend/tests/unit/test_auth.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.services.auth_service import AuthService
```

6. Mark tests with appropriate markers:
```python
# backend/tests/unit/test_auth.py
import pytest

@pytest.mark.unit
def test_password_hashing():
    """Unit test: password hashing logic."""
    pass

# backend/tests/integration/test_api_endpoints.py
import pytest

@pytest.mark.integration
async def test_register_endpoint(client):
    """Integration test: user registration endpoint."""
    response = client.post("/api/v1/auth/register", json={...})
    assert response.status_code == 201
```

7. Create mock data helper:
```python
# backend/tests/fixtures/mock_data.py
"""Mock data generators for testing."""

def create_test_user(email="test@example.com", role="user"):
    """Create a test user."""
    return {
        "user_id": "test-user-001",
        "email": email,
        "role": role
    }

def create_test_document(doc_type="INVOICE"):
    """Create a test document."""
    return {
        "document_id": "doc-001",
        "filename": "test.pdf",
        "document_type": doc_type,
        "status": "PENDING"
    }
```

---

#### Action Item 2: Create Pytest Configuration
**Effort:** 1-2 hours  
**Complexity:** Low  
**Impact:** Test execution, coverage reporting

**Required Files:**

`backend/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "kraftd-intel-backend"
version = "1.0.0"
description = "KraftdIntel backend FastAPI application"
requires-python = ">=3.9"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=backend",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-report=xml",
]

[tool.coverage.run]
source = ["backend"]
omit = [
    "*/tests/*",
    "*/__init__.py",
    "*/__pycache__/*",
    "*/venv/*",
    "*/site-packages/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "if sys.platform",
]
precision = 2
show_missing = true

[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']

[tool.isort]
profile = "black"
line_length = 100
multi_line_mode = 3

[tool.mypy]
python_version = "3.9"
ignore_missing_imports = true
strict = false
```

**Add to requirements.txt** (for development):
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
coverage==7.3.2
```

---

### Priority 3: HIGH (Before Production)

#### Action Item 3: Create GitHub Actions Workflows
**Effort:** 6-8 hours  
**Complexity:** Medium  
**Impact:** CI/CD automation, deployment safety

**Critical Fix Reference:** C003_GITHUB_ACTIONS_CICD.md (already created)

**File 1: `.github/workflows/test.yml`**
```yaml
name: Test Backend

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'backend/**'
      - '.github/workflows/test.yml'
  pull_request:
    branches: [ main, develop ]
    paths:
      - 'backend/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        cd backend
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: |
        cd backend
        pytest tests/ -v --cov=backend --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./backend/coverage.xml
        flags: unittests
```

**File 2: `.github/workflows/deploy-staging.yml`**
```yaml
name: Deploy to Staging

on:
  push:
    branches: [ develop ]
    paths:
      - 'backend/**'
      - '.github/workflows/deploy-staging.yml'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t kraftd-backend:${{ github.sha }} \
                     -t kraftd-backend:latest \
                     -f backend/Dockerfile .
    
    - name: Push to Azure Container Registry
      run: |
        docker login -u ${{ secrets.ACR_USERNAME }} \
                     -p ${{ secrets.ACR_PASSWORD }} \
                     ${{ secrets.ACR_REGISTRY }}
        docker tag kraftd-backend:latest \
                   ${{ secrets.ACR_REGISTRY }}/kraftd-backend:latest
        docker push ${{ secrets.ACR_REGISTRY }}/kraftd-backend:latest
    
    - name: Deploy to Azure Container Apps
      run: |
        az containerapp update \
          --name kraftd-backend-staging \
          --resource-group ${{ secrets.AZURE_RG }} \
          --image ${{ secrets.ACR_REGISTRY }}/kraftd-backend:latest
```

**File 3: `.github/workflows/deploy-production.yml`**
```yaml
name: Deploy to Production

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
      with:
        ref: ${{ github.ref }}
    
    - name: Run tests
      run: |
        cd backend
        python -m pip install -r requirements.txt pytest pytest-asyncio
        pytest tests/ -v
    
    - name: Build Docker image
      run: |
        docker build -t kraftd-backend:${{ github.ref_name }} \
                     -t kraftd-backend:latest \
                     -f backend/Dockerfile .
    
    - name: Push to Azure Container Registry
      run: |
        docker login -u ${{ secrets.ACR_USERNAME }} \
                     -p ${{ secrets.ACR_PASSWORD }} \
                     ${{ secrets.ACR_REGISTRY }}
        docker tag kraftd-backend:latest \
                   ${{ secrets.ACR_REGISTRY }}/kraftd-backend:${{ github.ref_name }}
        docker push ${{ secrets.ACR_REGISTRY }}/kraftd-backend:${{ github.ref_name }}
    
    - name: Deploy to Azure Container Apps
      run: |
        az containerapp update \
          --name kraftd-backend-production \
          --resource-group ${{ secrets.AZURE_RG }} \
          --image ${{ secrets.ACR_REGISTRY }}/kraftd-backend:${{ github.ref_name }}
```

**Secret Setup Required:**
```
In GitHub Repo Settings > Secrets and variables:

AZURE_RG              = "kraftd-rg"
AZURE_SUBSCRIPTION_ID = "your-subscription-id"
ACR_REGISTRY          = "kraftdacr.azurecr.io"
ACR_USERNAME          = "kraftdacr"
ACR_PASSWORD          = [from azure portal]
```

---

#### Action Item 4: Pin Package Versions
**Effort:** 2-3 hours  
**Complexity:** Low  
**Impact:** Reproducibility, security patching

**Current requirements.txt:**
```
fastapi
uvicorn
python-multipart
pydantic
# ... (unpinned versions)
```

**Updated requirements.txt:**
```
# Web Framework & Server
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6

# Data Validation
pydantic==2.5.0
email-validator==2.1.0

# Document Processing
pdfplumber==0.10.3
python-docx==0.8.11
openpyxl==3.11.2
pytesseract==0.3.10
pillow==10.1.0
reportlab==4.0.7
pandas==2.1.3

# HTTP & Async
httpx==0.25.2
aiofiles==23.2.1

# Azure Services
azure-storage-blob==12.17.0
azure-cosmos==4.5.1
azure-ai-documentintelligence==1.0.0
azure-identity==1.14.0

# Security
PyJWT==2.8.1
passlib==1.7.4
bcrypt==4.1.1
python-dotenv==1.0.0

# AI/ML
openai==1.3.5

# Email
sendgrid==6.10.0

# Database
psycopg2-binary==2.9.9

# Development/Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
coverage==7.3.2
```

**Steps:**
1. Run `pip install --upgrade -r requirements.txt`
2. Run `pip freeze > requirements-pinned.txt`
3. Review and clean up requirements-pinned.txt
4. Move pinned versions to requirements.txt
5. Test all functionality
6. Commit with message "build: pin dependencies to specific versions"

---

#### Action Item 5: Create Production Configuration
**Effort:** 2-3 hours  
**Complexity:** Medium  
**Impact:** Production deployment safety

**Create: `backend/.env.production`**
```env
# ===== PRODUCTION ENVIRONMENT =====

# Environment
ENVIRONMENT=production
DEBUG=false

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_WORKERS=4

# Timeouts (in seconds)
REQUEST_TIMEOUT=30
DOCUMENT_PROCESSING_TIMEOUT=25
FILE_PARSE_TIMEOUT=20

# Retry Configuration
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=0.5
RETRY_MAX_WAIT=10

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_REQUESTS_PER_HOUR=5000

# Monitoring
METRICS_ENABLED=true
METRICS_EXPORT_INTERVAL=60
LOG_LEVEL=WARNING
LOG_FILE=/var/log/kraftd/backend.log

# Connection Pooling
CONNECTION_POOL_SIZE=20
CONNECTION_POOL_TIMEOUT=30

# Storage
UPLOAD_DIR=/var/data/kraftd/uploads
MAX_UPLOAD_SIZE_MB=25

# Azure Services (references to Key Vault)
DOCUMENTINTELLIGENCE_ENDPOINT=@Microsoft.KeyVault(SecretUri=https://kraftd-kv.vault.azure.net/secrets/documentintelligence-endpoint/)
DOCUMENTINTELLIGENCE_API_KEY=@Microsoft.KeyVault(SecretUri=https://kraftd-kv.vault.azure.net/secrets/documentintelligence-api-key/)

# Database
COSMOS_ENDPOINT=@Microsoft.KeyVault(SecretUri=https://kraftd-kv.vault.azure.net/secrets/cosmos-endpoint/)
COSMOS_KEY=@Microsoft.KeyVault(SecretUri=https://kraftd-kv.vault.azure.net/secrets/cosmos-key/)

# Security
JWT_SECRET_KEY=@Microsoft.KeyVault(SecretUri=https://kraftd-kv.vault.azure.net/secrets/jwt-secret-key/)
TOKEN_EXPIRATION_HOURS=24

# Email
SENDGRID_API_KEY=@Microsoft.KeyVault(SecretUri=https://kraftd-kv.vault.azure.net/secrets/sendgrid-api-key/)
```

**Create: `backend/.env.example`**
```env
# Copy this file to .env and fill in your values
ENVIRONMENT=development
DEBUG=true
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
REQUEST_TIMEOUT=30
DOCUMENT_PROCESSING_TIMEOUT=25
MAX_RETRIES=3
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
METRICS_ENABLED=true
LOG_LEVEL=INFO
UPLOAD_DIR=/tmp/kraftd_uploads
MAX_UPLOAD_SIZE_MB=25

# Azure Services (optional for local dev)
DOCUMENTINTELLIGENCE_ENDPOINT=
DOCUMENTINTELLIGENCE_API_KEY=

# Database (optional for local dev)
COSMOS_ENDPOINT=
COSMOS_KEY=

# Security
JWT_SECRET_KEY=your-secret-key-here
TOKEN_EXPIRATION_HOURS=24

# Email
SENDGRID_API_KEY=
```

**Update: `backend/startup-production.sh`** (for Container Apps)
```bash
#!/bin/bash
# Production startup script for Azure Container Apps

# Load environment variables
set -a
source /etc/config/.env.production
set +a

# Run migrations/initialization if needed
# python scripts/init_db.py

# Start Uvicorn with production settings
exec python -m uvicorn main:app \
    --host ${SERVER_HOST:-0.0.0.0} \
    --port ${SERVER_PORT:-8000} \
    --workers ${SERVER_WORKERS:-4} \
    --log-level ${LOG_LEVEL:-info}
```

---

### Priority 4: MEDIUM (Before Production)

#### Action Item 6: Improve Documentation
**Effort:** 4-6 hours  
**Complexity:** Low  
**Impact:** Onboarding, troubleshooting

**Create: `backend/API_DOCUMENTATION.md`**
```markdown
# KraftdIntel Backend API Documentation

## Base URL
- **Development:** `http://localhost:8000`
- **Staging:** `https://staging-api.kraftdintel.com`
- **Production:** `https://api.kraftdintel.com`

## Authentication
All endpoints (except `/health` and `/auth/login`) require JWT token:
```
Authorization: Bearer <token>
```

## Endpoints

### Health Check
```
GET /health
Response: { "status": "healthy", "timestamp": "2026-01-18T..." }
```

### Authentication
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/verify
```

... [Full API documentation]
```

**Create: `backend/DEPLOYMENT_GUIDE.md`**
```markdown
# Backend Deployment Guide

## Local Development
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

## Docker
```bash
docker build -t kraftd-backend .
docker run -p 8000:8000 -e ENVIRONMENT=development kraftd-backend
```

## Azure Container Apps
```bash
az containerapp create \
  --name kraftd-backend \
  --resource-group kraftd-rg \
  --image kraftdacr.azurecr.io/kraftd-backend:latest \
  --target-port 8000
```
```

**Create: `backend/TROUBLESHOOTING.md`**
```markdown
# Troubleshooting Guide

## Server Shuts Down After Startup
**Symptom:** Server starts but exits after 4-15 seconds
**Cause:** Likely lifespan context manager issue
**Solution:** 
1. Check main.py lifespan handler
2. Verify no unhandled exceptions
3. Try running in Docker

## Database Connection Fails
**Symptom:** `Could not initialize Cosmos DB`
**Cause:** Missing credentials or network issue
**Solution:**
1. Check .env file has COSMOS_ENDPOINT and COSMOS_KEY
2. Verify network connectivity
3. Check Key Vault access permissions
```

---

## DEBUG INVESTIGATION PLAN {#debug-plan}

### Server Stability Issue - Root Cause Analysis

**Current Symptoms:**
```
INFO: Started server process [PID]
INFO: Waiting for application startup
[Startup completes successfully]
INFO: Application startup complete
INFO: Uvicorn running on http://127.0.0.1:8000
[After 4-15 seconds]
INFO: Shutting down
asyncio.exceptions.CancelledError
```

**Investigation Steps (Priority Order):**

1. **Check Lifespan Context Manager** (Most Likely)
   - File: `backend/main.py` lines 208-320
   - Look for: Early yield, exceptions, unfinished initialization
   - Test: Add detailed logging

2. **Verify Signal Handlers** (Likely)
   - Check: Are signal handlers triggering shutdown?
   - Test: Run with `--no-server` and handle manually

3. **Test Event Loop** (Possible)
   - Current: Using `WindowsProactorEventLoopPolicy`
   - Test: Try `WindowsSelectorEventLoopPolicy`
   - Test: Run in Docker (Linux environment)

4. **Check for sys.exit() Calls** (Unlikely)
   - Search: `git grep "sys.exit"` in backend/
   - Look for: Any explicit shutdown calls

5. **Database Connection Issues** (Unlikely but Possible)
   - Check: cosmos_service initialization
   - Test: Comment out Cosmos service, see if server stays running

### Debugging Steps

**Step 1: Add Detailed Logging**
```python
# backend/main.py - Add to lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("LIFESPAN: Starting up...")
    logger.info("=" * 50)
    
    try:
        logger.info("Initializing Cosmos DB...")
        initialize_cosmos()
        logger.info("✓ Cosmos DB initialized")
        
        logger.info("Loading routes...")
        # Routes should already be loaded
        logger.info("✓ Routes loaded")
        
        logger.info("=" * 50)
        logger.info("STARTUP COMPLETE - Entering running state")
        logger.info("=" * 50)
        
        yield
        
        logger.info("=" * 50)
        logger.info("LIFESPAN: Shutting down...")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"ERROR in lifespan: {e}", exc_info=True)
        raise
    finally:
        logger.info("Cleanup complete")
        logger.info("=" * 50)
```

**Step 2: Run with Different Event Loop Policies**
```powershell
# Test with different event loop policies
cd backend
.\.venv\Scripts\activate

# Test 1: Default
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level debug 2>&1 | Tee-Object debug.log

# Test 2: Windows Selector
python -c "
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import uvicorn
uvicorn.run('main:app', host='127.0.0.1', port=8000, log_level='debug')
" 2>&1 | Tee-Object debug2.log

# Test 3: Remove event loop override from main.py
# Comment out lines 17-18, rerun
```

**Step 3: Run in Docker**
```powershell
# Test in Docker (Linux environment eliminates Windows asyncio issues)
cd backend
docker build -t kraftd-debug .
docker run -p 8000:8000 -e LOG_LEVEL=debug kraftd-debug

# Watch for same shutdown pattern
```

**Step 4: Minimal Test**
```python
# backend/test_minimal.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up")
    yield
    print("Shutting down")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "Hello"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Step 5: Check for Blocking Operations**
```python
# Check if any blocking I/O in startup
# Look for:
# - time.sleep() → should be await asyncio.sleep()
# - synchronous database calls → should be async
# - file I/O without aiofiles → should use aiofiles

# Search:
# git grep "time.sleep" backend/
# git grep "\.get(" backend/main.py  # Sync Cosmos call
```

---

## TESTING STRATEGY

### Phase 1: Setup (1-2 hours)
- [ ] Create directory structure
- [ ] Create conftest.py
- [ ] Create pytest.ini
- [ ] Create pyproject.toml
- [ ] Add development dependencies

### Phase 2: Move Tests (1-2 hours)
- [ ] Move unit tests to tests/unit/
- [ ] Move integration tests to tests/integration/
- [ ] Update imports
- [ ] Add markers (@pytest.mark.unit, etc)
- [ ] Run tests to verify

### Phase 3: Configuration (1 hour)
- [ ] Create mock data helpers
- [ ] Create database fixtures
- [ ] Verify test isolation

### Phase 4: CI/CD (2-3 hours)
- [ ] Create test.yml workflow
- [ ] Create deploy-staging.yml workflow
- [ ] Create deploy-production.yml workflow
- [ ] Add secrets to GitHub
- [ ] Test workflows

---

## ROLLOUT TIMELINE

### Week 1 (5 days)
- **Day 1:** Debug backend stability issue (2-4 hours)
- **Day 1-2:** Reorganize tests (3-4 hours)
- **Day 2-3:** Create CI/CD workflows (6-8 hours)
- **Day 3:** Pin versions, create .env files (3-4 hours)
- **Day 4-5:** Documentation, buffer time

**By End of Week 1:** 
- ✅ Backend stable
- ✅ Tests organized
- ✅ CI/CD ready
- ✅ Ready for staging

### Week 2 (2-3 days)
- **Day 6:** Full testing suite validation
- **Day 7:** Production readiness checklist
- **Day 8:** Deploy to staging

**By End of Week 2:**
- ✅ Staging deployment complete
- ✅ All 4 critical issues fixed
- ✅ Ready for production

---

## SUCCESS CRITERIA

| Milestone | Target | Actual |
|-----------|--------|--------|
| Backend stability | >60s uptime | TBD |
| Tests organized | 100% in /tests/ | TBD |
| CI/CD workflows | 3 files created | TBD |
| Staging deployment | Successful | TBD |
| Code coverage | >80% | TBD |
| Production ready | 85/100 score | TBD |

---

**Generated:** January 18, 2026  
**Status:** READY FOR IMPLEMENTATION  
**Priority:** CRITICAL → Estimate 36-40 hours  

