# KraftdIntel ML Model Setup Plan

**Date**: January 18, 2026  
**Status**: Phase 11 - ML Model Integration

---

## 1. RECOMMENDED MODEL ARCHITECTURE

### Multi-Model Strategy for KraftdIntel

```
KraftdIntel Pipeline:
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│        Users upload documents → Submit queries              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Backend (FastAPI) - Router Layer               │
│  • Document Upload Handler                                  │
│  • Query Type Classifier                                    │
│  • Request Validator                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌─────────────┐
   │ Claude  │   │ GPT-4o   │   │ Phi-4-mini  │
   │ Opus 4.5│   │ mini     │   │             │
   │         │   │          │   │             │
   │Doc      │   │Price     │   │Anomaly      │
   │Analysis │   │Forecast  │   │Detection    │
   │Risk     │   │Analytics │   │Real-time    │
   │Extract  │   │Alerts    │   │Processing   │
   └────┬────┘   └────┬─────┘   └─────┬───────┘
        │             │              │
        └─────────────┼──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │  Response Aggregation      │
        │  & Formatting Layer        │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │   Cosmos DB (Persist)      │
        │   Redis Cache (Speed)      │
        └────────────────────────────┘
```

---

## 2. MODEL SELECTION BY USE CASE

### Use Case 1: Document Analysis & Risk Extraction
**Best Model**: Claude Opus 4.5 (Foundry) or Claude Sonnet 4.5

**Why**:
- 200K context window (can process entire documents)
- Excellent code/structured output ability
- Superior at understanding complex procurement documents
- Better at identifying hidden risks

**Implementation**:
```
Input: PDF procurement contract (100+ pages)
Task: Extract risks, validate terms, identify red flags
Output: Structured JSON with risk assessment
```

**Estimated Cost**: $0.02 - $0.10 per document

---

### Use Case 2: Price Trend Prediction & Forecasting
**Best Model**: GPT-5.1 or Claude Sonnet 4.5

**Why**:
- Advanced reasoning for time-series patterns
- Can incorporate multiple factors (supply, demand, seasonality)
- Multi-step logical thinking

**Implementation**:
```
Input: Historical price data + market signals
Task: Predict next 30/90 days prices
Output: Forecasts with confidence intervals
```

**Estimated Cost**: $0.005 - $0.02 per prediction

---

### Use Case 3: Real-time Anomaly Detection & Alerts
**Best Model**: Phi-4-mini-reasoning (Foundry) or GPT-4o mini

**Why**:
- Ultra-fast inference (28.88 output tokens/sec)
- Low cost ($0.1312/1M tokens)
- Minimal latency for real-time processing
- Perfect for edge/on-device deployment

**Implementation**:
```
Input: Live price stream, supplier data, order volumes
Task: Detect anomalies in real-time
Output: Alert triggers with severity levels
```

**Estimated Cost**: $0.001 per anomaly check

---

## 3. DEPLOYMENT OPTIONS

### Option A: Microsoft Foundry (Recommended)
**Advantages**:
- ✅ Full Azure integration
- ✅ Larger context windows
- ✅ Production-ready deployment
- ✅ Better support & SLAs
- ✅ Cosmos DB integration
- ✅ Private endpoints available

**Setup**:
1. Deploy models in Foundry via AI Toolkit
2. Get endpoints and keys
3. Integrate into FastAPI backend

**Cost**: Pay-per-token (varies by model)

---

### Option B: GitHub Models (Free to start)
**Advantages**:
- ✅ Free tier available
- ✅ No deployment needed
- ✅ Simple REST API
- ✅ Good for MVP/testing

**Setup**:
1. Create GitHub Personal Access Token
2. Call API directly from backend
3. Use GitHub PAT for authentication

**Cost**: Free (with rate limits) or paid billing

**Rate Limits (Free)**:
- 100 requests per 15 minutes
- 4,000 tokens per 1 minute

---

## 4. RECOMMENDED SETUP SEQUENCE

### Phase 1: Quick Start (Today - 2 hours)
```
1. Choose GitHub Models for MVP testing
2. Implement basic document analysis
3. Test with sample documents
4. Verify API integration
```

### Phase 2: Production Setup (This week - 4 hours)
```
1. Deploy models to Foundry
2. Configure authentication & endpoints
3. Implement prompt engineering
4. Set up caching layer (Redis)
```

### Phase 3: Advanced Features (Next week - 8 hours)
```
1. Fine-tune models for procurement domain
2. Implement multi-model orchestration
3. Add vector embeddings for similarity
4. Setup evaluation metrics
```

---

## 5. IMPLEMENTATION CHECKLIST

### Backend Integration Points

#### File: `backend/routes/agent.py` (Already exists!)
```python
# What needs to be added:
- Model initialization code
- Request routing based on task type
- Response formatting
- Error handling & retries
- Token counting & cost tracking
```

#### New File: `backend/services/ml_service.py`
```python
# Services to implement:
class DocumentAnalyzer:
    async def analyze(document: str, document_type: str)
    
class PricePredictor:
    async def forecast(historical_prices: List[float], days: int)
    
class AnomalyDetector:
    async def detect(data_point: dict, threshold: float)
```

#### New File: `backend/services/model_orchestrator.py`
```python
# Route requests to appropriate model
class ModelOrchestrator:
    async def process(request: dict) -> dict
    # - Determine best model for task
    # - Handle concurrent requests
    # - Aggregate responses
    # - Cache results
```

---

## 6. STEP-BY-STEP SETUP INSTRUCTIONS

### Step 1: Choose Your Model Host

**Option A: GitHub Models (Quick start)**
```bash
# 1. Create GitHub PAT
#    https://github.com/settings/tokens
#    Scopes: read:user (minimum)

# 2. Set environment variable
$env:GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

**Option B: Microsoft Foundry (Recommended)**
```bash
# 1. Open AI Toolkit Model Catalog
#    VSCode Command: ai-mlstudio.models
#    Filter: Microsoft Foundry

# 2. Deploy chosen model
#    VSCode Command: ai-mlstudio.triggerFoundryModelDeployment
#    Parameters: modelName="claude-opus-4-5"

# 3. Get endpoint and key
#    Save to .env file
```

---

### Step 2: Update Environment Configuration

**File**: `.env`
```bash
# GitHub Models (Option A)
GITHUB_API_KEY=ghp_xxxxxxxxxxxx
MODEL_HOST=github  # or foundry

# Foundry Models (Option B)
FOUNDRY_API_ENDPOINT=https://xxx.api.inference.ai.azure.com
FOUNDRY_API_KEY=xxxxxxxxxxxx
MODEL_HOST=foundry

# Model Selection
DOCUMENT_MODEL=claude-opus-4-5      # For complex document analysis
PRICE_MODEL=gpt-5.1                  # For time-series forecasting
ANOMALY_MODEL=phi-4-mini-reasoning   # For real-time detection

# Cache Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_TTL=3600  # 1 hour

# Cost Tracking
ENABLE_COST_TRACKING=true
COST_ALERT_THRESHOLD=50  # Daily spend limit
```

---

### Step 3: Implement Model Service

**File**: `backend/services/ml_service.py`
```python
from typing import Optional, Dict, List
from datetime import datetime
import os

class MLModelService:
    def __init__(self):
        self.model_host = os.getenv("MODEL_HOST")  # github or foundry
        self.github_token = os.getenv("GITHUB_API_KEY")
        self.foundry_key = os.getenv("FOUNDRY_API_KEY")
        
    async def analyze_document(
        self,
        document_content: str,
        document_type: str = "contract"
    ) -> Dict:
        """Analyze document using Claude Opus 4.5"""
        
        prompt = f"""
        Analyze this {document_type} document and provide:
        1. Key terms and conditions
        2. Identified risks (HIGH, MEDIUM, LOW)
        3. Important dates and deadlines
        4. Cost implications
        5. Recommendations
        
        Document:
        {document_content}
        
        Return as JSON.
        """
        
        response = await self._call_model(
            model="claude-opus-4-5",
            prompt=prompt,
            max_tokens=2000
        )
        
        return self._parse_response(response)
    
    async def predict_prices(
        self,
        item_id: str,
        historical_prices: List[float],
        forecast_days: int = 30
    ) -> Dict:
        """Predict price trends"""
        
        prompt = f"""
        Given historical prices: {historical_prices}
        
        Provide:
        1. Price forecast for next {forecast_days} days
        2. Trend direction (up/down/stable)
        3. Confidence level (0-100%)
        4. Factors affecting prediction
        
        Return as JSON with daily forecasts.
        """
        
        response = await self._call_model(
            model="gpt-5.1",
            prompt=prompt,
            max_tokens=1000
        )
        
        return self._parse_response(response)
    
    async def detect_anomalies(
        self,
        data_point: Dict,
        baseline_stats: Dict
    ) -> Dict:
        """Detect anomalies in real-time data"""
        
        prompt = f"""
        Baseline statistics: {baseline_stats}
        Current data point: {data_point}
        
        Is this an anomaly? 
        - Yes/No
        - Severity: LOW/MEDIUM/HIGH
        - Reason
        - Recommended action
        
        Return as JSON.
        """
        
        response = await self._call_model(
            model="phi-4-mini-reasoning",
            prompt=prompt,
            max_tokens=500
        )
        
        return self._parse_response(response)
    
    async def _call_model(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 1000
    ) -> str:
        """Call the appropriate model based on configuration"""
        
        if self.model_host == "github":
            return await self._call_github_model(model, prompt, max_tokens)
        elif self.model_host == "foundry":
            return await self._call_foundry_model(model, prompt, max_tokens)
    
    async def _call_github_model(self, model: str, prompt: str, max_tokens: int) -> str:
        """Call GitHub Models API"""
        import aiohttp
        
        url = f"https://models.github.ai/inference/{model}"
        headers = {"Authorization": f"Bearer {self.github_token}"}
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
    
    async def _call_foundry_model(self, model: str, prompt: str, max_tokens: int) -> str:
        """Call Azure Foundry Models API"""
        import aiohttp
        
        endpoint = os.getenv("FOUNDRY_API_ENDPOINT")
        headers = {"Authorization": f"Bearer {self.foundry_key}"}
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{endpoint}/chat", json=payload, headers=headers) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
    
    def _parse_response(self, response: str) -> Dict:
        """Parse model response into structured format"""
        import json
        try:
            return json.loads(response)
        except:
            return {"raw_response": response}
```

---

### Step 4: Create Model Orchestrator

**File**: `backend/services/model_orchestrator.py`
```python
from .ml_service import MLModelService
from cache import get_cache, set_cache
import json

class ModelOrchestrator:
    def __init__(self):
        self.ml_service = MLModelService()
        self.cache = get_cache()
    
    async def process_document(self, doc_id: str, content: str, doc_type: str):
        """Process document through analysis pipeline"""
        
        # Check cache first
        cache_key = f"doc_analysis:{doc_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Analyze document
        analysis = await self.ml_service.analyze_document(content, doc_type)
        
        # Cache result (1 hour)
        await self.cache.set(cache_key, json.dumps(analysis), 3600)
        
        return analysis
    
    async def process_price_forecast(self, item_id: str, prices: list):
        """Process price forecasting"""
        
        cache_key = f"forecast:{item_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return json.loads(cached)
        
        forecast = await self.ml_service.predict_prices(
            item_id=item_id,
            historical_prices=prices,
            forecast_days=30
        )
        
        await self.cache.set(cache_key, json.dumps(forecast), 3600)
        
        return forecast
    
    async def check_anomalies(self, data_point: dict, baseline: dict):
        """Real-time anomaly detection (no caching)"""
        
        return await self.ml_service.detect_anomalies(data_point, baseline)
```

---

### Step 5: Update FastAPI Routes

**File**: `backend/routes/agent.py` (Add to existing file)
```python
from services.model_orchestrator import ModelOrchestrator

orchestrator = ModelOrchestrator()

@router.post("/analyze-document")
async def analyze_document(
    document_id: str,
    content: str,
    doc_type: str = "contract",
    authorization: str = Header(None)
):
    """Analyze document for risks and insights"""
    
    # Verify auth token
    user = await verify_bearer_token(authorization)
    
    result = await orchestrator.process_document(document_id, content, doc_type)
    
    return {
        "document_id": document_id,
        "analysis": result,
        "timestamp": datetime.now(),
        "status": "complete"
    }

@router.post("/forecast-prices")
async def forecast_prices(
    item_id: str,
    historical_prices: List[float],
    days: int = 30,
    authorization: str = Header(None)
):
    """Forecast future prices"""
    
    user = await verify_bearer_token(authorization)
    
    forecast = await orchestrator.process_price_forecast(item_id, historical_prices)
    
    return {
        "item_id": item_id,
        "forecast_days": days,
        "forecast": forecast,
        "timestamp": datetime.now()
    }

@router.post("/detect-anomalies")
async def detect_anomalies(
    data: dict,
    baseline: dict,
    authorization: str = Header(None)
):
    """Real-time anomaly detection"""
    
    user = await verify_bearer_token(authorization)
    
    anomaly = await orchestrator.check_anomalies(data, baseline)
    
    return {
        "is_anomaly": anomaly.get("is_anomaly", False),
        "severity": anomaly.get("severity"),
        "reason": anomaly.get("reason"),
        "timestamp": datetime.now()
    }
```

---

## 7. QUICK START GUIDE

### Option 1: GitHub Models (Fastest - 10 minutes)

```bash
# 1. Create GitHub PAT
#    Go to: https://github.com/settings/tokens/new
#    Select: read:user
#    Copy token

# 2. Add to .env
echo "GITHUB_API_KEY=ghp_your_token" >> backend/.env
echo "MODEL_HOST=github" >> backend/.env

# 3. Install dependencies
cd backend
pip install aiohttp openai

# 4. Test it
python -c "
import asyncio
from services.ml_service import MLModelService

ml = MLModelService()
result = asyncio.run(ml.analyze_document('Sample contract text', 'contract'))
print(result)
"
```

### Option 2: Microsoft Foundry (Recommended - 20 minutes)

```bash
# 1. Open AI Toolkit in VS Code
#    Command: ai-mlstudio.models
#    Filter: Microsoft Foundry
#    Select: Claude Opus 4.5 or GPT-5.1

# 2. Deploy the model
#    Command: ai-mlstudio.triggerFoundryModelDeployment
#    Model: claude-opus-4-5

# 3. Get endpoint and key from Azure Portal

# 4. Add to .env
echo "FOUNDRY_API_ENDPOINT=https://xxx.api.inference.ai.azure.com" >> backend/.env
echo "FOUNDRY_API_KEY=your_key" >> backend/.env
echo "MODEL_HOST=foundry" >> backend/.env

# 5. Test integration
python -m pytest backend/test_ml_integration.py
```

---

## 8. COST ESTIMATION

### Monthly Usage Estimate (Small Scale)

| Task | Volume | Model | Cost/Month |
|------|--------|-------|-----------|
| Document Analysis | 100 docs/month | Claude Opus 4.5 | $2-5 |
| Price Forecasts | 1,000 forecasts | GPT-5.1 | $3-8 |
| Anomaly Detection | 10,000 checks | Phi-4-mini | $1-2 |
| **TOTAL** | | | **$6-15/month** |

### Monthly Usage Estimate (Medium Scale - 10x)

| Task | Volume | Model | Cost/Month |
|------|--------|-------|-----------|
| Document Analysis | 1,000 docs/month | Claude Opus 4.5 | $20-50 |
| Price Forecasts | 10,000 forecasts | GPT-5.1 | $30-80 |
| Anomaly Detection | 100,000 checks | Phi-4-mini | $10-20 |
| **TOTAL** | | | **$60-150/month** |

---

## 9. NEXT STEPS

### Immediate (Today)
- [ ] Choose model host (GitHub or Foundry)
- [ ] Get API credentials
- [ ] Test API connection

### Short-term (This week)
- [ ] Implement MLModelService
- [ ] Create ModelOrchestrator
- [ ] Add routes to agent.py
- [ ] Test with sample data

### Medium-term (Next 2 weeks)
- [ ] Fine-tune prompts for procurement domain
- [ ] Add evaluation metrics
- [ ] Implement cost tracking
- [ ] Set up monitoring

### Long-term
- [ ] Build custom models
- [ ] Implement vector embeddings
- [ ] Create domain-specific fine-tuning
- [ ] Set up automated retraining

---

## 10. RESOURCES

- **Microsoft Foundry**: https://ai.azure.com/
- **GitHub Models**: https://github.com/marketplace/models
- **OpenAI API**: https://platform.openai.com
- **Anthropic Claude**: https://claude.ai

---

**Status**: Ready to implement ✅  
**Estimated Setup Time**: 1-2 hours  
**Difficulty**: Intermediate  
