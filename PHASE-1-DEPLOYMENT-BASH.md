# Phase 1 Deployment Guide - Azure CLI (Bash)

## ✅ Deployment Package Ready

**File:** `phase1-deployment.zip` (22.8 KB)  
**Location:** `functions-python-web-crawler/functions-python-web-crawler/`  
**Date:** October 17, 2025

---

## 📦 What's Included in ZIP

- `function_app.py` - **Updated with unique filename generation**
- `host.json` - Function host configuration
- `requirements.txt` - Python dependencies
- `websites.json` - Website configuration
- `.funcignore` - Deployment exclusions

---

## 🚀 Deployment Commands (Azure CLI Bash)

### **Prerequisites**

Ensure you're logged into Azure CLI:
```bash
az login
az account show
```

### **Step 1: Set Variables**

```bash
# Set your Azure Function App details (from AZURE_RESOURCE_REFERENCE.md)
RESOURCE_GROUP="rg-btp-uks-prod-doc-mon-01"
FUNCTION_APP="func-btp-uks-prod-doc-crawler-01"
SUBSCRIPTION="96726562-1726-4984-88c6-2e4f28878873"
ZIP_FILE="phase1-deployment.zip"
```

### **Step 2: Deploy ZIP Package**

```bash
# Deploy the ZIP file to Azure Function App
az functionapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --subscription $SUBSCRIPTION \
  --src $ZIP_FILE
```

**Expected Output:**
```
Getting scm site credentials for zip deployment
Starting zip deployment. This operation can take a while to complete ...
Deployment endpoint responded with status code 202
```

### **Step 3: Verify Deployment**

```bash
# Check deployment status
az functionapp deployment list \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --query "[0].{Status:status, Message:message}" \
  --output table

# Restart function app to ensure changes are loaded
az functionapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP
```

### **Step 4: Monitor Deployment Logs**

```bash
# Stream logs to verify deployment
az functionapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP
```

Press `Ctrl+C` to stop streaming when you see the function app start.

---

## 🧪 Testing After Deployment

### **Option 1: Test with Dashboard (Recommended)**

1. Open the dashboard in your browser:
   ```bash
   echo "https://$FUNCTION_APP.azurewebsites.net/api/dashboard"
   ```

2. Wait for the next scheduled crawl (every 4 hours)

3. Monitor the dashboard for:
   - ✅ Documents Uploaded count
   - ✅ Total Documents in storage
   - **These should match!**

### **Option 2: Manual Trigger via API**

```bash
# Get the function key
FUNCTION_KEY=$(az functionapp function keys list \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --function-name orchestrator_start \
  --query "default" -o tsv)

# Trigger the orchestrator
curl -X POST \
  "https://$FUNCTION_APP.azurewebsites.net/api/orchestrator_start?code=$FUNCTION_KEY" \
  -H "Content-Type: application/json"
```

### **Option 3: Test Single Site First** (Safest)

Before triggering full crawl, edit `websites.json` to enable only one site:

```bash
# This should be done locally before creating the ZIP, but you can verify:
az functionapp config appsettings list \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --query "[?name=='WEBSITES_CONFIG_LOCATION'].value" -o tsv
```

---

## 📊 Verification Checklist

### **Check 1: Deployment Success**
```bash
# Verify function app is running
az functionapp show \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --query "state" -o tsv
# Expected: "Running"
```

### **Check 2: View Recent Logs**
```bash
# Check for errors in logs (requires Application Insights)
az monitor app-insights query \
  --app $FUNCTION_APP \
  --analytics-query "traces | where timestamp > ago(1h) | order by timestamp desc | take 50" \
  --output table
```

### **Check 3: Storage Document Count**
```bash
# Count documents in storage (requires storage permissions)
STORAGE_ACCOUNT="stbtpuksprodcrawler01"
CONTAINER="documents"

az storage blob list \
  --account-name $STORAGE_ACCOUNT \
  --container-name $CONTAINER \
  --auth-mode login \
  --query "length([?name!='document-hashes.json' && name!='crawl_history.json'])" \
  --output tsv
```

### **Check 4: Look for Unique Filenames in Logs**

After a crawl runs, check logs for the new format:
```bash
az functionapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  | grep "Uploaded"
```

**Expected log pattern:**
```
✅ Uploaded uk-legislation/a1b2c3d4_data.pdf (original: data.pdf) - Status: new
✅ Uploaded crown-prosecution-service/b2c3d4e5_guidance.pdf (original: guidance.pdf) - Status: new
```

---

## 🎯 Success Criteria

After deployment and one complete crawl cycle:

✅ **No deployment errors** in Azure portal or CLI  
✅ **Function app status: Running**  
✅ **Logs show unique filenames** with hash prefixes  
✅ **Storage count matches uploaded count** in dashboard  
✅ **Virtual folders created** in storage (site names)  
✅ **No filename collision warnings**

---

## 🔄 If Issues Occur

### **Rollback to Previous Version**

```bash
# List previous deployments
az functionapp deployment list \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --query "[].{ID:id, Status:status, Time:end_time}" \
  --output table

# Revert to previous deployment (if available)
# You'll need to redeploy the old ZIP file
```

### **View Detailed Errors**

```bash
# Get detailed deployment logs
az functionapp deployment list-publishing-credentials \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP
```

### **Check Application Insights**

```bash
# Query for errors
az monitor app-insights query \
  --app $FUNCTION_APP \
  --analytics-query "exceptions | where timestamp > ago(1h) | project timestamp, problemId, outerMessage" \
  --output table
```

---

## 📝 Post-Deployment Actions

1. **Monitor first crawl cycle** (check dashboard after 4 hours)
2. **Compare storage count** before and after
3. **Verify no data loss** (storage count should increase, not stay same)
4. **Check for folder structure** in Azure Storage Explorer
5. **Review logs** for any warnings or errors

---

## 🔗 Quick Reference Commands

```bash
# Check function app status
az functionapp show -g $RESOURCE_GROUP -n $FUNCTION_APP --query "state" -o tsv

# Restart function app
az functionapp restart -g $RESOURCE_GROUP -n $FUNCTION_APP

# Stream logs
az functionapp log tail -g $RESOURCE_GROUP -n $FUNCTION_APP

# List storage blobs
az storage blob list --account-name $STORAGE_ACCOUNT --container-name $CONTAINER --auth-mode login --output table

# View dashboard
open "https://$FUNCTION_APP.azurewebsites.net/api/dashboard"
```

---

## 📞 Support

If deployment issues persist:
1. Check Azure Portal > Function App > Deployment Center
2. Review Application Insights for exceptions
3. Verify Managed Identity has Storage Blob Data Contributor role
4. Ensure all required app settings are configured

---

**Deployment Package:** `phase1-deployment.zip`  
**Deployment Method:** Azure CLI `az functionapp deployment source config-zip`  
**Expected Downtime:** < 1 minute (during restart)  
**Risk Level:** Low (additive changes only)  

**Ready to deploy!** 🚀
