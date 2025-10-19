# Functions Not Appearing - Diagnostic Guide

## Current Status
✅ Authentication fixed (404 instead of 401)  
❌ Functions not registered (404 on all endpoints)

## What This Means
- Authentication is working correctly
- The deployment succeeded
- **BUT** Azure isn't discovering the functions in `function_app.py`

## Common Causes

### 1. **Python Worker Not Starting**
The Azure Functions Python worker may not be initializing properly.

**Check in Azure Portal:**
1. Go to your Function App: `func-btp-uks-prod-doc-crawler-01`
2. Click **"Functions"** in left menu
3. Do you see **any** functions listed?
   - If **NO** → Python worker issue
   - If **YES** but grayed out → Extension bundle issue

### 2. **Wrong Python Version**
**Check in Azure Portal:**
1. Function App → **Configuration** → **General settings**
2. Check **"Python Version"**
   - Should be: **Python 3.11** or **Python 3.12**
   - If it's 3.8 or 3.9 → **This is the problem**

**How to Fix:**
- Go to Configuration → General settings
- Change Python Version to **3.11**
- Click **Save**
- Wait 2-3 minutes for restart

### 3. **Extension Bundle Version Mismatch**
Your `host.json` uses bundle `[4.*, 5.0.0)` which requires Python 3.11+

**Check logs in Azure Portal:**
1. Function App → **Log stream** (in Monitoring section)
2. Look for errors mentioning:
   - "extension bundle"
   - "incompatible"
   - "python version"

### 4. **Deployment Package Missing function_app.py**
**Verify in Azure Portal:**
1. Function App → **Advanced Tools** → **Go**
2. In Kudu, click **Debug console** → **CMD**
3. Navigate to: `site/wwwroot`
4. Check if `function_app.py` exists
5. Check file size (should be ~89KB for 2685 lines)

**If missing or wrong size:**
- GitHub Actions deployment may have failed
- Re-run the deployment workflow

### 5. **Application Settings Issue**
**Required Setting:**

In Azure Portal → Configuration → Application settings, verify:

```
Name: FUNCTIONS_WORKER_RUNTIME
Value: python
```

**If missing or wrong:**
1. Click **New application setting**
2. Name: `FUNCTIONS_WORKER_RUNTIME`
3. Value: `python`
4. Click **OK** then **Save**

## Quick Diagnostic Checklist

Run through these in order:

- [ ] **Step 1:** Check Functions list in portal (Function App → Functions)
  - Expected: Should see 20+ functions
  - If empty → Continue to Step 2

- [ ] **Step 2:** Check Python version (Configuration → General settings)
  - Expected: Python 3.11 or 3.12
  - If wrong → Change to 3.11 and save

- [ ] **Step 3:** Check FUNCTIONS_WORKER_RUNTIME (Configuration → Application settings)
  - Expected: `python`
  - If missing → Add it

- [ ] **Step 4:** Check Log Stream (Monitoring → Log stream)
  - Look for startup errors
  - Look for "Function app started" message

- [ ] **Step 5:** Restart Function App
  - Click **Restart** button at top
  - Wait 2-3 minutes
  - Check Functions list again

- [ ] **Step 6:** Check deployed files (Advanced Tools → Kudu)
  - Verify `function_app.py` exists in `site/wwwroot`
  - Verify `host.json` exists
  - Verify `requirements.txt` exists

## Most Likely Solution

Based on similar issues, **99% of the time** this is caused by:

1. **Wrong Python version** (using 3.8 or 3.9 instead of 3.11+)
2. **Missing FUNCTIONS_WORKER_RUNTIME setting**

## After Fixing

Once you make changes:
1. Click **Restart** on the Function App
2. Wait 2-3 minutes
3. Test: `curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/ping`
4. Should get JSON response: `{"status": "ok", "message": "..."}`

## Need Help?

If none of these work, please share:
1. Screenshot of Functions list (empty or not)
2. Screenshot of Configuration → General settings (Python version)
3. Screenshot of Configuration → Application settings (FUNCTIONS_WORKER_RUNTIME)
4. Any error messages from Log stream
