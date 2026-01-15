# 🗺️ COMPREHENSIVE TRANSITION ANALYSIS & ROADMAP

**Date:** January 15, 2026  
**Application:** Kraftd Intel - Procurement Document Processing  
**Current Status:** App Service F1 + Container Registry  
**Goal:** Minimize costs while maintaining functionality  

---

## 📊 CURRENT INFRASTRUCTURE AUDIT

### Azure Resources Currently Deployed

| Resource | Type | SKU | Status | Cost/Month |
|----------|------|-----|--------|-----------|
| **kraftdintel-plan** | App Service Plan | F1 | Succeeded | $0 (Free) |
| **kraftdintel-app** | Web App | F1 | Succeeded | $0 (Free) |
| **kraftdintel** | Container Registry | Standard | Succeeded | $0 (12-mo trial) |
| **kraftdintelacr** | Container Registry | Standard | Succeeded | $0 (duplicate?) |
| **TOTAL** | - | - | - | **$0/month (trial period)** |

**⚠️ ISSUE IDENTIFIED:** You have TWO container registries! (`kraftdintel` and `kraftdintelacr`)

---

## 💻 APPLICATION ARCHITECTURE ANALYSIS

### Code Structure
```
KraftdIntel/
├── backend/
│   ├── main.py (722 lines)
│   │   ├── FastAPI application
│   │   ├── Async request handling
│   │   ├── Health checks (/health, /health/ready)
│   │   ├── Metrics endpoints (/metrics)
│   │   ├── Document processing API (/api/documents/process)
│   │   ├── Rate limiting middleware
│   │   └── Uvicorn ASGI server
│   ├── Dockerfile (multi-stage build)
│   ├── requirements.txt (18 packages)
│   └── document_processing/
│       ├── orchestrator.py (ExtractionPipeline)
│       ├── processors (PDF, Word, Excel, Image)
│       ├── extractors
│       ├── azure_service.py (Document Intelligence integration)
│       └── validators
├── host.json (Azure Functions config?)
├── local.settings.json (local dev config)
└── requirements.psd1 (PowerShell module manifest?)
```

### Key Application Characteristics

**✅ STRENGTHS:**
- Async/await architecture (efficient for I/O)
- Comprehensive error handling
- Health checks built-in
- Metrics/monitoring endpoints
- Rate limiting middleware
- Multiple document format support (PDF, Word, Excel, Images)
- Azure Document Intelligence integration
- Tesseract OCR fallback

**⚠️ CONSIDERATIONS:**
- FastAPI specific (ties to ASGI server)
- 18 package dependencies
- Requires Python 3.13
- Heavy libraries: `pytesseract`, `pdfplumber`, `azure-*`
- ~803 MB Docker image

---

## 🐳 DOCKER CONTAINERIZATION ANALYSIS

### Dockerfile Structure
**Multi-stage build:** Builder + Runtime (optimized)
- **Stage 1:** Installs dependencies in `/root/.local`
- **Stage 2:** Copies only installed packages, not build tools

**Runtime Dependencies:**
```
tesseract-ocr (OCR engine)
libtesseract-dev (OCR library)
libsm6, libxext6, libxrender-dev (image processing)
```

**Container Metadata:**
- Base image: `python:3.13-slim`
- Working directory: `/app`
- Upload directory: `/tmp/kraftd_uploads`
- Health check: HTTP GET to `http://localhost:8000/health`
- Exposed port: 8000 (from requirements.txt)

**Image Size:** ~803 MB (from deployment logs)

---

## 🏗️ APPLICATION ENTRY POINT

### Current FastAPI Setup
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown handler"""
    # Validates configuration
    # Initializes Azure Document Intelligence
    # Creates upload directory
    # Validates extraction pipeline
    # Logs startup metrics
```

### HTTP Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check (returns 200) |
| `/health/ready` | GET | Readiness probe |
| `/metrics` | GET | Prometheus metrics |
| `/api/documents/process` | POST | Document processing |
| (others) | (various) | Supporting endpoints |

**Request Flow:**
1. Upload file (multipart form-data)
2. ExtractionPipeline processes document
3. Returns extracted data as JSON

---

## 📦 DEPENDENCY ANALYSIS

### Critical Dependencies
```
FastAPI       - Web framework
uvicorn       - ASGI server
pydantic      - Data validation
pdfplumber    - PDF extraction
python-docx   - Word document processing
openpyxl      - Excel processing
pytesseract   - OCR wrapper
pillow        - Image processing
pandas        - Data manipulation
azure-ai-documentintelligence - Azure Document Intelligence SDK
azure-storage-blob - Blob storage access
azure-identity - Azure authentication
```

**Size Impact:** ~300 MB of the 803 MB image

---

## 🔄 TRANSITION IMPACT ANALYSIS

### Option 1: Azure Container Instances (Recommended - Fastest)

**Configuration:**
- Replace App Service Plan with Container Instances
- Keep Docker image as-is
- Keep Container Registry (single instance)
- Add managed identity for ACR access

**Impact:**
| Aspect | Impact | Details |
|--------|--------|---------|
| **Code** | ✅ ZERO changes | FastAPI runs as-is |
| **Docker Image** | ✅ NO changes | Use existing 803 MB image |
| **Deployment** | ⏱️ 5 minutes | Just delete App Service, create Container Instance |
| **Costs** | 💰 ~$15/month | Pay-per-use model (~$0.00324/hour running) |
| **Always-on** | ❌ NO | Runs on-demand only |
| **Scaling** | ❌ Manual | No auto-scaling |
| **Cold Start** | ⏱️ 30-60 sec | Container spin-up time |

**Configuration Example:**
```bash
az container create \
  --resource-group kraftdintel-rg \
  --name kraftdintel-aci \
  --image kraftdintel.azurecr.io/kraftd-backend:latest \
  --cpu 1 --memory 1.5 \
  --ports 8000 \
  --environment-variables LOG_LEVEL=INFO \
  --registry-login-server kraftdintel.azurecr.io \
  --registry-username {acr-user} \
  --registry-password {acr-password}
```

**✅ Pros:**
- Quickest to implement
- No code changes
- Cheaper than App Service B1 ($12.50/mo)
- Simple management

**❌ Cons:**
- Not always-on (won't work for 24/7 API)
- Cold start delays (30-60 seconds)
- Manual restart if container fails
- No auto-scaling

---

### Option 2: Azure Container Apps (Recommended - Best Balance)

**Configuration:**
- Replace App Service with Container Apps
- Keep Docker image as-is
- Keep Container Registry
- Add managed identity for ACR access
- Enable auto-scaling

**Impact:**
| Aspect | Impact | Details |
|--------|--------|---------|
| **Code** | ✅ ZERO changes | FastAPI runs as-is |
| **Docker Image** | ✅ NO changes | Use existing 803 MB image |
| **Deployment** | ⏱️ 10 minutes | Create environment, then container app |
| **Costs** | 💰 ~$25-40/month | Always-on + compute time |
| **Always-on** | ✅ YES | Persistent running instance |
| **Scaling** | ✅ AUTO | Scales 0-10 instances automatically |
| **Cold Start** | ⏱️ None | Warm instance ready |

**Configuration Example:**
```bash
# Create Container Apps environment
az containerapp env create \
  --name kraftdintel-env \
  --resource-group kraftdintel-rg \
  --location uaenorth

# Create container app
az containerapp create \
  --name kraftdintel-app \
  --resource-group kraftdintel-rg \
  --environment kraftdintel-env \
  --image kraftdintel.azurecr.io/kraftd-backend:latest \
  --cpu 0.5 --memory 1.0Gi \
  --target-port 8000 \
  --registry-server kraftdintel.azurecr.io \
  --registry-username {acr-user} \
  --registry-password {acr-password} \
  --scale-min-replicas 1 --scale-max-replicas 3
```

**✅ Pros:**
- Always-on, production-ready
- Auto-scaling for concurrent uploads
- No code changes
- Better than App Service B1
- VNET integration available
- Managed Kubernetes underneath

**❌ Cons:**
- Costs ~$25-40/month (more than App Service F1 but less than B1)
- Requires Container Apps environment setup
- Slightly more complex than App Service

---

### Option 3: Azure Functions (Recommended - Lowest Cost)

**Configuration:**
- Refactor FastAPI → Azure Functions
- Use Consumption plan (free tier)
- Keep Document Intelligence
- Deploy managed functions

**Impact:**
| Aspect | Impact | Details |
|--------|--------|---------|
| **Code** | 🔴 MAJOR refactor | Convert FastAPI routes → Functions |
| **Docker Image** | 🔴 Not needed | Deploy Python functions directly |
| **Deployment** | ⏱️ 1-2 weeks | Refactoring time |
| **Costs** | 💰 $0/month | Free tier: 1M requests/month |
| **Always-on** | ✅ YES | Event-driven, auto-scaling |
| **Scaling** | ✅ INFINITE | Auto-scales to 200+ instances |
| **Cold Start** | ⚠️ 2-5 sec | Consumption plan (acceptable) |

**Code Refactoring Required:**

**Current (FastAPI):**
```python
@app.post("/api/documents/process")
async def process_document(file: UploadFile = File(...)):
    # 100+ lines of processing
    return {"status": "success", "data": results}
```

**Refactored (Azure Functions):**
```python
import azure.functions as func

async def document_process(req: func.HttpRequest) -> func.HttpResponse:
    # Same 100+ lines of processing
    return func.HttpResponse(json.dumps(results), status_code=200)
```

**Effort Estimation:**
- Refactor main.py: ~4 hours
- Test endpoints: ~2 hours
- Deploy to Functions: ~2 hours
- **Total: 1-2 days of development**

**✅ Pros:**
- Completely FREE for moderate usage
- Infinite auto-scaling
- Built-in observability
- Serverless (no infrastructure management)
- Global distribution
- Saves $300/year

**❌ Cons:**
- Requires code refactoring
- Testing effort
- Dependency on Azure Functions runtime
- 45-second timeout per request (your OCR should fit)

---

## 🎯 RECOMMENDED TRANSITION PATH

### Immediate Term (This Week)
**Do this NOW to avoid costs:**

#### Step 1: Clean Up Duplicate Resources
```bash
# Delete duplicate container registry (if not needed)
az acr delete --resource-group kraftdintel-rg --name kraftdintelacr --yes

# Keep: kraftdintel (Standard, has your image)
```

#### Step 2: Choose Your Path Based on Timeline

**If you want IMMEDIATE savings (1 day):**
→ **Use Container Apps (Option 2 - RECOMMENDED)**
- No code changes
- Always-on, production-ready
- ~$25-40/month (acceptable for production)
- 10 minutes to deploy

**If you have 1-2 weeks:**
→ **Use Azure Functions (Option 3 - BEST VALUE)**
- Refactor FastAPI to Functions
- $0/month (free tier)
- Saves $300/year vs paid solutions
- Requires development effort

**If you need maximum flexibility:**
→ **Use Container Instances (Option 1 - CHEAPEST IF NOT RUNNING 24/7)**
- Pay only when processing documents
- No always-on costs
- Good for batch processing

---

### Medium Term (Next 2 Weeks)

#### If you chose Container Apps:
1. Monitor performance metrics
2. Fine-tune scaling rules
3. Set up Application Insights
4. Configure alerts

#### If you chose Functions:
1. Run migration of remaining endpoints
2. Set up CI/CD pipeline
3. Configure storage bindings
4. Set up monitoring

---

### Long Term (Ongoing)

**Optimize based on actual usage:**
- If free tier Functions sufficient: Stay on Functions (~$0/month)
- If need more scale: Move to Functions Premium (~$30/month)
- If need containers: Container Apps (~$25-40/month)
- Never use App Service B1 or higher ($12.50+/month minimum)

---

## 📋 TRANSITION CHECKLIST

### Pre-Transition (Today)
- [ ] Backup current App Service configuration
- [ ] Document current environment variables
- [ ] Test Docker image locally
- [ ] Verify Container Registry has latest image
- [ ] Delete duplicate container registry

### Transition (Choose One Path)

**Container Apps Path (Recommended for Quick Win):**
- [ ] Create Container Apps environment
- [ ] Create container app from Docker image
- [ ] Configure managed identity
- [ ] Test `/health` endpoint
- [ ] Test `/api/documents/process` endpoint
- [ ] Update DNS/load balancer if needed
- [ ] Delete old App Service Plan
- [ ] Delete old Web App

**Azure Functions Path (Recommended for Cost Savings):**
- [ ] Create Python Functions project
- [ ] Convert FastAPI routes to Functions
- [ ] Add bindings (blob storage, etc.)
- [ ] Test locally with `func start`
- [ ] Deploy to Azure
- [ ] Configure environment variables
- [ ] Test endpoints
- [ ] Set up CI/CD
- [ ] Delete Docker image (optional)

**Container Instances Path (On-Demand Processing):**
- [ ] Create container instance
- [ ] Configure registry credentials
- [ ] Start container
- [ ] Test endpoints
- [ ] Set up restart policy
- [ ] Delete App Service

### Post-Transition
- [ ] Monitor performance metrics
- [ ] Verify logs are flowing
- [ ] Check error rates
- [ ] Monitor costs in Azure Portal
- [ ] Set up billing alerts

---

## 💰 COST PROJECTION

### Next 12 Months

**Current Plan (App Service F1):**
- 0 months at F1: $0/month = $0
- 12 months at $12.50/month = $150 (after trial period)
- **Total: $150/year**

**Container Apps (Recommended):**
- Always-on + compute: ~$30/month
- Container Registry: ~$100/month (after trial)
- **Total: ~$156/month = $1,872/year** ❌ More expensive

**Azure Functions (Recommended):**
- Free tier: $0/month (first 1M requests)
- Container Registry: ~$100/month (after trial)
- **Total: ~$100/month = $1,200/year** after 12-month trial

**Optimized Hybrid:**
- Move image to Docker Hub: $0/month
- Azure Functions Consumption: $0/month (free tier)
- Delete Container Registry: $0/month
- **Total: $0/month = $0/year** ✅ 100% FREE

---

## 🚀 MY RECOMMENDATION

### Best Overall: **Azure Container Apps**
**Timeline:** 2-3 hours  
**Cost:** ~$25-40/month  
**Risk:** Very low (simple migration)  
**Benefit:** Production-ready, auto-scaling, no code changes

**Why:**
1. ✅ Fastest to implement (no refactoring)
2. ✅ Always-on for API requests
3. ✅ Auto-scaling for traffic spikes
4. ✅ Better than App Service B1 in every way
5. ✅ Acceptable monthly cost ($25-40 for production)
6. 📈 Easy to monitor and debug

**Execution:**
```bash
# 1. Clean up
az acr delete --resource-group kraftdintel-rg --name kraftdintelacr --yes

# 2. Create environment
az containerapp env create --name kraftdintel-env \
  --resource-group kraftdintel-rg --location uaenorth

# 3. Create app
az containerapp create --name kraftdintel-app \
  --resource-group kraftdintel-rg --environment kraftdintel-env \
  --image kraftdintel.azurecr.io/kraftd-backend:latest \
  --cpu 0.5 --memory 1.0Gi --target-port 8000

# 4. Delete old resources
az appservice plan delete --resource-group kraftdintel-rg \
  --name kraftdintel-plan --yes
az webapp delete --resource-group kraftdintel-rg \
  --name kraftdintel-app --yes
```

---

## 📞 DECISION NEEDED

**Which path do you prefer?**

1. **Container Apps** (~$25-40/month) - *RECOMMENDED*
   - No code changes, fastest deployment, production-ready

2. **Azure Functions** (~$0/month after refactoring)
   - Requires 1-2 weeks of development, completely free

3. **Container Instances** (~$15/month, pay-per-use)
   - Quick deployment, cheapest if not running 24/7

4. **Stay on App Service F1** (problematic)
   - Can't run Docker containers natively
   - Would need to upgrade to B1 ($12.50/month) anyway

**I recommend: Option 1 (Container Apps) for the best balance of speed, cost, and reliability.**

Ready to proceed?
