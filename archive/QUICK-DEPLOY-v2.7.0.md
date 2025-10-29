# Quick Deployment Commands - v2.7.0

## ⚡ Copy-Paste Commands for Bash

### Step 1: Create Deployment Package
```bash
cd /workspaces/functions-python-web-crawler
zip -r v2.7.0-deployment.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc" -x "*tests/*" -x "*.md" -x "archive/*" -x "docs/*" -x ".vscode/*" -x ".devcontainer/*" -x "*.zip"
ls -lh v2.7.0-deployment.zip
```

### Step 2: Set Your Azure Variables
**⚠️ IMPORTANT: Replace with your actual resource names!**

```bash
# CUSTOMIZE THESE VALUES
RESOURCE_GROUP="your-resource-group-name"
FUNCTION_APP="your-function-app-name"
SUBSCRIPTION_ID="your-subscription-id"
```

### Step 3: Deploy to Azure
```bash
az functionapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --src v2.7.0-deployment.zip \
  --subscription $SUBSCRIPTION_ID \
  --timeout 300
```

### Step 4: Verify Deployment
```bash
# Check function app status
az functionapp show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --subscription $SUBSCRIPTION_ID \
  --query "state" \
  --output tsv

# Get function URL
FUNCTION_URL=$(az functionapp show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --subscription $SUBSCRIPTION_ID \
  --query "defaultHostName" \
  --output tsv)

echo "Function URL: https://${FUNCTION_URL}"

# Test dashboard
curl "https://${FUNCTION_URL}/api/dashboard"

# Test storage stats
curl "https://${FUNCTION_URL}/api/storage_stats" | jq .
```

### Step 5: Monitor Logs
```bash
# Stream logs (Ctrl+C to exit)
az webapp log tail \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --subscription $SUBSCRIPTION_ID
```

### Optional: Cleanup Uncategorized Documents
```bash
# Check for uncategorized documents (safe dry run)
curl "https://${FUNCTION_URL}/api/cleanup_uncategorized" | jq .

# Delete uncategorized documents if found (they'll be re-downloaded on next crawl)
curl -X POST "https://${FUNCTION_URL}/api/cleanup_uncategorized" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}' | jq .

# Trigger manual crawl to re-download with proper structure (optional)
curl -X POST "https://${FUNCTION_URL}/api/manual_crawl" \
  -H "Content-Type: application/json" \
  -d '{"websites": ["all"]}' | jq .
```

### Optional: Cleanup After Success
```bash
# Move old deployments to archive
mv v2.6.0-deployment.zip archive/ 2>/dev/null || true

# Verify current deployment
ls -lh v2.7.0-deployment.zip
```

### Rollback to v2.6.0 (if needed)
```bash
# Extract from archive
cp archive/v2.6.0-deployment.zip .

# Deploy v2.6.0
az functionapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --src v2.6.0-deployment.zip \
  --subscription $SUBSCRIPTION_ID \
  --timeout 300
```

---

## 🎯 What This Fix Does

- ✅ Removes "Other" category from dashboard
- ✅ Filters out `.folder` placeholder files
- ✅ Logs any uncategorized documents
- ✅ Improves dashboard accuracy

## 📋 Expected Result

After deployment, your dashboard should show:
- Crown Prosecution Service: X documents
- College of Policing - App Portal: X documents  
- NPCC Publications - All Publications: X documents
- UK Legislation (Test - Working): X documents
- **NO "Other" category** (unless you have legacy files)

## 🔍 Troubleshooting

If "Uncategorized (Legacy)" appears, check logs:
```bash
az webapp log tail --name $FUNCTION_APP --resource-group $RESOURCE_GROUP | grep "without folder prefix"
```

---

**Version:** v2.7.0  
**Date:** October 21, 2025  
**Risk:** Low - Bug fix only, no breaking changes
