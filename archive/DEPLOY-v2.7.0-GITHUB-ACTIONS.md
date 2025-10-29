# Quick Deployment Guide - v2.7.0 (GitHub Actions)

## Overview
This project uses **GitHub Actions** for automated deployment. When you commit to the `main` branch, the code automatically deploys to Azure.

**Your Azure Resources:**
- **Function App**: `func-btp-uks-prod-doc-crawler-01`
- **Resource Group**: `rg-btp-uks-prod-doc-mon-01`
- **Subscription ID**: `96726562-1726-4984-88c6-2e4f28878873`
- **Region**: UK South (uks)

---

## Simple Deployment Process

### Step 1: Commit Your Changes

```bash
# Stage all changes
git add .

# Commit with descriptive message
git commit -m "v2.7.0: Fixed 'Other' category issue and added cleanup utility"

# Push to main branch (triggers automatic deployment)
git push origin main
```

### Step 2: Monitor Deployment

Watch the GitHub Actions workflow:

```bash
# Open in browser
gh workflow view

# Or monitor from CLI
gh run watch
```

**Or visit GitHub:**
`https://github.com/Russ-Holloway/functions-python-web-crawler/actions`

---

## What Happens Automatically

1. ✅ **Build Stage**
   - Checks out code
   - Sets up Python 3.11
   - Creates virtual environment
   - Installs dependencies
   - Creates artifact

2. ✅ **Deploy Stage**
   - Logs into Azure (using federated credentials)
   - Creates deployment ZIP
   - Deploys to `func-btp-uks-prod-doc-crawler-01`
   - Builds remotely on Azure

**Total Time:** ~3-5 minutes

---

## Verify Deployment

### Check Function Status

```bash
# Get function URL
FUNCTION_URL="func-btp-uks-prod-doc-crawler-01.azurewebsites.net"

# Test dashboard
curl "https://${FUNCTION_URL}/api/dashboard"

# Test storage stats
curl "https://${FUNCTION_URL}/api/storage_stats" | jq .

# Test new cleanup endpoint
curl "https://${FUNCTION_URL}/api/cleanup_uncategorized" | jq .
```

### Monitor Logs

```bash
# Stream function logs
az webapp log tail \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

## Clean Up Uncategorized Documents

After deployment completes:

```bash
# Set function URL
FUNCTION_URL="func-btp-uks-prod-doc-crawler-01.azurewebsites.net"

# Step 1: Check what will be deleted (dry run - safe)
curl "https://${FUNCTION_URL}/api/cleanup_uncategorized" | jq .

# Step 2: Review output, then delete if confirmed
curl -X POST "https://${FUNCTION_URL}/api/cleanup_uncategorized" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}' | jq .

# Step 3: Trigger manual crawl to re-download with proper structure
curl -X POST "https://${FUNCTION_URL}/api/manual_crawl" \
  -H "Content-Type: application/json" \
  -d '{"websites": ["all"]}' | jq .
```

---

## Complete Workflow

```bash
# =======================
# DEPLOY v2.7.0
# =======================

# 1. Commit and push changes
git add .
git commit -m "v2.7.0: Fixed 'Other' category issue and added cleanup utility"
git push origin main

# 2. Monitor deployment (open in browser or use gh CLI)
echo "Monitor deployment at: https://github.com/Russ-Holloway/functions-python-web-crawler/actions"

# Wait for deployment to complete (~3-5 minutes)

# =======================
# VERIFY DEPLOYMENT
# =======================

FUNCTION_URL="func-btp-uks-prod-doc-crawler-01.azurewebsites.net"

# 3. Test dashboard
curl "https://${FUNCTION_URL}/api/dashboard"

# =======================
# CLEANUP UNCATEGORIZED
# =======================

# 4. Check for uncategorized documents
curl "https://${FUNCTION_URL}/api/cleanup_uncategorized" | jq .

# 5. Delete uncategorized documents (if any found)
curl -X POST "https://${FUNCTION_URL}/api/cleanup_uncategorized" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}' | jq .

# 6. Trigger manual crawl
curl -X POST "https://${FUNCTION_URL}/api/manual_crawl" \
  -H "Content-Type: application/json" \
  -d '{"websites": ["all"]}' | jq .

# =======================
# MONITOR RESULTS
# =======================

# 7. Check dashboard again
curl "https://${FUNCTION_URL}/api/dashboard"

echo "✅ Deployment and cleanup complete!"
```

---

## Troubleshooting

### Deployment Failed

1. Check GitHub Actions logs:
   ```bash
   gh run list
   gh run view <run-id>
   ```

2. Common issues:
   - Python syntax errors → Check local tests first
   - Missing dependencies → Verify `requirements.txt`
   - Azure credentials → Check GitHub Secrets are configured

### Function Not Responding

```bash
# Restart function app
az functionapp restart \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873

# Wait 30 seconds
sleep 30

# Test again
curl "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard"
```

---

## Rollback

If you need to rollback to a previous version:

```bash
# 1. Find the commit hash of the working version
git log --oneline

# 2. Revert to that commit
git revert <commit-hash>

# 3. Push to trigger redeployment
git push origin main
```

---

## Manual Deployment (Emergency Only)

If GitHub Actions is down, you can deploy manually:

```bash
# Create deployment package
zip -r v2.7.0-deployment.zip . \
  -x ".git/*" ".vscode/*" "local.settings.json" \
  -x "test/*" ".venv/*" "venv/*" "__pycache__/*" "*.pyc"

# Deploy via Azure CLI
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v2.7.0-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --build-remote true
```

---

## Key Points

- ✅ **Automated**: Push to main = automatic deployment
- ✅ **No Manual ZIP**: GitHub Actions handles packaging
- ✅ **Federated Auth**: No passwords needed
- ✅ **Remote Build**: Azure builds on deployment
- ✅ **Fast**: 3-5 minutes start to finish

---

**Function App**: func-btp-uks-prod-doc-crawler-01  
**Version**: v2.7.0  
**Date**: October 21, 2025  
**Deployment Method**: GitHub Actions (Automated)
