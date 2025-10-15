# 🤖 COPILOT INSTRUCTIONS - AZURE FUNCTIONS WEB CRAWLER

## 🚨 CRITICAL SAFETY RULES - ALWAYS FOLLOW

### **BEFORE ANY CODE CHANGES:**
1. **ASK THESE QUESTIONS:**
   - "Is this change necessary for the core functionality?"
   - "Have I tested the current system first?"
   - "Do I have a rollback plan?"
   - "Have I created a versioned backup?"

2. **MANDATORY PRE-CHANGE CHECKLIST:**
   ```
   [ ] Current system status verified (run status endpoint test)
   [ ] Stable backup created with timestamp
   [ ] Change documented with version number
   [ ] Infrastructure confirmed intact (esp. App Service Plan)
   [ ] Deployment plan prepared
   ```

### **NEVER DO THESE THINGS:**
- ❌ Delete App Service Plan `asp-btp-uks-prod-doc-crawler-01`
- ❌ Change resource group `rg-btp-uks-prod-doc-crawler-01`
- ❌ Deploy without testing current system first
- ❌ Make changes without creating backup
- ❌ Use non-BTP-compliant naming (must start with asp- or plan-)

## 🎯 FOCUSED CHANGE APPROACH

### **For URL Configuration Changes:**
1. **Current Working State**: CPS prosecution-guidance is at `https://www.cps.gov.uk/prosecution-guidance` ✅
2. **Change Process**:
   - Update only the specific URL in SITES_CONFIG
   - Keep all other configurations identical
   - Test with single-site crawl first
   - Deploy with descriptive version name

### **For New Features:**
1. **Start Small**: Add feature incrementally
2. **Test in Isolation**: Create minimal test version first
3. **Preserve Core**: Don't modify working crawler logic
4. **Version Everything**: Each change gets a new version

### **For Bug Fixes:**
1. **Identify Root Cause**: Don't guess, investigate
2. **Minimal Changes**: Fix only what's broken
3. **Regression Test**: Ensure existing functionality still works
4. **Document Fix**: Clear explanation of what was fixed

## 🔄 STANDARDIZED WORKFLOWS

### **DEPLOYMENT WORKFLOW:**
```
1. Current Status Check:
   Invoke-WebRequest -Uri "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/status"

2. Create Backup:
   $version = "v1.X-{description}"
   $timestamp = Get-Date -Format "yyyy-MM-dd-HHmm"
   Compress-Archive -Path function_app.py,host.json,requirements.txt -DestinationPath "function-app-$version-$timestamp.zip"

3. Deploy in Cloud Shell:
   az functionapp deployment source config-zip --resource-group rg-btp-uks-prod-doc-crawler-01 --name func-btp-uks-prod-doc-crawler-01 --src your-file.zip

4. Post-Deployment Test:
   # Wait 60 seconds, then test endpoints
```

### **ROLLBACK WORKFLOW:**
```
If anything breaks:
1. Immediately deploy last known stable version
2. Use: function-app-v1.1-stable-cps-fixed-2025-10-15-1235.zip
3. Wait 60 seconds after deployment
4. Verify with status endpoint
5. Test manual crawl of CPS prosecution-guidance
```

## 📋 REQUIRED QUESTIONS TO ASK USER

### **Before Making Changes:**
1. "What specific functionality are you trying to change?"
2. "Have you verified the current system is working?"
3. "Do you want me to create a backup first?"
4. "Should I test this change in isolation?"

### **During Changes:**
1. "Should I preserve the existing [X] functionality?"
2. "Do you want me to test this before full deployment?"
3. "Shall I document this change for future reference?"

### **After Changes:**
1. "Should I run the full verification test suite?"
2. "Do you want me to update the version number?"
3. "Shall I commit this as a stable version?"

## 🎯 SUCCESS METRICS

### **System Health Indicators:**
- Status endpoint returns HTTP 200
- Manual crawl finds 269+ documents from CPS prosecution-guidance
- Azure Storage integration active
- Timer function operational (4-hour schedule)

### **Change Success Criteria:**
- No regression in existing functionality
- New feature works as intended
- All endpoints remain accessible
- Documentation updated
- Rollback plan exists

## 🔧 DEBUGGING PROTOCOL

### **When Things Break:**
1. **First Priority**: Get system working again
   - Deploy stable backup immediately
   - Don't investigate while system is down
2. **Second Priority**: Understand what happened
   - Check infrastructure (App Service Plan exists?)
   - Review recent changes
   - Identify root cause
3. **Third Priority**: Implement fix
   - Create new versioned approach
   - Test thoroughly before deployment

### **Common Issues & Solutions:**
- **404 on all endpoints**: App Service Plan deleted → Recreate with compliant naming
- **500 errors**: Code issue → Deploy stable backup, then fix incrementally  
- **Functions not detected**: Syntax error → Validate code, check function decorators
- **Storage issues**: Identity problem → Check managed identity and storage account

## 📚 KNOWLEDGE BASE

### **Working Configuration (v1.1):**
- **CPS URL**: `https://www.cps.gov.uk/prosecution-guidance` ✅
- **Auth Level**: ANONYMOUS (for troubleshooting endpoints)
- **Storage**: `stbtpuksprodcrawler01/documents`
- **Timer**: 4-hour schedule using `0 0 */4 * * *`
- **Function App**: Python v2 programming model

### **Infrastructure Dependencies:**
- App Service Plan: `asp-btp-uks-prod-doc-crawler-01` (EP1, Linux)
- Managed Identity: Enabled for storage access
- BTP Naming Policy: Resources must follow organizational standards
- UK South region for all resources

## 🏁 FINAL REMINDERS

### **Every Copilot Session Should:**
1. Start by checking current system status
2. Ask user about their specific goal
3. Create backup before changes
4. Test incrementally
5. Document what was done
6. Verify system health after changes

### **Never Assume:**
- That infrastructure is stable
- That previous changes are still working
- That small changes won't break things
- That the user wants to risk system downtime

### **Always Confirm:**
- Current system is working before starting
- User approves the approach
- Changes are tested before full deployment
- Rollback plan is clear and available

---

**Remember: This system is critical for document discovery. Stability > Speed. Working > Perfect.**