# 🎯 Kraftd Docs - Pre-Flight Production Deployment Checklist

**Status:** Ready for Immediate Execution  
**Estimated Completion Time:** 3-4 hours (1 hour deployment + 2-3 hours validation)  
**Go-Live Target:** January 20, 2026

---

## ✅ CRITICAL PRE-DEPLOYMENT ITEMS (Must Complete First)

### Security Hardening
- [ ] **CORS Configuration** - Remove wildcard, add production domain
  ```
  File: backend/main.py (line ~52)
  Action: Change allow_origins=["*"] to ["https://kraftd.io"]
  Impact: CRITICAL - blocks CORS attacks
  ```

- [ ] **Secrets Management** - Move to Azure Key Vault
  ```
  Current: .env files in repo/container
  Required: Azure Key Vault integration
  Impact: CRITICAL - prevents credential exposure
  ```

- [ ] **reCAPTCHA Production Keys** - Configure for production domain
  ```
  File: frontend/.env.production
  File: backend/.env.production
  Action: Update keys from Google Cloud console
  Impact: CRITICAL - bot protection
  ```

- [ ] **JWT Secret Key** - Rotate from development
  ```
  Current: "dev-secret-key-change-in-production"
  Required: Strong 32+ character secret (azure key vault)
  Impact: CRITICAL - authentication security
  ```

- [ ] **Database Firewall** - Restrict to Azure services only
  ```
  Azure Portal → Cosmos DB → Firewall
  Action: Add Azure services, remove public access
  Impact: CRITICAL - database security
  ```

### Database & Infrastructure
- [ ] **Cosmos DB Production Setup**
  ```bash
  # Verify setup
  python backend/scripts/init_cosmos.py --production
  
  # Check:
  ✓ Connection successful
  ✓ Containers created (documents, users, workflows, workflow_steps)
  ✓ Indexes created
  ✓ Partition keys correct (/owner_email)
  ✓ RU/s allocated (400 minimum)
  ```

- [ ] **Azure Container Apps** - Verify deployment
  ```
  Azure Portal → Container Apps
  Check:
  ✓ Image deployed (latest tag)
  ✓ Replicas running (1-4 range)
  ✓ Health checks passing
  ✓ CPU/Memory allocation set
  ```

- [ ] **Static Web App** - Verify frontend deployment
  ```
  Azure Portal → Static Web App
  Check:
  ✓ Build completed successfully
  ✓ All pages accessible
  ✓ Environment variables set
  ✓ HTTPS redirect enabled
  ```

### Monitoring & Alerting
- [ ] **Application Insights** - Activated & configured
  ```
  Azure Portal → Application Insights
  Check:
  ✓ Data collection enabled
  ✓ Custom events configured
  ✓ Alerts created (>5% errors, latency, availability)
  ✓ Dashboard created
  ```

- [ ] **Alert Email Notifications** - Tested
  ```
  Action: Send test alert to ops team
  Expected: Email received within 5 minutes
  ```

---

## 📋 PHASE 1: SECURITY VALIDATION (30 minutes)

### Identity & Access
- [ ] Verify JWT authentication working
  ```bash
  curl -X POST https://api.production.com/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@kraftd.io", "password":"Test@12345"}'
  
  Expected: 200 OK with JWT token
  ```

- [ ] Test token refresh mechanism
  ```bash
  # Token should auto-refresh on 401
  Expected: Transparent refresh, no logout
  ```

- [ ] Verify password hashing (bcrypt)
  ```bash
  # Stored password must be hashed (not plain text)
  Cosmos DB → documents container → users
  Check: password field is bcrypt hash (starts with $2b$)
  ```

### CORS & HTTPS
- [ ] Verify CORS whitelist (production domain only)
  ```bash
  curl -X OPTIONS https://api.production.com/api/v1/health \
    -H "Origin: https://kraftd.io" \
    -H "Access-Control-Request-Method: GET"
  
  Expected: 
  ✓ Access-Control-Allow-Origin: https://kraftd.io
  ✓ NOT wildcard (*)
  ```

- [ ] Verify HTTPS redirect
  ```bash
  curl -i http://api.production.com/api/v1/health
  
  Expected: 
  ✓ 308 Permanent Redirect to https://
  ✓ No unencrypted traffic processed
  ```

- [ ] Verify security headers
  ```bash
  curl -i https://api.production.com/api/v1/health
  
  Expected headers:
  ✓ Strict-Transport-Security: max-age=31536000
  ✓ X-Content-Type-Options: nosniff
  ✓ X-Frame-Options: DENY
  ✓ X-XSS-Protection: 1; mode=block
  ```

### Database Security
- [ ] Verify Cosmos DB connection uses endpoint (not connection string in code)
  ```bash
  grep -r "connect_from_connection_string" backend/ --exclude-dir=.venv
  
  Expected: No results (should use endpoint + key separately)
  ```

- [ ] Verify database read-only replica for backups
  ```
  Azure Portal → Cosmos DB → Replicate data
  Check: ✓ Secondary region enabled for HA
  ```

---

## 🧪 PHASE 2: FUNCTIONAL TESTING (45 minutes)

### Authentication Flow
- [ ] User Registration
  ```
  Test: Register new account
  Email: prod-test-1@kraftd.io
  Password: Test@ProductionX1
  
  Expected:
  ✓ Form validates
  ✓ reCAPTCHA v3 challenge
  ✓ User created in Cosmos DB
  ✓ Verification email sent within 30s
  ✓ Success page displayed
  ```

- [ ] Email Verification
  ```
  Test: Click verification link from email
  
  Expected:
  ✓ Link valid for 24 hours
  ✓ User marked as verified
  ✓ Redirect to login
  ```

- [ ] Login Flow
  ```
  Test: Login with verified credentials
  
  Expected:
  ✓ JWT token issued
  ✓ Token stored in localStorage
  ✓ Redirect to dashboard
  ✓ User data loaded (name, email)
  ```

### Document Processing
- [ ] File Upload
  ```
  Test: Upload sample contract (PDF, 5MB)
  
  Expected:
  ✓ Progress bar appears
  ✓ File validated (PDF only, max 10MB)
  ✓ Stored in Azure Storage
  ✓ Database record created
  ✓ Processing started (< 5s)
  ```

- [ ] AI Analysis
  ```
  Test: Wait for GPT-4o mini analysis
  
  Expected:
  ✓ Analysis completes < 30s
  ✓ Key clauses extracted
  ✓ Risks identified
  ✓ Results stored in Cosmos DB
  ```

- [ ] Export with Recommendations
  ```
  Test: Export with AI recommendations
  
  Expected:
  ✓ ZIP file generated < 5s
  ✓ Contains: contract.pdf, analysis.json, recommendations.txt
  ✓ Download starts automatically
  ✓ Feedback form displayed
  ```

### Rate Limiting
- [ ] Test rate limit enforcement
  ```bash
  # Simulate 100 login attempts in 1 minute
  for i in {1..100}; do
    curl -X POST https://api.production.com/auth/login \
      -H "Content-Type: application/json" \
      -d '{"email":"test@kraftd.io", "password":"wrong"}'
  done
  
  Expected:
  ✓ First 5 attempts: 401 Unauthorized
  ✓ After 5/15min: 429 Too Many Requests
  ✓ After 1 hour: Reset
  ```

### Error Handling
- [ ] Test invalid inputs
  ```
  ✓ Invalid email format → Validation error
  ✓ Weak password (< 8 chars) → Error message
  ✓ File > 10MB → Rejection
  ✓ Unsupported file type → Error
  ✓ Missing required fields → Form validation
  ```

- [ ] Test network failures
  ```
  ✓ Database down → 503 Service Unavailable
  ✓ API timeout → 504 Gateway Timeout
  ✓ Auth service down → 401 Unauthorized
  ✓ Storage failure → User-friendly error message
  ```

---

## 📊 PHASE 3: PERFORMANCE VALIDATION (30 minutes)

### Load Testing
- [ ] Run load test suite
  ```bash
  # 100 concurrent users, 5 minute duration
  ./tests/load-test.sh --users=100 --duration=300
  
  Expected metrics:
  ✓ Response time p95: < 2s
  ✓ Error rate: < 0.1%
  ✓ Throughput: ≥ 50 req/s
  ✓ Memory: Stable (no leaks)
  ✓ CPU: < 80% utilization
  ```

### Database Performance
- [ ] Query performance check
  ```
  Azure Portal → Query Explorer
  
  Sample query:
  SELECT * FROM documents WHERE owner_email = "test@kraftd.io"
  
  Expected:
  ✓ Execution time: < 100ms
  ✓ RU consumption: < 10 RU
  ✓ No index missing warnings
  ```

- [ ] RU/s allocation check
  ```
  Current: 400 RU/s provisioned
  Usage during load test: < 320 RU/s (80% utilization)
  
  If exceeds: Scale up to 600 or 800 RU/s
  ```

### Scalability
- [ ] Verify auto-scaling configuration
  ```
  Container Apps → Scale rules:
  ✓ CPU trigger: 70% → scale up
  ✓ Memory trigger: 80% → scale up
  ✓ Max replicas: 4 (configurable)
  ✓ Scale-down delay: 5 minutes
  ```

---

## 🚀 PHASE 4: DEPLOYMENT (30-45 minutes)

### Pre-Deployment
- [ ] Final code review
  ```
  ✓ No hardcoded secrets
  ✓ No console.log/print statements (DEBUG)
  ✓ No development-only code
  ✓ All error handling in place
  ```

- [ ] Database backup
  ```bash
  # Backup production database before deployment
  az cosmosdb sql database backup restore \
    --account-name kraftdintel-cosmos-prod \
    --resource-group kraftdintel-rg \
    --database-id kraftdintel \
    --target-database-name kraftdintel-backup-$(date +%Y%m%d)
  
  Verify: Backup completed (check Azure Portal)
  ```

- [ ] Team notification
  ```
  Message: "Production deployment starting at 10:15 UTC+4"
  Notify: Engineering, Product, Customer Success
  ```

### Deployment Execution
- [ ] GitHub Actions triggered
  ```bash
  # Push deployment tag to trigger workflow
  git tag -a v1.0.0-prod -m "Production release"
  git push origin v1.0.0-prod
  
  Monitor: GitHub Actions dashboard
  Expected: Build succeeds in < 5 minutes
  ```

- [ ] Container image validation
  ```bash
  # Verify image pushed to registry
  az acr repository show --name kraftdintelregistry --image kraftdintel:latest
  
  Expected:
  ✓ Image present in ACR
  ✓ Size: 200-300MB (reasonable)
  ✓ Scanned for vulnerabilities: 0 critical
  ```

- [ ] Container Apps deployment
  ```bash
  # Verify container is running
  az containerapp revision list \
    --resource-group kraftdintel-rg \
    --name kraftdintel-app
  
  Expected:
  ✓ Latest revision active
  ✓ All replicas ready (0-4 range)
  ✓ No error events in logs
  ```

- [ ] Health check verification
  ```bash
  # Test API health
  curl -i https://api.production.com/api/v1/health
  
  Expected: 200 OK
  {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-01-20T11:30:00Z"
  }
  ```

---

## ✨ PHASE 5: GO-LIVE VALIDATION (30-45 minutes)

### Smoke Tests
- [ ] Run automated smoke test suite
  ```bash
  ./tests/production-smoke-tests.sh
  
  Expected output:
  ✅ API health check
  ✅ Database connectivity
  ✅ Authentication flow (register → verify → login)
  ✅ Document upload
  ✅ AI analysis
  ✅ Export functionality
  ✅ Monitoring & alerts
  ✅ Rate limiting
  ✅ Email notifications
  
  Pass rate: 100% (9/9 tests)
  ```

### Manual User Journey
- [ ] Complete end-to-end flow
  ```
  1. ✓ Visit https://kraftd.io
  2. ✓ Click "Sign Up"
  3. ✓ Enter email: prod-final-test@kraftd.io
  4. ✓ Create password: Test@ProductionFinal123
  5. ✓ Accept Terms & Privacy
  6. ✓ Pass reCAPTCHA
  7. ✓ Submit registration
  8. ✓ Check email for verification link (< 30s)
  9. ✓ Click verification link
  10. ✓ Verify email success page
  11. ✓ Login with credentials
  12. ✓ See empty dashboard
  13. ✓ Upload sample contract (use test_document.pdf)
  14. ✓ Wait for analysis (should complete in < 30s)
  15. ✓ Review extracted data
  16. ✓ Click "Export with Recommendations"
  17. ✓ Download ZIP file
  18. ✓ Provide feedback ("Very Helpful")
  19. ✓ Logout
  20. ✓ Verify session cleared (can't access dashboard)
  
  Duration: Should complete in 5-10 minutes
  Expected: All steps succeed without errors
  ```

### Monitoring Review
- [ ] Application Insights Dashboard
  ```
  Verify:
  ✓ Requests graph shows incoming traffic
  ✓ Error rate: 0% (or very close)
  ✓ Response time: p95 < 2s
  ✓ Database latency: < 100ms
  ✓ No critical alerts firing
  ✓ User count increased (new registrations)
  
  Duration: Should stabilize after 5 minutes
  ```

- [ ] Container Apps Metrics
  ```
  Verify:
  ✓ CPU: < 60% average
  ✓ Memory: < 500MB per instance
  ✓ Replica count: Stable (1-4 range)
  ✓ Network I/O: Normal
  ✓ No crashes or restarts
  ```

- [ ] Cosmos DB Metrics
  ```
  Verify:
  ✓ RU/s consumed: < 80% of provisioned
  ✓ No throttling (429 errors)
  ✓ Latency: p95 < 100ms
  ✓ Document count: Increased with new user uploads
  ✓ No query failures
  ```

---

## 📈 PHASE 6: POST-LAUNCH MONITORING (24 hours)

### First Hour (Active Monitoring)
- [ ] Monitor every 5 minutes
  ```
  Check:
  ✓ Error rate stable (< 0.1%)
  ✓ Response time consistent (p95 < 2s)
  ✓ No memory leaks (gradual increase is OK)
  ✓ Database healthy (no throttling)
  ✓ No alerts firing
  ```

### First 4 Hours
- [ ] Monitor every 15 minutes
  ```
  Track:
  ✓ User registrations: Count increasing
  ✓ Documents processed: Volume stable
  ✓ Error patterns: None repetitive
  ✓ Performance degradation: None observed
  ✓ Security incidents: None reported
  ```

### First 24 Hours
- [ ] Monitor every 1-2 hours
  ```
  Daily checklist:
  ✓ Peak hour performance (usually 9-10 AM)
  ✓ Total user registrations
  ✓ Documents processed
  ✓ Export success rate
  ✓ Authentication success rate
  ✓ Error logs reviewed (if any)
  ✓ Cost trending
  ```

---

## 🔄 ROLLBACK PLAN (If Needed)

If critical issue detected, follow this order:

### Immediate Actions (< 5 minutes)
1. [ ] Stop accepting new traffic to problematic version
2. [ ] Activate incident response protocol
3. [ ] Notify all stakeholders
4. [ ] Begin rollback preparation

### Rollback Execution (5-10 minutes)
```bash
# Step 1: Revert code to previous stable version
git revert <problematic-commit-hash>
git push origin main

# Step 2: Redeploy from previous build
./scripts/deploy-production.ps1 --skip-tests --from-cache

# Step 3: Verify health checks
./tests/production-smoke-tests.sh

# Step 4: Confirm stable
# Monitor for 5 minutes
```

### Post-Rollback (< 30 minutes)
1. [ ] Notify stakeholders of rollback
2. [ ] Create incident ticket
3. [ ] Document root cause
4. [ ] Plan fix for next attempt
5. [ ] Schedule retry (next business day)

**Rollback target: < 10 minutes total downtime**

---

## ✅ GO-LIVE SIGN-OFF

| Checklist Item | Status | Owner | Time |
|---|---|---|---|
| Security validation complete | ☐ | | |
| Functional testing complete | ☐ | | |
| Performance testing passed | ☐ | | |
| Deployment successful | ☐ | | |
| Smoke tests passing | ☐ | | |
| Manual testing complete | ☐ | | |
| Monitoring active | ☐ | | |
| All alerts configured | ☐ | | |
| Team notified | ☐ | | |
| Production ready | ☐ | | |

---

## 📞 ESCALATION CONTACTS

| Role | Contact | Available |
|------|---------|-----------|
| Technical Lead | | 24/7 |
| DevOps Engineer | | 24/7 |
| Database Admin | | 24/7 |
| Security Officer | | Business hours |
| Product Manager | | Business hours |

---

## 📝 NOTES

```
Add production deployment notes here as you proceed:

[Will be updated during deployment]
```

---

**Status:** 🟢 **READY FOR PRODUCTION**  
**Last Updated:** January 20, 2026  
**Next Step:** Start Phase 1 Security Validation

---

## Quick Start Command

```bash
# Execute this to begin deployment
cd c:/Users/1R6/OneDrive/Project\ Catalyst/KraftdIntel
./KRAFTD_DOCS_PRODUCTION_ROLLOUT_PLAN.md

# Expected: 3-4 hours to production
# Critical path: Phases 1 → 2 → 3 → 4 → 5
```
