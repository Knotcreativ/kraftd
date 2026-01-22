# Kraftd AI Agent - Implementation Plan

## Vision
Build an intelligent AI agent that understands and orchestrates the entire Kraftd MVP procurement workflow. The agent will make smart decisions, validate documents, recommend actions, and automate procurement processes.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Kraftd AI Agent                          │
│  (Microsoft Agent Framework + Azure OpenAI/Foundry)         │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ┌───▼────┐        ┌────▼────┐       ┌────▼────┐
    │Document │       │Workflow  │       │Analysis  │
    │Tools    │       │Tools     │       │Tools     │
    └────────┘       └──────────┘       └──────────┘
        │                  │                  │
    ┌───▼──────────────────▼──────────────────▼────┐
    │      FastAPI Backend (Existing)               │
    │  - Document Upload & Extraction              │
    │  - Azure Document Intelligence               │
    │  - Workflow Orchestration                    │
    │  - Data Persistence                          │
    └─────────────────────────────────────────────┘
```

## Core Components

### 1. Agent Core
- **Framework**: Microsoft Agent Framework (Python)
- **Model**: Azure OpenAI GPT-4 or Microsoft Foundry model
- **Capabilities**:
  - Multi-turn conversation with context awareness
  - Tool calling (function execution)
  - Agentic loops for complex workflows
  - Thread-based conversation management

### 2. Agent Tools (Functions)

#### Document Management Tools
- `upload_document()` - Ingest documents
- `extract_intelligence()` - Call Azure Document Intelligence
- `validate_document()` - Check quality & completeness
- `get_document_details()` - Retrieve document info
- `list_documents()` - View all documents

#### Workflow Tools
- `create_inquiry()` - Start procurement inquiry
- `process_quotation()` - Analyze quotes
- `compare_quotes()` - Smart comparison
- `create_po()` - Generate purchase order
- `track_progress()` - Monitor workflow state

#### Analysis Tools
- `analyze_supplier()` - Extract supplier signals
- `detect_risks()` - Flag compliance/pricing risks
- `recommend_action()` - Suggest next steps
- `generate_report()` - Create summaries

#### Validation Tools
- `validate_line_items()` - Check quantities, prices, specs
- `validate_commercial_terms()` - Verify payment, delivery, currency
- `validate_parties()` - Confirm vendor/buyer info
- `calculate_total_cost()` - Aggregate pricing

### 3. Domain Knowledge Base
The agent will be trained/instructed with:
- **Procurement Best Practices**: Standard processes, compliance rules
- **Document Patterns**: RFQ/BOQ/PO/Contract structures
- **Commodity Knowledge**: Categories, standard specs
- **Market Knowledge**: Typical pricing, delivery times
- **Risk Patterns**: Red flags, anomalies

### 4. Agent Capabilities

#### Level 1: Document Intelligence
- "Upload this RFQ and extract all line items"
- "Is this quote complete? What's missing?"
- "Compare these 3 quotations and recommend the best"

#### Level 2: Workflow Automation
- "Create a PO from this approved quotation"
- "Process these invoices against the PO"
- "Update me on all open procurement requests"

#### Level 3: Decision Support
- "This supplier is offering 20% discount - is it valid?"
- "Flag any compliance risks in this contract"
- "What's the best payment term option given our cash flow?"

#### Level 4: Strategic Insights
- "Analyze our supplier concentration risk"
- "Which categories could we negotiate better pricing?"
- "Recommend cost optimization opportunities"

## Implementation Phases

### Phase 1: Foundation (Week 1)
1. Set up Microsoft Agent Framework in Python
2. Create Agent class with Azure OpenAI integration
3. Implement 5 core document tools
4. Deploy basic agent with single-turn conversations
5. Test with sample documents

### Phase 2: Expansion (Week 2)
1. Add workflow tools
2. Implement multi-turn conversations
3. Add analysis and validation tools
4. Train agent with domain prompts
5. Build agent interface/dashboard

### Phase 3: Intelligence (Week 3)
1. Add agentic loops for complex decisions
2. Implement conversation threads
3. Add risk detection capabilities
4. Build analytics dashboard
5. Optimize for production

### Phase 4: Optimization (Week 4)
1. Fine-tune model for Kraftd domain
2. Add batch processing
3. Implement caching/optimization
4. Production deployment
5. Monitoring and improvement

## Tech Stack

```
Language: Python 3.13
Framework: Microsoft Agent Framework
Model Host: Azure OpenAI / Microsoft Foundry
LLM: GPT-4 (or equivalent)
Backend API: FastAPI (existing)
Database: PostgreSQL / Cosmos DB (planned)
Deployment: Azure App Service
```

## Installation & Setup

```bash
# Install Agent Framework (--pre is required for preview)
pip install agent-framework-azure-ai --pre

# Install Azure AI client
pip install azure-ai-projects

# Install other dependencies
pip install aiohttp aiofiles
```

## Key Features for MVP

### 1. Smart Document Processing
```
User: "Process this RFQ and tell me what we need to do"
Agent: 
- Uploads document
- Extracts line items, pricing, dates
- Validates completeness
- Identifies missing information
- Recommends next action
```

### 2. Intelligent Comparison
```
User: "Compare these 3 quotations"
Agent:
- Analyzes all 3 documents
- Normalizes pricing (currency, taxes, delivery)
- Flags discrepancies
- Calculates total cost of ownership
- Recommends best option with reasoning
```

### 3. Risk Detection
```
User: "Is there anything unusual about this quotation?"
Agent:
- Checks pricing against benchmarks
- Validates supplier info
- Flags missing standard terms
- Alerts to unusual payment terms
- Recommends due diligence actions
```

### 4. Workflow Automation
```
User: "Create a PO from the approved quotation"
Agent:
- Retrieves quotation data
- Maps to PO template
- Adds company terms
- Generates PO document
- Requests approval
- Creates workflow step
```

## Agent System Prompt (Example)

```
You are Kraftd AI, an intelligent procurement assistant.

Your role is to:
1. Help process and analyze procurement documents (RFQs, BOQs, quotations, POs, contracts)
2. Extract structured data from unstructured documents
3. Validate document completeness and accuracy
4. Compare quotations and recommend best suppliers
5. Detect risks and anomalies
6. Automate procurement workflows
7. Provide strategic insights

You have access to tools that integrate with our backend API.

When processing documents:
- Always validate completeness before proceeding
- Flag missing required information
- Check for pricing anomalies
- Verify supplier information
- Ensure compliance with company policies

When making recommendations:
- Provide reasoning for your suggestions
- Consider total cost of ownership, not just unit price
- Factor in supplier reliability and delivery terms
- Alert to any risks or concerns
- Suggest follow-up actions

Always be proactive in identifying issues and providing solutions.
```

## Success Metrics

- **Document Processing**: 95%+ accuracy on extraction
- **Decision Support**: Agent recommendations accepted >80% of the time
- **Time Savings**: 50% reduction in manual procurement processing
- **Cost Optimization**: 10-15% savings through better supplier selection
- **Risk Reduction**: 100% detection of flagged compliance issues

## Next Steps

1. ✅ Read this plan
2. ⏳ Set up Microsoft Foundry project (if not exists)
3. ⏳ Create agent code structure
4. ⏳ Implement document tools
5. ⏳ Implement workflow tools
6. ⏳ Test with real Kraftd documents
7. ⏳ Deploy and iterate

---

**Decision Point**: Ready to build? Would you like to:
A) Start with Phase 1 implementation
B) Modify the plan first
C) Get more details on specific components
