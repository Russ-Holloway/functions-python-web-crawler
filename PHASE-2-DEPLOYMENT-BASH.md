# Phase 2 Deployment Guide - Azure CLI Bash

## Overview
Phase 2 adds monitoring and validation features to ensure Phase 1's unique filename generation works correctly. This deployment includes:
- ✅ Collision detection tracking
- ✅ Storage validation after each crawl
- ✅ Enhanced dashboard with validation metrics
- ✅ Automatic accuracy percentage calculation

## Prerequisites
- Phase 1 successfully deployed (unique filename generation)
- Azure CLI installed and configured
- Bash shell environment (Azure Cloud Shell or WSL)
- Logged into Azure: `az login`

## Deployment Steps

### 1. Navigate to Project Directory
```bash
cd "c:\\Users\\4530Holl\\OneDrive - British Transport Police\\_Open-Ai\\Web-Crawler-Repo\\functions-python-web-crawler\\functions-python-web-crawler"
```

### 2. Create Phase 2 Deployment Package
```bash
# Create ZIP file with all application files (Windows path)
powershell.exe -Command "Compress-Archive -Path * -DestinationPath phase2-deployment.zip -Force"

# Verify ZIP was created
ls -la phase2-deployment.zip
```

### 3. Deploy to Azure Function App
```bash
# Deploy using Azure CLI with correct resource names
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src phase2-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

### 4. Verify Deployment
```bash
# Check function app status
az functionapp show \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "{name:name, state:state, defaultHostName:defaultHostName}" \
  --output table
```

### 5. View Function App Logs (Optional)
```bash
# Stream live logs to verify deployment
az webapp log tail \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

## Phase 2 Features

### 1. Collision Detection
- Tracks all filenames generated during crawl
- Detects if MD5 hash algorithm produces duplicates
- Should always be **0 collisions** (hash algorithm is collision-resistant)
- Logs warning if collisions detected

### 2. Storage Validation
- New activity function: `validate_storage_activity`
- Runs after document uploads complete
- Compares uploaded count to actual storage count
- Calculates accuracy percentage
- Status: `match` or `mismatch`

### 3. Enhanced Dashboard
- New validation card showing Phase 2 metrics
- Displays:
  - Validation status (✅ Match / ⚠️ Mismatch)
  - Storage accuracy percentage
  - Last validation timestamp
  - Uploaded vs verified document counts
  - Collision count (should be 0)

### 4. Orchestrator Enhancements
- Aggregates `collision_count` from all site crawls
- Calls `validate_storage_activity` after hash storage
- Includes validation results in crawl summary
- Enhanced logging with collision and validation status

## Validation After Deployment

### Check Dashboard
Visit: `https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard`

Look for:
- ✅ New "Storage Validation (Phase 2)" card
- ✅ Collision count in Recent Activity
- ✅ Validation status and accuracy percentage

### Monitor Next Scheduled Crawl
The scheduled crawler runs every 4 hours. After the next run:
1. Check dashboard for validation results
2. Verify **0 collisions detected**
3. Confirm validation status is **MATCH**
4. Check accuracy percentage is **100%** or close

### API Stats
```bash
# Get statistics via API
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/api/stats
```

Look for new fields:
- `recent_activity.collisions_detected_24h` (should be 0)
- `validation.status` (should be "match")
- `validation.accuracy_percentage` (should be 100)

## Troubleshooting

### Deployment Fails
- Verify resource names match `AZURE_RESOURCE_REFERENCE.md`
- Check subscription ID is correct
- Ensure ZIP file was created successfully
- Verify Azure CLI is logged in: `az account show`

### Validation Shows Mismatch
- Check Application Insights logs for upload errors
- Verify blob storage permissions
- Review crawl history for error messages
- Check if storage account is accessible

### Collisions Detected (Unexpected)
- Should never happen with MD5 hash algorithm
- If detected, investigate immediately
- Check logs for duplicate hash values
- May indicate data corruption or logic error

## Success Criteria

Phase 2 deployment is successful when:
- ✅ Function app deploys without errors
- ✅ Dashboard displays Phase 2 validation card
- ✅ Next scheduled crawl runs successfully
- ✅ Validation status shows **MATCH**
- ✅ Collision count is **0**
- ✅ Accuracy percentage is **100%**
- ✅ Storage count matches upload count

## Resource Reference
All Azure resource names from: `AZURE_RESOURCE_REFERENCE.md`
- Resource Group: `rg-btp-uks-prod-doc-mon-01`
- Function App: `func-btp-uks-prod-doc-crawler-01`
- Storage Account: `stbtpuksprodcrawler01`
- Subscription: `96726562-1726-4984-88c6-2e4f28878873`

## Next Steps
After successful Phase 2 deployment:
1. Monitor validation results for 24-48 hours
2. Verify collision count remains at 0
3. Confirm storage accuracy stays at 100%
4. Phase 1 fix is validated by Phase 2 monitoring
5. System is production-ready with full monitoring

---
**Version**: v2.2.0 Phase 2  
**Date**: January 2025  
**Deployment Method**: Azure CLI with Bash + ZIP file
