# C-010: Backup & Disaster Recovery Implementation

**Status**: NOT STARTED  
**Effort**: 1 hour  
**Priority**: MEDIUM - Operations  

## Objective
Set up automated database backups and recovery procedures for Cosmos DB.

## Current State
- No automated backups
- No recovery procedures documented
- Risk of data loss

## Implementation Plan

### 1. Cosmos DB Automated Backups
Azure automatically provides:
- Continuous backup mode (latest version)
- 30-day retention by default
- Point-in-time restore capability

### 2. Configuration
```bash
# Enable continuous backup
az cosmosdb create \
  --name kraftd-db \
  --backup-policy-type Continuous \
  --continuous-tier-max-lookback-days 30
```

### 3. Backup Retention Policy
```yaml
BACKUP_RETENTION_DAYS: 30
BACKUP_FREQUENCY: Continuous
RESTORE_WINDOW: 30 days back
```

### 4. Manual Backup Export
```python
# Export data to JSON for offline backup
async def export_cosmos_backup(output_file: str):
    query = "SELECT * FROM c"
    items = cosmos_service.query(query)
    
    with open(output_file, 'w') as f:
        json.dump(items, f, indent=2)
```

### 5. Recovery Procedures

#### Scenario 1: Data Corruption
```bash
# Restore to point-in-time
az cosmosdb restore \
  --resource-group myResourceGroup \
  --account-name kraftd-db \
  --restore-timestamp 2026-01-17T10:00:00Z \
  --databases-to-restore database1=container1
```

#### Scenario 2: Accidental Deletion
```bash
# Check backup availability
az cosmosdb backup show \
  --resource-group myResourceGroup \
  --account-name kraftd-db

# Restore specific container
az cosmosdb sql container restore \
  --resource-group myResourceGroup \
  --account-name kraftd-db \
  --database-name kraftd \
  --name documents \
  --restore-timestamp 2026-01-17T15:30:00Z
```

#### Scenario 3: Complete Disaster
```bash
# Restore entire database
az cosmosdb restore \
  --resource-group myResourceGroup \
  --account-name kraftd-db-restore \
  --source-account-name kraftd-db \
  --restore-timestamp 2026-01-17T12:00:00Z
```

### 6. Backup Verification
```bash
# Automated daily verification job
schedule: "0 2 * * *"  # 2 AM daily

tasks:
  - Verify latest backup exists
  - Check backup integrity
  - Validate restore capability
  - Send status report
```

### 7. Disaster Recovery Checklist

**Before Disaster**:
- [ ] Backup strategy documented
- [ ] Retention policy configured
- [ ] Restore procedures tested
- [ ] Team trained on recovery
- [ ] Communication plan ready

**During Disaster**:
- [ ] Assess data loss scope
- [ ] Determine restore point
- [ ] Initiate restore process
- [ ] Verify data integrity
- [ ] Notify stakeholders

**After Disaster**:
- [ ] Complete data validation
- [ ] Resume normal operations
- [ ] Document lessons learned
- [ ] Update procedures

### 8. Configuration Files

**File**: `backend/scripts/backup_export.py`
```python
import json
import asyncio
from services.cosmos_service import get_cosmos_service

async def export_backup(output_file: str):
    """Export all data from Cosmos DB to JSON file"""
    service = get_cosmos_service()
    
    # Query all items
    query = "SELECT * FROM c"
    items = await service.query(query)
    
    # Export to file
    with open(output_file, 'w') as f:
        json.dump({
            "exported_at": datetime.now().isoformat(),
            "count": len(items),
            "items": items
        }, f, indent=2)
    
    print(f"Exported {len(items)} items to {output_file}")
```

**File**: `backend/scripts/disaster_recovery.sh`
```bash
#!/bin/bash
# Disaster Recovery Script

RESOURCE_GROUP="kraftd-rg"
ACCOUNT_NAME="kraftd-db"
RESTORE_TIMESTAMP=$1

if [ -z "$RESTORE_TIMESTAMP" ]; then
    echo "Usage: ./disaster_recovery.sh <timestamp>"
    echo "Example: ./disaster_recovery.sh 2026-01-17T10:00:00Z"
    exit 1
fi

echo "Initiating restore to: $RESTORE_TIMESTAMP"

az cosmosdb restore \
  --resource-group $RESOURCE_GROUP \
  --account-name $ACCOUNT_NAME \
  --restore-timestamp $RESTORE_TIMESTAMP

echo "Restore initiated. Monitor progress in Azure Portal"
```

### 9. Monitoring & Alerts

```yaml
Monitoring:
  - Backup job completion
  - Backup size trending
  - Restore capability validation
  - Database growth metrics

Alerts:
  - Backup failed
  - Backup size unusual
  - Restore test failed
  - Database unavailable
```

## Files to Create

1. `backend/scripts/backup_export.py` - Manual export
2. `backend/scripts/disaster_recovery.sh` - Recovery script
3. `backend/scripts/backup_verify.py` - Verification job
4. `docs/DISASTER_RECOVERY_PLAN.md` - Procedures
5. `docs/BACKUP_RETENTION_POLICY.md` - Policy document

## Testing

```bash
# Test backup export
python backend/scripts/backup_export.py \
  --output backups/test_export.json

# Verify export
ls -lh backups/test_export.json

# Test restore procedure (in staging)
./backend/scripts/disaster_recovery.sh "2026-01-17T10:00:00Z"
```

## Success Criteria

✅ Automated continuous backups enabled  
✅ 30-day retention configured  
✅ Manual export script working  
✅ Recovery procedures documented  
✅ Team trained on disaster recovery  
✅ Monthly restore tests passing  
✅ Alerts configured for backup failures  
