# Maintenance Schedule v1.0

**Document**: Regular Maintenance Procedures  
**Version**: 1.0  
**Last Updated**: January 2026  
**Audience**: Operations Team, DevOps Engineers

---

## Overview

Regular maintenance prevents incidents, improves performance, and ensures system reliability. Follow this schedule to keep KraftdIntel running smoothly.

---

## Daily Maintenance (5-10 minutes)

### Morning Check (8:00 AM)

**Tasks**:
```powershell
# 1. Check system health
curl http://127.0.0.1:8000/api/v1/health

# 2. Verify processes running
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# 3. Check storage space
Get-Volume C: | Select-Object SizeRemaining

# 4. Review error logs
# Open Application Insights → Logs
# Check for exceptions overnight
```

**Expected Results**:
- [ ] Health endpoint returns 200
- [ ] Backend and frontend processes running
- [ ] > 1GB disk space available
- [ ] < 10 exceptions overnight

### Evening Check (5:00 PM)

**Tasks**:
```powershell
# 1. Health check again
curl http://127.0.0.1:8000/api/v1/health

# 2. Check daily activity
# Application Insights → Overview
# Verify normal request volume

# 3. Check error count
# Application Insights → Failed Requests
# Should be < 1% of total requests

# 4. Memory check
Get-Process python | Select-Object ProcessName, @{
  Name="MemoryMB"; Expression={$_.WorkingSet/1MB}
}
# Should be < 500MB
```

---

## Weekly Maintenance (30 minutes - Friday afternoon)

### Weekly System Restart

**Purpose**: Clear caches, release memory, reset connections

**Schedule**: Friday at 5 PM (after business hours)

**Steps**:

1. **Notify users** (optional):
   - If production, announce maintenance window
   - Inform users 1 hour before

2. **Stop services**:
   ```powershell
   # Kill backend
   taskkill /IM python.exe /F
   
   # Kill frontend
   taskkill /IM node.exe /F
   
   # Wait for graceful shutdown
   Start-Sleep -Seconds 5
   ```

3. **Verify stopped**:
   ```powershell
   tasklist | findstr python
   tasklist | findstr node
   # Should show no results
   ```

4. **Restart backend**:
   ```powershell
   cd backend
   .venv\Scripts\Activate.ps1
   $env:COSMOS_ENDPOINT="https://YOUR_ENDPOINT/"
   $env:COSMOS_KEY="YOUR_KEY"
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```

5. **Restart frontend**:
   ```powershell
   cd frontend
   npm run dev
   ```

6. **Verify working**:
   - [ ] Health check returns 200
   - [ ] Can login at http://localhost:3000
   - [ ] Dashboard loads
   - [ ] No error messages

7. **Post-restart**:
   - Monitor for 10 minutes
   - Check error logs
   - Notify users if applicable

### Weekly Backup Check

**Purpose**: Verify backups are working

**Steps**:

1. **Check Cosmos DB backups**:
   ```
   Azure Portal → Cosmos DB → 
   Features → Backup and Restore
   Look for recent backups
   ```

2. **Verify backup location**:
   - Backups should be in secondary region
   - Check last backup timestamp
   - Ensure no errors in backup logs

3. **Test recovery procedure** (monthly):
   ```
   In test environment:
   Restore from last backup
   Verify all data present
   Verify no data loss
   ```

### Weekly Log Archive

**Purpose**: Keep logs manageable

**Steps**:

```powershell
# Archive logs older than 30 days
$logPath = "C:\KraftdIntel\logs"
$archivePath = "C:\KraftdIntel\logs\archive"

if (!(Test-Path $archivePath)) {
    New-Item -ItemType Directory -Path $archivePath
}

# Move old logs
Get-ChildItem -Path $logPath -Filter "*.log" | 
  Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} |
  Move-Item -Destination $archivePath

Write-Host "Logs archived successfully"
```

### Weekly Security Review

**Purpose**: Detect suspicious activity

**Checks**:
1. [ ] Failed login attempts normal (< 100/day)
2. [ ] No unusual API usage patterns
3. [ ] No suspicious user accounts
4. [ ] All access logs being recorded

---

## Monthly Maintenance (1-2 hours)

### 1st of Month: Full System Review

**Purpose**: Comprehensive health assessment

**Tasks**:

1. **Performance Analysis**:
   ```kusto
   // Check average performance metrics
   requests
   | where timestamp > ago(30d)
   | summarize 
       AvgDuration = avg(duration),
       P95Duration = percentile(duration, 95),
       FailureRate = countif(success == false) / count()
       by tostring(bin(timestamp, 1d))
   ```

2. **Capacity Planning**:
   - Cosmos DB: Check if approaching RU/s limit
   - Storage: Check upload folder size
   - Memory: Check trending memory usage
   - CPU: Check peak usage patterns

3. **Cost Analysis**:
   - Azure Cost Management → Cosmos DB costs
   - Check for unexpected increases
   - Review RU/s consumption
   - Optimize if needed

4. **Update Check**:
   ```powershell
   # Check for Python package updates
   cd backend
   pip list --outdated
   
   # Review: should update security patches only
   pip install --upgrade [PACKAGE]
   ```

5. **Documentation Update**:
   - [ ] Update this maintenance schedule if needed
   - [ ] Add any new procedures learned
   - [ ] Update contact information
   - [ ] Review SLA metrics

### 2nd of Month: Database Optimization

**Purpose**: Ensure optimal database performance

**Tasks**:

1. **Analyze partition distribution**:
   ```
   Azure Portal → Cosmos DB → 
   Metrics → Normalized RU Consumption by Partition Key
   Verify even distribution
   ```

2. **Review slow queries**:
   ```kusto
   dependencies
   | where type == "SQL"
   | where timestamp > ago(30d)
   | where duration > 1000
   | project name, duration, timestamp
   | sort by duration desc
   ```

3. **Optimize indexes if needed**:
   - Check query patterns
   - Add indexes for frequently queried fields
   - Remove unused indexes

4. **Archive old data**:
   ```powershell
   # Move 90+ day old documents to cold storage
   # Keep in Cosmos for performance, archive to blob
   ```

### 3rd of Month: Security Audit

**Purpose**: Verify security measures are working

**Tasks**:

1. **Review access logs**:
   - Who accessed what
   - Any unauthorized attempts
   - Suspicious patterns

2. **Check credentials rotation**:
   - [ ] Azure Cosmos DB keys rotated (quarterly)
   - [ ] SendGrid API key valid
   - [ ] Other API keys current

3. **Verify encryption**:
   - [ ] HTTPS enforced
   - [ ] Data at rest encrypted
   - [ ] Backups encrypted

4. **Security patch check**:
   - [ ] Python packages up to date (security patches)
   - [ ] OS security updates applied
   - [ ] No known vulnerabilities

### 4th of Month: Disaster Recovery Test

**Purpose**: Ensure we can recover from disaster

**Tasks**:

1. **Test backup restoration** (in dev environment):
   - Restore from latest backup
   - Verify data integrity
   - Check recovery time
   - Document any issues

2. **Test failover** (if multi-region):
   - Switch to secondary region
   - Verify all systems work
   - Switch back
   - Document recovery time

3. **Update runbook**:
   - Document actual recovery time
   - Update procedures if needed
   - List any challenges found

---

## Quarterly Maintenance (4 hours)

### Q1, Q2, Q3, Q4: Comprehensive Review

**1. Performance Benchmarking**:
```kusto
// Compare performance quarter-over-quarter
requests
| where timestamp > ago(90d)
| summarize 
    AvgDuration = avg(duration),
    P95Duration = percentile(duration, 95),
    ErrorRate = countif(success == false) / count(),
    RequestCount = count()
    by quarter = tostring(floor((todoftime(timestamp) - toint(1)) / 91.25) + 1)
```

2. **Capacity Planning**:
   - Project storage growth
   - Estimate future RU/s needs
   - Plan for scaling
   - Budget for next quarter

3. **Dependency Updates**:
   - Update Python packages (test first)
   - Update npm packages
   - Test thoroughly after updates
   - Document any breaking changes

4. **Load Testing**:
   ```powershell
   # Simulate peak load
   # Verify system handles expected volume
   # Check response times under load
   # Verify database can handle concurrent users
   ```

5. **Documentation Review**:
   - Update all procedures
   - Add new issues learned
   - Remove obsolete procedures
   - Verify accuracy

6. **Team Training**:
   - Train on-call engineers
   - Review incident procedures
   - Practice failure scenarios
   - Update runbooks based on lessons

---

## Yearly Maintenance (full day)

### Annual System Audit

**1. Architecture Review**:
- [ ] Current design still optimal?
- [ ] Any scalability concerns?
- [ ] Can upgrade to newer frameworks?
- [ ] Plan major improvements

**2. Cost Optimization**:
- [ ] Annual Azure costs reviewed
- [ ] Identify cost-saving opportunities
- [ ] Right-size resources
- [ ] Optimize database throughput

**3. Security Assessment**:
- [ ] Full security audit
- [ ] Penetration testing
- [ ] Compliance verification (if needed)
- [ ] Update security procedures

**4. Compliance Check** (if applicable):
- [ ] GDPR compliance verified
- [ ] Data retention policies enforced
- [ ] Audit logs complete
- [ ] Privacy controls working

**5. Team Retrospective**:
- [ ] Discuss major incidents
- [ ] Identify improvements
- [ ] Plan training for next year
- [ ] Update SLAs if needed

---

## Maintenance Log

Create file: `MAINTENANCE_LOG.txt`

```
Date: 2026-01-18
Task: Weekly system restart
Duration: 15 minutes
Status: Successful
Notes: All systems restored, memory usage normal
Next: Check monthly optimization - due Feb 1

Date: 2026-01-25
Task: Weekly system restart
Status: Successful
Notes: Backend restart took 2 minutes, frontend 1 minute
Issues: None

[Continue logging all maintenance tasks]
```

---

## Automated Maintenance

### Setup Scheduled Tasks

**Task 1: Daily Health Check**
```powershell
# File: daily_health_check.ps1
# Schedule: Every day at 8:00 AM

$uri = "http://127.0.0.1:8000/api/v1/health"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

try {
    $response = Invoke-WebRequest -Uri $uri -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "$timestamp - OK"
    } else {
        Write-Host "$timestamp - ERROR: Status $($response.StatusCode)"
        # Send alert
    }
} catch {
    Write-Host "$timestamp - ERROR: $($_.Exception.Message)"
    # Send alert
}
```

**Task 2: Weekly Restart**
```powershell
# File: weekly_restart.ps1
# Schedule: Every Friday at 5:00 PM

Write-Host "Starting weekly maintenance restart..."

# Stop services
taskkill /IM python.exe /F
taskkill /IM node.exe /F
Start-Sleep -Seconds 5

# Restart backend
# Restart frontend
# Verify health

Write-Host "Weekly restart complete"
```

**Task 3: Monthly Review**
```powershell
# Manual task - can't fully automate
# File: monthly_review.ps1
# Schedule: 1st of each month

Write-Host "Monthly review tasks:"
Write-Host "1. Review Application Insights metrics"
Write-Host "2. Check Cosmos DB capacity"
Write-Host "3. Review error logs"
Write-Host "4. Update documentation"

# Export metrics
# Create summary report
# Send to team
```

---

## Maintenance Contacts

**Level 1**: On-call engineer (routine)
**Level 2**: DevOps team (infrastructure issues)
**Level 3**: Senior engineer (major issues)
**Level 4**: Vendor support (Azure, SendGrid)

---

## Quick Reference

| Task | Frequency | Duration | Owner |
|------|-----------|----------|-------|
| Health check | Daily | 5 min | On-call |
| System restart | Weekly | 20 min | On-call |
| Log archive | Weekly | 10 min | DevOps |
| Performance review | Monthly | 60 min | DevOps |
| Database optimization | Monthly | 30 min | DevOps |
| Security audit | Monthly | 45 min | Security |
| Disaster recovery test | Quarterly | 120 min | DevOps |
| System audit | Yearly | 480 min | All |

---

**Document Complete** - Last updated January 2026
