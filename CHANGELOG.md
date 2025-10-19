## Functions Python Web Crawler Changelog

<a name="2.5.2"></a>
# 2.5.2 (2025-10-19)

*Features*
* **Dashboard:** Enhanced storage statistics to display documents grouped by actual website names instead of generic categories
* **UI:** Improved document source labels for better clarity (e.g., "Crown Prosecution Service" instead of "CPS")

*Technical Changes*
* Updated `get_storage_statistics()` to extract folder prefix from filenames for accurate categorization
* Changed from keyword-based matching to folder structure-based categorization
* Simplified dashboard JavaScript display logic
* Added proper mapping from sanitized folder names to display names

*Files Modified*
* `function_app.py` - Storage categorization logic and dashboard display

---

<a name="2.5.1"></a>
# 2.5.1 (2025-10-19)

*Bug Fixes*
* **Storage Permissions:** Fixed HTTP 403 error on dashboard by assigning "Storage Blob Data Contributor" role to Function App's managed identity on storage account `stbtpuksprodcrawler01`
* **Dashboard:** Storage statistics and crawl history now loading correctly
* **API:** `/api/stats` endpoint returning complete data including storage metrics

*Configuration Changes*
* Added RBAC role assignment for storage account access
* No code changes required - configuration-only fix

*Documentation*
* Added `STORAGE-PERMISSIONS-FIX.md` - Detailed permissions documentation
* Added `fix-storage-permissions.sh` - Automated permission fix script
* Added `FIX-COMMANDS.txt` - Manual command reference

---

<a name="2.5.0"></a>
# 2.5.0 (2025-10-19)

*Bug Fixes*
* **Critical:** Fixed functions not appearing in Azure Portal
* **Deployment:** Switched from Azure Functions GitHub Action to Azure CLI zip deploy with `--build-remote` flag
* **Configuration:** Removed problematic `WEBSITE_RUN_FROM_PACKAGE` setting that was preventing function discovery
* **Authentication:** Changed App Service Authentication to "Allow unauthenticated access" for anonymous function access

*Features*
* All 20+ functions now visible and operational in Azure Portal
* Functions returning proper JSON responses from API endpoints
* Durable Functions orchestration working correctly

*Breaking Changes*
* Deployment method changed: Now uses Azure CLI instead of Azure Functions GitHub Action
* GitHub Actions workflow updated to use `az functionapp deployment source config-zip`

---

<a name="x.y.z"></a>
# x.y.z (yyyy-mm-dd)

*Features*
* ...

*Bug Fixes*
* ...

*Breaking Changes*
* ...
