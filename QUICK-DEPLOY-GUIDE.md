# Quick Deployment Guide - ZIP Upload Method
**Durable Functions Web Crawler v3.0.0-alpha**

## 📦 Step 1: Create Deployment ZIP File

Run this PowerShell command in your project directory:

```powershell
# Navigate to project directory
cd "c:\Users\4530Holl\OneDrive - British Transport Police\_Open-Ai\Web-Crawler-Repo\functions-python-web-crawler\functions-python-web-crawler"

# Remove old deployment zip if exists
if (Test-Path "deploy.zip") { Remove-Item "deploy.zip" }

# Create deployment package (exclude unnecessary files)
$filesToInclude = @(
    "function_app.py",
    "host.json",
    "requirements.txt",
    "websites.json"
)

Compress-Archive -Path $filesToInclude -DestinationPath "deploy.zip" -Force

Write-Host "✓ Deployment package created: deploy.zip" -ForegroundColor Green
Write-Host "  Files included:" -ForegroundColor Cyan
Get-Item $filesToInclude | ForEach-Object { Write-Host "    - $($_.Name)" -ForegroundColor Gray }
```

**Verify the ZIP file:**
```powershell
# Check ZIP contents
Expand-Archive -Path "deploy.zip" -DestinationPath "temp_verify" -Force
Get-ChildItem "temp_verify" | Select-Object Name, Length
Remove-Item "temp_verify" -Recurse -Force
```

---

## 🚀 Step 2: Deploy ZIP to Azure

### First, set your Function App details:

```bash
# Replace with your actual values
FUNCTION_APP_NAME="<your-function-app-name>"
RESOURCE_GROUP="<your-resource-group>"
```

### Deploy the ZIP file:

```bash
# Method 1: ZIP Deploy (Recommended)
az functionapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP_NAME \
  --src deploy.zip
```

**Alternative if you get errors:**

```bash
# Method 2: Direct publish using kudu API
az functionapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP_NAME \
  --src deploy.zip \
  --build-remote true
```

**Wait for deployment to complete** (usually 2-3 minutes)

---

## ⚙️ Step 3: Configure Application Settings

```bash
# Set configuration location (use "blob" if websites.json is in blob storage, or "local" if included in ZIP)
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings WEBSITES_CONFIG_LOCATION=local

# Set storage account name
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings STORAGE_ACCOUNT_NAME=stbtpuksprodcrawler01

# Verify settings
az functionapp config appsettings list \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[?name=='WEBSITES_CONFIG_LOCATION' || name=='STORAGE_ACCOUNT_NAME'].{Name:name, Value:value}" \
  --output table
```

---

## 🔐 Step 4: Configure Managed Identity (If Not Already Done)

```bash
# Enable system-assigned identity
az functionapp identity assign \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Get the principal ID (save this for role assignment)
PRINCIPAL_ID=$(az functionapp identity show \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId \
  --output tsv)

echo "Principal ID: $PRINCIPAL_ID"

# Assign Storage Blob Data Contributor role
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/$(az account show --query id --output tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/stbtpuksprodcrawler01
```

---

## ✅ Step 5: Verify Deployment

```bash
# Check Function App status
az functionapp show \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "{Name:name, State:state, DefaultHostName:defaultHostName}" \
  --output table

# List deployed functions
az functionapp function list \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[].{Name:name, Type:type}" \
  --output table
```

**Expected functions:**
- web_crawler_orchestrator
- get_configuration_activity
- get_document_hashes_activity
- crawl_single_website_activity
- store_document_hashes_activity
- store_crawl_history_activity
- start_web_crawler_orchestration
- get_orchestration_status
- terminate_orchestration
- scheduled_crawler_orchestrated

---

## 🧪 Step 6: Test the Deployment

```bash
# Get function key
FUNCTION_KEY=$(az functionapp keys list \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query functionKeys.default \
  --output tsv)

echo "Function Key: $FUNCTION_KEY"

# Start orchestration
curl -X POST "https://$FUNCTION_APP_NAME.azurewebsites.net/api/start_web_crawler_orchestration?code=$FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{"config_location":"local"}'
```

**Expected response:**
```json
{
  "id": "abc123...",
  "statusQueryGetUri": "https://...",
  "sendEventPostUri": "https://...",
  "terminatePostUri": "https://...",
  ...
}
```

**Save the `statusQueryGetUri` and check status:**

```bash
# Replace with your actual statusQueryGetUri from the response above
curl "<your-statusQueryGetUri-here>"
```

---

## 📊 Step 7: Monitor Execution

```bash
# Stream logs
az functionapp log tail \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

**Or view in Azure Portal:**
- Go to your Function App
- Click "Log stream" in the left menu
- Watch for execution logs

---

## 🔄 Optional: Upload Configuration to Blob Storage

If you want to manage `websites.json` in blob storage instead of bundled in ZIP:

```bash
# Upload websites.json to blob storage
az storage blob upload \
  --account-name stbtpuksprodcrawler01 \
  --container-name configuration \
  --name websites.json \
  --file websites.json \
  --auth-mode login \
  --overwrite

# Update app setting to use blob
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings WEBSITES_CONFIG_LOCATION=blob
```

---

## 📝 Quick Reference Commands

### Redeploy after code changes:

```powershell
# PowerShell: Recreate ZIP and deploy
Compress-Archive -Path function_app.py,host.json,requirements.txt,websites.json -DestinationPath "deploy.zip" -Force
```

```bash
# Azure CLI: Deploy updated ZIP
az functionapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP_NAME \
  --src deploy.zip
```

### Check deployment status:

```bash
az functionapp deployment list \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[0].{Status:status, Message:message, Time:start_time}" \
  --output table
```

### View recent logs:

```bash
az functionapp log tail \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

### Restart Function App:

```bash
az functionapp restart \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

---

## ⚠️ Troubleshooting

### If deployment fails:

```bash
# Check deployment logs
az functionapp log deployment show \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Or list recent deployments
az functionapp deployment list \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table
```

### If functions don't appear:

```bash
# Sync triggers (forces Azure to reload functions)
az functionapp function keys list \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --function-name start_web_crawler_orchestration

# Or restart the app
az functionapp restart \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

### If you get permission errors:

```bash
# Re-check managed identity role assignment
az role assignment list \
  --assignee $PRINCIPAL_ID \
  --output table
```

---

## ✅ Deployment Checklist

- [ ] ZIP file created with all required files
- [ ] ZIP deployed to Azure successfully
- [ ] Application settings configured
- [ ] Managed Identity enabled and roles assigned
- [ ] Functions list shows all 10 functions
- [ ] Test orchestration started successfully
- [ ] Logs showing execution
- [ ] Blob storage accessible

---

**Ready to deploy!** Just copy and paste the commands above into Azure CLI, replacing the placeholder values with your actual Function App name and Resource Group.
