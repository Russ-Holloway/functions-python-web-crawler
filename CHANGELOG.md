## Functions Python Web Crawler Changelog

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
