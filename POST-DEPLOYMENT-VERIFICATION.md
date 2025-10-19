# v2.4.0 Post-Deployment Verification

## ✅ DEPLOYED: January 17, 2025

---

## Immediate Verification Steps

### 1. Check Function App Status

Visit Azure Portal and verify:
- ✅ Function app `func-btp-uks-prod-doc-crawler-01` is **Running**
- ✅ Deployment completed successfully
- ✅ No errors in deployment logs

**Or in Azure CLI Bash:**
```bash
az functionapp show \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "{name:name, state:state}" \
  --output table
```

**Expected**: `state: Running`

---

### 2. Check Dashboard (Now)

**URL**: `https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard`

**Look For:**
- ✅ Dashboard loads successfully
- ✅ New **"Storage Validation (Phase 2)"** card is visible
- ✅ "Recent Activity" section shows **collision count field** (even if no data yet)
- ✅ No errors displayed

**Screenshot**: Take a screenshot for reference

---

### 3. Check API Stats

Visit: `https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/api/stats`

**Look For New Fields:**
```json
{
  "recent_activity": {
    "collisions_detected_24h": 0  // New field
  },
  "validation": {  // New section
    "last_check": "...",
    "status": "unknown",  // Will be "match" after first crawl
    "uploaded_count": 0,
    "storage_count": 0,
    "accuracy_percentage": 0
  }
}
```

---

## Wait for Next Scheduled Crawl

### Scheduled Crawl Timing
- **Frequency**: Every 4 hours
- **Next Crawl**: Check Azure Function logs for next scheduled run time

### What to Expect
After the next crawl completes, Phase 2 metrics will populate:
- **Collision Count**: Should be **0** (zero collisions expected)
- **Validation Status**: Should be **MATCH**
- **Accuracy**: Should be **100%** or very close
- **Storage Count** should equal **Uploaded Count**

---

## Validation Checklist (After First Crawl)

### Dashboard Metrics
Visit dashboard after crawl completes:

- [ ] ✅ **Collision Count = 0** (Critical - no filename duplicates)
- [ ] ✅ **Validation Status = MATCH** (Storage count equals upload count)
- [ ] ✅ **Accuracy = 100%** (or 99.9%+)
- [ ] ✅ **Storage Count = Uploaded Count** (No document loss)
- [ ] ✅ **Collisions Detected (24h) = 0** in Recent Activity

### Application Insights (Optional)
Check logs for Phase 2 activity:
```
Search for: "validate_storage_activity"
Search for: "collision"
Search for: "Phase 2"
```

**Look For:**
- Validation activity execution
- No collision warnings
- Successful validation completion

---

## Success Criteria

v2.4.0 is **successfully validated** when:

1. ✅ Function app is running
2. ✅ Dashboard displays Phase 2 validation card
3. ✅ At least one scheduled crawl completed
4. ✅ **Collision count = 0** (no hash duplicates)
5. ✅ **Validation status = MATCH** (no data loss)
6. ✅ **Accuracy = 100%** (storage matches uploads)
7. ✅ No errors in logs

---

## Timeline

| Time | Action | Status |
|------|--------|--------|
| **Now** | Deployment complete | ✅ Done |
| **Now + 5 min** | Verify dashboard displays | ⏳ Check |
| **Next crawl** | Wait for scheduled run | ⏳ Waiting |
| **After crawl** | Verify Phase 2 metrics | ⏳ Pending |
| **+24-48 hours** | Monitor stability | ⏳ Pending |
| **After stable** | Run cleanup | ⏳ Pending |

---

## What Phase 2 Monitors

### 1. Collision Detection
**Purpose**: Ensure Phase 1's unique filename fix works  
**Expected**: 0 collisions (MD5 hash prevents duplicates)  
**Alert**: If > 0, indicates hash collision (very rare)

### 2. Storage Validation
**Purpose**: Confirm all uploaded documents are in storage  
**Expected**: MATCH status, 100% accuracy  
**Alert**: If MISMATCH, indicates storage issue

### 3. Dashboard Visibility
**Purpose**: Real-time monitoring of system health  
**Expected**: All metrics display correctly  
**Alert**: Missing data indicates problem

---

## Troubleshooting

### Dashboard Not Loading
- Check function app is running
- Check Application Insights for errors
- Verify network connectivity

### Phase 2 Card Not Visible
- Hard refresh browser (Ctrl+F5)
- Clear browser cache
- Check `/api/stats` endpoint directly

### Validation Shows "Unknown"
- Normal before first crawl
- Will populate after scheduled crawl runs
- Check back in 4 hours

### Collisions Detected (> 0)
- **URGENT**: This should not happen
- Review Application Insights logs
- Check for hash generation errors
- Contact support if persistent

---

## Next Steps

### Immediate (Now)
1. ✅ Verify dashboard loads
2. ✅ Confirm Phase 2 card visible
3. ✅ Check API endpoint for new fields

### Short Term (Next 4-24 Hours)
4. ⏳ Wait for next scheduled crawl
5. ⏳ Verify validation metrics populate
6. ⏳ Confirm 0 collisions
7. ⏳ Confirm MATCH status

### After Validation (24-48 Hours)
8. ⏳ Run cleanup checklist
9. ⏳ Archive deployment package
10. ⏳ Update CHANGELOG.md
11. ⏳ Update VERSION-TRACKING.md

---

## Cleanup Reminder

**Only run cleanup after v2.4.0 is verified stable!**

See: `CLEANUP-CHECKLIST-v2.4.0.md`

Commands to run:
```bash
# Delete old PHASE-* documentation
rm PHASE-1-DEPLOYMENT-BASH.md
rm PHASE-1-SUMMARY.md
rm PHASE-1-COMPLETION.md
rm PHASE-1-VERIFICATION-REPORT.md
rm PHASE-2-PLAN.md
rm PHASE-2-DEPLOYMENT-BASH.md
rm PHASE-2-COMPLETION.md
rm CORRECTED-DEPLOYMENT-COMMANDS.txt

# Archive deployment package (optional)
Move-Item v2.4.0-deployment.zip archive\

# Update documentation
# - CHANGELOG.md: Add deployment date
# - VERSION-TRACKING.md: Update status to "Deployed"
```

---

## Quick Reference

**Dashboard**: https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard  
**API Stats**: https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/api/stats  
**Cleanup Guide**: `CLEANUP-CHECKLIST-v2.4.0.md`  
**Version Tracking**: `VERSION-TRACKING.md`

---

**Deployment Status**: ✅ **COMPLETE**  
**Verification Status**: ⏳ **PENDING** (Check dashboard now)  
**Next Action**: Verify dashboard displays Phase 2 card  
**Date**: January 17, 2025
