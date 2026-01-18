# Incident Response Procedures v1.0

**Document**: Incident Response Guide  
**Version**: 1.0  
**Last Updated**: January 2026  
**Audience**: Operations Team, SREs, DevOps Engineers

---

## Overview

This guide provides step-by-step procedures for responding to common incidents in the KraftdIntel system. Follow these procedures to minimize impact and restore service quickly.

---

## 1. Authentication System Down (Login/Register Not Working)

### Severity: CRITICAL
**Impact**: Users cannot access the system  
**Response Time**: < 5 minutes  
**Escalation**: Immediate

### Detection
- Login endpoint returns 500 errors
- Dashboard shows "Authentication service unavailable"
- Users report "Cannot sign in"

### Investigation Steps
1. **Check backend service status**
   ```powershell
   # Check if backend is running
   netstat -ano | findstr :8000
   
   # Check Python process
   tasklist | findstr python
   ```

2. **Verify database connection**
   ```powershell
   # SSH to backend and test
   cd backend
   .venv\Scripts\Activate.ps1
   python -c "from services.cosmos_service import CosmosService; print('DB OK')"
   ```

3. **Check environment variables**
   ```powershell
   # Verify Azure credentials
   echo $env:COSMOS_ENDPOINT
   echo $env:COSMOS_KEY
   ```

### Resolution

**Option A: Restart Backend (Most Common)**
```powershell
# Kill existing process
taskkill /IM python.exe /F

# Wait 2 seconds
Start-Sleep -Seconds 2

# Start with environment variables
cd backend
.venv\Scripts\Activate.ps1
$env:COSMOS_ENDPOINT="https://YOUR_ENDPOINT/"
$env:COSMOS_KEY="YOUR_KEY"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level warning
```

**Option B: Check Azure Cosmos DB**
- Login to Azure Portal
- Navigate to Cosmos DB account
- Check "Metrics" for connectivity issues
- Verify throughput and quotas

**Option C: Check Network/Firewall**
- Verify backend can reach Cosmos DB endpoint
- Check Azure NSG rules
- Verify HTTPS connectivity to cosmos.azure.com

### Verification
- [ ] Login endpoint responds with HTTP 200
- [ ] User can register new account
- [ ] Tokens are generated correctly
- [ ] Dashboard loads after login

### Communication
- Notify users: "Authentication service restored"
- Document incident in INCIDENT_LOG.txt
- Post-mortem within 24 hours

---

## 2. Database Connection Timeout

### Severity: HIGH
**Impact**: Document operations fail, exports cannot complete  
**Response Time**: < 10 minutes  
**Escalation**: DevOps → Azure Support

### Detection
- Document upload returns 503 errors
- Export process hangs and times out
- Cosmos DB connection pooling shows timeouts

### Investigation Steps
1. **Check Cosmos DB availability**
   ```
   Azure Portal → Cosmos DB → Service Health
   Look for active incidents or maintenance
   ```

2. **Check connection string**
   ```powershell
   # Verify endpoint format
   echo $env:COSMOS_ENDPOINT
   # Should be: https://[account].documents.azure.com:443/
   ```

3. **Check throughput**
   - Portal → Cosmos DB → Scale & Settings
   - Verify RU/s is sufficient (at least 400 RU/s)
   - Check Request Units metrics

4. **Check network connectivity**
   ```powershell
   # Test connection
   Test-NetConnection -ComputerName "YOUR_COSMOS_ENDPOINT" -Port 443
   ```

### Resolution

**If Throughput Issue**:
1. Azure Portal → Cosmos DB → Scale & Settings
2. Increase RU/s (auto-scaling recommended)
3. Monitor Request Units metric
4. Restart API server

**If Connection Issue**:
1. Verify firewall rules allow outbound 443
2. Check NSG rules in virtual network
3. Verify service endpoint is accessible
4. Contact Azure Support if persistent

**If Maintenance Window**:
1. Switch to read-only mode
2. Queue operations
3. Notify users of temporary service limitation
4. Resume when Cosmos DB is back online

### Verification
- [ ] Document upload completes without timeout
- [ ] Export tracking shows progress
- [ ] Cosmos metrics show normal RU consumption
- [ ] No 503 errors in logs

---

## 3. Email Service Failure (SendGrid Down)

### Severity: MEDIUM
**Impact**: Email notifications, password recovery blocked  
**Response Time**: < 15 minutes  
**Escalation**: Email service provider

### Detection
- Verify email fails with 400-500 error codes
- Password recovery emails not sent
- SendGrid webhook shows failures

### Investigation Steps
1. **Check SendGrid status**
   - Visit status.sendgrid.com
   - Check SendGrid dashboard for API errors

2. **Verify API key**
   ```powershell
   echo $env:SENDGRID_API_KEY
   # Should be: SG.XXXXXXXXXXXXX
   ```

3. **Check rate limits**
   - SendGrid dashboard → Stats
   - Verify not hitting rate limits (100 emails/second default)

### Resolution

**Immediate (No emails)**:
1. Update application to queue emails
2. Store failed email attempts in database
3. Notify users of email service issues
4. Retry automatically every 5 minutes

**When Service Recovers**:
1. Verify SendGrid is operational
2. Process queued emails
3. Check delivery logs
4. Resume normal operation

**Alternative (Long-term)**:
1. Set up Azure Email Communication Services
2. Configure as backup email provider
3. Implement failover logic in email_service.py

### Verification
- [ ] Test email sends through SendGrid successfully
- [ ] Verify email rate limits not exceeded
- [ ] Check delivery logs for confirmation
- [ ] Verify webhook callbacks are received

---

## 4. High API Latency (Slow Responses)

### Severity: MEDIUM
**Impact**: User experience degradation, timeouts  
**Response Time**: < 20 minutes  
**Escalation**: Performance Engineer

### Detection
- API responses taking >2 seconds
- Users report "slow loading" issues
- Application Insights shows high P95 latency

### Investigation Steps
1. **Check Application Insights**
   - Azure Portal → Application Insights
   - Review Performance → Slow Requests
   - Identify which endpoints are slow
   - Check dependency performance (Cosmos DB, SendGrid)

2. **Check backend metrics**
   ```powershell
   # SSH to backend
   # Tail logs and look for slow operations
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
   ```

3. **Check database performance**
   - Azure Portal → Cosmos DB → Metrics
   - Look for high latency, throttling, or exceeded RU/s
   - Check individual partition performance

4. **Check network**
   - Verify consistent latency to Azure
   - Check regional failover status
   - Verify no DDoS protection triggered

### Resolution

**High Cosmos DB Latency**:
1. Increase RU/s (auto-scaling recommended)
2. Optimize queries (use partition key filters)
3. Check partition balance
4. Enable read replicas if needed

**High CPU/Memory Usage**:
1. Check for memory leaks (restart backend)
2. Implement request queuing
3. Scale up backend resources
4. Profile slow code paths

**Network Issues**:
1. Verify firewall rules
2. Check Azure region health
3. Enable traffic manager failover if available
4. Switch to read-only if necessary

### Verification
- [ ] API responses < 500ms (P99)
- [ ] Cosmos DB latency < 20ms
- [ ] No RU/s throttling
- [ ] Users report normal performance

---

## 5. Storage Issues (Disk Full, Upload Failures)

### Severity: MEDIUM-HIGH
**Impact**: Document uploads blocked, exports fail  
**Response Time**: < 10 minutes  
**Escalation**: Storage administrator

### Detection
- File upload returns 507 Insufficient Storage
- Exports cannot be saved
- Temporary files cannot be created

### Investigation Steps
1. **Check disk space**
   ```powershell
   # Check Windows drive
   Get-Volume | Where-Object {$_.DriveLetter -eq 'C'} | 
     Select-Object DriveLetter, Size, SizeRemaining
   ```

2. **Check upload directory**
   ```powershell
   # Find large directories
   Get-ChildItem -Path "C:\KraftdIntel\uploads" -Recurse |
     Measure-Object -Property Length -Sum
   ```

3. **Check temporary files**
   ```powershell
   # Remove old temp files
   ls $env:TEMP | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)}
   ```

### Resolution

**Immediate**:
1. Remove temporary files older than 30 days
2. Archive old uploads to cold storage
3. Clear cache directories
4. Restart application services

**Long-term**:
1. Implement automatic cleanup of old files
2. Move uploads to Azure Blob Storage
3. Implement quota management
4. Alert when disk usage > 80%

---

## 6. Authentication Token Expired (User Logged Out)

### Severity: LOW
**Impact**: User must re-login after 60 minutes  
**Response Time**: N/A (by design)  
**Notes**: This is expected behavior

### How Users Experience It
- User working for 60+ minutes
- Try to perform action
- See "Session expired" message
- Must click "Login again"
- Redirected to login page
- Auto-login with saved credentials (if enabled)

### What Happens Behind the Scenes
1. Access token expires after 60 minutes
2. Frontend detects 401 Unauthorized response
3. Frontend attempts token refresh using refresh token
4. If refresh succeeds → new access token issued, user continues
5. If refresh fails → redirect to login

### What Users Should Do
- Click "Login again"
- System may pre-fill email (if saved)
- Enter password
- Redirected back to previous page

### What Admins Should Know
- This is normal behavior (by design)
- Tokens expire for security
- Users won't lose work if they save often
- Consider longer expiry for internal users (if needed)

---

## 7. Service Health Check

### Daily Health Check (Quick - 5 minutes)

Run this daily to verify system health:

```powershell
# Check 1: Backend running
$health = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/health"
if ($health.StatusCode -eq 200) { 
    Write-Host "✓ Backend is healthy"
} else {
    Write-Host "✗ Backend returned status $($health.StatusCode)"
}

# Check 2: Database connection
# (Embedded in health endpoint)

# Check 3: Authentication working
$login = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/auth/profile" `
    -Headers @{"Authorization"="Bearer YOUR_TEST_TOKEN"}
Write-Host "✓ Auth system responsive"

# Check 4: Export service working
$exports = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/exports"
Write-Host "✓ Export service responding"
```

### Weekly Health Check (15 minutes)

- [ ] Full system restart (backend + frontend)
- [ ] Run authentication flow tests
- [ ] Test document upload → export workflow
- [ ] Verify all email notifications sending
- [ ] Check Azure resource metrics
- [ ] Review error logs for warnings

---

## Escalation Contacts

**Level 1**: Check status, attempt basic restart
**Level 2**: Review logs, check Azure portal
**Level 3**: Contact Azure Support (critical infrastructure issues)
**Level 4**: Contact SendGrid Support (email delivery issues)

---

## Incident Logging

After every incident, record:
1. **Time**: When did it start?
2. **Severity**: Critical/High/Medium/Low
3. **Duration**: How long was service down?
4. **Root Cause**: What caused it?
5. **Resolution**: How was it fixed?
6. **Prevention**: How do we prevent this next time?

Log all incidents in: `INCIDENT_LOG.txt`

---

## Post-Mortem Template

For significant incidents:

```
INCIDENT POST-MORTEM

Title: [Brief description]
Date: [Date/Time]
Severity: [Critical/High/Medium/Low]
Duration: [Start - End time]
Impact: [Number of users affected, business impact]

Root Cause Analysis:
[What caused this incident?]

Timeline:
[Exact sequence of events]

Resolution:
[What fixed it?]

Prevention:
[How do we prevent this in the future?]

Action Items:
- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

Status: [Open/Closed]
Owner: [Who's responsible for follow-up]
```

---

## Quick Reference

| Incident | Severity | Time | Check |
|----------|----------|------|-------|
| Auth down | CRITICAL | <5min | Backend running, DB connection |
| DB timeout | HIGH | <10min | Cosmos RU/s, throughput |
| Email failure | MEDIUM | <15min | SendGrid status, API key |
| High latency | MEDIUM | <20min | DB metrics, CPU usage |
| Storage full | MEDIUM-HIGH | <10min | Disk space, old files |
| Token expired | LOW | N/A | User re-login (expected) |

---

## Additional Resources

- [Cosmos DB Troubleshooting](https://learn.microsoft.com/azure/cosmos-db/troubleshoot-bad-request)
- [Azure Health Status](https://status.azure.com)
- [SendGrid Status](https://status.sendgrid.com)
- [Application Insights Guide](https://learn.microsoft.com/azure/azure-monitor/app/app-insights-overview)

---

**Document Complete** - Last updated January 2026
