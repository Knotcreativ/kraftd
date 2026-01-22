# AI Model Core Functions: User Handling & Document Intelligence Learning
## Kraftd AI Agent Backend Reference

**Status:** ✅ VERIFIED & COMPLETE  
**Location:** `backend/agent/kraft_agent.py`  
**Date:** January 18, 2026

---

## Overview

Your AI model has been given **two primary functions** for backend operations:

### 1. **`process_message()`** - User Handling & Conversation Management
- Handles all user interactions and messages
- Manages multi-turn conversations
- Supports document context
- Stores conversation history in Cosmos DB
- Returns structured responses with metadata

### 2. **`_learn_from_document_intelligence_tool()`** - Document Intelligence Learning
- Learns patterns from Azure Document Intelligence (ADI) extractions
- Builds knowledge base of document patterns
- Tracks supplier behavior, pricing trends, risks, quality metrics
- Continuously improves by comparing agent vs ADI performance

---

## Function 1: `process_message()` - User Handling

### Signature
```python
async def process_message(
    message: str,
    conversation_id: str,
    document_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
```

### Purpose
Primary API for integrating the AI agent with FastAPI endpoints. Handles all user messages and produces structured responses.

### Parameters

| Parameter | Type | Required | Purpose |
|-----------|------|----------|---------|
| `message` | str | ✅ Yes | User's input message/query |
| `conversation_id` | str | ✅ Yes | Unique identifier for conversation session |
| `document_context` | Dict | ❌ No | Optional context about a document (e.g., `{"document_id": "123"}`) |

### Return Value
```python
{
    "response": str,              # Agent's text response to user
    "reasoning": Optional[str],   # Optional explanation of reasoning
    "metadata": {                 # Response metadata
        "conversation_id": str,
        "document_context": Optional[Dict],
        "tools_used": List[str],
        "timestamp": str (ISO 8601),
        "error": Optional[str]    # If error occurred
    }
}
```

### How It Works

#### Step 1: Retrieve Conversation History
```
↓ Load prior messages (last 5) from Cosmos DB
↓ Build conversation context from previous turns
```

#### Step 2: Prepare Full Message
```
If document_context provided:
  └─ Add document ID to message: "[Document Context: doc_id]\n\nUser message"

If conversation history exists:
  └─ Prepend prior context:
     "Prior conversation context:
      - User: previous_message...
      - Agent: previous_response...
      New user message: {message}"
```

#### Step 3: Run Agent
```
↓ Call agent.run(full_message)
↓ Process through Azure OpenAI with tools
↓ Agent decides which tools to call (if any)
```

#### Step 4: Extract Metadata
```
↓ Determine which tools were used
↓ Extract reasoning (if available)
↓ Compile response metadata
```

#### Step 5: Save Conversation
```
↓ Store in Cosmos DB conversations_container
↓ Include all metadata
↓ Preserve for audit trail and learning
```

#### Step 6: Return Result
```
↓ Return structured response dict
↓ Include conversation context for next turn
```

### Usage Examples

#### Example 1: Simple User Query
```python
response = await agent.process_message(
    message="What are the payment terms in the latest quote?",
    conversation_id="user_123_session_001"
)

# Response:
{
    "response": "Based on the quote, the payment terms are Net 30...",
    "reasoning": None,
    "metadata": {
        "conversation_id": "user_123_session_001",
        "document_context": None,
        "tools_used": [],
        "timestamp": "2024-01-18T10:30:45.123Z"
    }
}
```

#### Example 2: Query with Document Context
```python
response = await agent.process_message(
    message="Analyze this document for risks",
    conversation_id="user_123_session_001",
    document_context={"document_id": "doc_abc123"}
)

# Response:
{
    "response": "Document analysis complete. Found 3 potential risks: 1) Missing payment terms... 2) Unusual pricing... 3) Supplier is new...",
    "reasoning": "Compared against historical patterns for similar suppliers",
    "metadata": {
        "conversation_id": "user_123_session_001",
        "document_context": {"document_id": "doc_abc123"},
        "tools_used": ["_detect_risks_tool", "_analyze_supplier_tool"],
        "timestamp": "2024-01-18T10:31:12.456Z"
    }
}
```

#### Example 3: Multi-turn Conversation
```python
# Turn 1
response1 = await agent.process_message(
    message="Show me quotes from three suppliers",
    conversation_id="user_123_session_001"
)

# Turn 2 - Agent remembers context from Turn 1
response2 = await agent.process_message(
    message="Which one is the best value?",  # Implicitly about the 3 quotes
    conversation_id="user_123_session_001"  # Same session ID
)

# Agent retrieves prior context and answers based on previous quotes
```

### Conversation History Management

#### Retrieval
```python
prior_messages = await agent.get_conversation_history(
    conversation_id="user_123_session_001",
    limit=5  # Last 5 messages
)
```

#### Storage Format (Cosmos DB)
```json
{
    "id": "conv_user_123_session_001_001",
    "conversation_id": "user_123_session_001",
    "user_message": "What are the payment terms?",
    "assistant_response": "Based on the quote, payment terms are...",
    "metadata": {
        "tools_used": ["_get_document_tool"],
        "timestamp": "2024-01-18T10:30:45.123Z",
        "document_context": null
    },
    "_ts": 1705590645
}
```

---

## Function 2: `_learn_from_document_intelligence_tool()` - Document Intelligence Learning

### Signature
```python
async def _learn_from_document_intelligence_tool(
    document_id: str,
    pattern_type: Optional[str] = None
) -> str:
```

### Purpose
Learn from Azure Document Intelligence extraction patterns and build knowledge base. The agent uses this to continuously improve by studying ADI's extractions and building learned patterns.

### Parameters

| Parameter | Type | Required | Purpose |
|-----------|------|----------|---------|
| `document_id` | str | ✅ Yes | ID of document to learn from |
| `pattern_type` | str | ❌ No | Specific pattern to learn (if None, learns all) |

### Supported Pattern Types

| Pattern Type | Purpose | Learns From |
|--------------|---------|-------------|
| `supplier_behavior` | Understand supplier habits | Payment terms, delivery terms, consistency |
| `pricing_trends` | Analyze price patterns | Unit prices, variance, line item counts |
| `risk_indicators` | Identify risky documents | Completeness score, accuracy, quality metrics |
| `document_quality` | Assess document quality | Document type, completeness, extraction quality |
| `market_analysis` | Market intelligence | Supplier trends, total values, currency patterns |

### Return Format

```json
{
    "status": "success|error",
    "document_id": "doc_abc123",
    "learnings": {
        "supplier_behavior": {
            "supplier_name": "ABC Trading LLC",
            "terms_consistency": "stable|variable",
            "payment_terms": "Net 30",
            "delivery_terms": "FOB",
            "confidence_score": 0.95
        },
        "pricing_trends": {
            "avg_price": 150.00,
            "price_variance": 50.00,
            "currency": "AED",
            "number_of_line_items": 5,
            "extraction_confidence": 0.92
        },
        "risk_indicators": {
            "completeness_score": 92,
            "accuracy_score": 88,
            "requires_manual_review": false,
            "di_confidence_threshold": 0.90,
            "high_risk": false
        },
        "document_quality": {
            "document_type": "invoice",
            "completeness": 92,
            "di_extraction_method": "AZURE_DI",
            "di_confidence_overall": 0.90,
            "quality_assessment": "high|medium|low"
        },
        "market_analysis": {
            "supplier": "ABC Trading LLC",
            "document_type": "invoice",
            "total_value": 750.00,
            "currency": "AED",
            "di_extraction_quality": 0.90,
            "analyzed_at": "2024-01-18T10:30:45.123Z"
        }
    },
    "di_confidence": 0.90,
    "message": "Learned patterns from doc_abc123 using Azure Document Intelligence insights"
}
```

### What Gets Learned

#### 1. SUPPLIER BEHAVIOR
```json
{
    "supplier_name": "ABC Trading LLC",
    "terms_consistency": "stable",        // Based on confidence > 0.8
    "payment_terms": "Net 30",
    "delivery_terms": "FOB",
    "confidence_score": 0.95              // ADI's confidence in extraction
}
```
**Purpose:** Predict this supplier's likely terms for future quotes

#### 2. PRICING TRENDS
```json
{
    "avg_price": 150.00,                  // Average unit price across items
    "price_variance": 50.00,              // Range (max - min)
    "currency": "AED",
    "number_of_line_items": 5,
    "extraction_confidence": 0.92         // ADI confidence in line items
}
```
**Purpose:** Detect pricing anomalies in future documents from this supplier

#### 3. RISK INDICATORS
```json
{
    "completeness_score": 92,             // % of expected fields found
    "accuracy_score": 88,                 // ADI's accuracy assessment
    "requires_manual_review": false,      // ADI flagged this?
    "di_confidence_threshold": 0.90,      // When to trust vs question
    "high_risk": false                    // Completeness < 60 OR confidence < 0.6
}
```
**Purpose:** Flag high-risk documents that need manual review

#### 4. DOCUMENT QUALITY
```json
{
    "document_type": "invoice",
    "completeness": 92,
    "di_extraction_method": "AZURE_DI",
    "di_confidence_overall": 0.90,
    "quality_assessment": "high"          // high: > 0.8, medium: > 0.6, low: < 0.6
}
```
**Purpose:** Assess trustworthiness of each document type extraction

#### 5. MARKET ANALYSIS
```json
{
    "supplier": "ABC Trading LLC",
    "document_type": "invoice",
    "total_value": 750.00,
    "currency": "AED",
    "di_extraction_quality": 0.90,
    "analyzed_at": "2024-01-18T10:30:45.123Z"
}
```
**Purpose:** Build market intelligence about suppliers and pricing trends

### How Learning Works

```
Document Flow:
┌─────────────────────────────────────────────────┐
│ User uploads document                           │
└──────────────┬──────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────┐
│ Azure Document Intelligence processes (ADI)      │
│ - Extracts all fields                           │
│ - Assigns confidence scores                     │
│ - Flags data quality issues                     │
└──────────────┬──────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────┐
│ Agent calls: _learn_from_document_intelligence  │
│ - Retrieves ADI's extraction + confidence       │
│ - Analyzes patterns (supplier, pricing, risks)  │
│ - Stores learning patterns in ocr_learning_db   │
│ - Records for future comparison                 │
└──────────────┬──────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────┐
│ Agent compares own extraction vs ADI            │
│ - Measures accuracy differences                 │
│ - Identifies patterns to improve                │
│ - Updates performance_metrics                   │
│ - Records in Cosmos DB learning_data container  │
└─────────────────────────────────────────────────┘
```

### Usage Examples

#### Example 1: Learn All Patterns from Document
```python
result = await agent._learn_from_document_intelligence_tool(
    document_id="doc_invoice_001"
)

# Result includes learnings for:
# - Supplier behavior
# - Pricing trends
# - Risk indicators
# - Document quality
# - Market analysis
```

#### Example 2: Learn Specific Pattern Type
```python
result = await agent._learn_from_document_intelligence_tool(
    document_id="doc_invoice_001",
    pattern_type="supplier_behavior"
)

# Result includes only supplier_behavior learnings
```

#### Example 3: Continuous Learning Loop
```python
# Called automatically for each processed document
documents = ["doc_001", "doc_002", "doc_003"]

for doc_id in documents:
    learning = await agent._learn_from_document_intelligence_tool(
        document_id=doc_id,
        pattern_type="risk_indicators"  # Focus on risks
    )
    
    # Agent now knows which document types are risky
    # Can flag future similar documents
```

---

## Integration Points

### Where These Functions Are Called

#### 1. **process_message()** - Called From:

**FastAPI Backend (main.py)**
```python
@app.post("/api/v1/docs/{document_id}/review")
async def review_document(document_id: str, user_message: str):
    result = await agent.process_message(
        message=user_message,
        conversation_id=f"user_{user_id}_session_{session_id}",
        document_context={"document_id": document_id}
    )
    return result
```

**Export Endpoint**
```python
@app.post("/api/v1/docs/{document_id}/export")
async def export_document(...):
    # AI summary uses process_message
    ai_response = await agent.process_message(
        message=f"Summarize this document...",
        conversation_id=conversation_id,
        document_context={"document_id": document_id}
    )
```

#### 2. **_learn_from_document_intelligence_tool()** - Called From:

**Agent's Process Function** (auto-called)
```python
async def run(self, user_input: str) -> str:
    # When agent needs to learn patterns:
    await self._learn_from_document_intelligence_tool(
        document_id=doc_id,
        pattern_type="pricing_trends"
    )
```

**Manual Learning Call**
```python
# In document review workflow
learning = await agent._learn_from_document_intelligence_tool(
    document_id="doc_abc123",
    pattern_type="risk_indicators"
)
```

---

## Performance Tracking

### Learning Metrics Stored

```python
self.performance_metrics = {
    "ocr_accuracy": [],           # List of OCR accuracy scores
    "extraction_speed": [],       # List of extraction times (ms)
    "field_confidence": {},       # {"field_name": 0.92, ...}
    "document_types": {},         # {"invoice": 0.94, "quote": 0.87, ...}
    "supplier_patterns": {}       # {"supplier_name": {...patterns...}}
}
```

### Methods for Tracking

```python
# Record extraction accuracy
await agent._record_extraction_accuracy(
    document_type="invoice",
    accuracy=0.92,
    source="gpt-4o-mini"
)

# Record supplier patterns
await agent._record_supplier_pattern(
    supplier_name="ABC Trading",
    pattern_data={...}
)

# Get learning insights
insights = await agent.get_learning_insights()
```

---

## Cosmos DB Storage

### Conversations Container
Stores all user messages and agent responses

```json
{
    "id": "conv_user_123_001",
    "conversation_id": "user_123_session_001",
    "user_message": "Compare these quotes",
    "assistant_response": "Quote A is better because...",
    "metadata": {
        "tools_used": ["_compare_quotations_tool"],
        "document_context": {"document_id": "doc_abc"},
        "timestamp": "2024-01-18T10:30:45.123Z"
    },
    "owner_email": "user@example.com",
    "_ts": 1705590645
}
```

### Learning Data Container
Stores learned patterns and performance metrics

```json
{
    "id": "ocr_learning_1705590645",
    "type": "ocr_learning",
    "patterns": {
        "supplier_behavior": {...},
        "pricing_trends": {...},
        "risk_indicators": {...}
    },
    "timestamp": "2024-01-18T10:30:45.123Z"
}
```

---

## Complete Data Flow Diagram

```
User Input
    ↓
┌─────────────────────────────────────┐
│ process_message()                   │
│ - User: "Compare quotes"            │
│ - Conv ID: user_123_session_001     │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│ 1. Load Conversation History        │
│    (Last 5 messages from Cosmos DB) │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│ 2. Add Document Context             │
│    (if provided)                    │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│ 3. run() - Execute Agent            │
│    - OpenAI with tools              │
│    - Decide which tools to call     │
└──────────┬──────────────────────────┘
           │
           ├─→ Tool: _compare_quotations_tool
           │       ↓
           │   Analyze quotes
           │       ↓
           │   Return comparison
           │
           ├─→ Tool: _detect_risks_tool
           │       ↓
           │   Find anomalies
           │       ↓
           │   Return risks
           │
           └─→ Tool: _learn_from_document_intelligence_tool
                   ↓
               ┌─────────────────────────────────────┐
               │ Learning Process:                   │
               │ 1. Get ADI extraction data          │
               │ 2. Extract patterns:                │
               │    - Supplier behavior              │
               │    - Pricing trends                 │
               │    - Risk indicators                │
               │    - Document quality               │
               │    - Market analysis                │
               │ 3. Store in ocr_learning_db         │
               │ 4. Record performance metrics       │
               │ 5. Update learning_data in Cosmos   │
               └─────────────────────────────────────┘
                           ↓
           ↓
┌─────────────────────────────────────┐
│ 4. Extract Metadata                 │
│    - Tools used                     │
│    - Reasoning                      │
│    - Timestamp                      │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│ 5. Save to Cosmos DB                │
│    conversations_container          │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│ 6. Return Response                  │
│    {                                │
│      "response": "...",             │
│      "reasoning": "...",            │
│      "metadata": {...}              │
│    }                                │
└─────────────────────────────────────┘
           ↓
     User sees response
```

---

## Summary

### `process_message()` - User Handling
- ✅ Handles all user queries and messages
- ✅ Manages multi-turn conversations
- ✅ Stores conversation history in Cosmos DB
- ✅ Supports document context
- ✅ Returns structured responses with metadata
- **Use Case:** Every user interaction with the AI

### `_learn_from_document_intelligence_tool()` - Document Learning
- ✅ Learns from Azure Document Intelligence extractions
- ✅ Builds 5 types of pattern knowledge (supplier, pricing, risk, quality, market)
- ✅ Tracks performance metrics vs ADI
- ✅ Improves future document analysis
- **Use Case:** Continuous AI improvement and pattern recognition

### Key Benefits
1. **User Experience:** process_message() ensures personalized, context-aware responses
2. **AI Improvement:** Learning tool ensures agent gets smarter with every document
3. **Data Persistence:** Both functions store data in Cosmos DB for audit trail
4. **Pattern Recognition:** Agent learns supplier habits, pricing norms, risk indicators
5. **Quality Assurance:** Comparison with ADI keeps agent calibrated

---

## Next Steps for Integration

1. ✅ Verify both functions are callable from FastAPI endpoints
2. ✅ Ensure Cosmos DB containers exist (conversations, learning_data)
3. ✅ Test process_message() with sample user queries
4. ✅ Test _learn_from_document_intelligence_tool() with real documents
5. ✅ Monitor learning metrics over time
6. ✅ Evaluate agent accuracy vs ADI accuracy
7. ✅ Refine patterns based on collected data
