# v2.6.0 Quick Deployment Commands

## 🚀 Fast Track Deployment

### 1. Create Package
```bash
cd /workspaces/functions-python-web-crawler
zip -r v2.6.0-deployment.zip . \
  -x "*.git*" "*__pycache__*" "*.pyc" "*archive/*" "*temp-compare/*" \
  "*.md" "*.txt" "*.ps1" "*.sh" "*DEPLOY*" "*deploy*" "*test*" "*Test*" \
  "validate_functions.py" ".vscode/*" ".devcontainer/*"
```

### 2. Deploy
```bash
az functionapp deployment source config-zip \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --src v2.6.0-deployment.zip \
  --build-remote true \
  --timeout 600
```

### 3. Initialize Folders (CRITICAL!)
```bash
# Wait 30 seconds after deployment
sleep 30

# Create all website folders
curl -X POST https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/initialize_folders
```

### 4. Verify
```bash
# Check health
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/health

# Check folders created
az storage blob list \
  --account-name stbtpuksprodcrawler01 \
  --container-name documents \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --auth-mode login \
  --query "[?contains(name, '.folder')].[name]" -o table
```

### 5. Test Crawl
```bash
# Crawl one website to test
curl -X POST https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"site_name": "College of Policing App Portal", "force_all": false}'
```

---

## ✅ Expected Results

### Initialize Folders Response:
```json
{
  "status": "success",
  "message": "Initialized 5 website folders",
  "created": 5,
  "failed": 0
}
```

### Folders in Storage:
- college-of-policing-app-portal/.folder
- crown-prosecution-service/.folder
- legislation-test-working/.folder
- npcc-publications-all-publications/.folder
- uk-legislation-test-working/.folder

### Dashboard Stats (After Crawl):
Documents now grouped by website name (not "Other")!

---

## 📚 Full Documentation

See `DEPLOYMENT-v2.6.0.md` for complete guide with troubleshooting.
