# Deployment Guide

Complete guide for deploying the Azure Functions Python Web Crawler.

---

## Prerequisites

### Required Tools

- **Git** - Version control
- **Python 3.11** - Local development and testing
- **Azure Subscription** - Active subscription with contributor access
- **GitHub Account** - For CI/CD integration

### Azure Resources Required

The following Azure resources must exist before deployment:

| Resource | Name | Type | Location |
|----------|------|------|----------|
| Resource Group | `rg-btp-uks-prod-doc-mon-01` | Resource Group | UK South |
| Function App | `func-btp-uks-prod-doc-crawler-01` | Function App (Python 3.11) | UK South |
| Storage Account | `stbtpuksprodcrawler01` | Storage Account (Standard LRS) | UK South |

---

## Deployment Methods

### Method 1: GitHub Actions (Recommended)

**Automatic deployment on every push to main branch.**

#### Setup (One-Time)

1. **GitHub Secrets Configuration**

   The repository must have these secrets configured:
   ```
   AZUREAPPSERVICE_CLIENTID_xxx
   AZUREAPPSERVICE_TENANTID_xxx
   AZUREAPPSERVICE_SUBSCRIPTIONID_xxx
   ```

   These are automatically configured when you create the Function App with GitHub integration.

2. **Workflow File**

   The workflow is already configured in `.github/workflows/main_func-btp-uks-prod-doc-crawler-01.yml`

#### Deploy

```bash
# Simply push to main
git add -A
git commit -m "Your commit message"
git push origin main

# GitHub Actions will automatically:
# 1. Build the Python application
# 2. Create deployment package
# 3. Deploy to Azure with remote build
# 4. Update function app
```

#### Monitor Deployment

1. Go to https://github.com/your-repo/actions
2. Watch the "Build and deploy" workflow
3. Deployment typically takes 3-5 minutes

---

### Method 2: Azure CLI (Manual)

**For one-off deployments or troubleshooting.**

#### Prerequisites

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Set subscription
az account set --subscription 96726562-1726-4984-88c6-2e4f28878873
```

#### Deploy

```bash
# 1. Navigate to project directory
cd /path/to/functions-python-web-crawler

# 2. Create deployment package
zip -r deployment.zip . \
  -x "*.git*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*archive/*" \
  -x "*temp-compare/*" \
  -x "*.md" \
  -x "*docs/*" \
  -x ".vscode/*" \
  -x ".venv/*" \
  -x "tests/*"

# 3. Deploy to Azure
az functionapp deployment source config-zip \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --src deployment.zip \
  --build-remote true \
  --timeout 600

# 4. Verify deployment
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/health
```

---

## Post-Deployment Steps

### 1. Initialize Folder Structure

**Critical:** Run this once after deploying a new version:

```bash
curl -X POST https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/initialize_folders
```

**Expected Response:**
```json
{
  "message": "Folder initialization complete",
  "total_websites": 8,
  "success_count": 8,
  "fail_count": 0
}
```

### 2. Verify Storage Permissions

The Function App's managed identity must have the "Storage Blob Data Contributor" role:

```bash
# Get Function App principal ID
PRINCIPAL_ID=$(az functionapp identity show \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query principalId -o tsv)

# Assign role (if not already assigned)
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/96726562-1726-4984-88c6-2e4f28878873/resourceGroups/rg-btp-uks-prod-doc-mon-01/providers/Microsoft.Storage/storageAccounts/stbtpuksprodcrawler01
```

### 3. Test Crawl

Run a test crawl for one website:

```bash
curl -X POST https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"site_name": "UK Legislation (Test - Working)", "force_all": false}'
```

### 4. Verify Dashboard

Open the dashboard in your browser:
```
https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard
```

Check that:
- ✅ Storage statistics load correctly
- ✅ Documents are grouped by website name
- ✅ No "Other" category (unless legitimate)

---

## Configuration

### Environment Variables

Set in Azure Portal → Function App → Configuration → Application Settings:

| Variable | Value | Required | Description |
|----------|-------|----------|-------------|
| `WEBSITES_CONFIG_LOCATION` | `local` | No | Config source (default: local) |
| `WEBSITE_HTTPLOGGING_RETENTION_DAYS` | `7` | No | Log retention period |

### Function App Settings

**Runtime:** Python 3.11  
**Operating System:** Linux  
**Plan Type:** Consumption  
**Region:** UK South

### Application Insights

Automatically configured. View logs and telemetry:
```
Azure Portal → Function App → Application Insights
```

---

## Website Configuration

### Editing websites.json

To add or modify websites, edit `websites.json`:

```json
{
  "version": "1.0.0",
  "websites": [
    {
      "id": "unique_id",
      "name": "Display Name",
      "url": "https://example.com/page",
      "enabled": true,
      "description": "Description of website",
      "document_types": ["pdf", "doc", "docx"],
      "crawl_depth": "deep",
      "priority": "high",
      "multi_level": false,
      "max_depth": 1
    }
  ]
}
```

**After editing:**
1. Commit and push to trigger deployment
2. Run `/api/initialize_folders` to create new folder
3. Trigger crawl for new website

---

## Troubleshooting

### Functions Not Appearing in Portal

**Symptom:** Functions list is empty in Azure Portal

**Solution:**
1. Ensure deployment used `--build-remote true`
2. Check `WEBSITE_RUN_FROM_PACKAGE` is NOT set (or set to `0`)
3. Redeploy using GitHub Actions or manual method above

### Storage Permission Errors (403)

**Symptom:** Dashboard shows empty or errors loading statistics

**Solution:**
```bash
# Re-assign storage role
az role assignment create \
  --assignee $(az functionapp identity show \
    --name func-btp-uks-prod-doc-crawler-01 \
    --resource-group rg-btp-uks-prod-doc-mon-01 \
    --subscription 96726562-1726-4984-88c6-2e4f28878873 \
    --query principalId -o tsv) \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/96726562-1726-4984-88c6-2e4f28878873/resourceGroups/rg-btp-uks-prod-doc-mon-01/providers/Microsoft.Storage/storageAccounts/stbtpuksprodcrawler01
```

### Dashboard Shows "Other" for All Documents

**Symptom:** Documents not grouped by website name

**Solution:**
1. Ensure you ran `/api/initialize_folders` after deployment
2. Verify `websites.json` deployed correctly
3. Check folder names match website names (sanitized)

### Cold Start Issues

**Symptom:** First request after idle period takes >5 seconds

**Solution:** This is normal for Consumption plan. Consider:
- Azure Functions Premium plan for always-warm instances
- Health check endpoint to keep function warm

---

## Monitoring

### Application Insights Queries

View recent errors:
```kusto
exceptions
| where timestamp > ago(1h)
| project timestamp, type, outerMessage, operation_Name
| order by timestamp desc
```

View function execution times:
```kusto
requests
| where timestamp > ago(1h)
| summarize avg(duration), max(duration) by name
| order by avg_duration desc
```

### Dashboard Monitoring

Regular checks:
- ✅ Storage size growth rate
- ✅ Document count trends
- ✅ Crawl success rate
- ✅ Error frequency

---

## Rollback Procedure

### Using GitHub

```bash
# 1. Find the commit to roll back to
git log --oneline

# 2. Revert to previous version
git revert HEAD

# 3. Push (triggers automatic deployment)
git push origin main
```

### Using Azure CLI

```bash
# Deploy a previous deployment package
az functionapp deployment source config-zip \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --src archive/v2.5.0-deployment.zip \
  --build-remote true
```

---

## Scaling Considerations

### Current Limits (Consumption Plan)

- **Max instances:** 200
- **Max execution time:** 5 minutes (default), 10 minutes (max)
- **Memory:** 1.5 GB per instance

### Upgrading to Premium

If you need:
- Always-warm instances
- VNet integration
- Longer execution times
- More memory

Consider Azure Functions Premium plan.

---

## Security Checklist

- ✅ Managed Identity enabled (no connection strings)
- ✅ RBAC roles properly assigned
- ✅ Application Insights enabled for monitoring
- ✅ HTTPS enforced (automatic)
- ⚠️ Public endpoints (consider VNet integration for production)
- ⚠️ No API key requirement (consider adding for production)

---

## Backup & Recovery

### Code Backup

- ✅ Git repository (GitHub)
- ✅ Backup branch created before major changes

### Data Backup

- Storage account has LRS replication
- Consider periodic export of `document_hashes.json`
- Crawl history is stored in blob storage

### Recovery Time

- **Function App:** 10 minutes (redeploy from GitHub)
- **Data:** 2-4 hours (re-run crawls)

---

## Cost Optimization

### Current Costs

~£10-15/month for:
- Function App (Consumption)
- Storage Account (~100GB)
- Application Insights

### Optimization Tips

1. Use change detection (avoid re-uploading unchanged files)
2. Consumption plan (pay per execution)
3. Monitor and cleanup old documents
4. Consider storage lifecycle policies

---

## Support

### Documentation

- **Architecture:** See `docs/ARCHITECTURE.md`
- **API Reference:** See `docs/API.md`
- **Troubleshooting:** See `docs/TROUBLESHOOTING.md`

### Logs

- **Application Insights:** Azure Portal → Function App → Application Insights
- **Function Logs:** Azure Portal → Function App → Log stream

---

**Last Updated:** October 20, 2025  
**Version:** 2.6.0
