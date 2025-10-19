# Deployment Guide - v2.4.0
## Storage Validation & Monitoring

**Version**: v2.4.0  
**Date**: January 17, 2025  
**Previous Version**: v2.3.0  
**Deployment Method**: Azure CLI with Bash + ZIP file

---

## What's New in v2.4.0

### Features Added
- ✅ **Collision Detection** - Tracks filename generation duplicates (should always be 0)
- ✅ **Storage Validation** - Automatically validates uploaded count matches storage count
- ✅ **Enhanced Dashboard** - New validation card with Phase 2 metrics
- ✅ **Accuracy Tracking** - Calculates and displays storage accuracy percentage
- ✅ **Validation Activity** - New `validate_storage_activity` function

### Purpose
Provides monitoring to ensure v2.3.0's unique filename fix works correctly and prevents future data loss.

---

## Prerequisites

- ✅ v2.3.0 deployed and running
- ✅ Azure CLI installed and configured
- ✅ Bash shell environment (Azure Cloud Shell or WSL)
- ✅ Logged into Azure: `az login`

---

## Deployment Steps

### Step 1: Navigate to Project Directory

```bash
cd "c:\\Users\\4530Holl\\OneDrive - British Transport Police\\_Open-Ai\\Web-Crawler-Repo\\functions-python-web-crawler\\functions-python-web-crawler"
```

### Step 2: Create v2.4.0 Deployment Package

```bash
# Create ZIP file with all application files
powershell.exe -Command "Compress-Archive -Path function_app.py,requirements.txt,host.json,local.settings.json,websites.json -DestinationPath v2.4.0-deployment.zip -Force"

# Verify ZIP was created
ls -la v2.4.0-deployment.zip
```

### Step 3: Deploy to Azure Function App

```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v2.4.0-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

### Step 4: Verify Deployment

```bash
# Check function app status
az functionapp show \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "{name:name, state:state, version:'v2.4.0'}" \
  --output table
```

### Step 5: Monitor Logs (Optional)

```bash
# Stream live logs
az webapp log tail \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

## Post-Deployment Verification

### 1. Check Dashboard
Visit: `https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard`

**Look For:**
- ✅ New "Storage Validation (Phase 2)" card
- ✅ Collision count in "Recent Activity" section
- ✅ Validation status indicator (should show ✅ MATCH after first crawl)
- ✅ Storage accuracy percentage (should be 100% or very close)

### 2. Verify API Response
```bash
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/api/stats
```

**Check for New Fields:**
```json
{
  "recent_activity": {
    "collisions_detected_24h": 0
  },
  "validation": {
    "last_check": "2025-01-17T...",
    "status": "match",
    "uploaded_count": 150,
    "storage_count": 150,
    "accuracy_percentage": 100.0
  }
}
```

### 3. Wait for Next Scheduled Crawl
- Runs every 4 hours automatically
- First crawl will populate validation metrics
- Expected: 0 collisions, 100% accuracy, MATCH status

---

## Success Criteria

v2.4.0 deployment is successful when:

1. ✅ Function app deploys without errors
2. ✅ Dashboard displays new validation card
3. ✅ Next crawl completes successfully
4. ✅ Validation status: **MATCH**
5. ✅ Collision count: **0**
6. ✅ Accuracy: **100%** (or very close)
7. ✅ Storage count equals uploaded count

---

## Troubleshooting

### Deployment Fails
- Verify resource names match `AZURE_RESOURCE_REFERENCE.md`
- Check Azure CLI is logged in: `az account show`
- Ensure ZIP file contains all required files
- Review error message for specific issue

### Validation Shows Mismatch
- Check Application Insights for upload errors
- Verify blob storage is accessible
- Review crawl logs for failures
- Confirm Managed Identity permissions

### Collisions Detected (Unexpected)
- **Should NEVER happen** with MD5 hash
- Indicates serious issue if detected
- Check logs immediately
- Review hash generation logic

---

## Cleanup After Successful Deployment

Once v2.4.0 is verified working:

1. **Rename old deployment package:**
   ```bash
   mkdir -p archive
   mv phase1-deployment.zip archive/v2.3.0-deployment.zip
   ```

2. **Delete old documentation:**
   ```bash
   rm PHASE-1-DEPLOYMENT-BASH.md
   rm PHASE-1-SUMMARY.md
   rm PHASE-2-PLAN.md
   rm PHASE-2-DEPLOYMENT-BASH.md
   ```

3. **Update CHANGELOG:**
   - Add v2.4.0 deployment date and notes

4. **Update VERSION-TRACKING:**
   - Mark v2.4.0 as deployed
   - Update "Current Production Version"

---

## Rollback Procedure (If Needed)

If v2.4.0 has issues:

```bash
# Redeploy v2.3.0
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src archive/v2.3.0-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

## Azure Resource Reference

**See**: `AZURE_RESOURCE_REFERENCE.md`

- **Resource Group**: `rg-btp-uks-prod-doc-mon-01`
- **Function App**: `func-btp-uks-prod-doc-crawler-01`
- **Storage Account**: `stbtpuksprodcrawler01`
- **Subscription**: `96726562-1726-4984-88c6-2e4f28878873`

---

## Files Modified in v2.4.0

### function_app.py
- Added `validate_storage_consistency()` function (~line 285)
- Added collision detection in document loop (~line 600)
- Added `validate_storage_activity()` function (~line 1181)
- Updated orchestrator with validation call (~line 1050)
- Enhanced API stats with Phase 2 metrics (~line 1900)
- Added dashboard validation card (~line 2220)
- Added `updateValidationStats()` JavaScript function (~line 2440)

---

## Next Steps After Deployment

1. Monitor dashboard for 24-48 hours
2. Verify validation metrics remain healthy
3. Confirm collision count stays at 0
4. Check accuracy percentage stays at 100%
5. Proceed with cleanup once validated
6. Update documentation with deployment date

---

**Deployment Status**: ⏳ Ready for Deployment  
**Last Updated**: January 17, 2025
