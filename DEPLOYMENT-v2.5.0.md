# 🚀 DEPLOYMENT GUIDE - v2.5.0: Functions Not Appearing Fix

## 📋 **Overview**

**Version**: v2.5.0  
**Issue**: Functions not appearing in Azure Portal  
**Status**: ✅ Ready to Deploy  
**Priority**: 🚨 CRITICAL FIX

---

## 🎯 **What This Fixes**

### Problem
Functions are not showing up in the Azure Portal Functions list, even though:
- Code has proper decorators
- Function App is deployed
- No errors in logs

### Root Cause
The deployed version in Azure may be:
1. Missing the latest code changes
2. Using an incorrect Python programming model
3. Not properly registered with the Azure Functions runtime
4. Has incorrect extension bundle configuration

### Solution
Complete redeployment with verified v2.5.0 package containing:
- ✅ 20+ properly decorated functions
- ✅ Correct host.json with extension bundle [4.*, 5.0.0)
- ✅ Python v2 programming model (decorator-based)
- ✅ Single `app` instance with proper initialization

---

## 📦 **Deployment Package Contents**

**File**: `v2.5.0-deployment.zip`

```
v2.5.0-deployment.zip
├── function_app.py       (2,685 lines - all functions decorated)
├── host.json             (Extension bundle configured)
├── requirements.txt      (Azure Functions packages)
└── websites.json         (Website configurations)
```

### Functions Included (20+ Total):

#### Durable Functions:
- `web_crawler_orchestrator` - Main orchestration
- `get_configuration_activity` - Load config
- `get_document_hashes_activity` - Get hashes
- `crawl_single_website_activity` - Crawl site
- `store_document_hashes_activity` - Store hashes
- `store_crawl_history_activity` - Store history
- `validate_storage_activity` - Validate storage

#### Timer Triggers:
- `scheduled_crawler_orchestrated` - Every 4 hours (durable)
- `scheduled_crawler` - Every 4 hours (legacy)

#### HTTP Triggers:
- `start_web_crawler_orchestration` - POST /api/orchestrators/web_crawler
- `get_orchestration_status` - GET /api/orchestrators/web_crawler/{instanceId}
- `terminate_orchestration` - POST /api/orchestrators/web_crawler/{instanceId}/terminate
- `manual_crawl` - POST /api/manual_crawl
- `search_site` - GET /api/search_site
- `api_stats` - GET /api/api/stats
- `dashboard` - GET /api/dashboard
- `websites` - GET /api/websites
- `crawl` - POST /api/crawl
- `manage_websites` - GET/POST /api/manage_websites
- `ping` - GET /api/ping

---

## 🔧 **Pre-Deployment Checklist**

Before deploying, ensure:

- [ ] Azure CLI is installed (`az --version`)
- [ ] Logged into Azure (`az login`)
- [ ] Correct subscription selected (`az account show`)
- [ ] Deployment package exists (`ls -lh v2.5.0-deployment.zip`)
- [ ] Resource names verified in `AZURE_RESOURCE_REFERENCE.md`

---

## 🚀 **DEPLOYMENT COMMANDS**

### Step 1: Deploy the Package

```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v2.5.0-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

**Expected Output:**
```json
{
  "active": true,
  "author": "N/A",
  "complete": true,
  "deployer": "ZipDeploy",
  "status": 4,
  "statusText": "Success"
}
```

### Step 2: Restart the Function App (CRITICAL!)

```bash
az functionapp restart \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

**Why Restart is Critical:**
The Azure Functions runtime needs to restart to:
- Discover newly deployed functions
- Reload the Python worker
- Re-register all function decorators
- Update the function metadata in the portal

---

## ✅ **POST-DEPLOYMENT VERIFICATION**

### 1. Check Functions in Portal

1. Go to: https://portal.azure.com
2. Navigate to: `func-btp-uks-prod-doc-crawler-01`
3. Click: **Functions** (left sidebar)
4. **Expected**: See 20+ functions listed

### 2. Test the Ping Endpoint

```bash
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/ping
```

**Expected Response:**
```json
{
  "status": "alive",
  "message": "Function app is running",
  "timestamp": "2025-10-19T...",
  "version": "v2.4.2"
}
```

### 3. Check Function Logs

```bash
az functionapp logs tail \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

**Look for:**
- "Host started"
- Function discovery messages
- No registration errors

### 4. Test Manual Crawl (Optional)

```bash
curl -X POST https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.legislation.gov.uk/uksi/2024/1052/contents"}'
```

---

## 🔍 **Troubleshooting**

### Functions Still Not Appearing?

#### Check 1: Verify Python Runtime
```bash
az functionapp config appsettings list \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "[?name=='FUNCTIONS_WORKER_RUNTIME'].value"
```
**Expected**: `"python"`

#### Check 2: Verify Extension Bundle
```bash
az functionapp config appsettings list \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "[?name=='AzureWebJobsFeatureFlags'].value"
```
**Expected**: Should include `"EnableWorkerIndexing"`

#### Check 3: Force Sync Triggers
```bash
az functionapp function keys list \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --function-name ping \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

This forces Azure to rescan and register all functions.

#### Check 4: Review Application Insights
If functions still don't appear, check Application Insights logs for startup errors:

1. Portal → Function App → Application Insights
2. Look for "Function host startup" entries
3. Check for Python worker initialization errors

---

## 📊 **Success Criteria**

Deployment is successful when:

- ✅ All 20+ functions appear in Azure Portal Functions list
- ✅ HTTP triggers show correct routes (e.g., /api/ping, /api/crawl)
- ✅ Timer triggers show schedule (0 0 */4 * * *)
- ✅ Durable Functions orchestrator is visible
- ✅ Activity functions are registered
- ✅ Ping endpoint returns v2.4.2 response
- ✅ No errors in Function App logs

---

## 🔄 **Rollback Plan**

If deployment fails, rollback to previous version:

```bash
# Deploy previous version (if archive exists)
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src archive/v2.4.2-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873

# Restart
az functionapp restart \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

## 📝 **Post-Deployment Actions**

After successful deployment:

1. **Archive Old Package**: `mkdir -p archive && mv v2.4.2-deployment.zip archive/`
2. **Update CHANGELOG.md**: Add v2.5.0 deployment entry
3. **Update VERSION-TRACKING.md**: Mark v2.5.0 as deployed
4. **Clean Up Old Docs**: Remove obsolete hotfix documentation
5. **Test Single Site Crawl**: Verify end-to-end functionality

---

## 📞 **Support**

If issues persist after following this guide:

1. Check Azure Portal → Function App → Diagnose and solve problems
2. Review Application Insights logs
3. Check `TROUBLESHOOTING.md` (if exists)
4. Contact Azure Support with deployment details

---

## 🎉 **Expected Outcome**

After successful deployment:
- **Portal**: All functions visible and healthy
- **Monitoring**: Functions execute successfully
- **Logs**: Clean startup, no errors
- **Status**: Full operational capability restored

---

**Deployment Guide Version**: v2.5.0  
**Last Updated**: October 19, 2025  
**Author**: GitHub Copilot (AI Assistant)
