# Deployment Guide: v2.6.0 - Smart Storage Organization + AI-Ready Metadata

## 🎯 What This Version Delivers

**v2.6.0** is a MAJOR enhancement that transforms your storage architecture to be both organized AND AI-search ready!

### Key Improvements:
1. ✅ **Automatic Folder Creation** - Each website gets its own folder
2. ✅ **Rich Blob Metadata** - Every document tagged with website info for AI search
3. ✅ **Single Container** - AI-friendly architecture (Azure AI Search compatible)
4. ✅ **Dynamic Dashboard** - Stats load from websites.json automatically
5. ✅ **Folder Initialization** - New endpoint to create all folders at once

---

## 📋 Pre-Deployment Checklist

### 1. Verify Current State
```bash
# Check current version
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/health

# Verify storage access
az storage blob list \
  --account-name stbtpuksprodcrawler01 \
  --container-name documents \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --auth-mode login \
  --query "[0:5].[name]" -o table
```

### 2. Review Changes
- Read `CHANGELOG.md` v2.6.0 section
- Understand new folder structure
- Review metadata schema

### 3. Backup Configuration
```bash
# Backup current websites.json
cp websites.json websites.json.backup.$(date +%Y%m%d)

# Optional: Export current function app settings
az functionapp config appsettings list \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  > function-app-settings-backup.json
```

---

## 🚀 Deployment Steps

### Step 1: Create Deployment Package

```bash
# Navigate to project root
cd /workspaces/functions-python-web-crawler

# Create clean deployment package
zip -r v2.6.0-deployment.zip . \
  -x "*.git*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*archive/*" \
  -x "*temp-compare/*" \
  -x "*.md" \
  -x "*.txt" \
  -x "*.ps1" \
  -x "*.sh" \
  -x "*DEPLOY*" \
  -x "*deploy*" \
  -x "*test*" \
  -x "*Test*" \
  -x "validate_functions.py" \
  -x ".vscode/*" \
  -x ".devcontainer/*"

# Verify package contents
unzip -l v2.6.0-deployment.zip | grep -E "(function_app.py|host.json|requirements.txt|websites.json)"
```

Expected files in package:
- `function_app.py` (main application)
- `host.json` (function host config)
- `requirements.txt` (Python dependencies)
- `websites.json` (website configurations)

### Step 2: Deploy to Azure

```bash
# Deploy using Azure CLI with remote build
az functionapp deployment source config-zip \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --src v2.6.0-deployment.zip \
  --build-remote true \
  --timeout 600

# Wait for deployment to complete (usually 2-3 minutes)
echo "Waiting for deployment to stabilize..."
sleep 30
```

### Step 3: Verify Deployment

```bash
# Check function app status
az functionapp show \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "{state:state, defaultHostName:defaultHostName}" -o table

# Test health endpoint
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/health

# Test dashboard
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard
```

---

## 🏗️ Post-Deployment: Initialize Folder Structure

### Critical Step: Create Folders for All Websites

After deploying v2.6.0, you MUST call the initialization endpoint to create folder structure:

```bash
# Initialize folders for all configured websites
curl -X POST https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/initialize_folders

# Expected response:
# {
#   "status": "success",
#   "message": "Initialized 5 website folders",
#   "created": 5,
#   "failed": 0,
#   "results": [
#     {"website": "College of Policing App Portal", "folder": "college-of-policing-app-portal", "status": "created"},
#     {"website": "Crown Prosecution Service", "folder": "crown-prosecution-service", "status": "created"},
#     ...
#   ]
# }
```

### Verify Folder Creation

```bash
# List all folders in storage
az storage blob list \
  --account-name stbtpuksprodcrawler01 \
  --container-name documents \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --auth-mode login \
  --query "[?contains(name, '.folder')].[name]" -o table
```

Expected folders:
- `college-of-policing-app-portal/.folder`
- `crown-prosecution-service/.folder`
- `legislation-test-working/.folder`
- `npcc-publications-all-publications/.folder`
- `uk-legislation-test-working/.folder`

---

## 🧪 Testing & Validation

### Test 1: Verify Folder Creation

```bash
# Check one folder's metadata
az storage blob show \
  --account-name stbtpuksprodcrawler01 \
  --container-name documents \
  --name "crown-prosecution-service/.folder" \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --auth-mode login \
  --query "metadata" -o json
```

Expected metadata:
```json
{
  "websiteid": "cps_working",
  "websitename": "Crown Prosecution Service",
  "createdate": "2025-10-19T..."
}
```

### Test 2: Trigger Single-Site Crawl

```bash
# Start crawl for one website (College of Policing)
curl -X POST https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"site_name": "College of Policing App Portal", "force_all": false}'

# Expected response:
# {"status": "success", "message": "Crawl started for College of Policing App Portal"}
```

### Test 3: Verify Document Upload with Metadata

After crawl completes (wait ~5 minutes), check uploaded documents:

```bash
# List documents in College of Policing folder
az storage blob list \
  --account-name stbtpuksprodcrawler01 \
  --container-name documents \
  --prefix "college-of-policing-app-portal/" \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --auth-mode login \
  --query "[0:3].[name]" -o table

# Check metadata on one document
az storage blob show \
  --account-name stbtpuksprodcrawler01 \
  --container-name documents \
  --name "college-of-policing-app-portal/abc123_document.pdf" \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --auth-mode login \
  --query "metadata" -o json
```

Expected metadata on document:
```json
{
  "websiteid": "college_of_policing",
  "websitename": "College of Policing App Portal",
  "crawldate": "2025-10-19T14:30:00",
  "documenttype": "application/pdf",
  "originalfilename": "document.pdf",
  "status": "new",
  "documenturl": "https://..."
}
```

### Test 4: Verify Dashboard Statistics

```bash
# Get storage statistics
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/stats | jq '.storage'
```

Expected output - documents grouped by website:
```json
{
  "total_documents": 150,
  "total_size_gb": 2.5,
  "by_site": [
    {
      "site": "Crown Prosecution Service",
      "folder": "crown-prosecution-service",
      "count": 45,
      "size_gb": 0.8
    },
    {
      "site": "College of Policing App Portal",
      "folder": "college-of-policing-app-portal",
      "count": 30,
      "size_gb": 0.5
    },
    ...
  ]
}
```

---

## 🎨 New Storage Architecture

### Before v2.6.0:
```
documents/
├── abc123_document.pdf (no metadata, no folder)
├── def456_guidance.pdf
└── ghi789_report.pdf
```

### After v2.6.0:
```
documents/
├── college-of-policing-app-portal/
│   ├── .folder (metadata: websiteid, websitename, createdate)
│   └── abc123_document.pdf (metadata: all fields)
├── crown-prosecution-service/
│   ├── .folder
│   └── def456_guidance.pdf (metadata: all fields)
└── npcc-publications-all-publications/
    ├── .folder
    └── ghi789_report.pdf (metadata: all fields)
```

---

## 🤖 AI Search Integration (Future)

### Why This Architecture is Perfect for AI:

1. **Single Container** - Azure AI Search works best with one datasource
2. **Rich Metadata** - Filter queries by website, date, type
3. **Organized Folders** - Visual structure in Azure Portal
4. **No Migration Needed** - Existing documents remain accessible

### Example AI Search Queries (Future):

```python
# Query documents from Crown Prosecution Service only
search_results = search_client.search(
    search_text="criminal law",
    filter="metadata_websiteid eq 'cps_working'"
)

# Query documents uploaded this month
search_results = search_client.search(
    search_text="guidance",
    filter="metadata_crawldate ge '2025-10-01'"
)

# Query by document type
search_results = search_client.search(
    search_text="policy",
    filter="metadata_documenttype eq 'application/pdf'"
)
```

---

## 📊 Monitoring & Verification

### Check Logs in Azure Portal

1. Navigate to Function App in Azure Portal
2. Go to **Monitoring** → **Logs**
3. Run query:
```kusto
traces
| where timestamp > ago(1h)
| where message contains "ensure_website_folder_exists" or message contains "upload_to_blob_storage_real"
| project timestamp, message, severityLevel
| order by timestamp desc
```

### Monitor Crawl Progress

```bash
# Check crawl status
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl_status

# Check recent crawl history
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl_history?limit=5
```

---

## 🛡️ Rollback Plan (If Needed)

If issues occur, rollback to v2.5.2:

```bash
# Deploy previous version
az functionapp deployment source config-zip \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --src archive/v2.5.2-deployment.zip \
  --build-remote true \
  --timeout 600

# Verify rollback
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/health
```

**Note:** Rollback is safe - no data loss. New folder structure and metadata won't break old code.

---

## 🧹 Post-Deployment Cleanup

After successful deployment and verification:

```bash
# Move old deployment package to archive
mkdir -p archive
mv v2.5.2-deployment.zip archive/ 2>/dev/null || true

# Delete old deployment documentation
rm -f DEPLOYMENT-v2.4.0.md DEPLOYMENT-v2.5.1.md HOTFIX-*.md

# Update CHANGELOG with deployment date
# (Manual step - add deployment timestamp to v2.6.0 entry)

# Commit version update
git add -A
git commit -m "v2.6.0: Deployed successfully to production"
git push origin main
```

---

## ✅ Success Criteria

Deployment is successful when:

1. ✅ Health endpoint returns v2.6.0
2. ✅ `/api/initialize_folders` creates all website folders
3. ✅ Folder `.folder` files exist in storage with metadata
4. ✅ Dashboard shows website-grouped statistics
5. ✅ Test crawl creates documents in correct folder with metadata
6. ✅ No errors in Application Insights logs

---

## 🆘 Troubleshooting

### Issue: Initialize Folders Returns Error

**Symptoms:** `/api/initialize_folders` returns 500 error

**Solution:**
```bash
# Check function app logs
az functionapp log tail \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873

# Verify storage permissions
az role assignment list \
  --assignee $(az functionapp identity show \
    --name func-btp-uks-prod-doc-crawler-01 \
    --resource-group rg-btp-uks-prod-doc-mon-01 \
    --subscription 96726562-1726-4984-88c6-2e4f28878873 \
    --query principalId -o tsv) \
  --scope /subscriptions/96726562-1726-4984-88c6-2e4f28878873/resourceGroups/rg-btp-uks-prod-doc-mon-01/providers/Microsoft.Storage/storageAccounts/stbtpuksprodcrawler01
```

### Issue: Dashboard Shows "Other" Instead of Website Names

**Symptoms:** Stats show all documents as "Other"

**Possible Causes:**
1. `websites.json` not deployed
2. Folder names don't match website names

**Solution:**
```bash
# Verify websites.json deployed
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/manage_websites

# Check folder names in storage
az storage blob list \
  --account-name stbtpuksprodcrawler01 \
  --container-name documents \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --auth-mode login \
  --query "[?contains(name, '.folder')].[name]" -o table
```

### Issue: Documents Not Getting Metadata

**Symptoms:** Blob metadata is empty or missing fields

**Solution:**
1. Check function logs for upload errors
2. Verify managed identity has "Storage Blob Data Contributor" role
3. Test with single document crawl
4. Check Application Insights for metadata attachment errors

---

## 📞 Support

- **Documentation:** See `README.md`, `CHANGELOG.md`, `VERSION-TRACKING.md`
- **Architecture:** See `AZURE_RESOURCE_REFERENCE.md`
- **Troubleshooting:** Check Application Insights in Azure Portal
- **Rollback:** See "Rollback Plan" section above

---

## 🎉 Next Steps After Deployment

1. ✅ Call `/api/initialize_folders` to create all folders
2. ✅ Verify folder creation in Azure Storage Explorer
3. ✅ Run test crawl on one website
4. ✅ Check document metadata
5. ✅ Verify dashboard categorization
6. ✅ Schedule full crawl for all websites
7. 🔮 Plan Azure AI Search integration (future enhancement)

---

**Deployment Date:** ________________  
**Deployed By:** ________________  
**Version:** v2.6.0  
**Rollback Package:** archive/v2.5.2-deployment.zip
