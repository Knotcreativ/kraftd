# 🔍 OVERLOOKED PREPARATIONS - DETAILED MATRIX

**Prepared:** January 18, 2026  
**Purpose:** Document-by-document inventory of prepared but underutilized systems

---

## 1. AI AGENT INTEGRATION OPPORTUNITY

### Current State
**Status:** ✅ Prepared, 🟡 Partially integrated, 🔴 Not fully exposed

**Files Ready:**
```
✅ backend/agent/kraft_agent.py          - Agent implementation
✅ AGENT_SETUP.md                        - Setup instructions
✅ AGENT_SUMMARY.md                      - Complete documentation
✅ AGENT_PLAN.md                         - Implementation roadmap
✅ AGENT_DEPLOYMENT_STATUS.md            - Deployment status
```

**What Works:**
- Agent runs standalone: `python agent/kraft_agent.py`
- Can be called directly in Python code
- Has complete setup instructions
- Integrated with Azure Foundry

**What's Missing:**
- ❌ No REST API endpoints to call agent
- ❌ Not integrated into `/api/v1/` routing
- ❌ Frontend cannot access agent capabilities
- ❌ No agent status/capabilities endpoints

### Recommended Implementation

**File to Create:** `backend/routes/agent.py`
```python
from fastapi import APIRouter, Depends, UploadFile, File
from models.agent import AgentRequest, AgentResponse
from services.kraft_agent import KraftdAgent

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])

@router.post("/analyze")
async def analyze_with_agent(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> AgentResponse:
    """Analyze document using KraftdIntel AI Agent"""
    agent = KraftdAgent()
    result = await agent.analyze_document(file)
    return AgentResponse(analysis=result)

@router.post("/chat")
async def chat_with_agent(
    message: str,
    context: dict = None,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Interactive chat with agent"""
    agent = KraftdAgent()
    response = await agent.chat(message, context)
    return {"response": response}

@router.get("/status")
async def get_agent_status() -> dict:
    """Get agent capabilities and status"""
    return {
        "status": "active",
        "capabilities": [
            "document_analysis",
            "ai_chat",
            "recommendations",
            "workflow_assistance"
        ],
        "model": "gpt-4o-mini",
        "version": "1.0.0"
    }
```

**Files to Update:**
1. `backend/main.py` - Add agent router: `app.include_router(agent_routes.router)`
2. `frontend/src/services/api.ts` - Add agent API client methods
3. `frontend/src/pages/Dashboard.tsx` - Add agent chat panel

**Effort:** 8-16 hours  
**Impact:** High - Unlocks AI capabilities

---

## 2. PASSWORD RECOVERY & EMAIL VERIFICATION FLOWS

### Current State
**Status:** ✅ Frontend components ready, 🔴 Backend endpoints missing

### Frontend Components Ready
```
✅ frontend/src/pages/ForgotPassword.tsx          (180+ lines)
✅ frontend/src/pages/ForgotPassword.css          (300+ lines)
✅ frontend/src/pages/ResetPassword.tsx           (200+ lines)
✅ frontend/src/pages/ResetPassword.css           (300+ lines)
✅ frontend/src/pages/VerifyEmail.tsx             (200+ lines)
✅ frontend/src/pages/VerifyEmail.css             (300+ lines)
✅ frontend/src/pages/Legal.css                   (200+ lines)
```

### What's Built in Frontend
1. **ForgotPassword.tsx** - Email input, submission handling, success screen
2. **ResetPassword.tsx** - Token verification, new password form, validation
3. **VerifyEmail.tsx** - Email verification with token, resend button
4. **All styled** with animations and responsive design

### What's Missing in Backend

**Endpoint 1: Forgot Password**
```python
# backend/routes/auth.py - ADD THIS:

@router.post("/api/v1/auth/forgot-password")
async def forgot_password(email: str, db: Cosmos = Depends(get_cosmos)) -> dict:
    """
    Send password reset email
    - Verify email exists
    - Generate reset token (unique, 30-min TTL)
    - Send email with reset link
    """
    user = await db.users.find_one({"email": email})
    if not user:
        return {"success": False, "message": "Email not found"}
    
    reset_token = generate_secure_token()
    await db.reset_tokens.insert({
        "token": reset_token,
        "email": email,
        "expires_at": datetime.utcnow() + timedelta(minutes=30),
        "used": False
    })
    
    await send_email(
        to=email,
        subject="Reset Your Kraftd Password",
        template="password_reset",
        reset_url=f"http://frontend/reset-password?token={reset_token}"
    )
    
    return {"success": True, "message": "Check your email"}
```

**Endpoint 2: Reset Password**
```python
@router.post("/api/v1/auth/reset-password")
async def reset_password(token: str, new_password: str, db: Cosmos = Depends(get_cosmos)) -> dict:
    """Verify token and update password"""
    reset_rec = await db.reset_tokens.find_one({"token": token, "used": False})
    
    if not reset_rec or reset_rec["expires_at"] < datetime.utcnow():
        return {"success": False, "message": "Invalid or expired token"}
    
    # Update user password
    user = await db.users.find_one({"email": reset_rec["email"]})
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    
    await db.users.update_one(
        {"email": reset_rec["email"]},
        {"$set": {"password_hash": hashed}}
    )
    
    # Mark token as used
    await db.reset_tokens.update_one(
        {"token": token},
        {"$set": {"used": True}}
    )
    
    return {"success": True, "message": "Password reset successful"}
```

**Endpoint 3: Verify Email**
```python
@router.post("/api/v1/auth/verify-email")
async def verify_email(token: str, db: Cosmos = Depends(get_cosmos)) -> dict:
    """Verify email with token from registration"""
    verify_rec = await db.verification_tokens.find_one({"token": token})
    
    if not verify_rec:
        return {"success": False, "message": "Invalid token"}
    
    await db.users.update_one(
        {"email": verify_rec["email"]},
        {"$set": {"verified": True, "verified_at": datetime.utcnow()}}
    )
    
    return {"success": True, "message": "Email verified successfully"}
```

### Files to Create
```
backend/models/reset_token.py              # Data model
backend/services/email_service.py          # Enhanced (already exists, add templates)
backend/templates/emails/password_reset.html
backend/templates/emails/email_verification.html
```

### Frontend Wiring
- Update `Login.tsx` - Add "Forgot Password?" link
- Update routing to include forgot/reset/verify pages
- Connect form submissions to new endpoints

**Effort:** 16-20 hours  
**Impact:** Medium - Completes user onboarding flows

---

## 3. DOCUMENT TEMPLATE & CONVERSION SYSTEM

### Current State
**Status:** 🟡 Documented but not implemented

**Referenced In:**
- KRAFTD_AI_SPECIFICATION.md - Full specification
- ARCHITECTURE_REVIEW_AND_OPTIMIZATION_ROADMAP.md - Implementation roadmap
- BACKEND_DEVELOPMENT_CHECKLIST.md - Phase 3 requirements

### What Should Be Built

**Files to Create:**
```
backend/models/template.py                  # Template data model
backend/services/conversion_service.py      # Conversion logic
backend/services/template_engine.py         # Jinja2 template rendering
backend/routes/conversions.py               # API endpoints
backend/templates/conversions/               # Jinja2 templates
├── po_to_invoice.jinja2
├── quote_to_csv.jinja2
├── invoice_to_excel.jinja2
├── rfq_to_pdf.jinja2
└── generic.jinja2
```

### API Endpoints Needed

**Endpoint 1: Create Template**
```python
@router.post("/api/v1/conversions/templates")
async def create_template(template: Template) -> dict:
    """Create new conversion template"""
    template_id = await db.templates.insert(template.dict())
    return {"template_id": template_id}
```

**Endpoint 2: List Templates**
```python
@router.get("/api/v1/conversions/templates")
async def list_templates() -> list:
    """List all available templates"""
    return await db.templates.find({}).to_list(None)
```

**Endpoint 3: Apply Template**
```python
@router.post("/api/v1/conversions/execute")
async def execute_conversion(doc_id: str, template_id: str) -> dict:
    """Convert document using template"""
    doc = await db.documents.find_one({"id": doc_id})
    template = await db.templates.find_one({"id": template_id})
    
    result = template_engine.render(template, doc)
    return {
        "converted": result,
        "format": template.output_format
    }
```

**Endpoint 4: Preview**
```python
@router.post("/api/v1/conversions/preview")
async def preview_conversion(doc_id: str, template_id: str) -> dict:
    """Preview conversion without saving"""
    # Same as execute but doesn't save
```

### Data Model

```python
class Template(BaseModel):
    name: str                    # "PO to Invoice"
    description: str
    source_format: str           # Input format
    target_format: str           # Output format (pdf, csv, xlsx, json)
    fields_mapping: dict         # {"PO.vendor": "Invoice.supplier"}
    transformations: dict        # Business logic rules
    template_content: str        # Jinja2 template
    is_built_in: bool           # Built-in vs custom
    created_by: str             # User ID
    created_at: datetime

class ConversionRule(BaseModel):
    source_field: str           # What to read from
    target_field: str           # Where to write to
    transform: str              # "uppercase", "currency", "date_format:YYYY-MM-DD", etc.
    default_value: Optional[str]
    required: bool
```

### Built-in Templates to Include

1. **PO to Invoice**
   - Takes PO data, generates invoice template
   - Maps PO number → Invoice number
   - Adds invoice-specific fields

2. **Quote to CSV**
   - Flattens quote structure to CSV
   - Handles line items as rows
   - Includes totals

3. **Invoice to Excel**
   - Creates formatted Excel workbook
   - Multiple sheets (summary, items, terms)
   - Includes charts/summaries

4. **RFQ to PDF**
   - Professional PDF generation
   - Logo, terms, formatted tables
   - Ready to send

**Effort:** 24-32 hours  
**Impact:** High - Adds document generation capability

---

## 4. OPERATIONS DOCUMENTATION (Directory is Empty)

### Current State
**Status:** 🔴 `/docs/06-operations/` is completely empty

### What Should Be Created

**Files to Create:**

```
docs/06-operations/
├── INCIDENT_RESPONSE_v1.0.md          # What to do when things go wrong
├── MONITORING_RUNBOOK_v1.0.md         # How to monitor the system
├── TROUBLESHOOTING_GUIDE_v1.0.md      # Common issues & fixes
├── MAINTENANCE_SCHEDULE_v1.0.md       # Regular maintenance tasks
├── DISASTER_RECOVERY_v1.0.md          # Backup & recovery procedures
├── ESCALATION_PROCEDURES_v1.0.md      # When & who to contact
└── PERFORMANCE_TUNING_v1.0.md         # Optimization guidelines
```

### File 1: INCIDENT_RESPONSE_v1.0.md

**Should Include:**
```markdown
# Incident Response Procedures

## Severity Levels
- SEV-1: System down, no users can access
- SEV-2: Core feature broken, most users affected
- SEV-3: Feature degraded, some users affected
- SEV-4: Minor issue, workaround available

## Response Timeline
- SEV-1: Respond within 15 min, resolve within 1 hour
- SEV-2: Respond within 30 min, resolve within 4 hours
- SEV-3: Respond within 1 hour, resolve within 24 hours

## Escalation Path
- On-call engineer → Team lead → CTO
- Escalate if: Not resolved in 15 min, customer impact >100 users

## Post-Incident
- RCA (Root Cause Analysis) within 24 hours
- Preventive measures within 1 week
- Update documentation
```

### File 2: MONITORING_RUNBOOK_v1.0.md

**Should Include:**
```markdown
# Monitoring & Alerting Runbook

## Key Metrics
- API latency: Alert if > 1000ms
- Error rate: Alert if > 1%
- Database: Alert if > 80% RU usage
- Auth failures: Alert if > 10/min

## Dashboard Views
- Overview: System health at a glance
- Performance: Latency, throughput, errors
- Usage: Active users, API calls, storage
- Errors: Error logs, stack traces, patterns

## Alert Escalation
- P1: Page on-call immediately
- P2: Email team within 15 min
- P3: Log for review

## Monitoring Tools
- Azure Application Insights (production)
- Log Analytics (queries, trends)
- Azure Monitor (alerts, dashboards)
```

**Effort:** 8-12 hours  
**Impact:** Critical for production operations

---

## 5. FRONTEND TESTING FRAMEWORK

### Current State
**Status:** 🔴 Not implemented

### What's Missing

**Setup Required:**
```bash
cd frontend
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom
npm install --save-dev @vitest/ui jsdom
```

### Test Files to Create

```
frontend/src/__tests__/
├── components/
│   ├── Login.test.tsx           # Auth component tests
│   ├── Dashboard.test.tsx       # Dashboard tests
│   ├── DocumentUpload.test.tsx  # Upload tests
│   └── Layout.test.tsx          # Navigation tests
├── services/
│   └── api.test.ts              # API client tests
├── context/
│   └── AuthContext.test.tsx     # Auth context tests
└── pages/
    ├── Login.test.tsx
    └── Dashboard.test.tsx
```

### Example Test File

**frontend/src/__tests__/components/Login.test.tsx**
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Login from '../../pages/Login';
import { describe, it, expect, vi } from 'vitest';

describe('Login Component', () => {
  it('renders login form', () => {
    render(<Login />);
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  it('submits login form', async () => {
    const mockLogin = vi.fn();
    render(<Login />);
    
    const emailInput = screen.getByPlaceholderText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    const submitBtn = screen.getByText(/sign in/i);
    
    fireEvent.change(emailInput, { target: { value: 'test@test.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitBtn);
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled();
    });
  });
});
```

**Effort:** 20-30 hours for comprehensive coverage  
**Impact:** Medium - Improves code quality

---

## 6. DOCUMENTATION CONSOLIDATION OPPORTUNITY

### Current State
**Status:** 🟡 Excellent content, poor organization

### Analysis of Duplication

**Deployment Documentation** (8 versions):
```
- DEPLOYMENT_CHECKLIST.md (root)
- DEPLOYMENT_GUIDE_v1.0.md (docs/04-deployment/)
- PRIORITY_4_DEPLOYMENT_GUIDE.md (root)
- DEPLOYMENT_QUICK_START.md (root)
- DEPLOYMENT_COMPLETE_SUMMARY.md (root)
- FINAL_DEPLOYMENT_CHECKLIST.md (root)
- PHASE1_CONFIG_EXECUTION.md (root)
- 00_START_LAUNCH_HERE.md (root)
```

**Setup Documentation** (6 versions):
```
- SETUP_GUIDE_v1.0.md (docs/03-development/)
- FRONTEND_SETUP_GUIDE.md (root)
- AGENT_SETUP.md (root)
- 00_START_HERE.md (root)
- README.md (root)
- README_PHASE_1.md (root)
```

### Consolidation Recommendation

**Create unified structure:**
```
/docs/
├── 00-START-HERE.md          # Single entry point
├── 01-project/
├── 02-architecture/
├── 03-development/
├── 04-deployment/
├── 05-testing/
├── 06-operations/
└── INDEX.md                  # Cross-referenced index
```

**Root level only keep:**
```
- README.md (main entry point - redirects to /docs/)
- QUICK_REFERENCE.md (1-page cheat sheet)
- NEXT_STEPS.md (what to do now)
```

**Archive the rest in `/docs/_archive/` with deprecation notice**

**Effort:** 8-12 hours  
**Impact:** Low-medium - Improves usability

---

## 7. WORKFLOW EXPANSION OPPORTUNITIES

### Current State
**Status:** ✅ Core export workflow done, 🟡 Can be expanded

**Current Workflow Types:**
```
✅ Export workflow (4-stage: summary → modifications → final → feedback)
```

**Could Add:**
```
🔴 Approval workflow (document → review → approve/reject → notify)
🔴 Collaboration workflow (document → share → collect feedback → merge)
🔴 Archive workflow (document → archive → restore capability)
🔴 Compliance workflow (document → validate → audit trail)
```

### Implementation Approach

**Generic Workflow Framework:**
```python
class WorkflowEngine:
    """Orchestrate multi-step workflows"""
    
    def create_workflow(self, workflow_type, document, participants):
        """Create new workflow instance"""
    
    def advance_stage(self, workflow_id, next_stage, data):
        """Move to next stage"""
    
    def get_status(self, workflow_id):
        """Get current status"""
    
    def get_history(self, workflow_id):
        """Get all stage transitions"""

class ApprovalWorkflow(WorkflowEngine):
    stages = ["submitted", "review", "approved/rejected", "notified"]

class CollaborationWorkflow(WorkflowEngine):
    stages = ["shared", "feedback_collected", "merged"]
```

**Files to Create:**
```
backend/models/workflow.py
backend/services/workflow_engine.py
backend/routes/workflows.py
```

**Effort:** 20-24 hours  
**Impact:** Medium-high - Extends core capabilities

---

## SUMMARY TABLE: OVERLOOKED PREPARATIONS

| Opportunity | Files Ready | Backend Work | Frontend Work | Total Effort | Priority |
|---|---|---|---|---|---|
| Agent API Integration | 5 files | 16 hrs | 8 hrs | 24 hrs | ⚡⚡⚡ HIGH |
| Password Recovery | 6 components | 12 hrs | 4 hrs | 16 hrs | ⚡⚡ HIGH |
| Template System | Spec only | 28 hrs | 12 hrs | 40 hrs | ⚡⚡ HIGH |
| Operations Docs | 0 files | N/A | 10 hrs | 10 hrs | ⚡⚡⚡ CRITICAL |
| Frontend Tests | 0 files | N/A | 24 hrs | 24 hrs | ⚡ MEDIUM |
| Doc Consolidation | 100+ files | N/A | 10 hrs | 10 hrs | ⚡ LOW |
| Workflow Expansion | Spec only | 20 hrs | 8 hrs | 28 hrs | 🟡 FUTURE |

---

## QUICK REFERENCE: WHICH TO START WITH?

**If you have 1 day:**
→ Implement Operations Documentation (#4)

**If you have 3 days:**
→ #4 + Agent API Integration (#1) 

**If you have 1 week:**
→ #1 + #4 + Password Recovery (#2)

**If you have 2 weeks:**
→ All of #1, #2, #4 + Frontend Tests (#5)

**If you have 4 weeks:**
→ All items above + Template System (#3)

---

**Report Generated:** January 18, 2026  
**Status:** All overlooked items documented and prioritized  
**Ready to:** Select priority and start implementation
