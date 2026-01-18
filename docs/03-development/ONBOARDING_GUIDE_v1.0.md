# Onboarding Guide

**Version:** 1.0  
**Status:** APPROVED  
**Target Audience:** New team members  
**Estimated Time:** 3 days to full productivity  
**Last Updated:** 2026-01-17

---

## Welcome to KraftdIntel! 👋

This guide helps new team members get productive quickly. Estimated time to first contribution: **3 days**.

---

## Day 1: Getting Started

### Morning: Account Setup & Access

**Accounts to Create/Obtain:**

1. **GitHub** (if not already member)
   - Ask your manager for invitation to `your-org/kraftdintel`
   - Link your Git client: `git config --global user.name "Your Name"`
   - Add SSH key to GitHub

2. **Azure Portal Access**
   - Ask manager for access to Azure subscription
   - Create account or use corporate credentials
   - Request role: Contributor (minimum)

3. **Key Vault Credentials**
   - Once Azure access approved, request access to:
     - Resource group: `kraftdintel`
     - Key Vault: `kraftdintel-kv`
     - Confirm you can read secrets

4. **GitHub Codespaces** (Optional)
   - You can develop in browser: https://codespaces.github.com
   - Or follow local setup below

### Mid-Morning: Local Development Setup

**Follow the setup guide:**

```bash
# Read: /docs/03-development/SETUP_GUIDE_v1.0.md

# Clone repository
git clone https://github.com/your-org/kraftdintel.git
cd kraftdintel

# Choose your path:
# - Backend developer? Follow Python setup
# - Frontend developer? Follow Node.js setup
# - Both? Follow both

# Estimated time: 30 minutes
```

**Verify setup works:**
```bash
# Backend check
curl -i http://localhost:8000/health
# Should return: {"status": "healthy"}

# Frontend check
open http://localhost:5173
# Should show login page
```

### Afternoon: Codebase Tour

**Read these documents in order:**

1. [SYSTEM_ARCHITECTURE_v1.0.md](../../02-architecture/SYSTEM_ARCHITECTURE_v1.0.md) (15 min)
   - High-level overview
   - Component breakdown
   - Data flows

2. [BACKEND_ARCHITECTURE_v1.0.md](../../02-architecture/BACKEND_ARCHITECTURE_v1.0.md) (20 min)
   - Project structure
   - Service layers
   - Key modules

3. [FRONTEND_ARCHITECTURE_v1.0.md](../../02-architecture/FRONTEND_ARCHITECTURE_v1.0.md) (15 min)
   - Page organization
   - Component structure
   - State management

4. [DATABASE_SCHEMA_v1.0.md](../../02-architecture/DATABASE_SCHEMA_v1.0.md) (15 min)
   - Collections overview
   - Key relationships
   - Indexing strategy

### Late Afternoon: Code Review

**Watch the codebase:**

```bash
# Backend structure
tree -L 2 backend/
# Observe:
# - /routes - API endpoints
# - /services - Business logic
# - /repositories - Data access

# Frontend structure  
tree -L 2 frontend/src/
# Observe:
# - /pages - Page components
# - /components - Reusable UI
# - /services - API client
# - /hooks - Custom hooks
```

**Run your first test:**
```bash
# Backend
cd backend
pytest tests/test_auth.py -v

# Frontend
cd frontend
npm run test -- DocumentCard.test.tsx
```

---

## Day 2: Feature Understanding & First Contribution

### Morning: Feature Review

**Understand the 10 core features:**

Read: [FEATURE_SPECIFICATIONS_v1.0.md](../../01-project/FEATURE_SPECIFICATIONS_v1.0.md)

Each feature has:
- Functional requirements
- API endpoints
- Database schema
- Success criteria

**Pick 2-3 features closest to your work.**

### Mid-Morning: First Pull Request (Backend Example)

**Setup your branch:**
```bash
git checkout -b feature/your-feature-name
# Branch naming: feature/, fix/, docs/, chore/
```

**Make a small change:**
```python
# Example: Add a log statement or optimize a query

# In backend/services/document_service.py
import logging
logger = logging.getLogger(__name__)

async def extract_document(document_id: str):
    logger.info(f"Extracting document: {document_id}")
    # ...
```

**Commit with clear message:**
```bash
git add backend/services/document_service.py
git commit -m "feat(extraction): add logging for debugging"
git push origin feature/your-feature-name
```

**Create Pull Request:**
- Go to GitHub
- Click "Compare & pull request"
- Fill in title & description
- Link related issue (if any)
- Request review from a teammate

### Mid-Morning: First PR (Frontend Example)

**Make a UI improvement:**
```typescript
// Example: Improve button styling
// In frontend/src/components/ui/Button.tsx

const Button = ({ variant = 'primary', disabled = false, ...props }) => (
  <button
    className={`btn btn-${variant} ${disabled ? 'disabled' : ''}`}
    disabled={disabled}
    {...props}
  />
);
```

**Submit PR same as backend.**

### Afternoon: Code Review Practice

**Review someone else's PR:**

1. Find an open PR in GitHub
2. Read the changes
3. Check:
   - Does it match the description?
   - Are there tests?
   - Does it follow [CODING_STANDARDS_v1.0.md](../CODING_STANDARDS_v1.0.md)?
   - Any edge cases missed?
4. Leave constructive comments
5. Approve or request changes

**Time:** 30-45 minutes

### Late Afternoon: Debugging Practice

**Debug an API call:**

```bash
# Start backend with debug logging
cd backend
LOG_LEVEL=DEBUG uvicorn main:app --reload

# Try calling an endpoint and watch logs
curl -X GET http://localhost:8000/api/v1/documents/abc123 \
  -H "Authorization: Bearer <token>"

# Examine logs for:
# - Request received
# - Parameters parsed
# - Database query
# - Response sent
```

---

## Day 3: Deep Dive & Productivity

### Morning: Testing Knowledge

**Understanding test structure:**

Read: [TEST_PLAN_v1.0.md](../../05-testing/TEST_PLAN_v1.0.md)

**Write your first test:**

Backend (pytest):
```python
# backend/tests/test_my_service.py
import pytest
from services.my_service import MyService

class TestMyService:
    @pytest.fixture
    def service(self):
        return MyService()
    
    @pytest.mark.asyncio
    async def test_my_function(self, service):
        result = await service.my_function()
        assert result is not None
```

Frontend (Jest):
```typescript
// frontend/src/components/MyComponent.test.tsx
import { render, screen } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText(/expected text/i)).toBeInTheDocument();
  });
});
```

### Mid-Morning: Documentation Review

**Key documents to understand:**

1. [CODING_STANDARDS_v1.0.md](../CODING_STANDARDS_v1.0.md) (20 min)
   - Code style rules
   - Type hints requirements
   - Component patterns

2. [SECURITY_CHECKLIST_v1.0.md](../../02-architecture/SECURITY_CHECKLIST_v1.0.md) (15 min)
   - Security practices
   - Authentication/authorization
   - Data protection

3. [TROUBLESHOOTING_RUNBOOK_v1.0.md](../../04-deployment/TROUBLESHOOTING_RUNBOOK_v1.0.md) (15 min)
   - Common issues
   - Debugging techniques
   - Where to find logs

### Mid-Day: Team Sync

**Attend team standup** (if available)
- Understand current sprint
- Learn about blockers
- Discover team dynamics

### Afternoon: First Meaningful Issue

**Find an issue to work on:**

1. Go to GitHub Issues
2. Filter: label:beginner, label:good-first-issue
3. Pick one that interests you
4. Comment: "I'll take this"
5. Implement the fix following [CODING_STANDARDS_v1.0.md](../CODING_STANDARDS_v1.0.md)

**Types of good starter issues:**
- Bug fixes (low risk)
- Documentation improvements
- Test coverage gaps
- Small feature enhancements
- Refactoring suggestions

### Late Afternoon: Architecture Deepdive

**Understand a feature end-to-end:**

Example: Document Upload Flow

**Frontend → Backend → Database journey:**

```
1. User clicks upload button
   File: frontend/src/pages/UploadDocument.tsx
   
2. File submitted to API
   Endpoint: POST /api/v1/documents/upload
   File: backend/routes/documents.py
   
3. Backend validates & stores
   Service: DocumentService.upload_document()
   File: backend/services/document_service.py
   
4. File saved to Blob Storage
   File: backend/external/blob_storage.py
   
5. Metadata saved to Cosmos DB
   File: backend/repositories/document_repository.py
   Schema: /docs/02-architecture/DATABASE_SCHEMA_v1.0.md
```

**Trace through the code** - 30 minutes well spent.

---

## Resources by Role

### If You're a Backend Engineer

**Priority reading (in order):**
1. [BACKEND_ARCHITECTURE_v1.0.md](../../02-architecture/BACKEND_ARCHITECTURE_v1.0.md)
2. [DATABASE_SCHEMA_v1.0.md](../../02-architecture/DATABASE_SCHEMA_v1.0.md)
3. [API_CONTRACT_v1.0.md](../../02-architecture/API_CONTRACT_v1.0.md)
4. [CODING_STANDARDS_v1.0.md](../CODING_STANDARDS_v1.0.md) - Python section

**First tasks:**
- Write a new API endpoint
- Optimize a database query
- Add comprehensive error handling
- Improve test coverage

**Key files to master:**
- `backend/main.py` - Entry point
- `backend/routes/*.py` - API endpoints
- `backend/services/*.py` - Business logic
- `backend/repositories/*.py` - Data access

### If You're a Frontend Engineer

**Priority reading (in order):**
1. [FRONTEND_ARCHITECTURE_v1.0.md](../../02-architecture/FRONTEND_ARCHITECTURE_v1.0.md)
2. [API_CONTRACT_v1.0.md](../../02-architecture/API_CONTRACT_v1.0.md)
3. [SYSTEM_ARCHITECTURE_v1.0.md](../../02-architecture/SYSTEM_ARCHITECTURE_v1.0.md)
4. [CODING_STANDARDS_v1.0.md](../CODING_STANDARDS_v1.0.md) - TypeScript section

**First tasks:**
- Build a new page component
- Refactor a component for reusability
- Improve styling/accessibility
- Add form validation

**Key files to master:**
- `frontend/src/App.tsx` - Router
- `frontend/src/pages/` - Page components
- `frontend/src/components/` - Reusable components
- `frontend/src/services/api.ts` - API client

### If You're DevOps/Infra

**Priority reading:**
1. [INFRASTRUCTURE_INVENTORY_v1.0.md](../../04-deployment/INFRASTRUCTURE_INVENTORY_v1.0.md)
2. [DEPLOYMENT_GUIDE_v1.0.md](../../04-deployment/DEPLOYMENT_GUIDE_v1.0.md)
3. [TROUBLESHOOTING_RUNBOOK_v1.0.md](../../04-deployment/TROUBLESHOOTING_RUNBOOK_v1.0.md)
4. [MONITORING_AND_ALERTING_v1.0.md](../../04-deployment/MONITORING_AND_ALERTING_v1.0.md)

**First tasks:**
- Review Azure resource configuration
- Set up local development environment
- Document infrastructure changes
- Improve monitoring/alerting

---

## Getting Help

### Getting Unstuck

**If you're stuck for 15 minutes:**

1. **Check documentation first**
   - [TROUBLESHOOTING_RUNBOOK_v1.0.md](../../04-deployment/TROUBLESHOOTING_RUNBOOK_v1.0.md)
   - [CODING_STANDARDS_v1.0.md](../CODING_STANDARDS_v1.0.md)

2. **Search GitHub Issues**
   - Others may have same problem

3. **Ask in team chat**
   - #engineering or #development channel
   - Include error message
   - Include steps to reproduce

4. **Ask senior engineer directly**
   - Pair programming (30 min max)
   - Code review
   - Mentoring session

### Common Questions

**Q: Where do I run tests?**
```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run test
```

**Q: How do I check my code style?**
```bash
# Backend
flake8 .

# Frontend
npm run lint
```

**Q: How do I deploy my changes?**
- Just push to GitHub main branch
- GitHub Actions handles deployment
- Monitor at: GitHub > Actions

**Q: How do I access the live app?**
- Frontend: https://jolly-coast-03a4f4d03.4.azurestaticapps.net
- Check credentials in team password manager

**Q: How do I debug production issues?**
- Check [TROUBLESHOOTING_RUNBOOK_v1.0.md](../../04-deployment/TROUBLESHOOTING_RUNBOOK_v1.0.md)
- View logs in Azure Portal > Application Insights

---

## Your First Week Checklist

- [ ] **Day 1**
  - [ ] All accounts created
  - [ ] Local dev environment working
  - [ ] Read architecture documents
  - [ ] Ran tests successfully

- [ ] **Day 2**
  - [ ] Understand 10 core features
  - [ ] Made first PR
  - [ ] Reviewed someone else's PR
  - [ ] Debugged an API call

- [ ] **Day 3**
  - [ ] Wrote a test
  - [ ] Understand security checklist
  - [ ] Traced feature end-to-end
  - [ ] Started working on first issue

- [ ] **Day 4-5**
  - [ ] Closed first issue/PR
  - [ ] Deployed code to production
  - [ ] Attended sprint planning
  - [ ] Scheduled 1-on-1 with manager

---

## Success Criteria

**After 1 week, you should:**
- ✅ Can run full stack locally
- ✅ Understand architecture
- ✅ Have merged first PR
- ✅ Know where to find help
- ✅ Can navigate codebase

**After 2 weeks, you should:**
- ✅ Own a feature area
- ✅ Have closed 3-5 issues
- ✅ Be familiar with CI/CD
- ✅ Know deployment process

**After 4 weeks, you should:**
- ✅ Productive contributor
- ✅ Can lead feature development
- ✅ Mentoring new members
- ✅ Contributing to architecture decisions

---

## Next Steps

**After completing this guide:**

1. **Book a 1-on-1** with your manager
   - Discuss first sprint assignment
   - Clarify expectations
   - Understand team goals

2. **Join team channels**
   - Slack: #engineering, #development
   - GitHub: Watch repository
   - Email: Subscribe to team alias

3. **Schedule pair programming**
   - With backend senior (if backend)
   - With frontend senior (if frontend)
   - With DevOps (if infrastructure)

4. **Start your first sprint**
   - Pick 2-3 issues
   - Estimate effort
   - Commit to delivery

---

## Additional Resources

**Documentation Hub:**
- All docs: `/docs/` folder
- Quick links: [INDEX.md](../INDEX.md)

**External Resources:**
- FastAPI docs: https://fastapi.tiangolo.com
- React docs: https://react.dev
- TypeScript: https://www.typescriptlang.org/docs
- MongoDB: https://docs.mongodb.com
- Azure: https://docs.microsoft.com/azure

**Learning Paths:**
- New to Python? https://www.python.org/about/gettingstarted/
- New to React? https://react.dev/learn
- New to TypeScript? https://www.typescriptlang.org/docs/handbook/

---

**Welcome aboard! We're excited to have you on the team! 🚀**

Questions? Ask in #engineering channel or your manager.

**Reference:** `/docs/03-development/ONBOARDING_GUIDE_v1.0.md`
