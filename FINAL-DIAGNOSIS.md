# Functions Not Appearing - Final Diagnosis

## Current Status
✅ **Function App is RUNNING** (HTTP 200 response)  
✅ **Authentication is configured correctly** (no 401 errors)  
✅ **Python version is correct** (3.11 in workflow, 3.11 in portal)  
✅ **All required settings are present**  
❌ **Functions are NOT being loaded/discovered by runtime**

## The Problem

When you visit the function app URL, you get the default **"Your Azure Function App is up and running"** HTML page. This is what Azure shows when:

1. ✅ The function app **is running**
2. ❌ But **ZERO functions** are registered/discovered

This means the Python worker is **not finding** or **not loading** your `function_app.py`.

## Root Cause Analysis

Based on your environment settings, I can see:

```
"ENABLE_ORYX_BUILD": "1"
"SCM_DO_BUILD_DURING_DEPLOYMENT": "false"  
```

**This is the problem!**

When `SCM_DO_BUILD_DURING_DEPLOYMENT` is `false`, Azure **expects a pre-built package** from GitHub Actions. But your GitHub Actions workflow is:

1. ❌ **Not installing the Azure Functions Core Tools**
2. ❌ **Not running `func extensions install`** 
3. ❌ **Just zipping everything**

This means the deployment package is **incomplete** - it's missing the compiled extensions that the Python v2 model needs!

## The Fix

You have **two options**:

### Option A: Let Azure Build (RECOMMENDED)

Change the app setting in Azure Portal:

1. Go to **Configuration** → **Application settings**
2. Find `SCM_DO_BUILD_DURING_DEPLOYMENT`
3. Change value from `false` to `true`
4. Click **Save**
5. **Restart** the Function App
6. Re-run your GitHub Actions deployment

This tells Azure to **build the function app on the server** after deployment.

### Option B: Fix GitHub Actions (More Complex)

Update your `.github/workflows/main_func-btp-uks-prod-doc-crawler-01.yml`:

```yaml
- name: Install Azure Functions Core Tools
  run: |
    wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb
    sudo dpkg -i packages-microsoft-prod.deb
    sudo apt-get update
    sudo apt-get install azure-functions-core-tools-4

- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    
- name: Install function extensions
  run: |
    func extensions install --python
```

But this is **much more complex** and error-prone.

## Why This Happened

Your original deployment was probably done **through VS Code** or **Azure CLI**, which automatically:
- Built the extensions
- Packaged everything correctly

But when GitHub Actions deployed, it just **zipped and uploaded** the raw files without building.

## Recommended Action

**Do Option A** (easiest and most reliable):

1. Portal → Configuration → Application settings
2. Change `SCM_DO_BUILD_DURING_DEPLOYMENT` from `false` to `true`
3. Save
4. Restart Function App
5. Re-deploy from GitHub Actions (push a commit or manually trigger)

After 2-3 minutes, your functions should appear!

## Verification Steps

After making the change:

```bash
# Wait 2-3 minutes after restart, then test:
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/ping
```

You should get JSON like:
```json
{"status": "ok", "message": "..."}
```

## Why Functions Still Won't Appear in Portal

Even after this fix, functions **may not appear** in the Portal's **Functions** list if you're using Python v2 model with `SCM_DO_BUILD_DURING_DEPLOYMENT=true`.

**This is normal!** The functions **will work** via API even if they don't show in the portal list.

To verify they work:
- Test API endpoints directly
- Check Application Insights logs
- Use `curl` commands

The portal's Functions list has **known issues** with Python v2 + remote build deployments.
