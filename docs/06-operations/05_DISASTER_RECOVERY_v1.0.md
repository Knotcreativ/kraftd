# Disaster Recovery Plan v1.0

**Document**: Backup and Recovery Procedures  
**Version**: 1.0  
**Last Updated**: January 2026  
**Audience**: Operations Team, Senior Engineers, Management

---

## Overview

This plan explains how to backup the system and recover from disasters. It covers data loss scenarios, corruption issues, and complete system failure.

**RTO (Recovery Time Objective)**: < 4 hours
**RPO (Recovery Point Objective)**: < 1 hour of data loss

---

## 1. Backup Strategy

### What Gets Backed Up

**Critical Data** (backed up continuously):
1. **Cosmos DB**
   - User accounts
   - Document metadata
   - Export tracking
   - Workflow state

2. **File Storage**
   - Uploaded documents
   - Generated exports
   - Temporary conversion files

3. **Configuration**
   - Environment variables
   - API keys
   - Database connection strings
   - Email templates

**Not Backed Up** (recreatable):
- Application logs (can be recreated)
- Temporary caches (can be rebuilt)
- Docker images (can be rebuilt from registry)

### Backup Schedule

**Database Backups**:
- Type: Continuous
- Frequency: Every 15 minutes (automatic)
- Retention: 30 days (default)
- Location: Geo-replicated (automatic)

**File Storage Backups**:
- Type: Incremental daily
- Frequency: Daily at 2 AM
- Retention: 30 days
- Location: Azure Blob Storage (geo-redundant)

**Configuration Backups**:
- Type: Manual
- Frequency: After each deployment
- Retention: All versions in Git
- Location: GitHub (secure, replicated)

---

## 2. Backup Verification

### Daily Backup Health Check

```powershell
# Check Cosmos DB backups
$resourceGroup = "KraftdIntel-rg"
$accountName = "kraftdintel-db"

az cosmosdb show \
  --resource-group $resourceGroup \
  --name $accountName \
  --query "backupPolicy"

# Should show:
# - automaticFailoverEnabled: true
# - backupInterval: 240 (minutes)
# - backupRetention: 2880 (minutes, 48 hours minimum)
```

### Weekly Restore Test

```powershell
# Once weekly, test restore in non-production
# Steps:
# 1. Create backup from main database
# 2. Create test container
# 3. Restore backup to test container
# 4. Verify data integrity
# 5. Delete test container

# This ensures:
# - Backups are actually working
# - Restore process documented
# - Recovery time measured
# - Team trained on procedure
```

---

## 3. Disaster Scenarios

### Scenario 1: Single Document Corrupted

**Impact**: Low - 1 user's document affected
**RTO**: < 30 minutes
**Recovery**: Restore from backup

**Steps**:
1. User reports corrupted document
2. Check backup timestamp
3. Restore single document from backup
4. Return to user
5. Document issue

**Prevention**:
- Validate documents after processing
- Add integrity checks

---

### Scenario 2: User Account Deleted Accidentally

**Impact**: Medium - 1 user locked out
**RTO**: < 1 hour
**Recovery**: Restore user record from backup

**Steps**:
1. User reports account deleted
2. Query backup from Azure Storage
3. Restore user record to Cosmos DB
4. Verify user can login
5. Notify user

**Prevention**:
- Add soft-delete before actual deletion
- Require confirmation for account deletion
- Email notification before deletion

---

### Scenario 3: Database Partially Corrupted

**Impact**: High - Multiple users affected
**RTO**: < 2 hours
**Recovery**: Restore entire database

**Steps**:
1. Detect corruption in logs
2. Stop accepting writes
3. Take database offline
4. Restore from latest backup
5. Bring back online
6. Notify users of 1-hour data loss
7. Investigate root cause

**Prevention**:
- Enable transaction logging
- Regular data validation
- Database integrity checks

---

### Scenario 4: Complete Database Loss

**Impact**: Critical - All data gone
**RTO**: < 4 hours
**Recovery**: Restore from geo-replicated backup

**Steps**:
1. **Alert**: Activate incident response team
2. **Assess**: Confirm data loss, check if recoverable
3. **Prepare**: Create new Cosmos DB account
4. **Restore**: Use point-in-time restore
   ```
   Azure Portal → Cosmos DB → 
   Backup and Restore → Point-in-Time Restore
   ```
5. **Verify**: Check all collections restored
6. **Communicate**: Notify users of incident
7. **Failover**: Switch applications to restored DB
8. **Investigate**: Root cause analysis
9. **Prevent**: Implement safeguards

**Root Causes to Investigate**:
- Accidental deletion
- Ransomware attack
- Storage corruption
- Catastrophic failure
- Bug in application code

---

### Scenario 5: File Storage Destroyed

**Impact**: High - All uploaded documents gone
**RTO**: < 4 hours
**Recovery**: Restore from Blob Storage backup

**Steps**:
1. Detect storage failure
2. Check backup in Azure Blob Storage
3. Provision new storage account
4. Restore all files from backup
5. Update storage paths in Cosmos DB
6. Verify all documents accessible
7. Notify users if applicable

---

### Scenario 6: Azure Region Failure

**Impact**: Critical - Entire deployment unavailable
**RTO**: < 1 hour (if multi-region)
**Recovery**: Failover to secondary region

**Steps**:
1. **Detect**: Azure alerts notify of region failure
2. **Verify**: Confirm region is unavailable
3. **Failover**: Traffic Manager automatically routes to secondary region
4. **Verify**: Test functionality in secondary region
5. **Monitor**: Watch for any issues
6. **Communicate**: Notify users of incident
7. **Failback**: Switch back when primary region recovers

---

## 4. Recovery Procedures

### Full Database Recovery (Step by Step)

**Time Required**: 60-120 minutes
**Prerequisites**: Write access to Azure, recent backup

```
Step 1: Create new Cosmos DB account (30 minutes)
  - Azure Portal → Create resource → Cosmos DB
  - Same region as original
  - Same throughput settings
  - Same consistency level

Step 2: Restore from backup (30 minutes)
  - Azure Portal → Source account → Backup and Restore
  - Point-in-time restore to 1 hour ago
  - Select target account (new one created)
  - Restore all collections

Step 3: Verify restoration (20 minutes)
  - Query restored data
  - Check counts match original
  - Sample document verification
  - No corrupted documents

Step 4: Update application (10 minutes)
  - Update connection string in environment
  - Restart backend service
  - Verify connectivity
  - Health check endpoint

Step 5: Final verification (10 minutes)
  - Login test
  - Document query test
  - Export functionality test
  - Check error logs for issues

Step 6: Archive old account (optional)
  - Keep old account for 30 days as backup
  - Then delete to reduce costs
```

### File Storage Recovery

**Time Required**: 30-60 minutes

```
Step 1: Create new storage account (15 minutes)
  - Same region as original
  - Geo-redundant replication
  - Same tier (hot/cool)

Step 2: Restore from backup (30 minutes)
  - Navigate to backup Blob Storage
  - Select all files from latest backup
  - Copy to new storage account
  - Or use Azure Data Box if large

Step 3: Verify files (15 minutes)
  - Check file counts
  - Spot-check document integrity
  - Verify no corruption

Step 4: Update application (5 minutes)
  - Update storage connection string
  - Restart backend service
  - Test file upload/download

Step 5: Cleanup (optional)
  - Archive old storage account
  - Delete after 30-day hold
```

### Application-Level Recovery

**Time Required**: 15-30 minutes

```
Step 1: Pull source code (5 minutes)
  git clone https://github.com/your-repo/KraftdIntel.git
  cd KraftdIntel
  git checkout main

Step 2: Build application (10 minutes)
  cd backend
  .venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  
  cd ../frontend
  npm install

Step 3: Deploy application (5 minutes)
  # Use deployment scripts
  ./scripts/deploy-production.ps1

Step 4: Verify (5 minutes)
  curl http://api.yourdomain.com/api/v1/health
  # Should return 200 OK
```

---

## 5. Testing Recovery

### Monthly Restore Test

**Objective**: Verify backups work, team trained

**Schedule**: First Friday of each month, 2-3 PM

**Process**:
1. Notify team: "Disaster recovery test starting"
2. Create test Cosmos DB account
3. Restore latest backup to test account
4. Verify data integrity
5. Test application against restored data
6. Document findings
7. Delete test account
8. Notify team: "Test complete, all systems normal"

**What to Check**:
- [ ] Backup timestamp is recent (< 1 hour old)
- [ ] All collections restored
- [ ] Document counts match
- [ ] No corrupted data
- [ ] Sample queries return correct results
- [ ] File integrity verified

---

## 6. Recovery Contact Tree

### Critical Disaster Declared

**On-Call Engineer** (first responder):
1. Detect/confirm disaster
2. Activate incident response
3. Call incident commander

**Incident Commander**:
1. Assess severity (RTO/RPO impact)
2. Call relevant stakeholders
3. Authorize recovery decision

**Recovery Team**:
1. Database admin: Prepare restore
2. DevOps: Prepare infrastructure
3. Backend lead: Application readiness
4. Frontend lead: Client-side readiness

**Communication Lead**:
1. Notify internal team
2. Notify management
3. Prepare customer notification if public

---

## 7. Recovery Runbook

### Attach to this document

```
DISASTER RECOVERY RUNBOOK
(Print and keep accessible)

STEP 1: Determine disaster type
  - Data loss?
  - Corruption?
  - System failure?
  - Region failure?

STEP 2: Calculate impact
  - RTO needed?
  - RPO acceptable?
  - User count affected?

STEP 3: Activate team
  - Call incident commander
  - Assemble recovery team
  - Declare incident status

STEP 4: Execute recovery
  - Follow relevant scenario above
  - Document all steps
  - Track timeline

STEP 5: Verify recovery
  - Health checks
  - Data validation
  - User testing

STEP 6: Communicate status
  - Team updates every 30 minutes
  - Management briefing
  - Customer notification

STEP 7: Return to normal
  - Notify all-clear
  - Begin post-mortem
  - Update procedures
```

---

## 8. Backup Costs

**Monthly Costs** (estimate):

| Component | Cost | Notes |
|-----------|------|-------|
| Cosmos DB backup | $0 | Included in account |
| Blob Storage backup | $50-100 | 1TB retention |
| Bandwidth for restore | $0-20 | Within region free |
| **Total** | **$50-120** | Per month |

---

## 9. Prevention Strategies

### High Availability Architecture

1. **Multi-region deployment** (if critical):
   - Primary: East US
   - Secondary: West US
   - Automatic failover on region failure

2. **Database redundancy**:
   - Geo-replicated backups (automatic)
   - Continuous backup (every 15 minutes)
   - Point-in-time restore capability

3. **File storage redundancy**:
   - Geo-redundant replication
   - Daily incremental backups
   - 30-day retention

4. **Monitoring and alerts**:
   - Real-time failure detection
   - Automatic incident creation
   - Team notification

### Data Protection

1. **Access control**:
   - Limit who can delete data
   - Require approval for dangerous operations
   - Audit all deletions

2. **Soft deletes**:
   - Mark as deleted, don't remove
   - Allow recovery for 30 days
   - Then permanently purge

3. **Immutable backups**:
   - Backups cannot be deleted
   - Protection against ransomware
   - Always have recovery point

---

## 10. Disaster Recovery Plan Review

**Review Frequency**: Yearly
**Last Reviewed**: January 2026
**Next Review**: January 2027

**Checklist for Annual Review**:
- [ ] Restore procedures still accurate?
- [ ] Contact information current?
- [ ] Backup retention policies still appropriate?
- [ ] Recovery time estimates still valid?
- [ ] New systems added that need backup?
- [ ] Team trained on latest procedures?
- [ ] Any incidents that revealed gaps?
- [ ] Regulations changed requiring new procedures?

---

## Appendix: Azure Cosmos DB Backup Details

### Automatic Backup
- **Frequency**: Every 4 hours
- **Retention**: 30 days (minimum)
- **Restore Window**: Last 30 days
- **RTO**: 30 minutes to 1 hour
- **RPO**: Up to 15 minutes

### Point-in-Time Restore
```
Azure Portal → Cosmos DB → Backup and Restore
↓
Select "Point-in-Time Restore"
↓
Choose restore timestamp
↓
Select target account
↓
Initiate restore
↓
Wait 30-60 minutes
↓
Verify data
```

### Cost
- Included in Cosmos DB pricing
- No additional cost for backups
- Only pay for storage of backup data

---

**Document Complete** - Last updated January 2026

**Keep in Secure Location** - This document contains critical recovery procedures
