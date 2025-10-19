# 🔧 COMPLETE FIX: Functions Not Appearing in Azure Portal

## Root Cause Analysis

Functions not appearing in Azure Portal is typically caused by:
1. ❌ Missing `AzureWebJobsFeatureFlags` app setting in Azure
2. ❌ Wrong deployment package contents
3. ❌ Function App not restarted after deployment
4. ❌ Python worker extensions not enabled

## ✅ COMPLETE FIX - Follow ALL Steps

### Step 1: Configure Azure Function App Settings (CRITICAL)

**Run these commands in Azure CLI (Bash):**

```bash
# Set the critical Worker Indexing flag
az functionapp config appsettings set \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --settings AzureWebJobsFeatureFlags=EnableWorkerIndexing

# Verify Python runtime
az functionapp config appsettings set \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --settings FUNCTIONS_WORKER_RUNTIME=python

# Enable Python worker extensions
az functionapp config appsettings set \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --settings PYTHON_ENABLE_WORKER_EXTENSIONS=1
```

### Step 2: Re-create Deployment Package (IMPORTANT)

The ZIP file must include ONLY these files:
- `function_app.py`
- `host.json`
- `requirements.txt`
- `websites.json`

**Do NOT include:**
- ❌ `local.settings.json` (excluded by .funcignore)
- ❌ `.md` documentation files
- ❌ `.ps1` or `.sh` scripts
- ❌ `tests/` folder
- ❌ `temp-compare/` folder
- ❌ `archive/` folder

**Create clean deployment package:**

```powershell
# In PowerShell
cd "c:\Users\4530Holl\OneDrive - British Transport Police\_Open-Ai\Web-Crawler-Repo\functions-python-web-crawler\functions-python-web-crawler"

# Delete old ZIP if exists
Remove-Item v2.4.2-deployment.zip -ErrorAction SilentlyContinue

# Create NEW ZIP with ONLY required files
Compress-Archive -Path function_app.py,host.json,requirements.txt,websites.json -DestinationPath v2.4.2-deployment.zip -Force

# Verify ZIP contents
Add-Type -Assembly System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead("$PWD\v2.4.2-deployment.zip")
$zip.Entries | Select-Object FullName
$zip.Dispose()
```

### Step 3: Deploy to Azure

**In Azure CLI Bash:**

```bash
cd /mnt/c/Users/4530Holl/OneDrive\ -\ British\ Transport\ Police/_Open-Ai/Web-Crawler-Repo/functions-python-web-crawler/functions-python-web-crawler

# Deploy the package
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --src v2.4.2-deployment.zip
```

### Step 4: Restart Function App (MANDATORY)

```bash
# Full restart to reinitialize worker process
az functionapp restart \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

**Wait 2-3 minutes after restart** for function discovery to complete.

### Step 5: Verify Deployment

```bash
# Check deployment status
az functionapp deployment list \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873

# Verify app settings
az functionapp config appsettings list \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "[?name=='AzureWebJobsFeatureFlags' || name=='FUNCTIONS_WORKER_RUNTIME' || name=='PYTHON_ENABLE_WORKER_EXTENSIONS']" \
  --output table
```

### Step 6: Check Function Discovery in Azure Portal

1. Open Azure Portal
2. Navigate to: **Function App** → `func-btp-uks-prod-doc-crawler-01`
3. Click on **"Functions"** in left menu
4. Wait for functions to load (may take 30-60 seconds)

**You should see these functions:**

#### Timer Triggers (2)
- ✅ `scheduled_crawler_orchestrated`
- ✅ `scheduled_crawler`

#### Durable Functions (7)
- ✅ `web_crawler_orchestrator` (Orchestrator)
- ✅ `get_configuration_activity` (Activity)
- ✅ `get_document_hashes_activity` (Activity)
- ✅ `crawl_single_website_activity` (Activity)
- ✅ `store_document_hashes_activity` (Activity)
- ✅ `store_crawl_history_activity` (Activity)
- ✅ `validate_storage_activity` (Activity)

#### HTTP Triggers (10)
- ✅ `http_start` (POST - Start orchestration)
- ✅ `http_get_status` (GET - Get orchestration status)
- ✅ `http_terminate` (POST - Terminate orchestration)
- ✅ `manual_crawl` (POST - Manual crawl trigger)
- ✅ `search_site` (GET - Search documents)
- ✅ `api_stats` (GET - Statistics)
- ✅ `dashboard` (GET - Dashboard)
- ✅ `websites` (GET - Website config)
- ✅ `crawl` (POST - Crawl alias)
- ✅ `manage_websites` (GET/POST - Website management)

---

## 🔍 Troubleshooting

### If functions STILL don't appear:

#### Check Application Insights Logs

```bash
# Get recent logs
az monitor app-insights query \
  --app func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --analytics-query "traces | where timestamp > ago(30m) | where message contains 'function' or message contains 'error' | project timestamp, message | order by timestamp desc" \
  --offset 30m
```

#### Check Function App Logs

1. Portal → Function App → **Log stream**
2. Look for errors like:
   - `Failed to index functions`
   - `Worker initialization failed`
   - `Python version mismatch`

#### Verify Python Version

```bash
az functionapp config show \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "linuxFxVersion"
```

Should return: `"PYTHON|3.10"` or `"PYTHON|3.11"`

If wrong version, set it:
```bash
az functionapp config set \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --linux-fx-version "PYTHON|3.10"
```

#### Test HTTP Endpoints Directly

Even if functions don't appear in portal, they might still work:

```bash
# Test dashboard
curl -v https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard

# Test websites
curl -v https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/websites

# Test info endpoint (if exists)
curl -v https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/info
```

---

## 🎯 Expected Results

After completing ALL steps above:

✅ All 19 functions appear in Azure Portal  
✅ HTTP endpoints return 200 OK responses  
✅ No errors in Application Insights logs  
✅ Function App status shows "Running"  
✅ Timer triggers show next scheduled run time  

---

## 🆘 Still Not Working?

If after following ALL steps functions still don't appear:

1. **Verify deployment package contents:**
   ```powershell
   # List ZIP contents
   Expand-Archive -Path v2.4.2-deployment.zip -DestinationPath temp-extract -Force
   Get-ChildItem temp-extract -Recurse | Select-Object FullName
   Remove-Item temp-extract -Recurse -Force
   ```

2. **Check for syntax errors in function_app.py:**
   - Open `function_app.py` in VS Code
   - Check for any red error markers
   - Look at the Problems panel (Ctrl+Shift+M)

3. **Force complete redeployment:**
   ```bash
   # Stop function app
   az functionapp stop \
     --resource-group rg-btp-uks-prod-doc-mon-01 \
     --name func-btp-uks-prod-doc-crawler-01 \
     --subscription 96726562-1726-4984-88c6-2e4f28878873
   
   # Deploy
   az functionapp deployment source config-zip \
     --resource-group rg-btp-uks-prod-doc-mon-01 \
     --name func-btp-uks-prod-doc-crawler-01 \
     --subscription 96726562-1726-4984-88c6-2e4f28878873 \
     --src v2.4.2-deployment.zip
   
   # Start function app
   az functionapp start \
     --resource-group rg-btp-uks-prod-doc-mon-01 \
     --name func-btp-uks-prod-doc-crawler-01 \
     --subscription 96726562-1726-4984-88c6-2e4f28878873
   ```

4. **Contact for advanced diagnostics** if none of the above works

---

**Created**: October 18, 2025  
**Version**: v2.4.2 Deployment Fix Guide  
**Status**: 🚨 FOLLOW ALL STEPS IN ORDER
