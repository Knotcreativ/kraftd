# Infrastructure Inventory

**Version:** 1.0  
**Status:** APPROVED  
**Last Updated:** 2026-01-17  
**Environment:** Production (West Europe + UAE North)

---

## Azure Resources Summary

| Resource | Name | Region | Status | Cost/Mo |
|----------|------|--------|--------|---------|
| Static Web App | kraftdintel-frontend | West Europe | ✅ Running | ~$12 |
| Container Apps | kraftdintel-backend | UAE North | ✅ Running | ~$50 |
| Cosmos DB | kraftdintel-mongo | West Europe | ✅ Running | ~$80 |
| Blob Storage | kraftdintelblob | East US | ✅ Running | ~$5 |
| Key Vault | kraftdintel-kv | West Europe | ✅ Running | ~$0.6 |
| Application Insights | kraftdintel-ai | West Europe | ✅ Running | ~$15 |
| **Monthly Total** | | | | **~$162.60** |

---

## Frontend Infrastructure

### Azure Static Web App
**Resource ID:** `/subscriptions/{sub-id}/resourceGroups/kraftdintel/providers/Microsoft.Web/staticSites/kraftdintel-frontend`

**Configuration:**
```
Name: kraftdintel-frontend
Region: West Europe
SKU: Free (suitable for MVP)
Custom Domain: https://jolly-coast-03a4f4d03.4.azurestaticapps.net
API Backend: https://kraftdintel-backend.azurecontainerapps.io
```

**Storage:**
- Source: GitHub repository (`main` branch)
- Build output: `frontend/dist/`
- Build framework: Vite
- Build command: `npm install --prefix frontend && npm run build --prefix frontend`

**Environment Variables:**
```
VITE_API_URL=https://kraftdintel-backend.azurecontainerapps.io
VITE_APP_VERSION=1.0.0
```

**GitHub Integration:**
- Repository: `your-org/kraftdintel`
- Branch: `main` (auto-deploy on push)
- Status: ✅ Connected
- Last Deployment: 2026-01-17 14:23 UTC

**Performance Metrics:**
- CDN: Enabled (global edge nodes)
- Cache: Browser cache 24 hours
- Compression: GZIP enabled
- Page Load Time: ~1.2 seconds (p95)

---

## Backend Infrastructure

### Azure Container Apps
**Resource ID:** `/subscriptions/{sub-id}/resourceGroups/kraftdintel/providers/Microsoft.App/containerApps/kraftdintel-backend`

**Configuration:**
```
Name: kraftdintel-backend
Region: UAE North
Environment: Container Apps
Managed Environment: kraftdintel-env
Replica Range: 1-10 (auto-scale)
```

**Container Configuration:**
```
Image: {registry}.azurecr.io/kraftdintel-backend:latest
Port: 8000
Memory: 1 Gi
vCPU: 0.5
Startup Command: uvicorn main:app --host 0.0.0.0 --port 8000
Health Check: GET /health (every 10s)
```

**Auto-Scaling Rules:**
```
Metric: CPU usage
Target: 70% average
Min replicas: 1
Max replicas: 10
Scale-out trigger: > 70% CPU
Scale-in delay: 300 seconds
```

**Environment Variables:**
```
LOG_LEVEL=INFO
API_WORKERS=4
CONNECTION_POOL_SIZE=10
```

**Secrets (from Key Vault):**
```
COSMOS_CONNECTION_STRING
AZURE_STORAGE_CONNECTION_STRING
DOCUMENT_INTELLIGENCE_KEY
JWT_SECRET_KEY
```

**Network Configuration:**
```
Ingress: Enabled
Allow traffic from: Static Web App
Traffic: 100% to latest revision
External IP: (assigned by Azure)
```

**Monitoring:**
```
Application Insights: Connected
Logs: Enabled
Metrics: CPU, Memory, Request rate
Alerts: P0 if unhealthy 5+ minutes
```

---

## Database Infrastructure

### Cosmos DB (MongoDB API)
**Resource ID:** `/subscriptions/{sub-id}/resourceGroups/kraftdintel/providers/Microsoft.DocumentDB/databaseAccounts/kraftdintel-mongo`

**Configuration:**
```
Name: kraftdintel-mongo
Region: West Europe (primary)
API: MongoDB (v4.0 compatible)
Account Type: Single write region
Consistency: Strong
```

**Collections:**
```
- users (25 GB partition)
- documents (500 GB partition)
- extracted_data (500 GB partition)
- workflows (100 GB partition)
- quotations (300 GB partition)
- comparisons (100 GB partition)
- purchase_orders (150 GB partition)
- audit_log (1 TB partition)
```

**Performance:**
```
Database Throughput: 1000 RU/s (shared)
Collection Allocation: Auto-scale
Max RU/s: 10,000
Current usage: ~300 RU/s average
```

**Backup:**
- Mode: Automatic backups
- Frequency: Hourly
- Retention: 30 days
- PITR (Point-in-time restore): Enabled

**Security:**
```
Encryption: At-rest (enabled)
Network: Private endpoint available
IP Whitelist: 
  - Static Web App IP
  - Container Apps IP
  - Development IPs
```

**Connection String:**
```
mongodb+srv://<user>:<pass>@kraftdintel-mongo.mongo.cosmos.azure.com:10255/?retryWrites=false
```

**Failover:**
- Failover: Manual enabled
- Failover regions: East Europe (on-demand)

---

## Storage Infrastructure

### Blob Storage Account
**Resource ID:** `/subscriptions/{sub-id}/resourceGroups/kraftdintel/providers/Microsoft.Storage/storageAccounts/kraftdintelblob`

**Configuration:**
```
Name: kraftdintelblob
Region: East US (cost optimized)
Tier: Standard (Hot)
Replication: LRS (Local Redundant)
Encryption: Microsoft-managed keys
```

**Containers:**
```
- documents/ (Original uploaded files)
- extractions/ (Extraction results)
- exports/ (Generated PDFs/Excel)
- previews/ (Document previews)
- temp/ (Temporary files, TTL 7 days)
```

**Capacity:**
```
Current usage: ~25 GB
Max quota: 100 TB (unlimited)
Growth rate: ~500 MB/month
```

**Access Control:**
```
Authentication: Managed identity
Shared access signatures: 1-hour expiry
Public access: None (all private)
```

---

## Secrets Management

### Key Vault
**Resource ID:** `/subscriptions/{sub-id}/resourceGroups/kraftdintel/providers/Microsoft.KeyVault/vaults/kraftdintel-kv`

**Configuration:**
```
Name: kraftdintel-kv
Region: West Europe
Sku: Standard
Purge protection: Enabled
```

**Secrets Stored:**
```
JWT_SECRET_KEY
COSMOS_CONNECTION_STRING
AZURE_STORAGE_CONNECTION_STRING
DOCUMENT_INTELLIGENCE_KEY
DOCUMENT_INTELLIGENCE_ENDPOINT
EMAIL_SERVICE_API_KEY
GITHUB_WEBHOOK_SECRET
```

**Access Policies:**
```
- Container Apps (managed identity): Get, List, Decrypt
- Deployment service: Get, Set, Delete
- Admin group: Full access
```

**Rotation Schedule:**
```
- JWT_SECRET_KEY: Never (not rotatable)
- API Keys: Quarterly
- Passwords: Quarterly
- Access Keys: Quarterly
- Audit: Monthly
```

---

## Monitoring & Diagnostics

### Application Insights
**Resource ID:** `/subscriptions/{sub-id}/resourceGroups/kraftdintel/providers/Microsoft.Insights/components/kraftdintel-ai`

**Configuration:**
```
Name: kraftdintel-ai
Region: West Europe
Retention: 90 days
```

**Tracked Metrics:**
```
- Page views (frontend)
- Server requests (backend)
- Failed requests
- Server response time
- Custom events
```

**Alerts Configured:**
```
- Backend unhealthy > 5 minutes: Alert
- Failed requests > 5%: Alert
- Response time > 2 seconds: Warning
- CPU > 80%: Alert
- Memory > 85%: Alert
- Request rate spikes: Alert
```

**Dashboards:**
```
- Overview: Health and performance
- Performance: Latency, throughput
- Failures: Error rates, exception details
- Users: Active users, sessions
```

---

## Network & Security

### Network Security Groups
**Resource ID:** `/subscriptions/{sub-id}/resourceGroups/kraftdintel/providers/Microsoft.Network/networkSecurityGroups/kraftdintel-nsg`

**Inbound Rules:**
```
Priority | Source | Protocol | Port | Action | Description
10       | Any    | TCP      | 443  | Allow  | HTTPS traffic
20       | Any    | TCP      | 80   | Deny   | Redirect to HTTPS
```

**Outbound Rules:**
```
Priority | Destination | Protocol | Port | Action | Description
10       | Azure       | TCP      | 443  | Allow  | Azure services
100      | Internet    | TCP      | 443  | Allow  | External APIs
```

### Firewall Configuration
```
Database firewall:
- Allow Static Web App IP
- Allow Container Apps IP
- Allow development IPs (conditional)

Storage firewall:
- Allow Container Apps network
- Allow CORS: https://jolly-coast-03a4f4d03.4.azurestaticapps.net
```

---

## DNS & CDN

### Custom Domain
```
Domain: https://jolly-coast-03a4f4d03.4.azurestaticapps.net
SSL Certificate: Auto-managed (*.azurestaticapps.net)
Status: ✅ Active
```

### CDN
```
Provider: Azure CDN (part of Static Web App)
Location: Global edge nodes
Cache rules: 24 hours for static assets
GZIP: Enabled
```

---

## Backup & Disaster Recovery

### Backup Strategy
```
Database:
- Frequency: Automatic hourly
- Retention: 30 days
- Recovery: Point-in-time restore

Storage:
- Geo-replication: Not enabled (cost)
- Backup: Manual snapshots before major changes
- Recovery time: < 1 hour

Configuration:
- Stored in: GitHub repository (IaC)
- Backup: Every push to main
```

### RTO/RPO
```
RTO (Recovery Time Objective): 4 hours
RPO (Recovery Point Objective): 1 hour
Critical data: Cosmos DB backups, GitHub repo
```

---

## Regional Failover

**Primary Region:** West Europe
**Failover Region:** East Europe (on-demand)

**Failover Process:**
1. Detect outage (manual or automated)
2. Failover Cosmos DB to East Europe
3. Update DNS to point to failover region
4. Redeploy backend to failover region
5. Verify all systems healthy

**Failover Time:** ~30 minutes

---

## Cost Optimization

### Current Costs
```
Monthly Estimate: $162.60
- Static Web App: $12 (free tier adequate)
- Container Apps: $50 (1 vCPU, 1 GB memory)
- Cosmos DB: $80 (1000 RU/s)
- Storage: $5 (< 100 GB)
- Other: $15.60
```

### Cost Reduction Opportunities
```
- Use reserved instances: Save 30-40%
- Reduce Cosmos DB RU to 500: Save $40/month
- Archive old documents: Save $5-10/month
- Use cheaper region: Save $5/month
```

### Cost Monitoring
```
Azure Cost Management:
- Budget alert: $200/month
- Forecast: Within budget
- Review: Monthly
```

---

## Maintenance Schedule

### Weekly Tasks
- [ ] Check Azure Service Health
- [ ] Review Application Insights alerts
- [ ] Check backup completion

### Monthly Tasks
- [ ] Review cost trends
- [ ] Update security patches
- [ ] Rotate credentials
- [ ] Performance review
- [ ] Capacity planning

### Quarterly Tasks
- [ ] Disaster recovery drill
- [ ] Security audit
- [ ] Compliance review
- [ ] Cost optimization review

---

## Escalation & Support

**Azure Support Level:** Standard ($100/month)
- Response time: 1 hour for P1
- 4 hours for P2

**Support Contact:** support@microsoft.com
**Support Plan:** Standard

---

**Reference:** `/docs/04-deployment/INFRASTRUCTURE_INVENTORY_v1.0.md`
