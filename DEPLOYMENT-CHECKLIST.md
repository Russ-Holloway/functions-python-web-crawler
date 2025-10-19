# ✅ DEPLOYMENT CHECKLIST - Functions Not Appearing Fix

## Before You Start
- [ ] Open **Azure CLI in Bash mode** (not PowerShell)
- [ ] Have subscription ID ready: `96726562-1726-4984-88c6-2e4f28878873`
- [ ] Package created: `v2.4.2-deployment.zip` ✅

---

## Step 1: Configure Azure App Settings

```bash
# CRITICAL: Set Worker Indexing flag
az functionapp config appsettings set \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --settings AzureWebJobsFeatureFlags=EnableWorkerIndexing
```

- [ ] Command completed successfully
- [ ] No errors in output

---

## Step 2: Deploy Package

```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --src v2.4.2-deployment.zip
```

- [ ] Deployment started
- [ ] Shows "Deployment successful" message
- [ ] No errors in output

---

## Step 3: Restart Function App

```bash
az functionapp restart \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

- [ ] Restart command completed
- [ ] Wait 2-3 minutes for worker initialization

---

## Step 4: Verify in Azure Portal

1. Open: https://portal.azure.com
2. Navigate to Function App: `func-btp-uks-prod-doc-crawler-01`
3. Click **"Functions"** in left menu
4. Wait 30-60 seconds for list to populate

### Expected: 19 Functions Total

- [ ] `scheduled_crawler_orchestrated` (Timer)
- [ ] `scheduled_crawler` (Timer)
- [ ] `web_crawler_orchestrator` (Orchestration)
- [ ] `get_configuration_activity` (Activity)
- [ ] `get_document_hashes_activity` (Activity)
- [ ] `crawl_single_website_activity` (Activity)
- [ ] `store_document_hashes_activity` (Activity)
- [ ] `store_crawl_history_activity` (Activity)
- [ ] `validate_storage_activity` (Activity)
- [ ] `http_start` (HTTP Trigger)
- [ ] `http_get_status` (HTTP Trigger)
- [ ] `http_terminate` (HTTP Trigger)
- [ ] `manual_crawl` (HTTP Trigger)
- [ ] `search_site` (HTTP Trigger)
- [ ] `api_stats` (HTTP Trigger)
- [ ] `dashboard` (HTTP Trigger)
- [ ] `websites` (HTTP Trigger)
- [ ] `crawl` (HTTP Trigger)
- [ ] `manage_websites` (HTTP Trigger)

---

## Step 5: Test HTTP Endpoint

```bash
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard
```

- [ ] Returns JSON response (not 404)
- [ ] Shows dashboard data

---

## ✅ Success Criteria

All checkboxes above are checked = **Functions are visible and working!** 🎉

## ❌ If Still Not Working

See: `COMPLETE-FIX-FUNCTIONS-NOT-APPEARING.md` for advanced troubleshooting

---

**Package**: v2.4.2-deployment.zip ✅  
**Date**: October 18, 2025  
**Status**: Ready to deploy
