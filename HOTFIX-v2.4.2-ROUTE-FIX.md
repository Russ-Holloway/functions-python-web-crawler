# 🔧 HOTFIX v2.4.2 - Route Prefix Configuration Fix

## Issue Description
**Problem**: Dashboard and other endpoints returning HTTP 404 errors  
**Root Cause**: Missing explicit HTTP route prefix configuration in `host.json`  
**Impact**: All HTTP-triggered functions may not be accessible via `/api/` prefix

---

## What Was Fixed

### 1. Added Explicit Route Prefix to `host.json`
```json
"extensions": {
  "durableTask": { ... },
  "http": {
    "routePrefix": "api"
  }
}
```

This ensures all routes are accessible with the `/api/` prefix as expected.

---

## 🚀 Quick Fix Deployment

### Option A: Test Current Deployment First (Recommended)

Before redeploying, try accessing endpoints **without** the `/api/` prefix:

```bash
# Test these URLs in your browser:
https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/dashboard
https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/websites
https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/manual_crawl
```

If these work, your routes are registered without the prefix and you need to redeploy with the updated `host.json`.

### Option B: Deploy v2.4.2 Hotfix (If Option A doesn't work)

**Prerequisites**:
- Bash shell (Azure Cloud Shell, WSL, or Git Bash)
- Azure CLI authenticated
- Access to subscription: `96726562-1726-4984-88c6-2e4f28878873`

**Deployment Steps**:

```bash
# Navigate to project directory
cd "/mnt/c/Users/4530Holl/OneDrive - British Transport Police/_Open-Ai/Web-Crawler-Repo/functions-python-web-crawler/functions-python-web-crawler"

# Create v2.4.2 deployment package
zip -r v2.4.2-route-fix.zip function_app.py requirements.txt host.json local.settings.json websites.json

# Deploy to Azure
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v2.4.2-route-fix.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873

# CRITICAL: Restart the function app
az functionapp restart \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

**Wait 60 seconds** after restart before testing.

---

## ✅ Verification Steps

After deployment or restart, test these endpoints:

### 1. Dashboard (HTML)
```bash
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard
# Should return HTML content starting with <!DOCTYPE html>
```

### 2. Websites (JSON)
```bash
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/websites
# Should return JSON with websites list
```

### 3. API Stats (JSON)
```bash
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/api/stats
# Should return statistics JSON
```

### 4. Check Azure Portal
1. Go to: https://portal.azure.com
2. Navigate to Function App: `func-btp-uks-prod-doc-crawler-01`
3. Click **Functions** → Select `dashboard`
4. Click **Get Function URL** → Copy URL
5. Open in browser → Should display dashboard

---

## 🔍 Alternative Diagnostics

### Check Function App Logs
```bash
# Stream live logs (in Bash)
az webapp log tail \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

### Check Function List
```bash
# List all deployed functions (in Bash)
az functionapp function list \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --output table
```

---

## 📋 What Changed

| File | Change | Reason |
|------|--------|--------|
| `host.json` | Added `"http": { "routePrefix": "api" }` | Explicit route prefix configuration |

**No code changes required** - only configuration fix.

---

## 🎯 Expected Outcome

After this fix:
- ✅ `https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard` → Returns HTML dashboard
- ✅ `https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/websites` → Returns websites JSON
- ✅ `https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/manual_crawl` → Accepts POST requests
- ✅ All other endpoints accessible via `/api/` prefix

---

## 📞 Troubleshooting

### Still Getting 404?

**Check 1**: Verify function app is running
```bash
az functionapp show \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "state" \
  --output tsv
```
Should return: `Running`

**Check 2**: Verify app settings
```bash
az functionapp config appsettings list \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```
Look for: `WEBSITE_RUN_FROM_PACKAGE` (should be absent or "0")

**Check 3**: Enable Worker Indexing (if not already enabled)
```bash
az functionapp config appsettings set \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --settings AzureWebJobsFeatureFlags=EnableWorkerIndexing
```

---

## 🔄 Rollback Plan

If this hotfix causes issues:

```bash
# Revert to v2.4.1 (previous working version)
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v2.4.1-hotfix-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873

az functionapp restart \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

**Date**: October 18, 2025  
**Version**: v2.4.2 (Route Fix Hotfix)  
**Previous**: v2.4.1 (Function Discovery Fix)
