# Production Repository Cleanup Plan - v2.6.0

## 🎯 Goal
Transform repository into production-ready, shareable state with only essential files.

---

## 📋 Files to KEEP (Production Essentials)

### Core Application Files
- ✅ `function_app.py` - Main application
- ✅ `host.json` - Azure Functions host configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `websites.json` - Website configurations
- ✅ `local.settings.json` - Local development settings (with .gitignore)

### GitHub & CI/CD
- ✅ `.github/workflows/` - GitHub Actions deployment
- ✅ `.gitignore` - Git ignore rules
- ✅ `.funcignore` - Function app ignore rules

### Documentation (Essential)
- ✅ `README.md` - Project overview and setup guide
- ✅ `CHANGELOG.md` - Version history
- ✅ `LICENSE.md` - License information
- ✅ `CONTRIBUTING.md` - Contribution guidelines
- ✅ `DEPLOYMENT-v2.6.0.md` - Current deployment guide

### Configuration
- ✅ `.vscode/` - VS Code settings (tasks, launch configs)

---

## 🗑️ Files to DELETE (Obsolete/Development Files)

### Old Deployment Documentation (50+ files)
- ❌ `AZURE_RESOURCE_REFERENCE.md` → Move to README
- ❌ `CHECK-DEPLOYED-FUNCTIONS.md`
- ❌ `CLEANUP-CHECKLIST-v2.4.0.md`
- ❌ `CLEANUP-SUMMARY.md`
- ❌ `COMPLETE-FIX-FUNCTIONS-NOT-APPEARING.md`
- ❌ `COMPLETE-FIX-GUIDE.md`
- ❌ `CONTAINER-PER-WEBSITE-PLAN.md`
- ❌ `COPILOT_INSTRUCTIONS.md` → Move to `.github/`
- ❌ `CORRECTED-DEPLOYMENT-COMMANDS.txt`
- ❌ `DEPLOY-GUIDE-v2.4.2.ps1`
- ❌ `DEPLOY-QUICK-START.txt`
- ❌ `DEPLOY-v2.4.0-NOW.md`
- ❌ `DEPLOY-v2.4.2-QUICK.md`
- ❌ `DEPLOY-v2.5.0-NOW.md`
- ❌ `DEPLOY-v2.6.0-QUICK.md`
- ❌ `DEPLOYMENT-CHECKLIST.md`
- ❌ `DEPLOYMENT-GUIDE.md`
- ❌ `DEPLOYMENT-v2.4.0.md`
- ❌ `DEPLOYMENT-v2.5.0.md`
- ❌ `DEPLOYMENT-v2.5.2.md`
- ❌ `DISABLE-AUTH-IN-PORTAL.md`
- ❌ `DURABLE-FUNCTIONS-IMPLEMENTATION-PLAN.md`
- ❌ `ENHANCEMENT-SUMMARY.md`
- ❌ `FINAL-DIAGNOSIS.md`
- ❌ `FIX-AUTHENTICATION-ISSUE.md`
- ❌ `FIX-COMMANDS.txt`
- ❌ `FIX-SUMMARY-v2.5.0.md`
- ❌ `FUNCTION-APP-AUDIT.md`
- ❌ `GITHUB-ACTIONS-DEPLOYMENT.md`
- ❌ `GITHUB-ACTIONS-READY.md`
- ❌ `HOTFIX-DEPLOYMENT-v2.4.1.md`
- ❌ `HOTFIX-v2.4.2-FUNCTION-REGISTRATION.md`
- ❌ `HOTFIX-v2.4.2-ROUTE-FIX.md`
- ❌ `PHASE-*.md` (8 files)
- ❌ `POST-DEPLOYMENT-VERIFICATION.md`
- ❌ `PRODUCTION-DEPLOYMENT-GUIDE.md`
- ❌ `QUICK-DEPLOY-GITHUB-ACTIONS.md`
- ❌ `QUICK-DEPLOY-GUIDE.md`
- ❌ `QUICK-FIX-SUMMARY.md`
- ❌ `README-v2.4.0-DEPLOYMENT.md`
- ❌ `RELEASE-v2.2.0-OFFICIAL.md`
- ❌ `REPOSITORY-ORGANIZATION.md`
- ❌ `SAFEGUARDS.md`
- ❌ `STATUS-REPORT-v2.5.1.md`
- ❌ `STORAGE-PERMISSIONS-FIX.md`
- ❌ `VERSION_SUMMARY.md`
- ❌ `VERSIONING.md`
- ❌ `WHY-NOT-WORKING.md`

### Old Scripts (PowerShell/Bash)
- ❌ `deploy-complete.ps1`
- ❌ `deploy-fix.sh`
- ❌ `deploy-v2.4.2.sh`
- ❌ `deploy.ps1`
- ❌ `diagnose-azure.sh`
- ❌ `diagnose-deployment.sh`
- ❌ `fix-auth-now.sh`
- ❌ `fix-azure.sh`
- ❌ `fix-storage-permissions.sh`
- ❌ `Fix-AzureFunctions.ps1`
- ❌ `test-deployment.ps1`

### Test/Development Files
- ❌ `test_categorization.py`
- ❌ `test_function.py`
- ❌ `validate_functions.py`
- ❌ `tests/` directory (or keep with proper test structure)

### Old Deployment Packages
- ❌ `v2.4.0-deployment.zip`
- ❌ `v2.4.1-deployment.zip`
- ❌ `v2.4.2-deployment.zip`
- ❌ `v2.5.0-deployment.zip`

### Temporary/Archive Folders
- ❌ `archive/` - Keep in git history, remove from working tree
- ❌ `temp-compare/` - Temporary comparison files
- ❌ `__pycache__/` - Python cache (should be in .gitignore)

### Old Requirements
- ❌ `requirements.txt.v230`

### Misc
- ❌ `.deployment-trigger`

---

## 📝 Files to UPDATE

### 1. README.md
- Add clear project description
- Add prerequisites
- Add setup instructions
- Add deployment instructions (reference DEPLOYMENT-v2.6.0.md)
- Add Azure resource names
- Add architecture diagram reference
- Add API documentation

### 2. CHANGELOG.md
- Ensure v2.6.0 is properly documented
- Archive old detailed changelogs

### 3. .gitignore
- Add `.venv/`
- Add `__pycache__/`
- Add `*.pyc`
- Add `local.settings.json`
- Add deployment ZIPs
- Add `.DS_Store`
- Add `*.log`

### 4. Create New Files

#### docs/ARCHITECTURE.md
- System architecture
- Storage structure
- Metadata schema
- AI search integration guide

#### docs/API.md
- Complete API documentation
- Endpoint descriptions
- Request/response examples

#### docs/DEPLOYMENT.md
- Simplified deployment guide
- GitHub Actions workflow
- Environment variables
- Azure resource setup

#### VERSION (new file)
```
2.6.0
```

---

## 🔄 Reorganization Structure

```
/
├── .github/
│   ├── workflows/
│   │   └── main_func-btp-uks-prod-doc-crawler-01.yml
│   └── copilot-instructions.md
├── .vscode/
│   └── (VS Code settings)
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── TROUBLESHOOTING.md
├── function_app.py
├── host.json
├── requirements.txt
├── websites.json
├── local.settings.json (gitignored)
├── .gitignore
├── .funcignore
├── README.md
├── CHANGELOG.md
├── LICENSE.md
├── CONTRIBUTING.md
└── VERSION
```

---

## ✅ Cleanup Execution Steps

1. Create backup branch
2. Create new documentation structure
3. Update README.md
4. Update .gitignore
5. Delete obsolete files
6. Reorganize remaining files
7. Update VERSION to 2.6.0
8. Commit as "v2.6.0: Production repository cleanup"
9. Tag release as v2.6.0
10. Push to GitHub

---

## 🏷️ Version Tagging

After cleanup, create proper Git tag:
```bash
git tag -a v2.6.0 -m "v2.6.0: Smart storage organization + AI-ready metadata"
git push origin v2.6.0
```

---

## 📊 Before/After

**Before:** 100+ files, 50+ documentation files, multiple deployment packages
**After:** ~20 essential files, organized docs/, clean structure, production-ready

---

**Ready to Execute?** This will make the repository professional, shareable, and maintainable.
