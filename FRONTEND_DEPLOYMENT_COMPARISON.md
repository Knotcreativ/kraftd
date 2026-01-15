# Frontend Deployment: Container Apps vs Static Web App

**Date:** January 15, 2026  
**Context:** Choosing optimal frontend hosting for KraftdIntel MVP

---

## Side-by-Side Comparison

| Feature | Container Apps | Static Web App |
|---------|---|---|
| **Type** | Full compute container | Static site hosting |
| **Best For** | Complex SPAs, SSR, Node.js | React/Vue/Angular static builds |
| **Setup Complexity** | Medium (Dockerfile, deploy) | Low (GitHub integration) |
| **Scalability** | Auto-scale 0-4 replicas | Built-in auto-scale |
| **Cold Start** | 30-60 seconds | Instant |
| **Build Process** | Docker build + push | GitHub Actions auto-build |

---

## COST ANALYSIS

### Container Apps (Recommended for your case)
```
Pricing Model: Consumption-based + vCPU-seconds

Frontend App (0.25 CPU, 0.5 Gi RAM):
  Min Replicas:     0 (scales to 0 when idle)
  Max Replicas:     4
  Monthly Estimate: $15-40 (shared with backend costs)

Total with Backend: ~$70-170/month
```

**✅ Cost-effective** - Shares infrastructure with backend

### Static Web App
```
Pricing Model: Free tier + pay-per-build

Standard Plan:
  Static hosting:   FREE ($0)
  Custom domain:    FREE
  HTTPS:            FREE
  Staging slots:    FREE
  API backups:      $5-10
  Monthly Estimate: $0-10

Total:            ~$0-10/month
```

**✅ Cheapest option** - Essentially free

---

## Feature Comparison

### Container Apps

**Advantages:**
- ✅ Same infrastructure (UAE North, same RG)
- ✅ Same monitoring & alerts (Application Insights)
- ✅ Same auto-scaling
- ✅ Same Key Vault integration
- ✅ Same Container Registry
- ✅ Can run Node.js server (SSR possible)
- ✅ Unified infrastructure management
- ✅ More control (custom middleware, server logic)
- ✅ Better for future enhancements

**Disadvantages:**
- ❌ Higher cost than Static Web App
- ❌ Slower cold starts (30-60 seconds)
- ❌ Requires Docker knowledge
- ❌ More configuration needed
- ❌ Manual CI/CD pipeline setup
- ❌ More infrastructure to manage

**Best For:**
- Complex React apps with backend logic
- Server-side rendering needs
- Custom authentication flow
- API proxying requirements
- Future expansion

---

### Static Web App

**Advantages:**
- ✅ Incredibly cheap (free tier!)
- ✅ Fastest cold starts (instant)
- ✅ Integrated GitHub Actions CI/CD
- ✅ Automatic builds from commits
- ✅ Staging environments included
- ✅ Zero infrastructure management
- ✅ Best for pure frontend
- ✅ Built-in custom domain support
- ✅ Built-in API integration patterns
- ✅ Simple deployment process

**Disadvantages:**
- ❌ Static sites only (no Node.js backend)
- ❌ Different resource from backend
- ❌ Separate monitoring setup
- ❌ Limited SSR capabilities
- ❌ Less scalable for complex apps
- ❌ Separate infrastructure to manage

**Best For:**
- Pure React/Vue.js static builds
- Marketing sites
- Simple frontends
- Cost-conscious projects
- Quick deployment

---

## Infrastructure Architecture Comparison

### Option 1: Container Apps (Unified)
```
Azure Container Registry
  ├── Backend Image (v6-cost-opt)
  └── Frontend Image (new)

Container Apps Environment (UAE North)
  ├── kraftdintel-app (Backend)     ← Running now
  └── kraftdintel-web (Frontend)    ← New

Shared:
  ✅ Resource Group: kraftdintel-rg
  ✅ Monitoring: Application Insights
  ✅ Secrets: Key Vault
  ✅ Environment: kraftdintel-env

Monthly Cost: $70-170
```

### Option 2: Static Web App (Separate)
```
GitHub Repository
  ├── Frontend source code
  └── Auto-build on commit

Static Web App (separate resource)
  ├── Auto-deploy from GitHub
  ├── Automatic builds
  └── Staging environment

Backend still in Container Apps

Monitoring: Separate setup needed

Monthly Cost: $0-10 frontend + $50-120 backend
```

---

## Deployment Workflow Comparison

### Container Apps Workflow
```
1. Create React app locally
2. Create Dockerfile (simple)
3. Build: docker build -t image:tag .
4. Push: az acr build -r registry -t image:tag .
5. Deploy: Update Container App with new image
6. Monitor: Same Application Insights
7. Time: ~15 minutes
```

### Static Web App Workflow
```
1. Create React app locally
2. Push to GitHub
3. Create Static Web App resource
4. Connect to GitHub repo
5. Auto-builds on every commit
6. Auto-deploys on build success
7. Monitor: Separate insights
8. Time: ~5 minutes
```

---

## Monitoring & Alerts

### Container Apps
```
✅ Same monitoring as backend
✅ Application Insights integration
✅ 5 alert rules (reuse existing)
✅ Unified dashboards
✅ Same response time tracking
✅ Same error tracking
```

### Static Web App
```
❌ Requires separate setup
❌ Different monitoring tool needed
❌ No built-in Application Insights
⚠️  Must configure Application Insights separately
⚠️  Separate alerting rules needed
```

---

## Performance Comparison

### Cold Start Time
```
Container Apps:      30-60 seconds (scales up from 0)
Static Web App:      Instant (no computation)
Winner:              Static Web App ✓
```

### Subsequent Requests
```
Container Apps:      ~200-500ms (varies by load)
Static Web App:      ~50-150ms (CDN cached)
Winner:              Static Web App ✓
```

### Under Load
```
Container Apps:      Scales 0-4 replicas (handles spike)
Static Web App:      Global CDN (handles spike better)
Winner:              Static Web App ✓
```

---

## RECOMMENDATION

### **If you want simplicity & cost: Static Web App** ✅
```
Pros:
  - Free tier sufficient for MVP
  - Automatic GitHub CI/CD
  - Instant deployments
  - Better performance (CDN)
  - Less infrastructure to manage
  - Best for pure React/Vue frontend

Setup Time: 5-10 minutes
Monthly Cost: $0-10
Complexity: Low
```

### **If you want unified infrastructure: Container Apps** ✅
```
Pros:
  - Same infrastructure as backend
  - Same monitoring (Application Insights)
  - Same resource group
  - Better for future enhancements
  - More control
  - Unified management

Setup Time: 20-30 minutes
Monthly Cost: $15-40
Complexity: Medium
```

---

## Decision Matrix

| Requirement | Container Apps | Static Web App |
|---|---|---|
| Cost | ⭐⭐⭐ ($15-40) | ⭐⭐⭐⭐⭐ ($0-10) |
| Simplicity | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Performance | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Unified Monitoring | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| GitHub Integration | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Future Scalability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Setup Speed | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Infrastructure Control | ⭐⭐⭐⭐⭐ | ⭐⭐ |

---

## FINAL RECOMMENDATION

### **Choose Static Web App IF:**
- ✅ Budget is primary concern
- ✅ Want fastest setup (5 minutes)
- ✅ Pure React/Vue.js app (no SSR)
- ✅ Best performance needed
- ✅ Automatic GitHub deployments desired
- ✅ Minimal infrastructure management

**Result:** Clean, simple, cost-effective ✓

---

### **Choose Container Apps IF:**
- ✅ Want unified infrastructure
- ✅ Need same monitoring as backend
- ✅ Plan future Node.js/SSR features
- ✅ Want one resource group management
- ✅ OK with extra cost ($15-40/month)
- ✅ More control over deployment

**Result:** Integrated, powerful, manageable ✓

---

## My Specific Recommendation for KraftdIntel

**→ START WITH STATIC WEB APP**

**Reasoning:**
1. **MVP Phase:** Static Web App is perfect for MVP frontend
2. **Cost:** Free tier covers development needs
3. **Speed:** Deploy in 5 minutes vs 30 minutes
4. **Performance:** Better cold starts + CDN
5. **GitHub CI/CD:** Automatic builds on commit
6. **Future-proof:** Can migrate to Container Apps later if needed

**Timeline:**
- Week 1: Deploy frontend to Static Web App
- Week 2-3: Integrate with live backend API
- Week 4: User testing
- Future: If you need SSR/backend logic → migrate to Container Apps

**Cost Comparison:**
```
Static Web App (recommended):    $0-10/month  ✓ MVP phase
Container Apps (future):         $15-40/month ✓ Production scale
```

---

## Next Steps (If you choose Static Web App)

1. ✅ Create React/Vue.js app (I can generate)
2. ✅ Push to GitHub repo
3. ✅ Create Static Web App resource in Azure
4. ✅ Connect to GitHub
5. ✅ Configure environment variables (API endpoint)
6. ✅ Deploy (auto)
7. ✅ Test with live backend

**Total setup: ~1 hour**

---

**Ready to proceed? Which option would you like?**

1. Static Web App (recommended, fastest, cheapest)
2. Container Apps (unified, more control)

