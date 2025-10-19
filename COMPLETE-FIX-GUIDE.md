# 🚨 COMPREHENSIVE FIX - Functions Not Appearing in Portal

## Current Situation Analysis

You mentioned **"no functions appeared in the portal"** after the hotfix. This could mean:

1. **Not yet deployed** - The hotfix hasn't been deployed to Azure yet
2. **Deployed but not restarted** - Deployed but Function App wasn't restarted
3. **Azure configuration issue** - App Settings might be incorrect
4. **Worker indexing disabled** - Feature flag not set

---

## 🔧 Complete Fix Process

### STEP 1: Verify Local File is Correct

Run this command to check your local function_app.py:

```powershell
cd "c:\Users\4530Holl\OneDrive - British Transport Police\_Open-Ai\Web-Crawler-Repo\functions-python-web-crawler\functions-python-web-crawler"
Get-Content function_app.py | Select-String "main = app"
```

**Expected Output**: Nothing (should be blank)
**If you see "main = app"**: The file wasn't saved correctly. Let me know and I'll fix it.

---

### STEP 2: Check Azure App Settings (CRITICAL!)

Open **Azure CLI Bash** and run:

```bash
az functionapp config appsettings list \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "[?name=='AzureWebJobsFeatureFlags' || name=='FUNCTIONS_WORKER_RUNTIME' || name=='WEBSITE_RUN_FROM_PACKAGE'].{Name:name, Value:value}" \
  --output table
```

**Expected Output**:
```
Name                          Value
----------------------------  -----------------
FUNCTIONS_WORKER_RUNTIME      python
AzureWebJobsFeatureFlags      EnableWorkerIndexing
WEBSITE_RUN_FROM_PACKAGE      1
```

**If any are missing or incorrect**, run this to fix:

```bash
# Set worker indexing (CRITICAL for Python v2)
az functionapp config appsettings set \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --settings "AzureWebJobsFeatureFlags=EnableWorkerIndexing" \
  --subscription 96726562-1726-4984-88c6-2e4f28878873

# Verify Python runtime
az functionapp config appsettings set \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --settings "FUNCTIONS_WORKER_RUNTIME=python" \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

### STEP 3: Deploy the Corrected Function App

```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v2.4.1-hotfix-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --timeout 600
```

**Wait for**: "Deployment successful" message (2-5 minutes)

---

### STEP 4: Full Restart (CRITICAL!)

```bash
# Stop the function app
az functionapp stop \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873

# Wait 30 seconds
echo "Waiting 30 seconds..."
sleep 30

# Start the function app
az functionapp start \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

**Wait**: 2-3 minutes for full startup and indexing

---

### STEP 5: Force Function Sync

```bash
az functionapp function sync \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

### STEP 6: Check Function App Logs

```bash
az functionapp logs tail \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

**Look for**:
- ✅ "Worker indexing is enabled"
- ✅ "Found functions: [list of function names]"
- ❌ Any error messages about function discovery

Press `Ctrl+C` to exit logs.

---

### STEP 7: Verify in Portal

1. Go to: https://portal.azure.com
2. Navigate to: `func-btp-uks-prod-doc-crawler-01`
3. Click **"Functions"** in left menu
4. **Refresh** the page (F5 or click refresh icon)

You should now see:
- ✅ scheduled_crawler_orchestrated
- ✅ scheduled_crawler
- ✅ http_start
- ✅ get_status  
- ✅ terminate
- ✅ manual_crawl
- ✅ search_site
- ✅ api_stats
- ✅ dashboard
- ✅ websites
- ✅ crawl
- ✅ manage_websites
- ✅ Plus orchestrator and activity functions

---

## 🆘 If Functions STILL Don't Appear

### Check 1: Python Version

```bash
az functionapp config show \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "linuxFxVersion"
```

**Expected**: `"PYTHON|3.10"` or `"PYTHON|3.11"`

**If wrong**, set it:
```bash
az functionapp config set \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --linux-fx-version "PYTHON|3.10" \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

### Check 2: Extension Bundle Version

Check your `host.json` has:
```json
"extensionBundle": {
  "id": "Microsoft.Azure.Functions.ExtensionBundle",
  "version": "[4.*, 5.0.0)"
}
```

### Check 3: Requirements.txt Dependencies

Ensure requirements.txt has:
```
azure-functions>=1.18.0
azure-functions-durable>=1.2.9
requests>=2.31.0
```

---

## 🎯 Most Common Issues

### Issue #1: Worker Indexing Not Enabled
**Symptom**: No functions visible in portal
**Fix**: Set `AzureWebJobsFeatureFlags=EnableWorkerIndexing` (Step 2 above)

### Issue #2: Function App Not Restarted
**Symptom**: Old code still running
**Fix**: Full stop/start cycle (Step 4 above)

### Issue #3: Deployment Package Corrupted
**Symptom**: Deployment succeeds but nothing works
**Fix**: Recreate ZIP and redeploy

```powershell
# In PowerShell, recreate the deployment package
cd "c:\Users\4530Holl\OneDrive - British Transport Police\_Open-Ai\Web-Crawler-Repo\functions-python-web-crawler\functions-python-web-crawler"
Compress-Archive -Path function_app.py,host.json,requirements.txt,websites.json,.funcignore -DestinationPath "v2.4.1-hotfix-deployment.zip" -Force
```

Then deploy again (Step 3).

### Issue #4: `main = app` Still in File
**Symptom**: Same problem persists
**Fix**: Check file content (Step 1) and let me know

---

## 📊 Debug Information to Collect

If nothing works, run these and share the output:

```bash
# Check app status
az functionapp show \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "{state:state, enabled:enabled, defaultHostName:defaultHostName}" \
  --output json

# Check recent deployments
az functionapp deployment list \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "[0:3].{id:id, status:status, start:startTime, complete:completeTime}" \
  --output table
```

---

## ✅ Success Criteria

You'll know it's working when:

1. ✅ Portal shows all functions listed
2. ✅ Each function shows "Enabled" status
3. ✅ You can click on a function and see its configuration
4. ✅ Timer triggers show "Last execution" time
5. ✅ HTTP triggers show their URL

---

**Follow this guide step-by-step and let me know at which step you encounter issues!**
