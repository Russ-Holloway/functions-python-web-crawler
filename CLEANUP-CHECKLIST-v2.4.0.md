# Post-Deployment Cleanup Checklist - v2.4.0

## Execute After v2.4.0 Deployment is Verified Successful

---

## Verification Requirements (Complete First)

Before running cleanup, verify:

- ✅ v2.4.0 deployed successfully to Azure
- ✅ Function app is running
- ✅ Dashboard displays validation card
- ✅ At least one scheduled crawl completed
- ✅ Validation status shows MATCH
- ✅ Collision count is 0
- ✅ No errors in Application Insights logs

**Only proceed with cleanup after all above items are verified!**

---

## Cleanup Commands

### Step 1: Remove Obsolete Documentation Files

```bash
cd "c:\Users\4530Holl\OneDrive - British Transport Police\_Open-Ai\Web-Crawler-Repo\functions-python-web-crawler\functions-python-web-crawler"

# Delete old Phase documentation
rm PHASE-1-DEPLOYMENT-BASH.md
rm PHASE-1-SUMMARY.md
rm PHASE-1-COMPLETION.md
rm PHASE-1-VERIFICATION-REPORT.md
rm PHASE-2-PLAN.md
rm PHASE-2-DEPLOYMENT-BASH.md
rm PHASE-2-COMPLETION.md
rm CORRECTED-DEPLOYMENT-COMMANDS.txt
```

### Step 2: Verify Current Files

```bash
# List remaining deployment docs (should only show current version)
Get-ChildItem -Filter "DEPLOYMENT-*.md"

# Should show: DEPLOYMENT-v2.4.0.md only
```

### Step 3: Update CHANGELOG.md

Add deployment entry:

```markdown
## [v2.4.0] - 2025-01-17

### Added
- Storage validation after each crawl
- Collision detection tracking
- Enhanced dashboard with Phase 2 metrics
- Automatic accuracy percentage calculation
- New `validate_storage_activity` function

### Changed
- Updated orchestrator to track collisions
- Enhanced API stats endpoint with validation data
- Improved dashboard with validation status card

### Deployed
- Date: January 17, 2025
- Status: ✅ Successful
- Verified: ✅ All validation metrics working correctly
```

### Step 4: Update VERSION-TRACKING.md

Update status section:

```markdown
### v2.4.0 - Storage Validation & Monitoring
**Status**: ✅ Deployed & Running  
**Date**: January 17, 2025  
**Deployment Package**: `archive/v2.4.0-deployment.zip` (archived after deployment)
```

Update current version:

```markdown
### Current Production Version
**v2.4.0** - Deployed with monitoring and validation features
```

---

## Files After Cleanup

### Root Directory Should Contain:

**Documentation (Current Only):**
- ✅ `VERSION-TRACKING.md` - Version overview
- ✅ `DEPLOYMENT-v2.4.0.md` - Current deployment guide
- ✅ `CHANGELOG.md` - Historical changes
- ✅ `AZURE_RESOURCE_REFERENCE.md` - Resource names
- ✅ `README.md` - Project overview
- ❌ ~~No old PHASE-* files~~
- ❌ ~~No old deployment guides~~

**Application Files:**
- ✅ `function_app.py` - Main application
- ✅ `requirements.txt` - Dependencies
- ✅ `host.json` - Function app config
- ✅ `local.settings.json` - Local dev settings
- ✅ `websites.json` - Website configurations

**Archive Folder:**
- ✅ `archive/v2.2.0-deployment.zip` - Original deployment
- ✅ `archive/v2.3.0-deployment.zip` - Phase 1 fix
- ✅ `archive/v2.4.0-deployment.zip` - **Move here after deployment**

---

## Optional: Archive Current Deployment Package

After v2.4.0 is stable for 24-48 hours:

```bash
# Move current deployment to archive
Move-Item -Path "v2.4.0-deployment.zip" -Destination "archive\v2.4.0-deployment.zip"
```

This keeps the root directory clean while preserving all deployment packages in archive.

---

## Verification After Cleanup

```bash
# Check root directory is clean
Get-ChildItem -Filter "PHASE-*.md"
# Should return: No items found

Get-ChildItem -Filter "DEPLOYMENT-*.md"
# Should return: Only DEPLOYMENT-v2.4.0.md

Get-ChildItem archive\
# Should show: v2.2.0, v2.3.0, v2.4.0 deployment ZIPs
```

---

## Next Deployment (v2.5.0)

When preparing next version:

1. Create new `DEPLOYMENT-v2.5.0.md`
2. Create `v2.5.0-deployment.zip`
3. Deploy to Azure
4. After verification:
   - Delete `DEPLOYMENT-v2.4.0.md`
   - Move `v2.4.0-deployment.zip` to archive (if not already there)
   - Update `VERSION-TRACKING.md`
   - Update `CHANGELOG.md`

**Keep repository clean - only current version documentation in root!**

---

## Summary

**Before Cleanup:**
- 7+ old PHASE-* documentation files
- 2 old deployment ZIPs in root
- Confusing file structure

**After Cleanup:**
- Only current version docs in root
- All old deployments archived
- Clear version tracking
- Clean, maintainable repository

---

**Cleanup Status**: ⏳ Pending v2.4.0 Verification  
**Execute After**: Successful deployment + validation metrics confirmed
