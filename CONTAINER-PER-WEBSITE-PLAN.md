# Container-Per-Website Architecture - Implementation Plan

## Overview
Implement automatic container creation per website for better organization and management.

## Current Structure (v2.5.2)
```
Storage Account: stbtpuksprodcrawler01
├── documents/                    ← All documents in one container
│   ├── crown-prosecution-service/abc123_doc.pdf
│   ├── npcc-publications/def456_report.pdf
│   └── uk-legislation/ghi789_act.xml
└── crawl-metadata/               ← Metadata
    ├── document_hashes.json
    └── crawl_history.json
```

**Problems:**
- All documents mixed in one container
- Hard to manage documents per website
- No clear separation of concerns
- Dashboard shows "Other" for uncategorized docs

## New Structure (v2.6.0)
```
Storage Account: stbtpuksprodcrawler01
├── college-of-policing/          ← One container per website
│   ├── abc123_document.pdf
│   └── def456_guidance.pdf
├── crown-prosecution-service/
│   ├── ghi789_legal-doc.pdf
│   └── jkl012_policy.pdf
├── npcc-publications/
│   ├── mno345_report.pdf
│   └── pqr678_strategy.pdf
├── uk-legislation/
│   ├── stu901_act.xml
│   └── vwx234_si.xml
├── uk-public-general-acts/
│   └── yza567_statute.xml
└── _metadata/                    ← Shared metadata container
    ├── document_hashes.json
    └── crawl_history.json
```

**Benefits:**
✅ Clean separation per website
✅ Easy to manage/delete documents per site
✅ Better organization and scalability
✅ Automatic container creation
✅ No more "Other" category issues
✅ Can set per-container policies/lifecycles

## Implementation Steps

### 1. Add Container Management Functions
```python
def get_container_name_for_website(website_id):
    """Convert website ID to container name"""
    # website_id like "cps_working" → "cps-working"
    return website_id.replace('_', '-').lower()

def ensure_container_exists(container_name, storage_account):
    """Create container if it doesn't exist"""
    # Use Azure Storage REST API
    # PUT /{container}?restype=container
```

### 2. Update Upload Function
```python
def upload_to_blob_storage_real(content, filename, website_id, storage_account):
    """Upload to website-specific container"""
    container = get_container_name_for_website(website_id)
    
    # Ensure container exists
    ensure_container_exists(container, storage_account)
    
    # Upload blob (no more folder prefixes needed!)
    blob_url = f"https://{storage_account}.blob.core.windows.net/{container}/{filename}"
    # ... rest of upload logic
```

### 3. Update Dashboard Statistics
```python
def get_storage_statistics_multi_container(storage_account):
    """Aggregate statistics across all website containers"""
    # List all containers
    # For each container:
    #   - Get container name
    #   - List blobs
    #   - Calculate stats
    # Return aggregated data by website
```

### 4. Update Crawl Activity Function
```python
def crawl_website_activity(site_config):
    """Crawl with website-specific container"""
    website_id = site_config["id"]
    website_name = site_config["name"]
    
    # ... crawl logic ...
    
    # Upload to website-specific container
    result = upload_to_blob_storage_real(
        content=doc_content,
        filename=simple_filename,  # No folder prefix needed!
        website_id=website_id,     # NEW parameter
        storage_account="stbtpuksprodcrawler01"
    )
```

## File Naming Changes

### Old (v2.5.2):
```python
# Filename includes folder prefix
filename = "crown-prosecution-service/abc123_document.pdf"
container = "documents"
```

### New (v2.6.0):
```python
# Simple filename, container is the website
filename = "abc123_document.pdf"
container = "crown-prosecution-service"
```

## Migration Strategy

### Option 1: Fresh Start (Recommended)
1. Deploy v2.6.0 with new container logic
2. Let next crawl populate new containers
3. Old `documents/` container remains as backup
4. Manually delete old container after verification

### Option 2: Migration Script
1. Create script to copy blobs to new containers
2. Parse folder prefix from old filenames
3. Copy to appropriate new container
4. Verify migration
5. Delete old container

**Recommendation:** Option 1 (Fresh Start) because:
- Simpler and less risky
- Next crawl will repopulate everything
- Old data available as backup
- No risk of migration errors

## Dashboard Updates

### Old Display Logic:
```javascript
// Parsed folder prefix from filename
site_folder = blob.name.split('/')[0]
```

### New Display Logic:
```javascript
// Container name IS the website
website_containers.forEach(container => {
    display_name = get_display_name(container.name)
    // Aggregate stats from each container
})
```

## Container Naming Convention

Based on `websites.json` IDs:
```
college_of_policing      → college-of-policing
cps_working              → cps-working
npcc_publications        → npcc-publications
legislation_test_working → legislation-test-working
uk_legislation_future    → uk-legislation-future
```

## Required Changes Summary

### Files to Modify:
1. **function_app.py**
   - Add `ensure_container_exists()` function
   - Add `get_container_name_for_website()` function
   - Update `upload_to_blob_storage_real()` to accept `website_id`
   - Update `crawl_website_activity()` to pass `website_id`
   - Replace `get_storage_statistics()` with multi-container version
   - Update dashboard display logic

2. **websites.json**
   - No changes needed (already has `id` field)

3. **Documentation**
   - Update architecture diagrams
   - Update deployment guide
   - Create migration guide (if needed)

## Testing Plan

1. **Local Testing:**
   - Test container creation function
   - Test upload with new parameters
   - Verify error handling

2. **Deployment Testing:**
   - Deploy to Azure
   - Trigger manual crawl for one website
   - Verify container created automatically
   - Verify blobs uploaded correctly
   - Check dashboard displays correctly

3. **Full System Test:**
   - Wait for scheduled crawl (all websites)
   - Verify all containers created
   - Verify dashboard aggregates correctly
   - Check storage account in portal

## Rollback Plan

If issues occur:
```bash
git revert <commit-hash>
git push origin main
```

Old `documents/` container remains untouched as backup.

## Deployment Checklist

- [ ] Implement container management functions
- [ ] Update upload function signature
- [ ] Update crawl activity function
- [ ] Implement multi-container statistics
- [ ] Update dashboard display
- [ ] Test locally with mock data
- [ ] Update version to v2.6.0
- [ ] Update CHANGELOG and VERSION-TRACKING
- [ ] Create deployment guide
- [ ] Deploy to Azure
- [ ] Test with single website crawl
- [ ] Verify dashboard
- [ ] Monitor scheduled crawl
- [ ] Document new architecture

## Estimated Timeline

- Implementation: 30-45 minutes
- Testing: 15 minutes
- Deployment: 5 minutes
- Verification: 10 minutes

**Total: ~1 hour**

---

**Status:** Ready to implement
**Priority:** High (improves architecture significantly)
**Risk:** Low (old data remains as backup)
