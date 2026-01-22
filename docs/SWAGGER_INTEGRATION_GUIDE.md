# FastAPI Swagger UI Integration

**Purpose:** Enable automatic OpenAPI documentation and interactive Swagger UI  
**Status:** Ready to integrate into main.py  

---

## Integration Instructions

### Option 1: Add to main.py (Recommended)

Add these parameters to your FastAPI app initialization in main.py:

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Kraftd Intelligence API",
    description="Document processing and procurement workflow automation",
    version="1.0.0-MVP",
    docs_url="/api/docs",           # Swagger UI endpoint
    redoc_url="/api/redoc",         # ReDoc endpoint
    openapi_url="/api/openapi.json" # OpenAPI spec endpoint
)

# Custom OpenAPI schema (optional)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Kraftd Intelligence API",
        version="1.0.0-MVP",
        description="Document processing and procurement workflow automation API",
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Option 2: Configuration with Tags and Groups

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Kraftd Intelligence API",
    version="1.0.0-MVP",
    openapi_tags=[
        {
            "name": "Documents",
            "description": "Document upload, extraction, and management endpoints"
        },
        {
            "name": "Workflows",
            "description": "Procurement workflow automation endpoints"
        },
        {
            "name": "System",
            "description": "System health and metrics endpoints"
        }
    ]
)
```

### Option 3: Custom Swagger UI Configuration

```python
from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
    get_redoc_html
)

app = FastAPI(
    title="Kraftd Intelligence API",
    version="1.0.0-MVP",
    swagger_ui_parameters={
        "deepLinking": True,
        "presets": ["swagger-ui/presets/apis", "swagger-ui/SwaggerUIBundle.presets.layout"],
        "layout": "BaseLayout",
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "syntaxHighlight": {
            "activate": True,
            "theme": "monokai"
        }
    }
)
```

---

## Accessing Documentation

Once integrated, access the documentation at:

1. **Swagger UI (Interactive):**
   ```
   http://localhost:7071/api/docs
   ```

2. **ReDoc (Alternative):**
   ```
   http://localhost:7071/api/redoc
   ```

3. **OpenAPI Schema (JSON):**
   ```
   http://localhost:7071/api/openapi.json
   ```

---

## Adding Route Tags

Tag your endpoints for better organization in Swagger UI:

```python
from fastapi import FastAPI

@app.post("/api/v1/docs/upload", tags=["Documents"])
async def upload_document(file: UploadFile):
    """Upload a PDF document for processing."""
    pass

@app.post("/api/v1/extract", tags=["Documents"])
async def extract_document(request: ExtractionRequest):
    """Extract structured data from document."""
    pass

@app.post("/api/v1/workflow/inquiry", tags=["Workflows"])
async def workflow_inquiry(request: WorkflowRequest):
    """Review and validate inquiry."""
    pass

@app.get("/health", tags=["System"])
async def health_check():
    """Check API health status."""
    pass
```

---

## Response Examples in Code

FastAPI automatically documents response models. Ensure your response models are properly defined:

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    file_size_bytes: int
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "doc-abc123",
                "filename": "invoice.pdf",
                "status": "uploaded",
                "file_size_bytes": 256432,
                "message": "Document uploaded successfully"
            }
        }

@app.post("/api/v1/docs/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile) -> DocumentUploadResponse:
    """Upload a PDF document for processing."""
    pass
```

---

## Error Response Documentation

Document error responses:

```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error": exc.detail,
            "detail": str(exc.detail),
            "request_id": request.headers.get("X-Request-ID", "unknown")
        }
    )
```

---

## Authentication in Swagger UI

Add security scheme to enable token testing in Swagger UI:

```python
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from fastapi import Depends

security = HTTPBearer()

@app.post("/api/v1/docs/upload")
async def upload_document(
    file: UploadFile,
    credentials: HTTPAuthCredentials = Depends(security)
):
    """
    Upload document.
    
    Security: Requires JWT Bearer token
    """
    pass
```

Then click "Authorize" button in Swagger UI and paste your JWT token.

---

## Complete Example Implementation

```python
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json

# Initialize app with documentation
app = FastAPI(
    title="Kraftd Intelligence API",
    description="Document processing and procurement workflow automation",
    version="1.0.0-MVP",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Security
security = HTTPBearer()

# Models
class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    file_size_bytes: int
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "doc-abc123",
                "filename": "invoice.pdf",
                "status": "uploaded",
                "file_size_bytes": 256432
            }
        }

# Routes with tags
@app.get("/health", tags=["System"])
async def health_check():
    """Check API health status"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post(
    "/api/v1/docs/upload",
    response_model=DocumentUploadResponse,
    tags=["Documents"]
)
async def upload_document(
    file: UploadFile = File(...),
    credentials: HTTPAuthCredentials = Depends(security)
):
    """
    Upload a PDF document for processing.
    
    - **file**: PDF file to upload
    - **Security**: Requires JWT Bearer token
    """
    return {
        "document_id": "doc-abc123",
        "filename": file.filename,
        "status": "uploaded",
        "file_size_bytes": 256432
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7071)
```

---

## Verification Checklist

After integration, verify:

- [ ] Swagger UI loads at `/api/docs`
- [ ] ReDoc loads at `/api/redoc`
- [ ] OpenAPI schema loads at `/api/openapi.json`
- [ ] All endpoints are documented
- [ ] Response models display correctly
- [ ] Error codes are documented
- [ ] Authentication button appears
- [ ] Examples display in schema
- [ ] Descriptions are visible
- [ ] Tags organize endpoints logically

---

## Static OpenAPI File

If you prefer to serve a static OpenAPI file instead:

```bash
# Copy openapi.json to a static directory
mkdir -p static
cp openapi.json static/

# Configure FastAPI to serve it
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")

# Update app configuration
app = FastAPI(openapi_url="/static/openapi.json")
```

---

## Next Steps

1. Copy the integration code above into your main.py
2. Add tags and response models to all endpoints
3. Test Swagger UI at `http://localhost:7071/api/docs`
4. Verify all endpoints appear correctly
5. Test authentication flow
6. Generate usage documentation

---

**Status:** Ready for implementation ✅  
**Estimated Integration Time:** 15-20 minutes  
**Files Required:** openapi.json, API_DOCUMENTATION.md, this guide