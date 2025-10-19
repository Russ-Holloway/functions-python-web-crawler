# 🚨 IMMEDIATE ACTION REQUIRED - Disable Authentication via Azure Portal

## Current Status

✅ **Your deployment is successful** - All functions are deployed and working  
🔒 **App Service Authentication is blocking access** - Returning 401 on all requests  
⚠️ **Azure CLI not available in Codespace** - Must use Azure Portal instead

---

## 🚀 FIX NOW - Azure Portal (5 minutes)

### Step 1: Open Azure Portal

Go to: **https://portal.azure.com**

### Step 2: Navigate to Your Function App

1. In the search bar at the top, type: `func-btp-uks-prod-doc-crawler-01`
2. Click on your Function App in the results
3. You should see your Function App overview page

### Step 3: Disable Authentication

**Option A - If you see "Authentication" in left menu:**

1. In the left sidebar, scroll down to **Settings** section
2. Click: **Authentication**
3. You'll see "Identity provider" configured (probably "Microsoft")
4. Click: **Delete** or click on the provider and then **Delete**
5. Confirm deletion
6. Click: **Save** at the top

**Option B - If you see "Authentication/Authorization":**

1. In the left sidebar, find: **Authentication/Authorization** (under Settings)
2. At the top, you'll see: **App Service Authentication**
3. Toggle it to: **Off**
4. Click: **Save** at the top

### Step 4: Wait 1-2 Minutes

The changes need time to propagate across Azure infrastructure.

### Step 5: Test It Works

After waiting 1-2 minutes, test from your Codespace:

```bash
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/ping
```

**Expected Response** (when working):
```json
{
  "status": "alive",
  "message": "Function app is running",
  "timestamp": "2025-10-19T...",
  "version": "v2.4.2"
}
```

---

## 📊 Check Functions in Portal

Once authentication is disabled:

1. Stay in Function App
2. Left sidebar: Click **Functions**
3. **You should now see all 20+ functions listed!**

Functions you should see:
- `ping` (HTTP GET)
- `dashboard` (HTTP GET)
- `websites` (HTTP GET)
- `manual_crawl` (HTTP POST)
- `search_site` (HTTP GET)
- `api_stats` (HTTP GET)
- `web_crawler_orchestrator` (Orchestration)
- `scheduled_crawler_orchestrated` (Timer)
- `scheduled_crawler` (Timer)
- And 11+ more functions...

---

## 🔍 Visual Guide - What to Look For

### In Authentication Settings Page

You might see something like:

```
App Service Authentication: [On/Off Toggle]
┌─────────────────────────────────────┐
│ Identity provider: Microsoft        │
│ Require authentication: Yes         │
│ Action to take: Redirect            │
│                                     │
│ [Delete] [Edit]                    │
└─────────────────────────────────────┘
```

**Action**: Delete the provider OR toggle authentication to OFF

### After Disabling

The page should show:
```
App Service Authentication: Off
No identity providers configured
```

---

## ⚡ Alternative - Use Azure Cloud Shell

If you have trouble with the portal:

1. Click the **Cloud Shell** icon (>_) at the top of Azure Portal
2. Choose **Bash**
3. Run this command:

```bash
az webapp auth update \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --enabled false
```

---

## ✅ Success Indicators

After disabling authentication:

1. **HTTP Status Changes**:
   - Before: 401 (Unauthorized)
   - After: 200 (OK) with JSON response

2. **Functions List**:
   - Before: May be empty or hidden
   - After: Shows all 20+ functions

3. **Test Endpoints Work**:
   ```bash
   # All should return 200 OK
   curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/ping
   curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/websites
   curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard
   ```

---

## 🎯 Why This is Happening

**Your code is 100% correct!** The issue is:

1. ✅ You have: `auth_level=func.AuthLevel.ANONYMOUS` in code
2. ✅ GitHub Actions deployment succeeded
3. ✅ All functions deployed properly
4. 🔒 BUT: Azure Platform Authentication is enabled (separate setting)
5. 🔒 Platform auth **overrides** function-level auth settings
6. 🔒 Result: All requests blocked with 401

**The deployment is perfect. Just need to turn off that one platform setting.**

---

## 📱 Need Help?

If you're stuck:

1. Take a screenshot of the Authentication page
2. Look for any toggle switches or Delete buttons
3. The key is to find where it says "Authentication" or "App Service Authentication"
4. Turn it OFF or DELETE the identity provider

---

## 🎉 What Happens After Fix

Within 1-2 minutes of disabling authentication:

- ✅ All HTTP endpoints become accessible
- ✅ Function list appears in portal
- ✅ Timer triggers start running
- ✅ Durable orchestrations work
- ✅ Full operational capability

**Your Function App will be fully working!**

---

**NEXT STEP**: Go to Azure Portal and disable authentication now!

https://portal.azure.com → func-btp-uks-prod-doc-crawler-01 → Authentication → Turn OFF
