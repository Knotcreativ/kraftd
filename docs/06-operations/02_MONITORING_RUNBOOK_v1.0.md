# Monitoring Runbook v1.0

**Document**: System Monitoring Guide  
**Version**: 1.0  
**Last Updated**: January 2026  
**Audience**: Operations Team, On-Call Engineers, DevOps

---

## Overview

This guide explains how to monitor KraftdIntel system health, interpret metrics, and set up alerts. Regular monitoring prevents incidents before they impact users.

---

## 1. Monitoring Dashboard

### Azure Application Insights

**Location**: Azure Portal → Application Insights → "KraftdIntel-AppInsights"

**Key Metrics to Monitor**:

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Availability | > 99.5% | 95-99.5% | < 95% |
| Avg Response Time | < 500ms | 500-2000ms | > 2000ms |
| Failed Requests | < 1% | 1-5% | > 5% |
| Server Exceptions | < 10/hour | 10-100/hour | > 100/hour |
| Dependency Failures | < 1% | 1-5% | > 5% |

### Daily Dashboard Check (5 minutes)

1. **Open Application Insights**
   - Azure Portal → Application Insights → KraftdIntel-AppInsights
   - Click "Overview"

2. **Check Availability**
   - Should show > 99% availability
   - If < 99%, click to see failed transactions

3. **Check Failed Requests**
   - Look at "Failed requests" chart
   - Should be flat near 0
   - If spike, check which endpoint is failing

4. **Check Performance**
   - Look at "Server response time" chart
   - P95 should be < 1 second
   - P99 should be < 2 seconds

5. **Check Exceptions**
   - Look at "Server exceptions" chart
   - Should be minimal (< 10/hour)
   - Click exceptions to see details

### Custom Queries

```kusto
// Failed requests last 24 hours
requests
| where timestamp > ago(24h)
| where success == false
| summarize count() by resultCode, name
| sort by count_ desc

// Slow endpoints
requests
| where timestamp > ago(1h)
| where duration > 2000
| project name, duration, timestamp
| sort by duration desc

// Exception rate
exceptions
| where timestamp > ago(24h)
| summarize count() by tostring(customMeasurements.severity)

// Dependency failures (Cosmos DB)
dependencies
| where timestamp > ago(1h)
| where success == false
| project name, resultCode, duration, timestamp
```

---

## 2. Azure Cosmos DB Monitoring

### Cosmos DB Metrics

**Location**: Azure Portal → Cosmos DB Account → Metrics

**Key Metrics**:

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| RU Consumption | < 80% capacity | 80-95% | > 95% |
| Latency (p99) | < 20ms | 20-100ms | > 100ms |
| Throttled Requests | 0 | < 1% | > 1% |
| Replication Lag | < 100ms | 100-500ms | > 500ms |

### Daily Cosmos Check (5 minutes)

1. **Open Cosmos DB**
   - Azure Portal → Cosmos DB → Your Account
   - Click "Metrics"

2. **Check Request Units**
   - Select metric: "Normalized RU Consumption by Partition Key"
   - Should see usage < 80% of provisioned
   - If > 90%, plan to increase RU/s

3. **Check Latency**
   - Select metric: "Server-side Latency (p99)"
   - Should be < 20ms
   - If > 100ms, check network or container throughput

4. **Check Throttling**
   - Select metric: "Throttled Requests"
   - Should be 0
   - If > 0, increase RU/s immediately

5. **Check Availability**
   - Select metric: "Service Availability"
   - Should be 99.99%
   - If < 100%, contact Azure Support

### RU/s Scaling

**When to Increase**:
- If using > 80% of provisioned RU/s
- If getting 429 "Too Many Requests" errors
- If seeing increased latency

**How to Increase**:
```
Azure Portal → Cosmos DB → Scale & Settings → 
Select container → Increase RU/s (recommend auto-scale)
```

**Cost Impact**:
- Provisioned: $0.12 per RU/s per hour
- Auto-scale: Pay only for what you use (4-6x multiplier)
- Recommendation: Use auto-scale (200-4000 RU/s)

---

## 3. Backend Service Monitoring

### Backend Health Check

**Endpoint**: `GET http://YOUR_API/api/v1/health`

**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-18T12:00:00Z",
  "database": "connected",
  "version": "1.0.0"
}
```

### Manual Health Check Script

```powershell
# Test backend health
$uri = "http://127.0.0.1:8000/api/v1/health"
$response = Invoke-WebRequest -Uri $uri -ErrorAction SilentlyContinue

if ($response) {
    Write-Host "✓ Backend healthy" -ForegroundColor Green
    Write-Host "Response: $($response.Content)"
} else {
    Write-Host "✗ Backend unhealthy" -ForegroundColor Red
    Write-Host "Check if service is running: netstat -ano | findstr :8000"
}
```

### Automated Monitoring

**Create Scheduled Task** (runs every 5 minutes):

```powershell
# Health check script: health_check.ps1
$uri = "http://127.0.0.1:8000/api/v1/health"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

try {
    $response = Invoke-WebRequest -Uri $uri -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Add-Content -Path "health_log.txt" -Value "$timestamp - OK"
    } else {
        Add-Content -Path "health_log.txt" -Value "$timestamp - ERROR: Status $($response.StatusCode)"
    }
} catch {
    Add-Content -Path "health_log.txt" -Value "$timestamp - ERROR: $($_.Exception.Message)"
}
```

### Key Indicators

- **Memory Usage**: Should be < 500MB
- **CPU Usage**: Should be < 50% average
- **Request Rate**: Should be stable (spikes < 2x baseline)
- **Error Rate**: Should be < 1%

---

## 4. Frontend Monitoring

### Browser Console Errors

**Check**:
1. Open http://localhost:3000 (or production URL)
2. Press F12 (Developer Tools)
3. Click "Console" tab
4. Look for red error messages
5. Record any errors for investigation

### Frontend Performance Metrics

**Check via Developer Tools**:
1. F12 → "Network" tab
2. Load dashboard
3. Check:
   - Total page load time: Should be < 3 seconds
   - API response time: Should be < 500ms
   - Bundle size: Should be < 500KB

### Common Frontend Issues

| Issue | Sign | Fix |
|-------|------|-----|
| Old cache | Page shows stale data | Ctrl+Shift+Delete (clear cache) |
| Token expired | "Login again" message | Re-authenticate |
| Network error | API calls fail | Check backend connectivity |
| CSS broken | Styling looks wrong | Check CSS files loaded in Network tab |

---

## 5. Alert Configuration

### Azure Alerts (Critical - must have)

**Alert 1: High Error Rate**
```
Condition: Failed Requests > 5% over 5 minutes
Action: Email ops team + create incident
Severity: HIGH
```

**Alert 2: Low Availability**
```
Condition: Availability < 95% over 30 minutes
Action: Email ops team + page on-call engineer
Severity: CRITICAL
```

**Alert 3: Cosmos DB Throttling**
```
Condition: Throttled Requests > 0 over 1 minute
Action: Email ops team + auto-increase RU/s
Severity: HIGH
```

**Alert 4: High Latency**
```
Condition: Server response time (p99) > 2000ms over 5 minutes
Action: Email ops team + alert performance team
Severity: MEDIUM
```

**Alert 5: Backend Down**
```
Condition: Health endpoint unreachable for 2 minutes
Action: Page on-call engineer immediately
Severity: CRITICAL
```

### Setting Up Alerts

```
Azure Portal → Application Insights → Alerts → 
New Alert Rule → Create custom condition above
```

---

## 6. Log Monitoring

### Backend Logs

**Location**: Application Insights → Logs

**Query for errors**:
```kusto
traces
| where timestamp > ago(24h)
| where severityLevel >= 2 // Error and above
| project message, timestamp, operation_Name
| sort by timestamp desc
```

**Query for slow requests**:
```kusto
requests
| where timestamp > ago(1h)
| where duration > 1000
| project name, duration, timestamp
| sort by duration desc
```

### Log Levels

- **DEBUG**: Development only
- **INFO**: Normal operations
- **WARNING**: Something unexpected, but recoverable
- **ERROR**: Something failed, needs investigation
- **CRITICAL**: System cannot continue, needs immediate action

### Common Log Patterns

| Pattern | Meaning | Action |
|---------|---------|--------|
| "Connection timeout" | Can't reach database | Check Cosmos DB, network |
| "429 Too Many Requests" | Rate limited | Increase RU/s |
| "Authentication failed" | Bad credentials | Check token, re-login |
| "File not found" | Missing resource | Check deployment |

---

## 7. Weekly Monitoring Report

### Generate Weekly Report (Friday 5 PM)

```kusto
// Weekly metrics summary
let start = ago(7d);
requests
| where timestamp > start
| summarize 
    Total_Requests = count(),
    Failed_Requests = countif(success == false),
    Avg_Duration = avg(duration),
    P95_Duration = percentile(duration, 95),
    P99_Duration = percentile(duration, 99)
    by bin(timestamp, 1d)
```

### Email Report Format

```
WEEKLY MONITORING REPORT
Week: Jan 15-21, 2026

Availability: 99.95% ✓
Failed Requests: 0.3% ✓
Avg Response Time: 245ms ✓
P99 Response Time: 1200ms ✓
Server Exceptions: 8 total
Cosmos DB Throttles: 0 ✓

Issues Found:
- Slow requests on Monday (resolved)
- One authentication service restart
- Normal operation otherwise

Recommendations:
- Continue monitoring
- Plan for increased load (peak at 2 PM)
- No immediate action needed
```

---

## 8. On-Call Runbook

### Starting On-Call Shift

1. **Setup**
   - [ ] Save monitoring dashboard as bookmark
   - [ ] Get on-call phone number/pager
   - [ ] Update status message (Slack/Teams)
   - [ ] Test alert notification channels

2. **First Check**
   - [ ] Verify all systems show green
   - [ ] Check logs for warnings
   - [ ] Review incident log for context

### During Shift

**Every Hour**:
- [ ] Check Application Insights dashboard
- [ ] Verify Cosmos DB metrics
- [ ] Scan error logs

**On Alert**:
1. Check alert details
2. Determine severity (Critical/High/Medium/Low)
3. Start troubleshooting (see Incident Response guide)
4. Escalate if needed
5. Document everything
6. Post-mortem within 24 hours

### Ending On-Call Shift

1. **Handoff**
   - [ ] Brief next engineer on status
   - [ ] Mention any ongoing issues
   - [ ] Share recent incident logs

2. **Cleanup**
   - [ ] Clear dashboard filters
   - [ ] Close any incident tickets
   - [ ] Update status messages

---

## 9. Performance Benchmarks

### Expected Performance (Baseline)

**API Endpoints**:
```
GET  /api/v1/health              < 50ms
GET  /api/v1/auth/profile        < 100ms
POST /api/v1/auth/login          < 500ms
POST /api/v1/auth/register       < 1000ms
POST /api/v1/documents/upload    < 2000ms
POST /api/v1/documents/convert   < 5000ms
POST /api/v1/exports             < 3000ms
```

**Frontend Pages**:
```
Page Load Time (First Paint)     < 1000ms
Page Load Time (Interactive)     < 2000ms
Script Bundle Size               < 500KB
API Response Time               < 500ms
```

**Database Operations**:
```
User Lookup (by email)          < 20ms
Document Retrieve              < 50ms
Export Tracking Write          < 100ms
User Profile Read              < 30ms
```

---

## 10. Dashboard Recommendations

### Create Custom Dashboard

**What to Add**:
1. Availability (last 24 hours)
2. Failed Requests chart
3. Response time (avg, p95, p99)
4. RU consumption (Cosmos DB)
5. Server exceptions list
6. Active users count
7. Top slow endpoints

**Location**:
```
Azure Portal → Application Insights → 
Workbooks → Create New → Add charts
```

---

## Quick Reference

**Daily Checks** (5 minutes):
- [ ] App Insights dashboard
- [ ] Cosmos DB metrics
- [ ] Backend health endpoint
- [ ] No critical alerts

**Weekly Checks** (30 minutes):
- [ ] Full performance metrics
- [ ] Log review
- [ ] Generate report
- [ ] Plan any scaling needed

**Monthly Checks** (1 hour):
- [ ] Capacity planning
- [ ] Cost optimization
- [ ] Security audit
- [ ] Documentation updates

---

## Useful Links

- [Azure Application Insights](https://portal.azure.com/#blade/HubsExtension/BrowseResourceBlade/resourceType/microsoft.insights%2Fcomponents)
- [Cosmos DB Metrics](https://portal.azure.com/#blade/HubsExtension/BrowseResourceBlade/resourceType/Microsoft.DocumentDB%2FdatabaseAccounts)
- [Azure Health Status](https://status.azure.com)
- [SendGrid Status](https://status.sendgrid.com)

---

**Document Complete** - Last updated January 2026
