# Version Tracking - Web Crawler Project

## Current Version: v2.7.0 (Fixed 'Other' Category Issue - Ready to Deploy)

---

## Version History

### v2.7.0 - Fixed 'Other' Category Issue (BUG FIX)
**Status**: 🚀 **READY TO DEPLOY**  
**Date**: October 21, 2025  
**Type**: Bug Fix - Dashboard Accuracy

**Problem Fixed:**
Documents were appearing in the dashboard as "Other" category even though all documents should be properly categorized by website.

**Root Cause:**
The `get_storage_statistics()` function was not properly filtering out folder placeholder files (`.folder`) that were being created by `ensure_website_folder_exists()`. These system files don't have document content but were being counted in statistics.

**Changes Made:**

1. ✅ **Enhanced File Filtering** - Now excludes `.folder` placeholder files from statistics (line 983)
2. ✅ **Better Error Logging** - Documents without folder prefix now logged as warnings for investigation
3. ✅ **Clearer Categorization** - Changed "other" to "Uncategorized (Legacy)" for better clarity
4. ✅ **NEW: Cleanup Utility** - Added `/api/cleanup_uncategorized` endpoint to delete uncategorized documents
   - GET: Lists uncategorized documents (dry run - safe)
   - POST with `{"dry_run": false}`: Actually deletes documents
   - Deleted documents re-downloaded on next crawl with proper structure
5. ✅ **Code Quality** - Improved comments and structure for maintainability

**Technical Details:**
```python
# Before: Only filtered specific filenames
if name and name not in ['document_hashes.json', 'crawl_history.json']:

# After: Also filters folder placeholders
if name and name not in ['document_hashes.json', 'crawl_history.json'] and not name.endswith('/.folder'):
```

**Impact:**
- ✅ Dashboard now shows accurate document counts per website
- ✅ No more "Other" category for properly stored documents
- ✅ Better visibility into any legacy documents without folder structure
- ✅ Cleaner storage statistics

**Deployment:**
- No breaking changes - safe to deploy over v2.6.0
- Backward compatible with existing storage structure
- Immediate dashboard accuracy improvement

---

### v2.6.0 - Smart Storage Organization + AI-Ready Metadata (MAJOR ENHANCEMENT)
**Status**: 🚀 **READY TO DEPLOY**  
**Date**: October 19, 2025  
**Type**: Major Enhancement - Architecture Improvement

**What This Delivers:**
This is the BEST implementation combining organization AND AI-search capability!

**Key Features:**
1. ✅ **Automatic Folder Creation** - Each website gets its own folder in storage
2. ✅ **Rich Blob Metadata** - Every document tagged with website info for AI search
3. ✅ **Single Container** - AI-friendly `documents/` container structure
4. ✅ **Dynamic Dashboard** - Stats automatically grouped by website
5. ✅ **Folder Initialization** - New endpoint to create folders for all websites

**Architecture:**
```
Storage: stbtpuksprodcrawler01/documents/
├── college-of-policing-app-portal/
│   └── abc123_document.pdf (+ metadata: websiteid, websitename, crawldate)
├── crown-prosecution-service/
│   └── def456_guidance.pdf (+ metadata)
├── npcc-publications-all-publications/
│   └── ghi789_report.pdf (+ metadata)
└── uk-legislation-test-working/
    └── jkl012_act.xml (+ metadata)
```

**Blob Metadata Attached:**
- `websiteid` - Website ID from config (e.g., "cps_working")
- `websitename` - Display name (e.g., "Crown Prosecution Service")
- `crawldate` - ISO timestamp of crawl
- `documenttype` - Type of document
- `originalfilename` - Original filename before sanitization
- `status` - "new", "changed", or "unchanged"
- `documenturl` - Original source URL

**Benefits:**
- ✅ **AI Search Ready** - Single container for Azure AI Search/OpenAI
- ✅ **Rich Filtering** - Query by website, date, type using metadata
- ✅ **Visual Organization** - Clear folder structure in Azure Portal
- ✅ **Auto-Initialization** - Folders created automatically on first crawl
- ✅ **Easy Management** - Navigate/manage docs by website folder
- ✅ **Future-Proof** - New websites automatically get folders

**New Functions:**
- `get_folder_name_for_website()` - Convert website name to folder name
- `ensure_website_folder_exists()` - Create folder with placeholder
- Enhanced `upload_to_blob_storage_real()` - Now adds rich metadata
- Enhanced `get_storage_statistics()` - Dynamic website mapping
- New endpoint: `/api/initialize_folders` - Create all folders at once

**Changes:**
- `upload_to_blob_storage_real()` - Added metadata parameters
- `crawl_website_core()` - Automatic folder creation before crawl
- `get_storage_statistics()` - Dynamic loading from websites.json
- `generate_unique_filename()` - Reverted to folder prefix structure

**Deployment:**
```bash
# Deploy
git add -A
git commit -m "v2.6.0: Smart storage with folders + AI-ready metadata"
git push origin main

# After deployment, initialize folders
curl -X POST https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/initialize_folders
```

**AI Integration Ready:**
This structure is PERFECT for:
- Azure AI Search indexing (single container)
- Azure OpenAI on Your Data
- Custom RAG (Retrieval-Augmented Generation) solutions
- Filtered searches by website using metadata

**No Breaking Changes:**
- Existing documents remain accessible
- New crawls use enhanced structure
- Dashboard automatically adapts

---

### v2.5.2 - Dashboard Storage Labels Enhancement
**Status**: 🚀 **READY TO DEPLOY**  
**Date**: October 19, 2025  
**Type**: Enhancement - UI Improvement

**Enhancement:**
Updated dashboard storage statistics to display documents grouped by actual website names instead of generic categories.

**Changes:**
- **Before:** Documents labeled as "CPS", "LEGISLATION", "OTHER" (keyword-based matching)
- **After:** Documents labeled by actual website titles:
  - "College of Policing"
  - "Crown Prosecution Service"
  - "UK Legislation"
  - "NPCC Publications"
  - "UK Legislation - Public Acts"

**Technical Details:**
- Modified `get_storage_statistics()` to extract folder prefix from filenames
- Updated site categorization to use folder structure instead of keyword matching
- Simplified dashboard JavaScript to display names as-is (no transformation)
- Added proper mapping from sanitized folder names to display names

**Files Modified:**
- `function_app.py` - Lines 781-808 (categorization logic)
- `function_app.py` - Lines 2397-2407 (dashboard display)

**Deployment:**
```bash
# Automatic via GitHub Actions
git add function_app.py VERSION-TRACKING.md CHANGELOG.md
git commit -m "v2.5.2: Enhanced dashboard labels with website names"
git push origin main
```

**No breaking changes** - Purely cosmetic UI enhancement

---

### v2.5.1 - Storage Permissions Fix
**Status**: ✅ **DEPLOYED & OPERATIONAL**  
**Date**: October 19, 2025  
**Type**: Configuration Fix (No code changes)

**Issue Resolved:**
Dashboard displaying "HTTP Error 403: This request is not authorized to perform this operation using this permission" when accessing storage statistics.

**Root Cause:**
Function App's managed identity lacked RBAC permissions on storage account `stbtpuksprodcrawler01`.

**Solution Applied:**
Assigned **"Storage Blob Data Contributor"** role to Function App's managed identity on storage account.

**Azure CLI Commands Used:**
```bash
# Get Function App managed identity principal ID
PRINCIPAL_ID=$(az functionapp identity show --name func-btp-uks-prod-doc-crawler-01 --resource-group rg-btp-uks-prod-doc-mon-01 --subscription 96726562-1726-4984-88c6-2e4f28878873 --query principalId --output tsv)

# Assign Storage Blob Data Contributor role
az role assignment create --assignee $PRINCIPAL_ID --role "Storage Blob Data Contributor" --scope /subscriptions/96726562-1726-4984-88c6-2e4f28878873/resourceGroups/rg-btp-uks-prod-doc-mon-01/providers/Microsoft.Storage/storageAccounts/stbtpuksprodcrawler01 --subscription 96726562-1726-4984-88c6-2e4f28878873
```

**What This Fixes:**
- ✅ Dashboard storage statistics now loading correctly
- ✅ `/api/stats` endpoint returning complete data
- ✅ Storage operations (list, read, write blobs) working
- ✅ Crawl history accessible
- ✅ Document upload tracking functional

**Files Created:**
- `fix-storage-permissions.sh` - Automated fix script
- `STORAGE-PERMISSIONS-FIX.md` - Detailed documentation
- `FIX-COMMANDS.txt` - Manual command reference

**No deployment required** - Configuration change only

---

### v2.5.0 - Complete Function App Fix (CRITICAL)
**Status**: ✅ **DEPLOYED** - Functions now appearing in portal  
**Date**: October 19, 2025  
**Deployment Package**: `v2.5.0-deployment.zip`

**Issue Resolved:**
Functions not appearing in Azure Portal despite proper decorator-based registration. This comprehensive fix ensures:
- ✅ Proper Python v2 programming model structure
- ✅ Correct extension bundle configuration ([4.*, 5.0.0))
- ✅ All decorators properly applied to functions
- ✅ Single `app` instance initialization
- ✅ Verified deployment package structure

**What This Fixes:**
1. Functions not showing up in Azure Portal Functions list
2. Missing HTTP triggers in portal UI
3. Durable Functions orchestrator not visible
4. Activity functions not registered

**Files Verified:**
- `function_app.py` - Complete with 20+ decorated functions
  - 1 orchestration trigger (`web_crawler_orchestrator`)
  - 6 activity triggers (configuration, hashes, crawling, storage, validation)
  - 2 timer triggers (orchestrated + legacy schedulers)
  - 13 HTTP route triggers (API endpoints)
- `host.json` - Extension bundle [4.*, 5.0.0) configured
- `requirements.txt` - Latest Azure Functions packages
- `websites.json` - Website configuration

**Deployment Method:**
GitHub Actions CI/CD (Automatic on push to main)

**Quick Deploy:**
```bash
git add .
git commit -m "v2.5.0: Fix functions not appearing in portal"
git push origin main
```

**Alternative - Manual ZIP Deployment:**
```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v2.5.0-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

### v2.4.2 - Function Registration Fix (CRITICAL)
**Status**: 🚨 **HOTFIX READY** - Deploy Immediately  
**Date**: October 18, 2025  
**Deployment Package**: `v2.4.2-deployment.zip`

**Critical Fix:**
- ✅ Fixed function registration using proper decorator-based approach
- ✅ Moved app initialization before function definitions
- ✅ Added decorators to orchestrator and all activity functions
- ✅ Removed incorrect manual registration code
- ✅ All functions now discoverable by Azure runtime

**Issue Resolved:**
Functions were not appearing in Azure Portal because they lacked proper decorator-based registration. The orchestrator and activity functions were defined as plain Python functions without decorators, then manually registered afterward. The Azure Functions v2 programming model requires decorators to be applied at function definition time.

**Files Modified:**
- `function_app.py` - Complete registration overhaul:
  - Moved `app = df.DFApp()` initialization to line 955 (before functions)
  - Added `@app.orchestration_trigger()` decorator to orchestrator
  - Added `@app.activity_trigger()` decorators to 6 activity functions
  - Removed manual registration section (lines 1202-1219 deleted)

**Documentation:**
- `HOTFIX-v2.4.2-FUNCTION-REGISTRATION.md` - Complete fix analysis and deployment guide

**Deployment Command:**
```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v2.4.2-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873

# CRITICAL: Restart after deployment
az functionapp restart \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

### v2.4.1 - Function Discovery Hotfix (SUPERSEDED)
**Status**: 🚨 **HOTFIX READY** - Deploy Immediately  
**Date**: October 17, 2025  
**Deployment Package**: `v2.4.1-hotfix-deployment.zip`

**Critical Fix:**
- ❌ Removed incorrect `main = app` export statement
- ✅ Fixed function discovery in Azure Portal
- ✅ All functions now visible and operational

**Issue Resolved:**
Functions were not appearing in Azure Portal due to incorrect export statement at end of function_app.py. The Python v2 programming model expects only the `app` object, not a `main` variable.

**Files Modified:**
- `function_app.py` - Removed lines 2671-2673 (incorrect export)

**Documentation:**
- `HOTFIX-DEPLOYMENT-v2.4.1.md` - Full hotfix deployment guide

**Deployment Command:**
```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v2.4.1-hotfix-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873

# CRITICAL: Restart after deployment
az functionapp restart \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

### v2.4.0 - Storage Validation & Monitoring (Phase 2)
**Status**: 🚀 **DEPLOYED** - Awaiting Validation  
**Date**: January 17, 2025  
**Deployment Package**: `v2.4.0-deployment.zip`

**What's New:**
- ✅ Collision detection tracking
- ✅ Storage validation after each crawl
- ✅ Enhanced dashboard with validation metrics
- ✅ Automatic accuracy percentage calculation
- ✅ New validation activity function

**Files Modified:**
- `function_app.py` - Added validation function, collision tracking, dashboard enhancements

**Documentation:**
- `DEPLOYMENT-v2.4.0.md` - Full deployment guide

**Deployment Command:**
```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v2.4.0-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

### v2.3.0 - Unique Filename Fix (Phase 1)
**Status**: ✅ Deployed & Running  
**Date**: January 17, 2025  
**Deployment Package**: `v2.3.0-deployment.zip` (previously named phase1-deployment.zip)

**What's New:**
- ✅ Unique filename generation using MD5 URL hash
- ✅ Prevents filename collisions
- ✅ Format: `{site}/{8-char-hash}_{filename}.{ext}`
- ✅ Fixes 90% data loss issue

**Files Modified:**
- `function_app.py` - Added `generate_unique_filename()` function
- `.github/copilot-instructions.md` - Updated deployment workflow

**Documentation:**
- ~~`PHASE-1-DEPLOYMENT-BASH.md`~~ (Archived after deployment)
- ~~`PHASE-1-SUMMARY.md`~~ (Archived after deployment)
- ~~`PHASE-1-COMPLETION.md`~~ (Archived after deployment)

**Verification:**
- Function app status: Running ✅
- Awaiting next scheduled crawl for validation

---

### v2.2.0 - Baseline (Production)
**Status**: ✅ Previously Deployed (Storage Issue Identified)  
**Date**: Before January 2025  
**Issue**: 90% data loss due to filename collisions

**Problem:**
- 21,555 documents processed
- 2,810 documents uploaded
- Only 281 documents in storage (90% loss)
- Cause: Same filenames from different URLs overwriting each other

**Resolution:** Fixed in v2.3.0

---

## File Naming Convention

### Deployment Packages
- `v{major}.{minor}.{patch}-deployment.zip`
- Example: `v2.4.0-deployment.zip`

### Documentation (Keep Only Current Version)
- `DEPLOYMENT-v{version}.md` - Current deployment guide
- `CHANGELOG.md` - Historical record of all changes
- `VERSION-TRACKING.md` - This file (version overview)

### Cleanup After Successful Deployment
After deployment is verified successful:
1. Archive old deployment ZIP: `archive/v{old-version}-deployment.zip`
2. Delete old deployment documentation
3. Update `CHANGELOG.md` with deployment date
4. Update this file with new current version

---

## Next Version: v2.5.0 (Planned)

**Potential Features:**
- Additional monitoring capabilities
- Performance optimizations
- Enhanced error handling
- Dashboard improvements

---

## Quick Reference

### Current Production Version
**v2.3.0** - Deployed and running with unique filename fix

### Ready to Deploy
**v2.4.0** - Monitoring and validation features

### Resource Information
See: `AZURE_RESOURCE_REFERENCE.md`
- Resource Group: `rg-btp-uks-prod-doc-mon-01`
- Function App: `func-btp-uks-prod-doc-crawler-01`
- Storage Account: `stbtpuksprodcrawler01`
- Subscription: `96726562-1726-4984-88c6-2e4f28878873`

---

**Last Updated**: January 17, 2025  
**Maintained By**: Development Team
