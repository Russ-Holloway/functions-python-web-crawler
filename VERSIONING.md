# 🔢 VERSIONING SYSTEM - Azure Functions Web Crawler

## 📋 VERSION NAMING CONVENTION

### **Format**: `v{MAJOR}.{MINOR}.{PATCH}`

### **Rules**:
- **HIGHEST number = CURRENT version** (always use latest)
- **Semantic Versioning** for clear change tracking
- **File naming**: `function-app-v{VERSION}-{description}-{timestamp}.zip`

### **Version Types**:
- **MAJOR** (v2.0.0 → v3.0.0): Breaking changes, major features, infrastructure changes
- **MINOR** (v2.0.0 → v2.1.0): New features, new sites added, significant improvements
- **PATCH** (v2.0.0 → v2.0.1): Bug fixes, small tweaks, configuration updates

## 📈 VERSION HISTORY

| Version | Date | Description | Status |
|---------|------|-------------|--------|
| **v2.0.0** | 2025-10-15 | CPS prosecution-guidance fix + safeguards | ✅ **CURRENT** |
| v1.1 | 2025-10-15 | Status endpoint working | ✅ Superseded |
| v1.0 | 2025-10-13 | Initial production version | ✅ Superseded |

## 🎯 CURRENT VERSION: **v2.0.0**

### **Features**:
- ✅ CPS prosecution-guidance crawling (269 documents)
- ✅ Full Azure Storage integration
- ✅ 4-hour timer scheduling
- ✅ All endpoints operational
- ✅ Comprehensive safeguards
- ✅ Emergency recovery procedures

### **Files**:
- **Deployed**: `function-app-v2.0.0-stable-2025-10-15-1243.zip`
- **Local**: `function_app.py` (v2.0.0)
- **Emergency Backup**: `function-app-v2.0.0-stable-2025-10-15-1243.zip`

## 🔄 VERSION WORKFLOW

### **When Creating New Versions**:

1. **Determine Version Type**:
   ```
   Bug fix     → v2.0.1
   New feature → v2.1.0  
   Major change → v3.0.0
   ```

2. **Update function_app.py**:
   ```python
   "version": "v2.0.1",  # Update this line
   ```

3. **Create Versioned Backup**:
   ```powershell
   $timestamp = Get-Date -Format "yyyy-MM-dd-HHmm"
   Compress-Archive -Path function_app.py,host.json,requirements.txt -DestinationPath "function-app-v2.0.1-description-$timestamp.zip" -Force
   ```

4. **Git Commit with Version**:
   ```bash
   git commit -m "v2.0.1: Description of changes"
   ```

5. **Deploy with Version Tag**:
   ```bash
   az functionapp deployment source config-zip --resource-group rg-btp-uks-prod-doc-crawler-01 --name func-btp-uks-prod-doc-crawler-01 --src function-app-v2.0.1-description-timestamp.zip
   ```

## 📊 VERSION IDENTIFICATION

### **Quick Check Current Version**:
```powershell
# Check deployed version
Invoke-WebRequest -Uri "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/status" | ConvertFrom-Json | Select version

# Check local version  
Select-String '"version"' function_app.py
```

### **Find Latest Backup**:
```powershell
# List all versions (highest = current)
Get-ChildItem function-app-v*.zip | Sort-Object Name -Descending | Select-Object Name -First 5
```

## 🎯 VERSION EXAMPLES

### **v2.0.1** - Bug Fix Example:
- Fix timer function issue
- Correct storage authentication
- Small configuration update

### **v2.1.0** - Feature Addition Example:
- Add new government site
- Improve document detection
- Add new crawl endpoint

### **v3.0.0** - Major Update Example:
- Change to Python v3 model
- Infrastructure upgrade
- Breaking API changes

## 🛡️ VERSION SAFEGUARDS

### **Before Version Change**:
- [ ] Current system working (run status test)
- [ ] Backup current version created
- [ ] Change documented with version rationale
- [ ] Rollback plan confirmed

### **After Version Deployment**:
- [ ] New version responds correctly
- [ ] All endpoints functional
- [ ] Version number updated in response
- [ ] Emergency backup confirmed working

## 📋 VERSION COMMANDS REFERENCE

### **Create New Version**:
```powershell
# 1. Update version in function_app.py
# 2. Create backup
$version = "v2.0.1"
$desc = "bug-fix"
$timestamp = Get-Date -Format "yyyy-MM-dd-HHmm"
Compress-Archive -Path function_app.py,host.json,requirements.txt -DestinationPath "function-app-$version-$desc-$timestamp.zip" -Force

# 3. Commit
git add function_app.py
git commit -m "$version: Description of changes"
git push
```

### **Emergency Rollback**:
```bash
# Always deploy the highest v2.x.x version available
az functionapp deployment source config-zip --resource-group rg-btp-uks-prod-doc-crawler-01 --name func-btp-uks-prod-doc-crawler-01 --src function-app-v2.0.0-stable-2025-10-15-1243.zip
```

## 🎯 REMEMBER

- **HIGHEST version number = CURRENT**
- **Always increment properly** (don't skip numbers)
- **Document every change** with version commit
- **Test before incrementing** version
- **Keep emergency backup** of each working version

---

**Current Stable: v2.0.0** | **Next: v2.0.1 or v2.1.0** | **Emergency: v2.0.0**