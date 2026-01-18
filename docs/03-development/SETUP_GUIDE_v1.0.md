# Development Setup Guide

**Version:** 1.0  
**Status:** APPROVED  
**Target Environment:** Local Machine (macOS, Windows, Linux)  
**Last Updated:** 2026-01-17

---

## Prerequisites

### System Requirements
- **OS:** Windows 10+, macOS 11+, or Ubuntu 20.04+
- **RAM:** 8 GB minimum
- **Disk:** 5 GB free space
- **Internet:** Required for cloud service access

### Required Software
- **Python:** 3.13+ (for backend)
- **Node.js:** 18.17+ (for frontend)
- **Git:** 2.40+
- **Docker:** 24.0+ (optional, for local Cosmos DB)
- **Azure CLI:** 2.54+ (for Azure services)

---

## Installation Steps

### 1. Clone Repository

```bash
# Navigate to projects folder
cd ~/Projects  # or C:\Projects on Windows

# Clone repository
git clone https://github.com/your-org/kraftdintel.git
cd kraftdintel

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Backend Setup (FastAPI)

#### Install Python Dependencies

```bash
# Navigate to backend
cd backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m pip list
```

#### Configure Environment Variables

Create `.env` file in `backend/` directory:

```bash
# Database
COSMOS_CONNECTION_STRING=mongodb+srv://username:password@cluster.cosmosdb.azure.com:10255/database?retryWrites=false
COSMOS_DATABASE=kraftdintel

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...

# Document Intelligence
DOCUMENT_INTELLIGENCE_KEY=your_key_here
DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-region.api.cognitive.microsoft.com/

# Authentication
JWT_SECRET_KEY=your-secret-key-at-least-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Logging
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000
```

#### Start Backend Server

```bash
# From backend/ directory with venv activated
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Server running at:
# http://localhost:8000
# API docs at: http://localhost:8000/docs
```

**Notes:**
- `--reload` enables auto-restart on file changes
- Visit http://localhost:8000/docs for interactive API documentation
- If port 8000 is in use, specify different port: `--port 8001`

### 3. Frontend Setup (React/Vite)

#### Install Node Dependencies

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Verify installation
npm list react react-dom
```

#### Configure Environment Variables

Create `.env` file in `frontend/` directory:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# App Configuration
VITE_APP_NAME=KraftdIntel
VITE_APP_VERSION=1.0.0

# Feature Flags (optional)
VITE_ENABLE_LOGGING=true
```

#### Start Frontend Development Server

```bash
# From frontend/ directory
npm run dev

# Server running at:
# http://localhost:5173

# To access:
# Open browser: http://localhost:5173
```

**Notes:**
- Hot module replacement (HMR) enabled - changes appear instantly
- If port 5173 is in use, Vite auto-selects next available port
- Console shows compilation errors in real-time

### 4. Database Setup (Local Development)

#### Option A: Use Cloud Cosmos DB (Recommended)

Use your Azure Cosmos DB instance:
- Update `COSMOS_CONNECTION_STRING` in backend `.env`
- No local setup needed
- Full feature support

#### Option B: Use Azure Cosmos DB Emulator (Offline)

```bash
# Download from: https://aka.ms/cosmosdb-emulator

# Run emulator (Docker recommended):
docker run -p 8081:8081 \
  -e AZURE_COSMOS_EMULATOR=true \
  mcr.microsoft.com/cosmosdb/emulator:latest

# Connection string:
COSMOS_CONNECTION_STRING=mongodb://localhost:27017

# Access emulator UI:
# https://localhost:8081/_explorer/index.html
```

#### Option C: MongoDB Atlas (Community)

```bash
# Create free account: https://www.mongodb.com/cloud/atlas
# Create cluster and get connection string
# Update COSMOS_CONNECTION_STRING in .env
```

---

## Development Workflow

### Running Full Stack Locally

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate  # macOS/Linux
# venv\Scripts\Activate.ps1  # Windows
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
# Opens http://localhost:5173

# Terminal 3: Database (if using emulator)
docker run -p 8081:8081 mcr.microsoft.com/cosmosdb/emulator:latest

# Now all services running:
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
# DB:       mongodb://localhost:27017
```

### Testing Workflow

```bash
# Backend tests
cd backend
pytest tests/ -v
pytest tests/ --cov=.

# Frontend tests
cd frontend
npm run test
npm run test:coverage

# E2E tests (if available)
npm run test:e2e
```

### Code Quality Checks

```bash
# Backend linting
cd backend
flake8 .
black . --check

# Frontend linting
cd frontend
npm run lint
npm run type-check  # TypeScript

# Format code
npm run format
```

### Building for Production

```bash
# Frontend build
cd frontend
npm run build
# Output in: frontend/dist/

# Backend build (containerized)
cd backend
docker build -t kraftdintel:latest .
```

---

## Common Development Tasks

### Creating a New API Endpoint

1. **Create route** in `backend/routes/`:
```python
# backend/routes/new_route.py
from fastapi import APIRouter, Depends
from schemas import NewRequestSchema, NewResponseSchema

router = APIRouter(prefix="/api/v1/new", tags=["new"])

@router.post("/action")
async def perform_action(
    request: NewRequestSchema,
    current_user: User = Depends(get_current_user)
) -> NewResponseSchema:
    # Implementation
    return response
```

2. **Register route** in `backend/main.py`:
```python
from routes import new_route
app.include_router(new_route.router)
```

3. **Add schema** in `backend/schemas.py`:
```python
class NewRequestSchema(BaseModel):
    field: str
    value: int
```

4. **Test via API docs** at http://localhost:8000/docs

### Creating a New Page Component

1. **Create page** in `frontend/src/pages/`:
```typescript
// frontend/src/pages/NewPage.tsx
import { useState, useEffect } from 'react';
import { Layout } from '../components/common/Layout';

export function NewPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Fetch data
  }, []);

  return (
    <Layout>
      <h1>New Page</h1>
      {/* Page content */}
    </Layout>
  );
}
```

2. **Add route** in `frontend/src/App.tsx`:
```typescript
<Route path="/new-page" element={<NewPage />} />
```

3. **Test in browser** at http://localhost:5173/new-page

### Running with Docker Locally

```bash
# Build frontend
cd frontend
npm run build

# Build backend container
cd backend
docker build -t kraftdintel-backend:dev .

# Run all services
docker-compose up --build

# Services accessible at:
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# DB:       localhost:27017
```

---

## Debugging

### Backend Debugging

```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or use VS Code debugger
# Create .vscode/launch.json:
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### Frontend Debugging

```typescript
// Chrome DevTools (F12)
// React DevTools browser extension
// VS Code JavaScript Debugger
// console.log() for quick debugging
```

### Database Debugging

```bash
# MongoDB Compass for visual browsing
# Download: https://www.mongodb.com/products/compass

# CLI access
mongosh "connection-string"
use kraftdintel
db.documents.find().pretty()
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | Use different port: `--port 8001` or kill process |
| Dependencies not found | Delete node_modules/venv, reinstall |
| .env not loading | Restart dev server after creating .env |
| CORS errors | Verify VITE_API_URL matches backend |
| Database connection fails | Check connection string and network |
| JWT token expired | Clear localStorage and re-login |
| Hot reload not working | Restart dev server |

---

## IDE Configuration (VS Code)

### Recommended Extensions
```
ms-python.python
ms-python.vscode-pylance
ms-azuretools.vscode-cosmosdb
esbenp.prettier-vscode
dbaeumer.vscode-eslint
```

### Workspace Settings (`.vscode/settings.json`)
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

---

## Next Steps

1. ✅ Complete setup using these steps
2. ✅ Verify all services running (Frontend, Backend, DB)
3. ✅ Test login at http://localhost:5173
4. ✅ Check API docs at http://localhost:8000/docs
5. ✅ Review [CODING_STANDARDS_v1.0.md](../03-development/CODING_STANDARDS_v1.0.md)
6. ✅ Start working on first feature

---

**Reference:** `/docs/03-development/SETUP_GUIDE_v1.0.md`
