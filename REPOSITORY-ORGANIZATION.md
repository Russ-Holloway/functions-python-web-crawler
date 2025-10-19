# Repository Organization & Versioning System

## Overview

This document explains the new incremental versioning and cleanup system implemented for this project.

---

## Version Numbering System

### Format: `v{major}.{minor}.{patch}`

**Example Versions:**
- `v2.2.0` - Original system (had storage issue)
- `v2.3.0` - Phase 1 fix (unique filenames)
- `v2.4.0` - Phase 2 monitoring (current)
- `v2.5.0` - Future version

### When to Increment:

- **Major** (v3.0.0): Breaking changes, major architecture updates
- **Minor** (v2.5.0): New features, enhancements
- **Patch** (v2.4.1): Bug fixes, small updates

---

## File Naming Standards

### Deployment Packages
**Format**: `v{version}-deployment.zip`  
**Location**: Root directory (until deployed)  
**After Deployment**: Move to `archive/` folder

**Examples:**
```
✅ v2.4.0-deployment.zip     (Current - in root)
✅ archive/v2.3.0-deployment.zip  (Deployed - archived)
✅ archive/v2.2.0-deployment.zip  (Deployed - archived)
```

### Documentation Files
**Format**: `DEPLOYMENT-v{version}.md`  
**Location**: Root directory (current version only)  
**After New Deployment**: Delete old version

**Examples:**
```
✅ DEPLOYMENT-v2.4.0.md      (Current version only)
❌ DEPLOYMENT-v2.3.0.md      (Delete after v2.4.0 deploys)
❌ PHASE-1-*.md              (Delete - old naming system)
```

---

## Repository Structure

### Root Directory (Clean & Current Only)

```
project-root/
├── function_app.py              # Application code
├── requirements.txt             # Dependencies
├── host.json                    # Function app config
├── local.settings.json          # Local dev settings
├── websites.json                # Website configurations
│
├── v2.4.0-deployment.zip        # CURRENT deployment package
│
├── VERSION-TRACKING.md          # Version overview (THIS IS THE SOURCE OF TRUTH)
├── DEPLOYMENT-v2.4.0.md         # Current deployment guide only
├── CLEANUP-CHECKLIST-v2.4.0.md  # Post-deployment cleanup steps
├── CHANGELOG.md                 # Historical changes log
├── AZURE_RESOURCE_REFERENCE.md  # Azure resource names
├── README.md                    # Project overview
│
├── .github/
│   └── copilot-instructions.md  # AI assistant guidelines
│
├── archive/                     # Old deployment packages
│   ├── v2.2.0-deployment.zip
│   └── v2.3.0-deployment.zip
│
└── tests/                       # Test files
    └── ...
```

### What Should NOT Be in Root

❌ Old `PHASE-*` files (confusing, unclear versioning)  
❌ Multiple deployment guides for different versions  
❌ Redundant documentation files  
❌ Old deployment ZIP files after successful deployment  

---

## Deployment Workflow

### 1. Development Phase

```bash
# Work on new features in function_app.py
# Update VERSION-TRACKING.md with planned version
# Create DEPLOYMENT-v{new-version}.md guide
```

### 2. Create Deployment Package

```bash
# Version: v2.4.0 (example)
cd project-root/

Compress-Archive -Path function_app.py,requirements.txt,host.json,local.settings.json,websites.json \
  -DestinationPath v2.4.0-deployment.zip -Force
```

### 3. Deploy to Azure

```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v2.4.0-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

### 4. Verify Deployment

```bash
# Check function app is running
az functionapp show \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --query "{name:name, state:state}"

# Check dashboard
# Visit: https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard

# Wait for scheduled crawl (every 4 hours)
# Verify new features work correctly
```

### 5. Post-Deployment Cleanup

**After verification (24-48 hours):**

```bash
# 1. Archive deployment package
mkdir archive -ErrorAction SilentlyContinue
Move-Item v2.4.0-deployment.zip archive/

# 2. Delete old deployment documentation
rm DEPLOYMENT-v2.3.0.md

# 3. Delete obsolete files
rm PHASE-1-*.md
rm PHASE-2-*.md
# (etc.)

# 4. Update CHANGELOG.md with deployment date
# 5. Update VERSION-TRACKING.md status
```

---

## Key Reference Files

### VERSION-TRACKING.md (SOURCE OF TRUTH)

**Purpose**: Single source of truth for version history  
**Location**: Root directory (always)  
**Updates**: After each deployment

**Contains:**
- Current production version
- Version ready for deployment
- Version history with status
- Deployment commands
- File cleanup instructions

### DEPLOYMENT-v{version}.md (CURRENT VERSION ONLY)

**Purpose**: Step-by-step deployment guide for current version  
**Location**: Root directory (current version only)  
**Lifecycle**: Created with version, deleted when superseded

**Contains:**
- What's new in this version
- Prerequisites
- Deployment steps
- Verification steps
- Troubleshooting
- Rollback procedure

### CHANGELOG.md (PERMANENT HISTORY)

**Purpose**: Historical record of all changes  
**Location**: Root directory (always)  
**Updates**: After each deployment verified

**Format:**
```markdown
## [v2.4.0] - 2025-01-17
### Added
- Feature descriptions
### Changed
- Modification descriptions
### Deployed
- Deployment date and status
```

---

## Benefits of This System

### ✅ Clear Version Tracking
- Incremental version numbers (v2.3.0, v2.4.0, v2.5.0)
- Easy to see what version is current
- Easy to compare versions

### ✅ Clean Repository
- Only current version docs in root
- Old deployments archived
- No confusion from multiple "Phase" files

### ✅ Easy Rollback
- All old deployment packages in `archive/`
- Can redeploy previous version if needed
- Clear history of what changed

### ✅ Maintainable
- VERSION-TRACKING.md = single source of truth
- Clear naming conventions
- Documented cleanup process

### ✅ Professional
- Standard semantic versioning
- Clean file structure
- Easy for new developers to understand

---

## Migration from Old System

### Old System (Confusing)
```
PHASE-1-COMPLETION.md
PHASE-1-SUMMARY.md
PHASE-1-DEPLOYMENT-BASH.md
PHASE-1-VERIFICATION-REPORT.md
PHASE-2-PLAN.md
PHASE-2-DEPLOYMENT-BASH.md
PHASE-2-COMPLETION.md
phase1-deployment.zip
deploy.zip
```

### New System (Clear)
```
VERSION-TRACKING.md           # Source of truth
DEPLOYMENT-v2.4.0.md          # Current version only
v2.4.0-deployment.zip         # Current package
CHANGELOG.md                  # Historical record
archive/v2.2.0-deployment.zip # Old versions
archive/v2.3.0-deployment.zip
```

---

## Quick Reference Commands

### Check Current Version
```bash
cat VERSION-TRACKING.md | grep "Current Version"
```

### List Archived Deployments
```bash
ls archive/
```

### Create New Deployment
```bash
Compress-Archive -Path function_app.py,requirements.txt,host.json,local.settings.json,websites.json \
  -DestinationPath v{NEW_VERSION}-deployment.zip -Force
```

### Deploy to Azure
```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v{VERSION}-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

## Questions?

**Q: What version are we on?**  
A: Check `VERSION-TRACKING.md` - "Current Production Version" section

**Q: What's ready to deploy?**  
A: Check `VERSION-TRACKING.md` - Look for "Ready for Deployment" status

**Q: Where are old deployments?**  
A: In `archive/` folder - all previous deployment ZIPs

**Q: How do I know what changed?**  
A: Check `CHANGELOG.md` for complete history of all changes

**Q: What files should be in root?**  
A: Only current version docs + permanent files (README, CHANGELOG, VERSION-TRACKING)

---

**Last Updated**: January 17, 2025  
**System Version**: v1.0 (Documentation System)
