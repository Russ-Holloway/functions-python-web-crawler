# v2.7.0 Deployment - Quick Commands

## 🚀 Deploy via GitHub Actions (RECOMMENDED)

```bash
# Stage all changes
git add .

# Commit with message
git commit -m "v2.7.0: Fixed 'Other' category issue and added cleanup utility"

# Push to main (triggers automatic deployment)
git push origin main
```

**Monitor deployment:**
https://github.com/Russ-Holloway/functions-python-web-crawler/actions

---

## ✅ Verify Deployment

```bash
# Set function URL
FUNCTION_URL="func-btp-uks-prod-doc-crawler-01.azurewebsites.net"

# Test dashboard
curl "https://${FUNCTION_URL}/api/dashboard"

# Test new cleanup endpoint
curl "https://${FUNCTION_URL}/api/cleanup_uncategorized" | jq .
```

---

## 🧹 Clean Up "Other" Documents

```bash
# Step 1: Check what will be deleted (safe)
curl "https://${FUNCTION_URL}/api/cleanup_uncategorized" | jq .

# Step 2: Delete uncategorized documents
curl -X POST "https://${FUNCTION_URL}/api/cleanup_uncategorized" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}' | jq .

# Step 3: Trigger manual crawl to re-download
curl -X POST "https://${FUNCTION_URL}/api/manual_crawl" \
  -H "Content-Type: application/json" \
  -d '{"websites": ["all"]}' | jq .
```

---

## 📊 Monitor Logs

```bash
az webapp log tail \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

---

## Azure Resources

- **Function App**: `func-btp-uks-prod-doc-crawler-01`
- **Resource Group**: `rg-btp-uks-prod-doc-mon-01`
- **Subscription**: `96726562-1726-4984-88c6-2e4f28878873`
- **Region**: UK South

---

**Deployment**: GitHub Actions (Automated)  
**Version**: v2.7.0
