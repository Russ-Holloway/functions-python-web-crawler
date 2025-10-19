# 🚀 GitHub Actions Deployment Guide - v2.5.0

## Overview

Your Function App uses **GitHub Actions CI/CD** for automatic deployment. This is the recommended approach for production deployments.

**Workflow**: `.github/workflows/main_func-btp-uks-prod-doc-crawler-01.yml`

---

## ✅ How It Works

### Automatic Deployment Trigger

The GitHub Actions workflow deploys automatically when:
- ✅ You push code to the `main` branch
- ✅ You manually trigger the workflow from GitHub

### Deployment Process

1. **Build Stage**:
   - Checks out code from repository
   - Sets up Python 3.11 environment
   - Installs dependencies from `requirements.txt`
   - Creates deployment ZIP package
   - Uploads artifact

2. **Deploy Stage**:
   - Downloads build artifact
   - Authenticates to Azure using managed identity
   - Deploys to Function App: `func-btp-uks-prod-doc-crawler-01`
   - Deploys to Production slot

---

## 🎯 Deploy v2.5.0 Now

### Option 1: Commit and Push (Recommended)

Since all your fixes are already in the local files, just commit and push:

```bash
# Stage all changes
git add .

# Commit with version tag
git commit -m "v2.5.0: Fix functions not appearing in portal

- Complete function app with 20+ decorated functions
- Proper Python v2 programming model
- Extension bundle [4.*, 5.0.0) configured
- All HTTP, timer, and durable functions registered
- Fixes: Functions not visible in Azure Portal"

# Push to trigger deployment
git push origin main
```

### Option 2: Manual Workflow Trigger

1. Go to: https://github.com/Russ-Holloway/functions-python-web-crawler/actions
2. Click: **Build and deploy Python project to Azure Function App**
3. Click: **Run workflow** → **Run workflow**

---

## 📊 Monitor Deployment

### Watch GitHub Actions

```bash
# View workflow runs
https://github.com/Russ-Holloway/functions-python-web-crawler/actions
```

You'll see:
1. ⚙️ Build job running (1-2 minutes)
2. 🚀 Deploy job running (2-3 minutes)
3. ✅ Deployment complete (green checkmark)

### Check Deployment Logs

In the GitHub Actions run:
1. Click on the workflow run
2. View **build** job logs
3. View **deploy** job logs
4. Look for: "Successfully deployed to Azure Functions"

---

## ✅ Post-Deployment Verification

### 1. Check Azure Portal (2-3 minutes after deployment)

1. Go to: Azure Portal → `func-btp-uks-prod-doc-crawler-01`
2. Click: **Functions** (left sidebar)
3. **Expected**: See all 20+ functions listed

### 2. Test Health Endpoint

```bash
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/ping
```

**Expected Response:**
```json
{
  "status": "alive",
  "message": "Function app is running",
  "timestamp": "2025-10-19T...",
  "version": "v2.4.2"
}
```

### 3. Verify Functions Appear

Check these key endpoints:
```bash
# Dashboard
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard

# Statistics
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/api/stats

# Websites
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/websites
```

---

## 🔧 Workflow Configuration

### Current Settings

```yaml
Trigger: Push to main branch or manual dispatch
Python Version: 3.11
Function App: func-btp-uks-prod-doc-crawler-01
Slot: Production
Package Path: . (repository root)
```

### Authentication

Uses Azure Federated Credentials:
- `AZUREAPPSERVICE_CLIENTID_*`
- `AZUREAPPSERVICE_TENANTID_*`
- `AZUREAPPSERVICE_SUBSCRIPTIONID_*`

These secrets are configured in GitHub repository settings.

---

## 🎯 What Gets Deployed

The workflow deploys **everything in the repository root**:

Essential Files:
- ✅ `function_app.py` - All function code
- ✅ `host.json` - Runtime configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `websites.json` - Site configurations

Excluded Files:
- ❌ `.venv/` - Virtual environment
- ❌ `.git/` - Git metadata
- ❌ `__pycache__/` - Python cache
- ❌ `local.settings.json` - Local settings

---

## 📋 Deployment Checklist

Before pushing:
- [ ] All changes saved
- [ ] `function_app.py` has all 20+ functions
- [ ] `host.json` properly configured
- [ ] `requirements.txt` includes all dependencies
- [ ] `websites.json` has correct site configs
- [ ] Commit message is descriptive

After pushing:
- [ ] GitHub Actions workflow triggered
- [ ] Build job succeeded
- [ ] Deploy job succeeded
- [ ] Functions appear in Azure Portal
- [ ] Health endpoint responds
- [ ] No errors in logs

---

## 🚨 Troubleshooting

### Workflow Fails

**Build Job Fails**:
- Check Python dependencies in `requirements.txt`
- Verify Python version compatibility (3.11)
- Check build logs for syntax errors

**Deploy Job Fails**:
- Verify Azure credentials in GitHub Secrets
- Check Function App is running in Azure
- Review deploy logs for authentication errors

### Functions Don't Appear After Deployment

**Wait**: Functions can take 2-3 minutes to appear after deployment

**Force Restart**:
```bash
az functionapp restart \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

**Check Logs**:
1. Azure Portal → Function App → Log stream
2. Look for function registration messages
3. Check for Python worker errors

---

## 🔄 Rollback

If deployment causes issues:

### Option 1: Revert Git Commit

```bash
# Revert to previous commit
git revert HEAD

# Push to trigger rollback deployment
git push origin main
```

### Option 2: Restore Previous Release

1. GitHub Actions → Previous successful workflow run
2. Re-run the deployment job
3. Or restore from archive ZIP manually

---

## 📈 Best Practices

### ✅ Do:
- Commit with descriptive messages
- Test locally before pushing
- Monitor GitHub Actions after push
- Verify deployment in Azure Portal
- Keep archive of deployment packages

### ❌ Don't:
- Push directly to main without testing
- Commit secrets or credentials
- Deploy during high-traffic periods
- Skip verification steps
- Ignore workflow failures

---

## 🎉 Success Indicators

Deployment is successful when:
- ✅ GitHub Actions shows green checkmark
- ✅ All 20+ functions visible in Azure Portal
- ✅ Health endpoint returns success
- ✅ No errors in Application Insights
- ✅ Timer triggers show next run times
- ✅ HTTP endpoints are accessible

---

## 📞 Support

Need help?
1. Check GitHub Actions logs
2. Review Azure Portal diagnostics
3. Check Application Insights logs
4. See `DEPLOYMENT-v2.5.0.md` for manual deployment
5. Contact Azure Support if needed

---

**Ready to Deploy?** Just commit and push to `main` branch!

```bash
git add .
git commit -m "v2.5.0: Fix functions not appearing in portal"
git push origin main
```

Then watch the magic happen at:
https://github.com/Russ-Holloway/functions-python-web-crawler/actions
