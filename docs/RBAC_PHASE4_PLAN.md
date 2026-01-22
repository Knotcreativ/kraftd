# RBAC Phase 4 - Database Integration & Tenant Isolation - PLAN

**Status:** 🔄 PLANNING  
**Target Completion:** 2-3 hours  
**Priority:** HIGH - Required for production deployment

---

## Phase 4 Overview

This phase focuses on integrating the RBAC system with persistent database storage and implementing multi-tenant isolation for enterprise scalability.

### Key Objectives:

1. **Database Integration** - Connect ProfileService to Cosmos DB
2. **Tenant Isolation** - Implement TenantContext for multi-tenant support
3. **Data Ownership** - Enforce resource ownership validation
4. **Query Context Scoping** - Automatically scope queries to tenant/user
5. **Migration & Testing** - Validate all changes with integration tests

---

## Detailed Tasks

### Task 1: Database Integration for ProfileService (Priority 1)

**Objective:** Wire ProfileService to actual Cosmos DB instead of mock

**Changes Required:**

1. **Update `main.py`:**
   - Initialize ProfileService with cosmos_service
   - Register ProfileService dependency injection
   - Add user_profile routes to app

   ```python
   # In startup lifespan
   cosmos_service = get_cosmos_service()
   profile_service = ProfileService(cosmos_service)
   
   # In routes registration
   from routes.user_profile import router as profile_router, set_profile_service
   set_profile_service(profile_service)
   app.include_router(profile_router)
   ```

2. **Update `profile_service.py`:**
   - Change from MongoDB interface to Cosmos SDK
   - Use `cosmos_service.db` instead of direct connection
   - Update collection references for Cosmos DB

3. **Update `user_preferences.py`:**
   - Ensure model compatibility with Cosmos DB serialization
   - Add partition key handling for multi-tenant support

**Files to Modify:**
- `backend/main.py`
- `backend/services/profile_service.py`
- `backend/models/user_preferences.py` (minimal changes)

**Estimated Time:** 1 hour

---

### Task 2: Tenant Context Implementation (Priority 2)

**Objective:** Create TenantContext for multi-tenant isolation

**New File: `backend/services/tenant_service.py`**

```python
class TenantContext:
    """Thread-safe tenant context for multi-tenant isolation"""
    
    def __init__(self, tenant_id: str, user_email: str, user_role: UserRole):
        self.tenant_id = tenant_id
        self.user_email = user_email
        self.user_role = user_role
    
    def is_tenant_admin(self) -> bool:
        """Check if user is tenant admin"""
        pass
    
    def can_access_resource(self, resource_id: str) -> bool:
        """Verify access to resource within tenant"""
        pass

class TenantService:
    """Service for tenant management"""
    
    @staticmethod
    def get_current_tenant() -> TenantContext:
        """Get current tenant context (from thread-local storage)"""
        pass
    
    @staticmethod
    def set_current_tenant(context: TenantContext):
        """Set tenant context for current request"""
        pass
    
    @staticmethod
    def verify_tenant_access(email: str) -> str:
        """Get tenant_id for user, verify access"""
        pass
```

**Usage Pattern:**
```python
@router.get("/profile")
async def get_profile(current_user: Tuple[str, UserRole] = Depends(...)):
    email, role = current_user
    tenant_id = TenantService.verify_tenant_access(email)
    tenant_context = TenantContext(tenant_id, email, role)
    
    # All queries automatically scoped to tenant
    profile = await profile_service.get_profile(email, tenant_id)
```

**Files to Create:**
- `backend/services/tenant_service.py` (250+ lines)

**Estimated Time:** 45 minutes

---

### Task 3: Data Ownership Enforcement (Priority 2)

**Objective:** Add ownership validation to all data access

**New File: `backend/services/ownership_service.py`**

```python
class OwnershipService:
    """Service for verifying resource ownership"""
    
    async def verify_resource_owner(
        self, 
        user_email: str, 
        resource_id: str, 
        resource_type: str,
        tenant_id: str
    ) -> bool:
        """Verify user owns resource"""
        pass
    
    async def get_owned_resources(
        self,
        user_email: str,
        resource_type: str,
        tenant_id: str
    ) -> List[str]:
        """Get all resources owned by user"""
        pass
    
    async def transfer_ownership(
        self,
        resource_id: str,
        from_user: str,
        to_user: str,
        resource_type: str,
        tenant_id: str
    ) -> bool:
        """Transfer resource ownership"""
        pass
```

**Integration Points:**
- Update `templates.py` - Verify document ownership
- Update `documents.py` - Verify document ownership
- Update `user_profile.py` - Only own profile modifications
- Update `signals.py` - Verify signal ownership

**Files to Create:**
- `backend/services/ownership_service.py` (200+ lines)

**Files to Modify:**
- `backend/routes/templates.py`
- `backend/routes/user_profile.py`
- Other route files

**Estimated Time:** 1 hour

---

### Task 4: Query Context Scoping (Priority 3)

**Objective:** Automatically filter queries by tenant/user

**New File: `backend/utils/query_scope.py`**

```python
class QueryScope:
    """Utility for scoping queries to tenant/user context"""
    
    @staticmethod
    def add_tenant_filter(query: dict, tenant_id: str) -> dict:
        """Add tenant filter to query"""
        query["tenant_id"] = tenant_id
        return query
    
    @staticmethod
    def add_user_filter(query: dict, user_email: str) -> dict:
        """Add user filter to query"""
        query["owner_email"] = user_email
        return query
    
    @staticmethod
    def scope_to_tenant_and_user(
        query: dict, 
        tenant_id: str,
        user_email: str,
        require_ownership: bool = False
    ) -> dict:
        """Scope query to both tenant and user"""
        pass
```

**Integration Pattern:**
```python
# Before: Vulnerable to cross-tenant access
documents = db.documents.find({"status": "active"})

# After: Scoped to tenant
query = {"status": "active"}
query = QueryScope.add_tenant_filter(query, tenant_id)
documents = db.documents.find(query)
```

**Files to Create:**
- `backend/utils/query_scope.py` (150+ lines)

**Files to Modify:**
- All repository files
- All service files

**Estimated Time:** 1.5 hours

---

### Task 5: Middleware Update for Tenant Context (Priority 2)

**Objective:** Automatically set tenant context for each request

**Update File: `backend/middleware/rbac.py`**

```python
async def set_tenant_context_middleware(request: Request, call_next):
    """Middleware to set tenant context for each request"""
    
    # Get user from token
    token = request.headers.get("Authorization")
    if token:
        payload = TokenService.verify_token(token)
        user_email = payload.get("sub")
        user_role = UserRole[payload.get("role")]
        
        # Get tenant for user
        tenant_id = await TenantService.verify_tenant_access(user_email)
        
        # Set thread-local context
        tenant_context = TenantContext(tenant_id, user_email, user_role)
        TenantService.set_current_tenant(tenant_context)
    
    response = await call_next(request)
    return response
```

**Files to Modify:**
- `backend/middleware/rbac.py`
- `backend/main.py` (add middleware)

**Estimated Time:** 30 minutes

---

### Task 6: Migration & Testing (Priority 3)

**Objective:** Test all Phase 4 changes

**Test Cases:**

1. **Database Integration Tests:**
   - [ ] ProfileService connects to Cosmos DB
   - [ ] Profiles persisted and retrieved correctly
   - [ ] Preferences stored and updated
   - [ ] Avatar upload/download works

2. **Tenant Isolation Tests:**
   - [ ] User A cannot access User B's profile
   - [ ] Tenant A data isolated from Tenant B
   - [ ] Query filtering applied automatically
   - [ ] Cross-tenant queries rejected

3. **Ownership Validation Tests:**
   - [ ] User can only modify own profile
   - [ ] Document ownership enforced
   - [ ] Ownership transfer works correctly
   - [ ] Admin override working

4. **WebSocket Tests:**
   - [ ] WebSocket connection respects tenant
   - [ ] Messages scoped to tenant subscriptions
   - [ ] Cross-tenant message access prevented

**Test Files to Create:**
- `backend/tests/test_profile_service.py`
- `backend/tests/test_tenant_isolation.py`
- `backend/tests/test_ownership.py`

**Estimated Time:** 1.5 hours

---

## Implementation Sequence

### Day 1 - Database & Tenant Integration (2 hours)

**Morning:**
1. **Task 1** - Database Integration (1 hour)
   - Update ProfileService for Cosmos DB
   - Wire up in main.py
   - Test profile CRUD

2. **Task 2** - Tenant Context (45 mins)
   - Create TenantService
   - Create TenantContext class
   - Add middleware

**Afternoon:**
3. **Task 5** - Middleware Integration (30 mins)
   - Update rbac.py with tenant middleware
   - Register in main.py
   - Test context propagation

### Day 2 - Ownership & Query Scoping (2.5 hours)

**Morning:**
4. **Task 3** - Ownership Service (1 hour)
   - Create OwnershipService
   - Update route files
   - Enforce ownership checks

5. **Task 4** - Query Scoping (1.5 hours)
   - Create QueryScope utility
   - Update repositories
   - Integrate with queries

**Afternoon:**
6. **Task 6** - Testing & Validation (1 hour)
   - Create test files
   - Run integration tests
   - Validate isolation

---

## Success Criteria

### Phase 4 Complete When:

✅ **Database Integration:**
- [ ] ProfileService connected to Cosmos DB
- [ ] All CRUD operations work
- [ ] Data persisted across restarts

✅ **Tenant Isolation:**
- [ ] TenantContext implemented
- [ ] Tenant middleware active
- [ ] Cross-tenant access prevented

✅ **Ownership Enforcement:**
- [ ] OwnershipService created
- [ ] All resources ownership-validated
- [ ] Ownership transfer working

✅ **Query Scoping:**
- [ ] Automatic tenant filtering
- [ ] User-level filtering applied
- [ ] No cross-tenant data leaks

✅ **Validation:**
- [ ] Zero compilation errors
- [ ] All integration tests passing
- [ ] Zero security warnings

✅ **Deployment:**
- [ ] Committed to GitHub
- [ ] Pushed to main
- [ ] CI/CD pipeline passing

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Data leakage | Low | High | Query scoping, ownership checks |
| Performance | Medium | Medium | Index optimization, query optimization |
| Breaking changes | Low | Medium | Comprehensive testing, gradual rollout |
| Cosmos DB limits | Low | Low | Partition strategy, monitoring |

---

## Estimated Effort

| Task | Hours | Priority |
|------|-------|----------|
| Database Integration | 1.0 | 1 |
| Tenant Context | 0.75 | 1 |
| Middleware Update | 0.5 | 1 |
| Ownership Service | 1.0 | 2 |
| Query Scoping | 1.5 | 2 |
| Testing & Validation | 1.5 | 3 |
| **Total** | **~6 hours** | - |

---

## Next Steps

### To Begin Phase 4:

1. **Confirm priorities** - Is database integration first priority?
2. **Setup testing environment** - Prepare test data and fixtures
3. **Code review** - Review existing patterns for consistency
4. **Documentation** - Document tenant isolation architecture

### After Phase 4:

- **Phase 5:** Advanced Features (caching, notifications, analytics)
- **Phase 6:** Security Hardening (encryption, audit logging, compliance)
- **Phase 7:** Performance Optimization (query optimization, indexing, monitoring)

---

## Ready to Begin?

Type `task1` to start with Database Integration  
Type `full` to implement all tasks at once  
Type `skip` to skip to Phase 5

