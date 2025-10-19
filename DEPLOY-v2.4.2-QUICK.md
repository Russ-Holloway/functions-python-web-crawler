# 🚀 QUICK DEPLOY - v2.4.2 Hotfix

## What's Fixed
✅ Functions now appear in Azure Portal (proper decorator registration)

## Deploy Now

### Step 1: Deploy Package
```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --src v2.4.2-deployment.zip
```

### Step 2: Restart (CRITICAL)
```bash
az functionapp restart \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

### Step 3: Verify
Open Azure Portal → Function App → Functions

You should see:
- ✅ scheduled_crawler_orchestrated (Timer)
- ✅ scheduled_crawler (Timer)
- ✅ web_crawler_orchestrator (Orchestrator)
- ✅ 6 activity functions
- ✅ 10 HTTP trigger functions

## Test Endpoints
```bash
# Test dashboard
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard

# Test websites config
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/websites

# Test info
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/info
```

## Done! 🎉
All functions should now be visible and operational in Azure Portal.

---
**For detailed technical explanation, see:** `HOTFIX-v2.4.2-FUNCTION-REGISTRATION.md`
