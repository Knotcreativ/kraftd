# KraftdIntel Documentation Index

**Last Updated:** 2026-01-17  
**Status:** Production  
**Version:** 1.0  
**Accuracy:** All 26 API endpoints documented and verified

---

## 🔍 Start Here

**New Team Member?** → Start with [START_HERE.txt](START_HERE.txt)  
**Want the Complete Flow?** → Read [USER_FLOW.md](USER_FLOW.md) (end-to-end narrative)  
**Need Quick Overview?** → Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (visual guide with examples)  
**Verify Documentation Quality?** → See [DOCUMENTATION_ACCURACY_REPORT.md](DOCUMENTATION_ACCURACY_REPORT.md)  
**Need API Details?** → Go to [02-architecture/API_CONTRACT_v1.0.md](02-architecture/API_CONTRACT_v1.0.md)

---

## 📚 Documentation Structure

All documentation is organized in versioned folders. Always reference documents from this folder structure. **DO NOT reference documents from root directory** - they are outdated.

### **01. Project Documentation** (`/01-project/`)
**Folder Location:** `docs/01-project/`
- `README_v1.0.md` - Project overview, features, and quick start
- `CHANGELOG_v1.0.md` - Version history and release notes
- `MVP_REQUIREMENTS_v1.0.md` - Detailed project objectives and scope
- `USER_FLOW_MAP_v1.0.md` - User interaction flows and journeys
- `FEATURE_SPECIFICATIONS_v1.0.md` - All 26 API endpoints with examples
- `DEVELOPMENT_ROADMAP_v1.0.md` - Planned features and timeline
- `TECHNICAL_DECISION_LOG_v1.0.md` - Architecture decisions and trade-offs
- **`USER_FLOW.md`** - Complete end-to-end user narrative ⭐
- **`QUICK_REFERENCE.md`** - Visual guide with examples and diagrams ⭐

### **02. Architecture Documentation** (`/02-architecture/`)
**Folder Location:** `docs/02-architecture/`
- `SYSTEM_ARCHITECTURE_v1.0.md` - System design and high-level overview
- `BACKEND_ARCHITECTURE_v1.0.md` - Backend services and components
- `FRONTEND_ARCHITECTURE_v1.0.md` - Frontend structure and components
- `API_CONTRACT_v1.0.md` - **All 26 endpoints with request/response** ⭐
- `DATABASE_SCHEMA_v1.0.md` - Cosmos DB collections and data model
- `SECURITY_CHECKLIST_v1.0.md` - Security measures and best practices

### **03. Development Documentation** (`/03-development/`)
**Folder Location:** `docs/03-development/`
- `SETUP_GUIDE_v1.0.md` - Local development environment setup
- `CODING_STANDARDS_v1.0.md` - Code style, conventions, and standards
- `ONBOARDING_GUIDE_v1.0.md` - New developer onboarding guide

### **04. Deployment Documentation** (`/04-deployment/`)
**Folder Location:** `docs/04-deployment/`
- `DEPLOYMENT_GUIDE_v1.0.md` - Step-by-step deployment procedures
- `INFRASTRUCTURE_INVENTORY_v1.0.md` - Azure resources and setup
- `TROUBLESHOOTING_RUNBOOK_v1.0.md` - Operations and troubleshooting

### **05. Testing Documentation** (`/05-testing/`)
**Folder Location:** `docs/05-testing/`
- `TEST_PLAN_v1.0.md` - Testing strategy and test cases

---

## 📊 Documentation Summary

| Category | Document | Endpoints/Features | Status |
|----------|----------|-------------------|--------|
| **API** | API_CONTRACT_v1.0.md | **26 total** | ✅ Complete |
| | - Auth | 5 endpoints | ✅ Documented |
| | - Documents | 6 endpoints | ✅ Documented |
| | - Workflows | 7 endpoints | ✅ Documented |
| | - AI Agent | 4 endpoints | ✅ Documented |
| | - System | 4 endpoints | ✅ Documented |
| **Features** | FEATURE_SPECIFICATIONS_v1.0.md | All features | ✅ Updated |
| **Project** | MVP_REQUIREMENTS_v1.0.md | MVP scope | ✅ Defined |
| **Architecture** | SYSTEM_ARCHITECTURE_v1.0.md | System design | ✅ Defined |
| **Database** | DATABASE_SCHEMA_v1.0.md | Data model | ✅ Defined |
| **Deployment** | DEPLOYMENT_GUIDE_v1.0.md | Azure setup | ✅ Complete |

---

## 🔐 Version Control System

### **Versioning Format**
- **Current Version:** `FILENAME_v1.0.md`
- **Updated Version:** `FILENAME_v1.1.md`, then `v1.2.md`, etc.
- **Major Release:** `FILENAME_v2.0.md` (used for significant changes)

### **Version History**
All previous versions are stored in `_versions/` subfolder:
```
/docs/01-project/_versions/
    ├── README_v0.9.md (outdated)
    ├── README_v1.0.md (current, kept for reference)
    └── CHANGELOG.md (tracks all versions)
```

### **Rules for Documentation Updates**
1. **Read Current Version:** Always check the latest version before editing
2. **Increment Version:** Change `v1.0` → `v1.1` in filename
3. **Update Changelog:** Document what changed in `CHANGELOG.md`
4. **Archive Old:** Move old version to `_versions/` subfolder
5. **Never Modify Root:** Root directory docs are outdated - ignore them

---

## 🔄 Documentation Workflow

### **When You Update a Document:**

1. **Check Current Version**
   ```bash
   # Open current file from /docs/01-project/README_v1.0.md
   ```

2. **Make Changes**
   - Edit content as needed
   - Update date/status

3. **Increment Version**
   ```bash
   # Rename: README_v1.0.md → README_v1.1.md
   ```

4. **Archive Old Version**
   ```bash
   # Move: README_v1.0.md → _versions/README_v1.0.md
   ```

5. **Update Changelog**
   - Add entry: `- v1.1 (2026-01-17): Updated API endpoints`

6. **Create Redirect Link** (optional)
   ```bash
   # Create: README_CURRENT.md → Links to v1.1
   ```

---

## ❌ IGNORE Root Directory Docs

**These files are OUTDATED and SHOULD NOT BE USED:**
- AGENT_DEPLOYMENT_STATUS.md
- STEP6_DECISION_REQUIRED.md
- ROOT_CAUSE_ANALYSIS*.md
- VERIFICATION_*.md
- PIPELINE_*.md
- PHASE_*.md
- And 100+ others...

**All current documentation is in `/docs/`**

---

## 🎯 Quick Reference

| Need | Location | Filename |
|------|----------|----------|
| Project Overview | `/01-project/` | `README_v1.0.md` |
| Setup Instructions | `/03-development/` | `SETUP_GUIDE_v1.0.md` |
| API Docs | `/03-development/` | `API_REFERENCE_v1.0.md` |
| Deploy to Azure | `/04-deployment/` | `DEPLOYMENT_GUIDE_v1.0.md` |
| Fix an Issue | `/06-operations/` | `TROUBLESHOOTING_v1.0.md` |
| Run Tests | `/05-testing/` | `TEST_STRATEGY_v1.0.md` |
| Architecture | `/02-architecture/` | `ARCHITECTURE_v1.0.md` |

---

## 📝 Next Steps

1. ✅ Structure created
2. ⏳ Migrate essential documents (in progress)
3. ⏳ Set up version control
4. ⏳ Create Changelog
5. ⏳ Delete outdated root files

**Questions?** This is your source of truth for documentation location and versioning.
