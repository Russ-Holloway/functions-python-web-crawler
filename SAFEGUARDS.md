# 🛡️ AZURE FUNCTIONS WEB CRAWLER - SAFEGUARDS & PROCEDURES

## 🚨 CRITICAL INFRASTRUCTURE - DO NOT DELETE

### **NEVER DELETE THESE RESOURCES:**
- **App Service Plan**: `asp-btp-uks-prod-doc-crawler-01` 
  - ⚠️ **DELETION CAUSES TOTAL SYSTEM FAILURE**
  - Must comply with BTP naming: start with `asp-` or `plan-`
- **Resource Group**: `rg-btp-uks-prod-doc-crawler-01`
- **Function App**: `func-btp-uks-prod-doc-crawler-01`
- **Storage Account**: `stbtpuksprodcrawler01`

## 📋 CURRENT STABLE CONFIGURATION (v1.1)

### **Verified Working State** ✅
- **Status Endpoint**: HTTP 200 - `https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/status`
- **Manual Crawl**: HTTP 200 - 269 documents from CPS prosecution-guidance
- **Azure Storage**: Active integration to `stbtpuksprodcrawler01/documents`
- **Timer Function**: 4-hour automatic scheduling operational
- **CPS Target**: `https://www.cps.gov.uk/prosecution-guidance` ✅ WORKING

### **Stable Backup File**
- **File**: `function-app-v1.1-stable-cps-fixed-2025-10-15-1235.zip`
- **Contents**: function_app.py, host.json, requirements.txt
- **Status**: Verified working - use for emergency restore

## 🔄 SAFE DEPLOYMENT PROCEDURES

### **BEFORE ANY CHANGES:**
1. **Test the current system**: Run status endpoint test
2. **Create versioned backup**: `function-app-v{version}-{description}-{timestamp}.zip`
3. **Document the change**: What, why, expected impact
4. **Test locally first**: If possible, validate changes before deployment

### **DEPLOYMENT COMMANDS (Cloud Shell):**
```bash
# Upload your zip file to Cloud Shell first, then:
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-crawler-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src your-function-app.zip
```

### **POST-DEPLOYMENT VERIFICATION:**
```powershell
# Test status endpoint
Invoke-WebRequest -Uri "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/status" -Headers @{"Accept"="application/json"}

# Test manual crawl (should find 269+ documents from CPS)
$body = @{ target_url = "https://www.cps.gov.uk/prosecution-guidance"; max_depth = 1 } | ConvertTo-Json
Invoke-WebRequest -Uri "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl" -Method POST -Body $body -ContentType "application/json"
```

## 🚨 EMERGENCY RECOVERY PROCEDURES

### **If System Stops Working:**
1. **Check App Service Plan exists**: `asp-btp-uks-prod-doc-crawler-01`
2. **If deleted**: Recreate with BTP-compliant naming (asp-* or plan-*)
3. **Redeploy stable version**: Use `function-app-v1.1-stable-cps-fixed-2025-10-15-1235.zip`
4. **Wait 60 seconds** after deployment before testing
5. **Run verification tests** (status + manual crawl)

### **Emergency Restore Command:**
```bash
# In Cloud Shell (upload stable zip first):
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-crawler-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src function-app-v1.1-stable-cps-fixed-2025-10-15-1235.zip
```

## 📊 KNOWN WORKING ENDPOINTS

| Endpoint | Method | Status | Purpose |
|----------|--------|--------|---------|
| `/api/status` | GET | ✅ 200 | System health check |
| `/api/crawl` | POST | ✅ 200 | Manual crawl with parameters |
| `/api/manual_crawl` | POST | ⚠️ 500 | Alternative manual crawl |
| `/api/timer_crawl` | Timer | ✅ Working | Auto 4-hour crawling |

## 🏗️ BTP ORGANIZATIONAL POLICIES

### **Naming Conventions:**
- App Service Plans: Must start with `asp-` or `plan-`
- **VIOLATION = AUTOMATIC DELETION**
- Current compliant name: `asp-btp-uks-prod-doc-crawler-01`

### **Resource Monitoring:**
- Check resources exist before major changes
- BTP may delete non-compliant resources without warning
- Always use compliant naming for new resources

## 📈 CONFIGURATION SITES (Current)

The system currently crawls these sites automatically every 4 hours:

1. **CPS Prosecution Guidance**: `https://www.cps.gov.uk/prosecution-guidance` ✅
2. **CPS Main Site**: `https://www.cps.gov.uk/`
3. **College of Policing**: `https://www.college.police.uk/`
4. **Police Professional Standards**: `https://www.policeconduct.gov.uk/`
5. **Home Office Police**: `https://www.gov.uk/government/organisations/home-office/about/recruitment`
6. **NPCC**: `https://www.npcc.police.uk/`

## 🔧 TROUBLESHOOTING GUIDE

### **404 Errors on all endpoints:**
- **Cause**: App Service Plan deleted or functions not detected
- **Solution**: Check infrastructure, redeploy stable version

### **500 Errors:**
- **Cause**: Code issues or configuration problems  
- **Solution**: Redeploy last known working version

### **Functions not detected by Azure:**
- **Cause**: Code syntax errors or missing function definitions
- **Solution**: Validate function_app.py syntax, check function decorators

### **Storage integration issues:**
- **Cause**: Managed identity or storage account problems
- **Solution**: Check storage account exists, verify managed identity setup

## 📝 CHANGE LOG TEMPLATE

When making changes, use this template:

```
VERSION: v{X.X}
DATE: {YYYY-MM-DD}
CHANGE DESCRIPTION: {What was changed}
REASON: {Why the change was needed}
TESTED: {How it was verified}
BACKUP CREATED: {filename.zip}
ROLLBACK PLAN: {How to undo if needed}
```

## ⚡ QUICK REFERENCE

- **Current Version**: v1.1-stable-cps-fixed
- **Last Verified**: 2025-10-15 12:35
- **Status URL**: https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/status
- **Emergency Backup**: function-app-v1.1-stable-cps-fixed-2025-10-15-1235.zip
- **Critical Rule**: NEVER delete App Service Plan `asp-btp-uks-prod-doc-crawler-01`