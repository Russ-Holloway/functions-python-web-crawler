# API Documentation

Complete reference for all Azure Function endpoints in the Web Crawler application.

**Base URL:** `https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net`

---

## Table of Contents

- [Health & Status](#health--status)
- [Crawling Operations](#crawling-operations)
- [Storage & Statistics](#storage--statistics)
- [Website Management](#website-management)
- [Dashboard](#dashboard)

---

## Health & Status

### GET /api/health

Health check endpoint to verify function app is running.

**Authentication:** None

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-20T14:30:00Z",
  "version": "2.6.0"
}
```

**Status Codes:**
- `200` - OK

---

## Crawling Operations

### POST /api/crawl

Trigger a crawl for a specific website.

**Authentication:** None

**Request Body:**
```json
{
  "site_name": "Crown Prosecution Service",
  "force_all": false
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `site_name` | string | Yes | Exact name from websites.json |
| `force_all` | boolean | No | Force re-upload of all documents (default: false) |

**Response:**
```json
{
  "status": "success",
  "site_name": "Crown Prosecution Service",
  "url": "https://www.cps.gov.uk/prosecution-guidance",
  "documents_found": 145,
  "documents_processed": 145,
  "documents_uploaded": 12,
  "documents_unchanged": 133,
  "timestamp": "2025-10-20T14:30:00Z",
  "duration_seconds": 180
}
```

**Status Codes:**
- `200` - Crawl completed successfully
- `400` - Invalid site_name or missing parameter
- `404` - Website not found in configuration
- `500` - Server error during crawl

**Example:**
```bash
curl -X POST https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"site_name": "Crown Prosecution Service", "force_all": false}'
```

---

### POST /api/crawl_all

Trigger crawls for all enabled websites sequentially.

**Authentication:** None

**Request Body:** None (optional empty JSON `{}`)

**Response:**
```json
{
  "status": "success",
  "total_sites": 5,
  "sites_crawled": 5,
  "sites_failed": 0,
  "total_documents_uploaded": 47,
  "results": [
    {
      "site_name": "College of Policing - App Portal",
      "status": "success",
      "documents_uploaded": 15,
      "duration_seconds": 120
    },
    {
      "site_name": "Crown Prosecution Service",
      "status": "success",
      "documents_uploaded": 12,
      "duration_seconds": 180
    }
  ],
  "timestamp": "2025-10-20T14:35:00Z",
  "total_duration_seconds": 900
}
```

**Status Codes:**
- `200` - All crawls completed (check individual statuses)
- `500` - Critical error preventing crawl execution

**Example:**
```bash
curl -X POST https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl_all
```

**Note:** This operation can take several minutes depending on the number of websites and documents.

---

### GET /api/crawl_status

Get status of currently running crawl (if any).

**Authentication:** None

**Response:**
```json
{
  "is_crawling": true,
  "current_site": "Crown Prosecution Service",
  "progress": {
    "documents_processed": 45,
    "documents_uploaded": 5,
    "elapsed_seconds": 60
  }
}
```

Or if no crawl is running:
```json
{
  "is_crawling": false,
  "message": "No active crawl"
}
```

**Status Codes:**
- `200` - OK

---

### GET /api/crawl_history

Get history of recent crawls.

**Authentication:** None

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Number of records to return (default: 10, max: 100) |

**Response:**
```json
{
  "history": [
    {
      "site_name": "Crown Prosecution Service",
      "timestamp": "2025-10-20T14:30:00Z",
      "documents_found": 145,
      "documents_uploaded": 12,
      "duration_seconds": 180,
      "status": "success"
    },
    {
      "site_name": "College of Policing - App Portal",
      "timestamp": "2025-10-20T10:00:00Z",
      "documents_found": 98,
      "documents_uploaded": 15,
      "duration_seconds": 120,
      "status": "success"
    }
  ],
  "total_records": 47,
  "limit": 10
}
```

**Status Codes:**
- `200` - OK

**Example:**
```bash
curl "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl_history?limit=5"
```

---

### POST /api/initialize_folders

Create folder structure in storage for all configured websites. This is a one-time initialization step after deployment.

**Authentication:** None

**Request Body:** None (optional empty JSON `{}`)

**Response:**
```json
{
  "message": "Folder initialization complete",
  "total_websites": 8,
  "success_count": 8,
  "fail_count": 0,
  "results": [
    {
      "website": "College of Policing - App Portal",
      "status": "success",
      "folder": "college-of-policing---app-portal"
    },
    {
      "website": "Crown Prosecution Service",
      "status": "success",
      "folder": "crown-prosecution-service"
    }
  ],
  "timestamp": "2025-10-20T14:00:00Z"
}
```

**Status Codes:**
- `200` - Initialization completed
- `500` - Error during initialization

**Example:**
```bash
curl -X POST https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/initialize_folders
```

**Note:** This should be called once after deploying a new version or adding new websites to websites.json.

---

## Storage & Statistics

### GET /api/stats

Get comprehensive storage statistics and system metrics.

**Authentication:** None

**Response:**
```json
{
  "storage": {
    "total_documents": 487,
    "total_size_bytes": 2684354560,
    "total_size_mb": 2560.25,
    "site_breakdown": {
      "Crown Prosecution Service": {
        "count": 145,
        "size": 524288000,
        "size_mb": 500.0,
        "folder": "crown-prosecution-service",
        "files": [...]
      },
      "College of Policing - App Portal": {
        "count": 98,
        "size": 314572800,
        "size_mb": 300.0,
        "folder": "college-of-policing---app-portal",
        "files": [...]
      }
    },
    "container": "documents",
    "storage_account": "stbtpuksprodcrawler01"
  },
  "system": {
    "version": "2.6.0",
    "uptime_seconds": 86400,
    "last_crawl": "2025-10-20T14:30:00Z"
  },
  "timestamp": "2025-10-20T15:00:00Z"
}
```

**Status Codes:**
- `200` - OK
- `500` - Error retrieving statistics

**Example:**
```bash
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/stats
```

---

## Website Management

### GET /api/manage_websites

Get list of all configured websites and their status.

**Authentication:** None

**Response:**
```json
{
  "message": "Multi-website crawler configuration",
  "enabled_sites": [
    {
      "id": "cps_working",
      "name": "Crown Prosecution Service",
      "url": "https://www.cps.gov.uk/prosecution-guidance",
      "enabled": true,
      "description": "CPS prosecution guidance and legal policies",
      "document_types": ["pdf", "doc", "docx", "xml", "html"],
      "crawl_depth": "deep",
      "priority": "high",
      "multi_level": true,
      "max_depth": 2
    }
  ],
  "disabled_sites": [
    {
      "id": "test_site",
      "name": "Test Website",
      "enabled": false
    }
  ],
  "total_enabled": 5,
  "total_disabled": 2,
  "next_scheduled_run": "Every 4 hours at 12:00 AM, 4:00 AM, 8:00 AM, 12:00 PM, 4:00 PM, 8:00 PM"
}
```

**Status Codes:**
- `200` - OK

**Example:**
```bash
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/manage_websites
```

---

## Dashboard

### GET /api/dashboard

Web-based dashboard UI for monitoring and management.

**Authentication:** None

**Response:** HTML page with:
- Storage statistics
- Document counts per website
- Recent crawl history
- System status
- Quick action buttons

**Example:**
Open in browser:
```
https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/dashboard
```

---

## Error Responses

All endpoints may return error responses in this format:

```json
{
  "error": "Error description",
  "details": "Additional context if available",
  "timestamp": "2025-10-20T15:00:00Z"
}
```

**Common Status Codes:**
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error
- `503` - Service Unavailable (temporary failure)

---

## Rate Limiting

**Current Implementation:** None

**Recommendations:**
- Avoid triggering multiple `/api/crawl_all` requests simultaneously
- Use `/api/crawl_status` to check if crawl is in progress before triggering new crawl
- Respect source website rate limits

---

## Blob Storage Direct Access

### Document URL Pattern

Documents can be accessed directly via Azure Storage URLs:

```
https://stbtpuksprodcrawler01.blob.core.windows.net/documents/
  {website-folder}/{hash}_{filename}.{ext}
```

**Example:**
```
https://stbtpuksprodcrawler01.blob.core.windows.net/documents/
  crown-prosecution-service/abc123_guidance-2025.pdf
```

**Note:** Storage account must have appropriate access configured (currently requires authentication).

---

## Metadata Queries (Future)

With Azure AI Search integration, you'll be able to query documents by metadata:

```
// Get all PDFs from CPS uploaded in last 30 days
GET /api/search?filter=websiteid eq 'cps_working' 
  and documenttype eq 'application/pdf' 
  and crawldate ge '2025-09-20'
```

---

## Webhook Integration (Future)

Planned webhook support for crawl notifications:

```json
POST https://your-endpoint.com/webhook
{
  "event": "crawl_completed",
  "site_name": "Crown Prosecution Service",
  "documents_uploaded": 12,
  "timestamp": "2025-10-20T14:30:00Z"
}
```

---

## Best Practices

### For Automated Systems

1. **Check Status First:** Call `/api/crawl_status` before triggering new crawls
2. **Use Single Site Crawls:** Prefer `/api/crawl` over `/api/crawl_all` for targeted updates
3. **Monitor History:** Use `/api/crawl_history` to track success/failure patterns
4. **Handle Errors:** Implement retry logic with exponential backoff
5. **Respect Timing:** Don't trigger crawls more frequently than source data updates

### For Monitoring

1. **Health Checks:** Call `/api/health` for liveness probes
2. **Statistics:** Monitor `/api/stats` for storage growth
3. **Dashboard:** Use `/api/dashboard` for human-readable overview
4. **Application Insights:** Review Azure Application Insights for detailed telemetry

---

## SDK Examples

### Python

```python
import requests

# Trigger a crawl
response = requests.post(
    'https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl',
    json={'site_name': 'Crown Prosecution Service', 'force_all': False}
)
result = response.json()
print(f"Uploaded {result['documents_uploaded']} documents")

# Get statistics
stats = requests.get(
    'https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/stats'
).json()
print(f"Total documents: {stats['storage']['total_documents']}")
```

### PowerShell

```powershell
# Trigger a crawl
$body = @{
    site_name = "Crown Prosecution Service"
    force_all = $false
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"

Write-Host "Uploaded $($response.documents_uploaded) documents"
```

### Bash/curl

```bash
# Trigger a crawl
curl -X POST \
  https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"site_name":"Crown Prosecution Service","force_all":false}' \
  | jq '.documents_uploaded'

# Get statistics
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/stats \
  | jq '.storage.total_documents'
```

---

## Changelog

### v2.6.0 (Current)
- Added `/api/initialize_folders` endpoint
- Enhanced storage statistics with dynamic website mapping
- Added rich blob metadata support
- Improved folder-based organization

### v2.5.x
- Added managed identity authentication
- Fixed dashboard categorization
- Improved error handling

---

**Last Updated:** October 20, 2025  
**API Version:** 2.6.0  
**Base URL:** https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net
