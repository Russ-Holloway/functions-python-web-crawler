# Cleanup Uncategorized Documents - Quick Guide

## Overview
This guide helps you clean up any "Other" or uncategorized documents in your storage account. These are documents that don't have a proper folder structure (no folder prefix). After deletion, they'll be re-crawled with the correct classification on the next scheduled run.

---

## Why Clean Up?

**Problem:** Old documents without folder structure appear as "Other" or "Uncategorized (Legacy)" in the dashboard.

**Solution:** Delete them and let the next crawl re-download them with proper folder structure.

**Benefits:**
- ✅ Clean dashboard with accurate categorization
- ✅ All documents properly organized by website
- ✅ Consistent folder structure across all files
- ✅ Next crawl will detect them as "new" and re-download with correct paths

---

## Step 1: Check What Will Be Deleted (DRY RUN)

First, see which files will be deleted WITHOUT actually deleting them:

### Using curl:
```bash
# Set your function URL
FUNCTION_URL="your-function-app.azurewebsites.net"

# List uncategorized documents (dry run - safe)
curl "https://${FUNCTION_URL}/api/cleanup_uncategorized" | jq .
```

### Expected Response:
```json
{
  "message": "DRY RUN: Found 15 uncategorized documents",
  "count": 15,
  "total_size_mb": 5.3,
  "files": [
    {
      "name": "old-document.pdf",
      "size": 524288,
      "size_mb": 0.5
    },
    {
      "name": "legacy-file.xml",
      "size": 102400,
      "size_mb": 0.1
    }
  ],
  "dry_run": true,
  "note": "Set dry_run=false to actually delete these files"
}
```

**Review the list carefully!** These files will be deleted in Step 2.

---

## Step 2: Delete Uncategorized Documents

Once you've reviewed the list and confirmed you want to delete them:

### Using curl:
```bash
# Actually delete uncategorized documents
curl -X POST "https://${FUNCTION_URL}/api/cleanup_uncategorized" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}' | jq .
```

### Expected Response:
```json
{
  "message": "Deleted 15 uncategorized documents",
  "deleted_count": 15,
  "failed_count": 0,
  "total_size_mb": 5.3,
  "deleted_files": [
    {
      "name": "old-document.pdf",
      "size": 524288,
      "size_mb": 0.5
    }
  ],
  "failed_deletions": [],
  "dry_run": false,
  "timestamp": "2025-10-21T14:30:00Z"
}
```

---

## Step 3: Verify Cleanup

Check the dashboard to confirm "Other" category is gone or reduced:

```bash
# Check dashboard
curl "https://${FUNCTION_URL}/api/dashboard"

# Check storage stats
curl "https://${FUNCTION_URL}/api/storage_stats" | jq .
```

---

## Step 4: Wait for Next Crawl

The deleted documents will be re-downloaded on the next scheduled crawl (every 4 hours) with proper folder structure.

### Monitor the crawl:
```bash
# Check when next crawl will run
# Crawls happen every 4 hours: 12:00 AM, 4:00 AM, 8:00 AM, 12:00 PM, 4:00 PM, 8:00 PM

# Monitor Azure function logs
az webapp log tail \
  --name YOUR_FUNCTION_APP \
  --resource-group YOUR_RESOURCE_GROUP \
  --subscription YOUR_SUBSCRIPTION_ID
```

### What to look for:
- ✅ Documents detected as "new" (they were deleted, so they're new again)
- ✅ Documents uploaded with proper folder structure (e.g., `crown-prosecution-service/abc123_doc.pdf`)
- ✅ Dashboard shows all documents under correct website categories

---

## Alternative: Trigger Manual Crawl

Don't want to wait? Trigger a manual crawl immediately:

```bash
# Trigger manual crawl
curl -X POST "https://${FUNCTION_URL}/api/manual_crawl" \
  -H "Content-Type: application/json" \
  -d '{"websites": ["all"]}' | jq .
```

This will:
1. Crawl all enabled websites
2. Detect deleted documents as "new"
3. Re-download them with proper folder structure
4. Update the dashboard immediately

---

## Complete Workflow (Copy-Paste Ready)

```bash
# STEP 1: Set your function URL
FUNCTION_URL="your-function-app.azurewebsites.net"

# STEP 2: Check what will be deleted (safe dry run)
echo "=== Checking for uncategorized documents ==="
curl "https://${FUNCTION_URL}/api/cleanup_uncategorized" | jq .

# STEP 3: Review the output above, then delete if confirmed
read -p "Do you want to delete these files? (yes/no) " -n 3 -r
echo
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]
then
    echo "=== Deleting uncategorized documents ==="
    curl -X POST "https://${FUNCTION_URL}/api/cleanup_uncategorized" \
      -H "Content-Type: application/json" \
      -d '{"dry_run": false}' | jq .
fi

# STEP 4: Verify cleanup
echo "=== Checking dashboard ==="
curl "https://${FUNCTION_URL}/api/dashboard"

# STEP 5: Trigger manual crawl to re-download (optional)
read -p "Trigger manual crawl now? (yes/no) " -n 3 -r
echo
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]
then
    echo "=== Triggering manual crawl ==="
    curl -X POST "https://${FUNCTION_URL}/api/manual_crawl" \
      -H "Content-Type: application/json" \
      -d '{"websites": ["all"]}' | jq .
fi
```

---

## Safety Features

### Built-in Protections:
1. ✅ **Dry run by default** - GET and POST default to dry_run=true
2. ✅ **System files protected** - Never deletes `document_hashes.json`, `crawl_history.json`, or `.folder` files
3. ✅ **Only targets uncategorized** - Only deletes files without `/` in the name
4. ✅ **Detailed logging** - Every deletion is logged with timestamp
5. ✅ **Failure tracking** - Reports which files failed to delete (if any)

### What Gets Deleted:
- ❌ Files without folder prefix: `old-file.pdf`
- ✅ Files with folder prefix: `crown-prosecution-service/abc123_doc.pdf` (KEPT)
- ✅ System files: `document_hashes.json` (KEPT)
- ✅ Folder placeholders: `website-name/.folder` (KEPT)

---

## Troubleshooting

### No Uncategorized Documents Found
```json
{
  "message": "No uncategorized documents found",
  "count": 0,
  "files": [],
  "dry_run": true
}
```
**Meaning:** All documents already have proper folder structure. Nothing to clean up!

### Some Deletions Failed
```json
{
  "deleted_count": 12,
  "failed_count": 3,
  "failed_deletions": [
    {
      "file": "locked-file.pdf",
      "reason": "HTTP 403"
    }
  ]
}
```
**Solution:** Check Azure Portal for file locks or permissions issues.

### Authentication Error
```json
{
  "error": "Authentication failed"
}
```
**Solution:** Ensure the Function App has Managed Identity enabled and Storage Blob Data Contributor role.

---

## After Cleanup

### Expected Results:
1. ✅ Dashboard shows no "Other" or "Uncategorized (Legacy)" category
2. ✅ All documents categorized under correct website names
3. ✅ Reduced total document count (temporarily, until next crawl)
4. ✅ Clean, organized storage structure

### Next Crawl Will:
1. 🔄 Detect deleted documents as "missing"
2. 📥 Download them again (marked as "new")
3. 📁 Store with proper folder structure
4. ✅ Dashboard updates with correct categorization

---

## Questions?

**Q: Will this delete documents permanently?**  
A: Yes from storage, but they'll be re-downloaded on the next crawl from the source websites.

**Q: What if I want to keep some uncategorized files?**  
A: Use the dry run first, review the list, then manually delete specific files from Azure Portal instead.

**Q: How long until documents are re-downloaded?**  
A: Next scheduled crawl (every 4 hours) or trigger manual crawl immediately.

**Q: Will document hashes be reset?**  
A: No, the hash database is preserved. Re-downloaded documents will match their previous hashes.

---

**Created:** October 21, 2025  
**Version:** v2.7.0  
**Purpose:** Clean up legacy uncategorized documents
