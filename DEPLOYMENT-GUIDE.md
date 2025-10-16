# Azure Deployment Guide
**Durable Functions Web Crawler - v3.0.0-alpha**

## 📋 Pre-Deployment Checklist

### ✅ Code Preparation
- [x] All tests passing locally (Phase 4 completed)
- [x] Error handling verified
- [x] Logging statements added
- [x] Comments and documentation updated
- [x] No sensitive data in code
- [x] Git repository up-to-date

### ✅ Configuration Files
- [x] `requirements.txt` includes `azure-functions-durable>=1.2.9`
- [x] `host.json` updated with Durable Task configuration
- [x] `websites.json` created and validated
- [x] `local.settings.json` has all required variables (local only)

### 🔲 Azure Resources (To be verified)
- [ ] Function App exists in Azure
- [ ] Storage Account accessible (`stbtpuksprodcrawler01`)
- [ ] Managed Identity configured
- [ ] RBAC permissions assigned
- [ ] Application Insights enabled

---

## 🚀 Deployment Options

### Option A: Azure Functions Core Tools (Recommended for Development)

**Prerequisites:**
- Azure CLI installed and logged in
- Azure Functions Core Tools v4 installed
- Access to Azure subscription

**Steps:**

1. **Login to Azure**
   ```powershell
   az login
   ```

2. **Verify Function App exists**
   ```powershell
   # List Function Apps in subscription
   az functionapp list --output table
   
   # Or check specific Function App
   az functionapp show `
     --name <your-function-app-name> `
     --resource-group <your-resource-group> `
     --query "{Name:name, State:state, Location:location}"
   ```

3. **Deploy Function App**
   ```powershell
   # Navigate to project directory
   cd "c:\Users\4530Holl\OneDrive - British Transport Police\_Open-Ai\Web-Crawler-Repo\functions-python-web-crawler\functions-python-web-crawler"
   
   # Deploy to Azure
   func azure functionapp publish <your-function-app-name>
   ```

4. **Monitor Deployment**
   - Deployment logs will appear in terminal
   - Look for "Deployment successful" message
   - Note any warnings or errors

---

### Option B: VS Code Extension

**Prerequisites:**
- VS Code with Azure Functions extension installed
- Signed into Azure account in VS Code

**Steps:**

1. **Open Project in VS Code**
   - Open the `functions-python-web-crawler` folder

2. **Deploy**
   - Open Azure Functions extension (Azure icon in sidebar)
   - Find "Local Project" section
   - Click "Deploy to Function App" icon
   - Select your Azure subscription
   - Choose existing Function App or create new
   - Confirm deployment

3. **Monitor Progress**
   - Deployment progress shown in VS Code output panel
   - Check for "Deployment successful" message

---

### Option C: Azure Portal (Manual Upload)

**Prerequisites:**
- Access to Azure Portal
- Zip file of project

**Steps:**

1. **Create Deployment Package**
   ```powershell
   # Ensure you're in the project root
   cd "c:\Users\4530Holl\OneDrive - British Transport Police\_Open-Ai\Web-Crawler-Repo\functions-python-web-crawler\functions-python-web-crawler"
   
   # Create zip (exclude .git, .venv, tests)
   Compress-Archive -Path function_app.py,host.json,requirements.txt,websites.json -DestinationPath deploy.zip -Force
   ```

2. **Upload via Portal**
   - Navigate to your Function App in Azure Portal
   - Go to "Deployment Center"
   - Select "ZIP Deploy"
   - Upload `deploy.zip`
   - Wait for deployment to complete

---

## ⚙️ Post-Deployment Configuration

### Step 1: Upload Configuration to Blob Storage (Optional but Recommended)

**Upload websites.json to Azure Blob Storage:**

```powershell
# Using Azure CLI with Managed Identity authentication
az storage blob upload `
  --account-name stbtpuksprodcrawler01 `
  --container-name configuration `
  --name websites.json `
  --file websites.json `
  --auth-mode login `
  --overwrite
```

**Verify upload:**
```powershell
az storage blob list `
  --account-name stbtpuksprodcrawler01 `
  --container-name configuration `
  --auth-mode login `
  --output table
```

---

### Step 2: Configure Application Settings

**Required Environment Variables:**

```powershell
# Get your Function App name and Resource Group
$functionAppName = "<your-function-app-name>"
$resourceGroup = "<your-resource-group>"

# Set configuration location (blob or local)
az functionapp config appsettings set `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --settings WEBSITES_CONFIG_LOCATION=blob

# Set storage account name
az functionapp config appsettings set `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --settings STORAGE_ACCOUNT_NAME=stbtpuksprodcrawler01

# Verify Python version
az functionapp config appsettings set `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --settings FUNCTIONS_WORKER_RUNTIME=python

# List all settings to verify
az functionapp config appsettings list `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --output table
```

**Expected Settings:**
- `AzureWebJobsStorage`: Connection string (auto-configured)
- `WEBSITES_CONFIG_LOCATION`: `blob` or `local`
- `STORAGE_ACCOUNT_NAME`: `stbtpuksprodcrawler01`
- `FUNCTIONS_WORKER_RUNTIME`: `python`
- `FUNCTIONS_EXTENSION_VERSION`: `~4`

---

### Step 3: Configure Managed Identity

**Enable System-Assigned Managed Identity:**

```powershell
# Enable system-assigned identity
az functionapp identity assign `
  --name $functionAppName `
  --resource-group $resourceGroup

# Get the Principal ID (needed for role assignment)
$principalId = az functionapp identity show `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --query principalId `
  --output tsv

Write-Host "Managed Identity Principal ID: $principalId"
```

**Assign RBAC Roles:**

```powershell
# Get your subscription ID
$subscriptionId = az account show --query id --output tsv

# Assign Storage Blob Data Contributor role
az role assignment create `
  --assignee $principalId `
  --role "Storage Blob Data Contributor" `
  --scope "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Storage/storageAccounts/stbtpuksprodcrawler01"

# Verify role assignment
az role assignment list `
  --assignee $principalId `
  --output table
```

**Expected Roles:**
- Storage Blob Data Contributor (on storage account)
- Any other required roles for your environment

---

### Step 4: Verify Deployment

**Check Function App Status:**

```powershell
# Check if Function App is running
az functionapp show `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --query "{Name:name, State:state, HostNames:defaultHostName}"
```

**List Deployed Functions:**

```powershell
az functionapp function list `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --output table
```

**Expected Functions:**
- `web_crawler_orchestrator` (Orchestrator)
- `get_configuration_activity` (Activity)
- `get_document_hashes_activity` (Activity)
- `crawl_single_website_activity` (Activity)
- `store_document_hashes_activity` (Activity)
- `store_crawl_history_activity` (Activity)
- `start_web_crawler_orchestration` (HTTP Trigger)
- `get_orchestration_status` (HTTP Trigger)
- `terminate_orchestration` (HTTP Trigger)
- `scheduled_crawler_orchestrated` (Timer Trigger)

---

## 🧪 Post-Deployment Testing

### Test 1: Manual HTTP Trigger

**Get Function URL and Key:**

```powershell
# Get function app hostname
$functionAppUrl = "https://$functionAppName.azurewebsites.net"

# Get function key (master key or function-specific key)
$functionKey = az functionapp keys list `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --query functionKeys.default `
  --output tsv
```

**Start Orchestration:**

```powershell
# Start crawler orchestration
$response = Invoke-RestMethod `
  -Uri "$functionAppUrl/api/start_web_crawler_orchestration?code=$functionKey" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"config_location":"blob"}'

# Display response
$response | ConvertTo-Json -Depth 10

# Save instance ID for status checking
$instanceId = $response.instance_id
Write-Host "Orchestration started: $instanceId"
```

**Expected Response:**
```json
{
  "message": "Web crawler orchestration started",
  "instanceId": "abc123def456...",
  "statusQueryGetUri": "https://...",
  "sendEventPostUri": "https://...",
  "terminatePostUri": "https://...",
  "rewindPostUri": "https://...",
  "purgeHistoryDeleteUri": "https://...",
  "restartPostUri": "https://..."
}
```

---

### Test 2: Check Orchestration Status

**Poll Status Endpoint:**

```powershell
# Check orchestration status
$statusResponse = Invoke-RestMethod `
  -Uri "$functionAppUrl/api/get_orchestration_status/$instanceId?code=$functionKey" `
  -Method GET

# Display status
$statusResponse | ConvertTo-Json -Depth 10
```

**Expected Status Progression:**
1. `Running` - Orchestration in progress
2. `Completed` - Orchestration finished successfully
3. `Failed` - Orchestration encountered error

**Completed Response Example:**
```json
{
  "name": "web_crawler_orchestrator",
  "instanceId": "abc123def456...",
  "runtimeStatus": "Completed",
  "input": {...},
  "customStatus": null,
  "output": {
    "orchestration_id": "abc123def456...",
    "total_websites": 5,
    "successful_crawls": 5,
    "failed_crawls": 0,
    "total_documents": 127,
    "new_documents": 12,
    "updated_documents": 3,
    "start_time": "2025-10-16T10:00:00Z",
    "end_time": "2025-10-16T10:03:45Z",
    "duration_seconds": 225
  },
  "createdTime": "2025-10-16T10:00:00Z",
  "lastUpdatedTime": "2025-10-16T10:03:45Z"
}
```

---

### Test 3: Verify Results in Blob Storage

**Check for Uploaded Documents:**

```powershell
# List recent blobs in documents container
az storage blob list `
  --account-name stbtpuksprodcrawler01 `
  --container-name documents `
  --auth-mode login `
  --query "[?properties.lastModified >= '2025-10-16'].{Name:name, Size:properties.contentLength, Modified:properties.lastModified}" `
  --output table
```

**Check for Document Hashes:**

```powershell
# Download and view document hashes
az storage blob download `
  --account-name stbtpuksprodcrawler01 `
  --container-name documents `
  --name document_hashes.json `
  --file document_hashes_downloaded.json `
  --auth-mode login

# View content
Get-Content document_hashes_downloaded.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Check Crawl History:**

```powershell
# List crawl history files
az storage blob list `
  --account-name stbtpuksprodcrawler01 `
  --container-name crawl-history `
  --auth-mode login `
  --output table
```

---

### Test 4: Monitor in Azure Portal

**Application Insights Monitoring:**

1. Navigate to your Function App in Azure Portal
2. Click "Application Insights" in left menu
3. Click "Live Metrics" to see real-time telemetry
4. Check for:
   - Incoming requests
   - Outgoing dependencies (Blob Storage calls)
   - Logs and traces
   - No errors or exceptions

**Function Monitor:**

1. Navigate to Function App → Functions
2. Click on `web_crawler_orchestrator`
3. Click "Monitor" tab
4. View recent invocations
5. Click on specific invocation to see:
   - Execution timeline
   - Logs
   - Activity function calls
   - Final output

---

### Test 5: Timer Trigger Verification

**Check Timer Schedule:**

```powershell
# View function configuration
az functionapp function show `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --function-name scheduled_crawler_orchestrated
```

**Verify Next Scheduled Run:**

- Navigate to Function App → Functions → `scheduled_crawler_orchestrated`
- Check "Overview" tab for next execution time
- Default: Every 4 hours (`0 0 */4 * * *`)

**Manually Trigger Timer (for testing):**

- In Azure Portal, go to function
- Click "Code + Test"
- Click "Test/Run"
- Click "Run"
- Monitor execution

---

## 📊 Monitoring and Alerting

### Application Insights Queries

**Open Application Insights:**
```powershell
# Get Application Insights resource
az monitor app-insights component show `
  --app <app-insights-name> `
  --resource-group $resourceGroup
```

**Useful KQL Queries:**

**1. Orchestration Success Rate (Last 24 Hours)**
```kusto
traces
| where timestamp > ago(24h)
| where message contains "🎯 Orchestrator completed"
| extend 
    TotalSites = toint(extract("crawled (\\d+) sites", 1, message)),
    NewDocs = toint(extract("(\\d+) new documents", 1, message)),
    UpdatedDocs = toint(extract("(\\d+) updated", 1, message))
| summarize 
    TotalRuns = count(),
    AvgSites = avg(TotalSites),
    TotalNewDocs = sum(NewDocs),
    TotalUpdatedDocs = sum(UpdatedDocs)
```

**2. Activity Function Performance**
```kusto
traces
| where timestamp > ago(24h)
| where message contains "🔄 Activity:"
| extend 
    Site = extract("crawling (.+)", 1, message),
    Duration = extract("(\\d+\\.\\d+)s", 1, message)
| summarize 
    AvgDuration = avg(todouble(Duration)),
    MaxDuration = max(todouble(Duration)),
    MinDuration = min(todouble(Duration))
    by Site
| order by AvgDuration desc
```

**3. Error Analysis**
```kusto
traces
| where timestamp > ago(24h)
| where severityLevel >= 3  // Warning or higher
| where message contains "Orchestrator:" or message contains "Activity:"
| summarize ErrorCount = count() by message
| order by ErrorCount desc
```

**4. Document Discovery Trends**
```kusto
traces
| where timestamp > ago(7d)
| where message contains "new documents"
| extend NewDocs = toint(extract("(\\d+) new documents", 1, message))
| summarize TotalNew = sum(NewDocs) by bin(timestamp, 1d)
| render timechart
```

---

### Configure Alerts

**Alert 1: Orchestration Failures**

```powershell
# Create action group (if not exists)
az monitor action-group create `
  --name "FunctionAppAlerts" `
  --resource-group $resourceGroup `
  --short-name "FuncAlert" `
  --email-receiver name=Admin email=admin@example.com

# Create metric alert for failures
az monitor metrics alert create `
  --name "OrchestrationFailures" `
  --resource-group $resourceGroup `
  --scopes /subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/$functionAppName `
  --condition "count exceptions > 0" `
  --window-size 5m `
  --evaluation-frequency 1m `
  --action FunctionAppAlerts
```

**Alert 2: No Documents Found (24 Hours)**

- Create in Application Insights → Alerts
- Condition: Custom log search
- Query:
  ```kusto
  traces
  | where timestamp > ago(24h)
  | where message contains "new documents found"
  | extend NewDocs = toint(extract("(\\d+) new documents", 1, message))
  | summarize TotalNew = sum(NewDocs)
  | where TotalNew == 0
  ```
- Threshold: TotalNew == 0
- Action: Email notification

---

## 🔄 Operational Procedures

### Adding New Websites

**Method 1: Update Blob Configuration**

```powershell
# 1. Download current configuration
az storage blob download `
  --account-name stbtpuksprodcrawler01 `
  --container-name configuration `
  --name websites.json `
  --file websites_current.json `
  --auth-mode login

# 2. Edit websites_current.json - add new website entry

# 3. Upload updated configuration
az storage blob upload `
  --account-name stbtpuksprodcrawler01 `
  --container-name configuration `
  --name websites.json `
  --file websites_current.json `
  --auth-mode login `
  --overwrite

# 4. No deployment needed - next run will use new config
```

**Method 2: Update Local and Redeploy**

```powershell
# 1. Edit websites.json locally
# 2. Deploy updated function app
func azure functionapp publish $functionAppName
```

---

### Disabling/Enabling Websites

**Quick Disable:**

```powershell
# Download, edit, re-upload websites.json
# Change specific website: "enabled": false
# No code changes needed
```

---

### Manual Crawler Execution

**Trigger via HTTP:**

```powershell
# Start orchestration manually
Invoke-RestMethod `
  -Uri "$functionAppUrl/api/start_web_crawler_orchestration?code=$functionKey" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"config_location":"blob"}'
```

---

### Adjusting Concurrency

**Edit host.json:**

```json
{
  "extensions": {
    "durableTask": {
      "maxConcurrentActivityFunctions": 20,  // Increase for more parallelism
      "maxConcurrentOrchestratorFunctions": 10
    }
  }
}
```

**Deploy changes:**

```powershell
func azure functionapp publish $functionAppName
```

---

## 🔐 Security Best Practices

### 1. Use Managed Identity (Already Configured)
- ✅ No connection strings in code
- ✅ Azure handles credential rotation
- ✅ RBAC-based access control

### 2. Secure Function Keys
```powershell
# Regenerate function keys periodically
az functionapp keys set `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --key-type functionKeys `
  --key-name default
```

### 3. Enable Authentication (Optional)
```powershell
# Enable Azure AD authentication
az functionapp auth update `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --enabled true `
  --action LoginWithAzureActiveDirectory
```

### 4. Network Security
- Configure firewall rules on Storage Account
- Use Private Endpoints for production
- Enable HTTPS only

---

## 📝 Troubleshooting

### Issue: Deployment Fails

**Check 1: Verify Python Version**
```powershell
# Ensure Function App uses Python 3.11
az functionapp config show `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --query linuxFxVersion
```

**Check 2: Review Deployment Logs**
```powershell
# Stream logs during deployment
func azure functionapp logstream $functionAppName
```

---

### Issue: Orchestration Not Starting

**Check 1: Verify Timer Trigger**
- Check cron expression in function_app.py
- Verify `run_on_startup` setting

**Check 2: Application Settings**
```powershell
# List all settings
az functionapp config appsettings list `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --output table
```

---

### Issue: Blob Storage Access Denied

**Check 1: Verify Managed Identity**
```powershell
# Check if identity is enabled
az functionapp identity show `
  --name $functionAppName `
  --resource-group $resourceGroup
```

**Check 2: Verify RBAC Assignment**
```powershell
# List role assignments
az role assignment list `
  --assignee <principal-id> `
  --output table
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] All tests passing locally
- [ ] Configuration files validated
- [ ] Git repository committed and tagged
- [ ] Azure resources verified

### Deployment
- [ ] Function App deployed successfully
- [ ] Configuration uploaded to blob storage
- [ ] Application settings configured
- [ ] Managed Identity enabled and roles assigned

### Post-Deployment
- [ ] Manual HTTP trigger tested
- [ ] Orchestration status verified
- [ ] Results in blob storage confirmed
- [ ] Application Insights working
- [ ] Alerts configured

### Monitoring
- [ ] Live metrics showing activity
- [ ] No errors in logs
- [ ] Timer trigger scheduled
- [ ] Documentation updated

---

**Deployment Status:** 🔲 READY FOR DEPLOYMENT  
**Next Phase:** Phase 6 - Monitoring and Maintenance

---

*Deployment Guide - Generated: October 16, 2025*  
*Durable Functions Web Crawler v3.0.0-alpha*
