## Functions Python Web Crawler Changelog

<a name="2.6.0"></a>
# 2.6.0 (2025-10-19)

*Major Enhancement*
* **Smart Storage Organization:** Implemented automatic folder creation for each website in single `documents/` container
* **AI-Ready Metadata:** Added rich blob metadata (websiteid, websitename, crawldate, documenttype, etc.) to every uploaded document for Azure AI Search compatibility
* **Dynamic Dashboard:** Storage statistics now load website configurations from `websites.json` for accurate, maintainable categorization
* **Folder Initialization:** New `/api/initialize_folders` endpoint to create folder structure for all configured websites at once

*Features*
* **Automatic Folder Management:**
  - `get_folder_name_for_website()` - Converts website names to sanitized folder names
  - `ensure_website_folder_exists()` - Creates folders with metadata placeholder files (.folder)
  - Folders automatically created on first crawl of any website
* **Rich Metadata Support:**
  - Every blob gets x-ms-meta headers: websiteid, websitename, crawldate
  - Custom metadata support: documenttype, originalfilename, status, documenturl
  - Metadata enables powerful AI search filtering without multiple containers
* **Dynamic Configuration:**
  - Dashboard stats load from `websites.json` instead of hardcoded mappings
  - Automatically adapts when websites are added/removed
  - Folder-to-displayname mapping built dynamically

*API Changes*
* **New Endpoint:** `POST /api/initialize_folders` - Creates folder structure for all websites
* **Enhanced Function:** `upload_to_blob_storage_real()` - Now accepts website_id, website_name, and metadata parameters
* **Updated Function:** `crawl_website_core()` - Automatically ensures folder exists before crawling

*Architecture Benefits*
* **AI Search Ready:** Single container perfect for Azure AI Search, Azure OpenAI, RAG solutions
* **Rich Filtering:** Query documents by website, date, type using blob metadata
* **Visual Organization:** Clear folder structure visible in Azure Portal
* **No Breaking Changes:** Existing documents remain accessible, new crawls use enhanced structure

*Files Modified*
* `function_app.py` - Lines 217-289 (folder management), Lines 291-365 (metadata upload), Lines 666-670 (auto folder creation), Lines 942-975 (dynamic stats), Lines 2782-2842 (initialization endpoint)
* `VERSION-TRACKING.md` - Updated to v2.6.0

*Deployment Notes*
After deploying v2.6.0, call the initialization endpoint to create folders for existing websites:
```bash
curl -X POST https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/initialize_folders
```

---

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
