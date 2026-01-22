# Azure CLI Commands to Retrieve Cosmos DB Details

**Run these commands in PowerShell to get your Cosmos DB connection details:**

---

## Step 1: Verify Azure Login

```powershell
# Check if logged in to Azure
az account show

# If not logged in, login:
az login
```

---

## Step 2: Get Your Resource Group and Account Name

```powershell
# List all Cosmos DB accounts
az cosmosdb list --output table

# Output will show:
# Name                  ResourceGroup       Location
# --------------------  ------------------  ----------
# your-account-name     your-resource-group your-location
```

**Save these values:**
- Resource Group: `<your-rg>`
- Account Name: `<your-account>`

---

## Step 3: Get Connection String (MOST IMPORTANT)

```powershell
# Replace <your-rg> and <your-account> with your values
az cosmosdb keys list \
  --resource-group <your-rg> \
  --name <your-account> \
  --type connection-strings

# Output example:
# connectionStrings: [
#   {
#     "connectionString": "AccountEndpoint=https://your-account.documents.azure.com:443/;AccountKey=xxxx...",
#     "description": "Primary SQL Connection String"
#   },
#   ...
# ]

# Copy the PRIMARY connection string (first one)
```

---

## Step 4: Get Endpoint

```powershell
az cosmosdb show \
  --resource-group <your-rg> \
  --name <your-account> \
  --query documentEndpoint

# Output example:
# "https://your-account.documents.azure.com:443/"
```

---

## Step 5: Get Keys

```powershell
az cosmosdb keys list \
  --resource-group <your-rg> \
  --name <your-account> \
  --type keys

# Output example:
# primaryMasterKey: "xxxx..."
# secondaryMasterKey: "yyyy..."

# Copy the primaryMasterKey
```

---

## Complete Script (All in One)

```powershell
# Set these variables
$resourceGroup = "<your-rg>"
$accountName = "<your-account>"

# Get connection string
Write-Host "=== CONNECTION STRING ===" -ForegroundColor Green
$connString = az cosmosdb keys list `
  --resource-group $resourceGroup `
  --name $accountName `
  --type connection-strings `
  --query "connectionStrings[0].connectionString" -o tsv

Write-Host $connString
Write-Host ""

# Get endpoint
Write-Host "=== ENDPOINT ===" -ForegroundColor Green
$endpoint = az cosmosdb show `
  --resource-group $resourceGroup `
  --name $accountName `
  --query documentEndpoint -o tsv

Write-Host $endpoint
Write-Host ""

# Get primary key
Write-Host "=== PRIMARY KEY ===" -ForegroundColor Green
$primaryKey = az cosmosdb keys list `
  --resource-group $resourceGroup `
  --name $accountName `
  --type keys `
  --query primaryMasterKey -o tsv

Write-Host $primaryKey
Write-Host ""

# Display environment variables to set
Write-Host "=== ENVIRONMENT VARIABLES TO SET ===" -ForegroundColor Yellow
Write-Host "`$env:COSMOS_DB_ENDPOINT = `"$endpoint`""
Write-Host "`$env:COSMOS_DB_KEY = `"$primaryKey`""
Write-Host "`$env:COSMOS_DB_NAME = `"kraftd_audit`""
Write-Host "`$env:COSMOS_DB_AUDIT_CONTAINER = `"audit_events`""
Write-Host "`$env:COSMOS_DB_THROUGHPUT = `"400`""
Write-Host "`$env:COSMOS_DB_TTL_DAYS = `"2555`""
```

---

## How to Use the Complete Script

1. **Save as file**: `get-cosmos-details.ps1`

2. **Edit the variables at the top**:
   ```powershell
   $resourceGroup = "your-actual-resource-group"
   $accountName = "your-actual-cosmos-account"
   ```

3. **Run it**:
   ```powershell
   .\get-cosmos-details.ps1
   ```

4. **Output will show all details you need** ✅

---

## Then Set Environment Variables

**From the output above, copy and paste:**

```powershell
$env:COSMOS_DB_ENDPOINT = "https://your-account.documents.azure.com:443/"
$env:COSMOS_DB_KEY = "your-primary-key"
$env:COSMOS_DB_NAME = "kraftd_audit"
$env:COSMOS_DB_AUDIT_CONTAINER = "audit_events"
$env:COSMOS_DB_THROUGHPUT = "400"
$env:COSMOS_DB_TTL_DAYS = "2555"
```

---

## Alternative: Use Portal (If You Prefer GUI)

1. Go to https://portal.azure.com
2. Search for "Cosmos DB"
3. Click your account name
4. Left menu → Click "Keys"
5. Copy "Primary Connection String"
6. Extract:
   - **Endpoint**: The URL part (https://xxx.documents.azure.com:443/)
   - **Key**: The key portion

---

**Now run the script or commands above and share the resource group + account name, and I can provide the exact environment variables to use!**
