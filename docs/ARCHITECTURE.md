# System Architecture

## Overview

The Azure Functions Python Web Crawler is a serverless document crawling and storage solution designed to automatically discover, download, and organize documents from multiple websites with AI-ready metadata tagging.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                         │
│                    (Auto-deploy on push)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ GitHub Actions
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Azure Function App (Python 3.11)                    │
│  func-btp-uks-prod-doc-crawler-01 (UK South)                   │
│                                                                  │
│  Functions:                                                      │
│  • /api/crawl - Trigger website crawl                          │
│  • /api/crawl_all - Crawl all enabled websites                 │
│  • /api/initialize_folders - Create folder structure           │
│  • /api/stats - Storage statistics                             │
│  • /api/dashboard - Web dashboard                              │
│  • /api/manage_websites - Website management                   │
│  • /api/health - Health check                                  │
└──────────────┬──────────────────────────────────┬───────────────┘
               │                                  │
               │ Managed Identity                 │ Managed Identity
               │ (Storage Blob Data Contributor)  │ (Storage Blob Data Reader)
               ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│           Azure Storage Account (stbtpuksprodcrawler01)         │
│                                                                  │
│  Container: documents/                                          │
│  ├── college-of-policing---app-portal/                         │
│  │   ├── .folder (metadata placeholder)                        │
│  │   └── abc123_document.pdf (+ blob metadata)                 │
│  ├── crown-prosecution-service/                                │
│  │   ├── .folder                                               │
│  │   └── def456_guidance.pdf (+ blob metadata)                 │
│  ├── uk-legislation-test---working/                            │
│  │   ├── .folder                                               │
│  │   └── ghi789_act.xml (+ blob metadata)                      │
│  └── [other website folders...]                                │
│                                                                  │
│  System Files:                                                  │
│  ├── document_hashes.json - Change detection                   │
│  └── crawl_history.json - Crawl audit log                      │
└─────────────────────────────────────────────────────────────────┘
               │
               │ (Future Integration)
               ▼
┌─────────────────────────────────────────────────────────────────┐
│              Azure AI Search / OpenAI                           │
│  • Single datasource (documents/ container)                     │
│  • Metadata filtering (by website, date, type)                 │
│  • RAG (Retrieval-Augmented Generation)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Azure Function App

**Resource:** `func-btp-uks-prod-doc-crawler-01`  
**Region:** UK South  
**Runtime:** Python 3.11  
**Trigger:** HTTP (Timer scheduled via external system)

**Key Features:**
- Serverless auto-scaling
- Managed Identity authentication
- Application Insights monitoring
- GitHub Actions CI/CD

### 2. Azure Storage Account

**Resource:** `stbtpuksprodcrawler01`  
**Container:** `documents`  
**Access:** Managed Identity (RBAC)

**Storage Organization:**
```
documents/
├── [website-folder]/
│   ├── .folder                    # Metadata placeholder
│   └── [hash]_[filename].[ext]    # Document with metadata
```

**Folder Naming Convention:**
- Website name sanitized to lowercase
- Spaces → dashes
- Special chars removed
- Example: "Crown Prosecution Service" → "crown-prosecution-service"

### 3. Blob Metadata Schema

Every document blob includes x-ms-meta headers:

| Metadata Key | Description | Example |
|-------------|-------------|---------|
| `websiteid` | Website identifier from config | `cps_working` |
| `websitename` | Display name of website | `Crown Prosecution Service` |
| `crawldate` | ISO timestamp of crawl | `2025-10-20T14:30:00Z` |
| `documenttype` | MIME type | `application/pdf` |
| `originalfilename` | Original filename before hashing | `guidance-2025.pdf` |
| `status` | Change status | `new`, `changed`, `unchanged` |
| `documenturl` | Source URL | `https://...` |

**Benefits:**
- Enables metadata filtering without database
- AI search can filter by website, date, type
- Single container simplifies Azure AI Search indexing
- No performance impact on document retrieval

---

## Data Flow

### Document Crawl Flow

```
1. Trigger
   └─> /api/crawl (POST with site_name)
   
2. Website Discovery
   └─> Load websites.json
   └─> Find matching website config
   
3. Folder Initialization
   └─> ensure_website_folder_exists()
   └─> Create .folder placeholder if needed
   
4. Page Crawling
   └─> Fetch HTML from website
   └─> Parse for document links (PDF, DOC, XML, etc.)
   └─> Follow multi-level links (if enabled)
   
5. Document Processing
   └─> Download document content
   └─> Calculate SHA-256 hash
   └─> Check against document_hashes.json
   └─> Determine status: new/changed/unchanged
   
6. Storage Upload
   └─> Generate unique filename: [folder]/[hash]_[name].[ext]
   └─> Attach blob metadata (websiteid, websitename, etc.)
   └─> Upload to Azure Storage
   
7. History & Hashing
   └─> Update document_hashes.json
   └─> Append to crawl_history.json
   └─> Return summary statistics
```

### Dashboard Statistics Flow

```
1. Request
   └─> /api/stats
   
2. Enumerate Blobs
   └─> List all blobs in documents/ container
   └─> Skip system files (document_hashes.json, etc.)
   
3. Dynamic Categorization
   └─> Load websites.json
   └─> Build folder → display name mapping
   └─> Extract folder prefix from blob names
   └─> Group documents by website
   
4. Response
   └─> Total documents count
   └─> Total storage size
   └─> Per-website breakdown with counts and sizes
```

---

## Storage Strategy

### Why Single Container + Folders?

**Chosen Approach:** Single `documents/` container with website-specific folders

**Alternatives Considered:**
1. ❌ **Container per website** - Azure AI Search limitation (single datasource)
2. ❌ **Flat structure** - Poor organization, difficult navigation
3. ✅ **Folders + Metadata** - Best of both worlds

**Benefits:**
- ✅ Azure AI Search can index entire container as single datasource
- ✅ Visual organization in Azure Portal
- ✅ Metadata enables powerful filtering
- ✅ Easy to navigate and manage
- ✅ RAG solutions can filter by website using metadata
- ✅ No performance penalty vs containers

---

## Change Detection

### Hash-Based Change Detection

**System:** `document_hashes.json` in storage root

**Structure:**
```json
{
  "https://example.com/doc.pdf": {
    "hash": "abc123...",
    "filename": "abc123_doc.pdf",
    "last_seen": "2025-10-20T14:30:00Z",
    "size": 1048576
  }
}
```

**Process:**
1. Download document content
2. Calculate SHA-256 hash
3. Compare with stored hash
4. Status:
   - **new** - URL never seen before
   - **changed** - Hash differs from stored
   - **unchanged** - Hash matches stored

**Benefits:**
- Avoids re-uploading unchanged documents
- Detects updated documents
- Tracks document history
- Reduces storage costs and bandwidth

---

## Security

### Authentication & Authorization

**Function App Access:**
- Public endpoints: `AuthLevel.ANONYMOUS`
- No API keys required for read operations
- Managed Identity for Azure resource access

**Storage Access:**
- Managed Identity (no connection strings)
- RBAC role: `Storage Blob Data Contributor`
- Principle of least privilege

### Network Security

**Current:** Public endpoints
**Future Consideration:** 
- VNet integration
- Private endpoints
- Application Gateway with WAF

---

## Scalability

### Current Capacity

- **Concurrent crawls:** 1 at a time (single orchestration)
- **Documents per crawl:** Unlimited (memory efficient streaming)
- **Storage:** Practically unlimited (Azure Blob)
- **Function scaling:** Auto-scale based on load

### Future Enhancements

1. **Parallel Crawling:** Azure Durable Functions orchestration
2. **Queue-Based:** Decouple crawl triggers from processing
3. **Batch Processing:** Process documents in parallel activities
4. **CDN:** Azure CDN for frequently accessed documents

---

## Monitoring & Observability

### Application Insights

**Telemetry:**
- Function execution times
- Success/failure rates
- Exception tracking
- Custom metrics (documents processed, upload times)

**Logging:**
- Structured logging with severity levels
- Crawl start/end timestamps
- Document processing status
- Error diagnostics

### Dashboards

**Built-in Dashboard:**
- `/api/dashboard` - Web UI
- `/api/stats` - JSON statistics
- Real-time storage metrics
- Per-website breakdown

---

## AI Integration (Future)

### Azure AI Search

**Configuration:**
```
Datasource: Azure Blob Storage (documents/ container)
Index: Include all metadata fields
Skillset: Optional (OCR, entity extraction)
```

**Query Examples:**
```
// Documents from specific website
filter: metadata_websiteid eq 'cps_working'

// Documents from last 30 days
filter: metadata_crawldate ge '2025-09-20'

// PDF documents only
filter: metadata_documenttype eq 'application/pdf'
```

### Azure OpenAI (RAG)

**Setup:**
```
Data Source: Azure AI Search index
Embedding: ada-002
Model: gpt-4o
```

**Benefits:**
- Ask questions across all documents
- Cite sources with website context
- Filter responses by website
- Understand document relationships

---

## Deployment Architecture

### CI/CD Pipeline

```
Developer
  └─> git push origin main
      └─> GitHub Actions triggered
          └─> Build Python app
          └─> Create deployment ZIP
          └─> Deploy to Azure (az functionapp deployment)
          └─> Remote build on Azure
          └─> Function app updated
```

**Deployment Time:** 3-5 minutes  
**Zero Downtime:** Yes (rolling deployment)  
**Rollback:** Git revert + automatic redeploy

---

## Configuration Management

### Environment Variables

Managed in Azure Portal Function App Configuration:

| Variable | Purpose | Example |
|----------|---------|---------|
| `WEBSITES_CONFIG_LOCATION` | Config source | `local` |
| `WEBSITE_HTTPLOGGING_RETENTION_DAYS` | Log retention | `7` |
| `AZURE_SUBSCRIPTION_ID` | Subscription | `96726562-...` |

### websites.json

**Purpose:** Centralized website configuration  
**Location:** Repository root (deployed with app)  
**Format:** JSON array of website objects

**Schema:**
```json
{
  "id": "unique_identifier",
  "name": "Display Name",
  "url": "https://...",
  "enabled": true/false,
  "document_types": ["pdf", "doc", "xml"],
  "crawl_depth": "single|deep",
  "multi_level": true/false,
  "max_depth": 1-3
}
```

---

## Resource Naming Convention

**Pattern:** `[type]-[project]-[region]-[env]-[purpose]-[instance]`

**Examples:**
- `func-btp-uks-prod-doc-crawler-01` - Function App
- `stbtpuksprodcrawler01` - Storage Account (24 char limit, no dashes)
- `rg-btp-uks-prod-doc-mon-01` - Resource Group

**Legend:**
- `func` = Function App
- `st` = Storage Account
- `rg` = Resource Group
- `btp` = British Transport Police (project)
- `uks` = UK South (region)
- `prod` = Production (environment)
- `doc` = Document (workload)
- `crawler/mon` = Specific purpose
- `01` = Instance number

---

## Cost Optimization

### Current Costs (Estimated)

| Resource | Tier | Monthly Cost |
|----------|------|--------------|
| Function App | Consumption | ~£5-10 |
| Storage (100GB) | Standard LRS | ~£2 |
| Application Insights | Basic | ~£3 |
| **Total** | | **~£10-15/month** |

### Cost-Saving Strategies

1. **Efficient Change Detection** - Only upload changed documents
2. **Consumption Plan** - Pay only for execution time
3. **Storage Lifecycle** - Archive old versions
4. **Bandwidth** - Single region deployment

---

## Disaster Recovery

### Backup Strategy

**Code:** Git repository (GitHub)  
**Configuration:** Documented in repository  
**Data:** 
- Storage account replication (LRS)
- Periodic export of document_hashes.json
- Crawl history in blob storage

### Recovery Procedures

**Function App Failure:**
1. Redeploy from GitHub Actions
2. Restore configuration from documentation
3. ETA: 10 minutes

**Storage Corruption:**
1. Re-run crawls for affected websites
2. Rebuild document_hashes.json
3. ETA: 2-4 hours (depending on volume)

---

## Performance Characteristics

### Benchmarks

| Metric | Value |
|--------|-------|
| Cold start | 3-5 seconds |
| Warm execution | <1 second |
| Document download | 2-10 seconds (depends on source) |
| Hash calculation | 100ms per MB |
| Upload to storage | 1-5 seconds per document |
| **Avg documents/minute** | **10-20** |

### Bottlenecks

1. **Source website response time** - Mitigated by timeout settings
2. **Document size** - Large PDFs take longer to hash/upload
3. **Network latency** - Single region deployment minimizes this

---

## Future Enhancements

### Planned Features

1. **Durable Functions Orchestration** - Parallel processing
2. **Advanced Scheduling** - Configurable cron triggers
3. **Document Classification** - ML-based categorization
4. **Duplicate Detection** - Content similarity analysis
5. **Format Conversion** - PDF → Text extraction
6. **Search API** - Built-in document search
7. **Webhook Notifications** - Crawl completion alerts
8. **Multi-Region** - Geographic distribution

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Runtime | Python | 3.11 |
| Framework | Azure Functions | v2 |
| Storage SDK | Azure Storage Blob | 12.x |
| Auth | Azure Identity | 1.x |
| Deployment | GitHub Actions | N/A |
| Monitoring | Application Insights | N/A |
| Web Scraping | urllib, BeautifulSoup | stdlib + 4.x |

---

**Last Updated:** October 20, 2025  
**Version:** 2.6.0
