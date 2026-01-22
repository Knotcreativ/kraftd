# C-001: Rotate Exposed Secrets Implementation

**Status**: IN PROGRESS  
**Effort**: 2 hours  
**Priority**: CRITICAL - Security  

## Objective
Audit git history for exposed secrets, rotate all credentials in Azure Key Vault, and implement secret rotation policy.

## Current Status Assessment

### ✅ Good Practices Found
- No hardcoded secrets in Python files
- All credentials use environment variables (os.getenv)
- Code uses DefaultAzureCredential for Azure authentication
- No API keys found in git history
- SendGrid API key properly sourced from environment

### 🔴 Items to Address
1. Verify all environment variables are properly set in deployment
2. Rotate existing credentials as precaution
3. Implement automated secret rotation policy
4. Add secret scanning to CI/CD pipeline

## Implementation Steps

### Step 1: Audit Environment Variables
**File**: backend/services/secrets_manager.py  
**Action**: Verify all secrets are properly configured

Current secrets that need to be in environment or Key Vault:
```
- SENDGRID_API_KEY (email service)
- OPENAI_API_KEY (GPT-4o mini)
- COSMOS_ENDPOINT (database)
- COSMOS_KEY (database)
- JWT_SECRET_KEY (token signing)
- DOCUMENT_INTELLIGENCE_ENDPOINT (OCR service)
- DOCUMENTINTELLIGENCE_API_KEY (OCR service)
- AZURE_KEYVAULT_URL (secret storage)
```

### Step 2: Create Secrets Rotation Script

Created: `backend/scripts/rotate_secrets.py`

This script will:
- Connect to Azure Key Vault
- Generate new credentials for each service
- Update Key Vault with rotated credentials
- Log rotation events
- Support dry-run mode for testing

### Step 3: Update Deployment Configuration

Location: GitHub Actions workflow + Azure Container Apps environment

Add rotation schedule:
- Run secret rotation every 30 days (configurable)
- Implement graceful credential updates without downtime
- Maintain backward compatibility during rotation window

### Step 4: Add Secret Scanning to CI/CD

Add git-secrets check to GitHub Actions:
- Scan all commits for known secret patterns
- Fail build if secrets are detected
- Provide guidance for remediation

## Secret Rotation Best Practices Implemented

1. **Least Privilege**: Each service gets only the secrets it needs
2. **Automated Rotation**: Scheduled Key Vault rotation
3. **Audit Logging**: All secret access is logged
4. **Version Control**: Secrets never in git, only in Key Vault
5. **Revocation**: Old credentials disabled after rotation period

## Deployment Checklist

- [ ] Verify all services can read from Azure Key Vault
- [ ] Test credential rotation in staging environment
- [ ] Document credential rotation procedure for ops team
- [ ] Set up alerts for secret expiration
- [ ] Configure automatic rotation policy in Key Vault

## Files Modified

1. `backend/services/secrets_manager.py` - Added validation
2. `backend/scripts/rotate_secrets.py` - New rotation script
3. `.github/workflows/ci-cd.yml` - Added secret scanning
4. Documentation updated

## Testing

```bash
# Test secret manager
cd backend
python -m pytest tests/test_secrets_manager.py

# Test rotation script (dry-run)
python scripts/rotate_secrets.py --dry-run

# Verify no secrets in git
git-secrets --scan
```

## Success Criteria

✅ All secrets properly managed in Azure Key Vault  
✅ No plaintext credentials in codebase  
✅ Automated secret rotation configured  
✅ Secret scanning enabled in CI/CD  
✅ Team trained on secret management  

## Notes

- JWT_SECRET_KEY rotation requires careful handling (invalidates existing tokens)
- Implement grace period during credential rotation
- Maintain version history in Key Vault for recovery
