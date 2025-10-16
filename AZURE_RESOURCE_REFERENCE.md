# 🏗️ AZURE RESOURCE REFERENCE - DEFINITIVE STATIC DETAILS

## ⚠️ CRITICAL: USE THESE EXACT VALUES - NO VARIATIONS ALLOWED

This document contains the definitive, verified Azure resource details for the BTP Document Crawler system. **ANY deviation from these exact values will cause deployment failures.**

---

## 🎯 **AZURE FUNCTION APP**
- **Name**: `func-btp-uks-prod-doc-crawler-01`
- **URL**: `https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net`
- **Region**: `uksouth`

## 📁 **RESOURCE GROUP**
- **Name**: `rg-btp-uks-prod-doc-mon-01`
- **Region**: `uksouth`

## 💾 **STORAGE ACCOUNT**
- **Name**: `stbtpuksprodcrawler01`
- **Container**: `documents`
- **Full Path**: `stbtpuksprodcrawler01/documents`
- **Region**: `uksouth`

## 🗄️ **COSMOS DB**
- **Name**: `db-btp-uks-prod-doc-mon-01`
- **Region**: `uksouth`

## 📋 **APP SERVICE PLAN**
- **Name**: `asp-btp-uks-prod-doc-crawler-01`
- **BTP Compliance**: ✅ Starts with `asp-` (required)
- **Region**: `uksouth`

## 🔑 **SUBSCRIPTION**
- **Name**: `sub-btp-prod-AI-01`
- **ID**: `96726562-1726-4984-88c6-2e4f28878873`

---

## 🚀 **DEPLOYMENT COMMAND TEMPLATE**

### **Standard Deployment:**
```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --src "your-deployment-file.zip"
```

### **Emergency Rollback:**
```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --src "function-app-v2.0.0-current-working-backup-2025-10-15-1318.zip"
```

---

## 🧪 **VERIFICATION COMMAND TEMPLATES**

### **Status Check:**
```powershell
Invoke-WebRequest -Uri "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/status"
```

### **Websites List:**
```powershell
Invoke-WebRequest -Uri "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/websites"
```

### **Manual Crawl Test:**
```powershell
$body = @{ target_url = "https://www.npcc.police.uk/publications/All-publications/" } | ConvertTo-Json
Invoke-WebRequest -Uri "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl" -Method POST -Body $body -ContentType "application/json"
```

---

## 🔗 **STORAGE INTEGRATION DETAILS**

### **Blob Storage URLs:**
- **Base URL**: `https://stbtpuksprodcrawler01.blob.core.windows.net`
- **Documents Container**: `https://stbtpuksprodcrawler01.blob.core.windows.net/documents`
- **Hash Storage**: `https://stbtpuksprodcrawler01.blob.core.windows.net/documents/document_hashes.json`

### **Authentication Method:**
- **Type**: Managed Identity (Azure Functions environment)
- **Variables**: `IDENTITY_ENDPOINT` and `IDENTITY_HEADER`

---

## 📊 **BTP COMPLIANCE REQUIREMENTS**

### **Naming Conventions:**
- ✅ **App Service Plans**: Must start with `asp-` or `plan-`
- ✅ **Resource Groups**: Must start with `rg-`
- ✅ **Function Apps**: Must start with `func-`
- ✅ **Storage Accounts**: Must start with `st` (lowercase)
- ✅ **Cosmos DB**: Must start with `db-`

### **Critical Rule:**
⚠️ **NEVER DELETE** the App Service Plan `asp-btp-uks-prod-doc-crawler-01` - causes total system failure

---

## 🎯 **QUICK COPY-PASTE REFERENCE**

**Resource Group**: `rg-btp-uks-prod-doc-mon-01`  
**Function App**: `func-btp-uks-prod-doc-crawler-01`  
**Storage Account**: `stbtpuksprodcrawler01`  
**Cosmos DB**: `db-btp-uks-prod-doc-mon-01`  
**Subscription ID**: `96726562-1726-4984-88c6-2e4f28878873`  
**Region**: `uksouth`  

---

## 📝 **LAST VERIFIED**
- **Date**: 2025-10-15
- **Verified By**: User confirmation
- **Status**: ✅ All details confirmed working

**⚠️ DO NOT MODIFY THESE VALUES WITHOUT USER CONFIRMATION**