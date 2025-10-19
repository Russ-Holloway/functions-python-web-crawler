# Storage Permissions Fix - HTTP 403 Error

## Problem
Dashboard displays error: **"Storage Error: HTTP Error 403: This request is not authorized to perform this operation using this permission."**

## Root Cause
The Function App's **managed identity** doesn't have the necessary RBAC (Role-Based Access Control) permissions on the storage account `stbtpuksprodcrawler01`.

The application uses **managed identity authentication** to access Azure Blob Storage (which is the secure, recommended approach), but the identity needs explicit permissions assigned.

## What the Dashboard Does
1. `/api/dashboard` → `/api/stats` endpoint
2. Calls `get_storage_statistics()` function
3. Attempts to list blobs in storage account: `https://stbtpuksprodcrawler01.blob.core.windows.net/documents`
4. **Fails with 403** because managed identity lacks permissions

## Solution
Assign the **"Storage Blob Data Contributor"** role to the Function App's managed identity on the storage account.

### Quick Fix (Run in Azure CLI Bash)

```bash
# Make the script executable
chmod +x fix-storage-permissions.sh

# Run the fix script
./fix-storage-permissions.sh
```

### Manual Fix (Alternative)

If you prefer to do it manually via Azure Portal:

1. **Navigate to Storage Account:**
   - Go to Azure Portal
   - Open `stbtpuksprodcrawler01` storage account
   - Select **"Access Control (IAM)"** from left menu

2. **Add Role Assignment:**
   - Click **"+ Add"** → **"Add role assignment"**
   - Select role: **"Storage Blob Data Contributor"**
   - Click **"Next"**

3. **Assign Access:**
   - Select **"Managed identity"**
   - Click **"+ Select members"**
   - Subscription: **96726562-1726-4984-88c6-2e4f28878873**
   - Managed identity: **Function App**
   - Select: **func-btp-uks-prod-doc-crawler-01**
   - Click **"Select"**

4. **Review and Assign:**
   - Click **"Review + assign"**
   - Confirm by clicking **"Review + assign"** again

### Verify the Fix

After assigning permissions:

1. **Wait 1-2 minutes** for role assignment to propagate
2. **Refresh the dashboard** in your browser
3. **Test the endpoint:**
   ```bash
   curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/stats
   ```

If you still see the error:
```bash
# Restart the Function App to refresh token cache
az functionapp restart \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

## Why This Permission is Needed

The function app performs these operations:
- ✅ **Read blobs** - Get crawl history, document hashes
- ✅ **Write blobs** - Upload crawled documents, save metadata
- ✅ **List blobs** - Get storage statistics, count documents
- ✅ **Delete blobs** - (Future) Clean up old documents

**"Storage Blob Data Contributor"** role provides all these permissions.

## Security Notes

✅ **This is secure because:**
- Uses Azure AD authentication (no connection strings)
- Follows principle of least privilege
- Scoped to specific storage account
- Can be audited via Azure Activity Log
- No credentials stored in code or configuration

❌ **DO NOT use:**
- Storage account access keys in app settings
- Connection strings with secrets
- Overly permissive roles like "Contributor" or "Owner"

## Related Files
- `function_app.py` - Lines 188-216: `get_managed_identity_token()`
- `function_app.py` - Lines 217-289: `upload_to_blob_storage_real()`
- `function_app.py` - Lines 778-871: `get_storage_statistics()`

## Technical Details

### Managed Identity Token Flow
1. Function App requests token from `IDENTITY_ENDPOINT` 
2. Azure provides token for resource: `https://storage.azure.com/`
3. Token includes claims based on assigned RBAC roles
4. Token used as Bearer token in Storage REST API calls

### Error Details
```
HTTP/1.1 403 Forbidden
Server: Windows-Azure-Blob/1.0 Microsoft-HTTPAPI/2.0
x-ms-error-code: AuthorizationPermissionMismatch
x-ms-request-id: [...]

<?xml version="1.0" encoding="utf-8"?>
<Error>
  <Code>AuthorizationPermissionMismatch</Code>
  <Message>This request is not authorized to perform this operation using this permission.</Message>
</Error>
```

This error specifically means: "I know who you are (authentication succeeded), but you don't have permission to do this (authorization failed)."

## Verification Commands

```bash
# Check if managed identity is enabled
az functionapp identity show \
  --name func-btp-uks-prod-doc-crawler-01 \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873

# List current role assignments
az role assignment list \
  --scope /subscriptions/96726562-1726-4984-88c6-2e4f28878873/resourceGroups/rg-btp-uks-prod-doc-mon-01/providers/Microsoft.Storage/storageAccounts/stbtpuksprodcrawler01 \
  --output table
```

## Resolution Status
- ⏳ **Status:** Pending - Awaiting role assignment
- 📅 **Date Identified:** 2025-10-19
- 🎯 **Priority:** High - Blocking dashboard functionality
- ⚙️ **Fix:** Run `fix-storage-permissions.sh` script

---

**Quick Command:**
```bash
chmod +x fix-storage-permissions.sh && ./fix-storage-permissions.sh
```
