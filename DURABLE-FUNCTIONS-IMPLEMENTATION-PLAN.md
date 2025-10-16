# Durable Functions Implementation Plan
## Web Crawler Orchestrator Upgrade

**Date Created:** October 16, 2025  
**Current Version:** v2.2.0  
**Target Version:** v3.0.0 (Durable Functions)

---

## Executive Summary

This plan outlines the step-by-step process to upgrade the existing web crawler Azure Function to use **Azure Durable Functions** with an orchestrator pattern. The orchestrator will manage multiple website crawls in parallel, reading configurations from a settings file, and invoking the existing crawler logic as activity functions.

### Key Benefits
- **Scalability**: Parallel execution of multiple website crawls
- **Reliability**: Built-in retry logic and checkpointing
- **Maintainability**: Separation of orchestration logic from business logic
- **Monitoring**: Better tracking and observability of crawl operations
- **Flexibility**: Easy to add/remove websites without code changes

---

## Current Architecture Overview

### Existing Components
1. **Timer Trigger**: `scheduled_crawler` - Runs every 4 hours
2. **HTTP Triggers**: `manual_crawl`, `search_site`, `status`, etc.
3. **Core Functions**:
   - `get_enabled_websites()` - Returns hardcoded website configurations
   - HTML parsing and document detection
   - Hash-based change detection
   - Azure Blob Storage integration (Managed Identity)
   - Crawl history tracking

### Current Website Configuration
Currently defined in `get_enabled_websites()` function with enabled sites:
- College of Policing (App Portal)
- Crown Prosecution Service (CPS)
- UK Legislation Test
- NPCC Publications
- UK Public General Acts

---

## Target Architecture

### New Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Timer Trigger                           │
│                  (Every 4 hours)                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Durable Orchestrator Function                  │
│                                                             │
│  1. Read websites.json configuration                       │
│  2. Start parallel activity functions                      │
│  3. Monitor and aggregate results                          │
│  4. Handle failures and retries                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┬──────────────┐
         │              │              │              │
         ▼              ▼              ▼              ▼
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│ Activity 1 │  │ Activity 2 │  │ Activity 3 │  │ Activity N │
│  (CPS)     │  │  (NPCC)    │  │ (College)  │  │   (...)    │
└────────────┘  └────────────┘  └────────────┘  └────────────┘
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│           Azure Blob Storage (Managed Identity)             │
│  • Document storage                                         │
│  • Hash tracking (document_hashes.json)                    │
│  • Crawl history                                           │
│  • Configuration (websites.json)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Phase 1: Prerequisites and Setup

#### Step 1.1: Install Durable Functions SDK
**Location**: `requirements.txt`

**Action**: Add the Azure Durable Functions package

```bash
# Current requirements.txt
azure-functions
requests

# Updated requirements.txt
azure-functions
azure-functions-durable>=1.2.9
requests
```

**Verification**:
```powershell
pip install -r requirements.txt
```

**Expected Output**: Successfully installed azure-functions-durable

---

#### Step 1.2: Update host.json Configuration
**Location**: `host.json`

**Current Configuration**:
```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 20
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[3.*, 4.0.0)"
  }
}
```

**Updated Configuration**:
```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 20
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  },
  "extensions": {
    "durableTask": {
      "hubName": "WebCrawlerHub",
      "storageProvider": {
        "connectionStringName": "AzureWebJobsStorage"
      },
      "maxConcurrentActivityFunctions": 10,
      "maxConcurrentOrchestratorFunctions": 5
    }
  }
}
```

**Key Changes**:
- Updated extension bundle to `[4.*, 5.0.0)` (Azure best practice)
- Added `durableTask` configuration section
- Set `maxConcurrentActivityFunctions` to 10 (allows parallel website crawls)
- Named the hub `WebCrawlerHub` for identification

---

#### Step 1.3: Create Website Configuration File
**Location**: Create new file `websites.json`

**Purpose**: Externalize website configurations for easy management without code changes

**Structure**:
```json
{
  "version": "1.0.0",
  "last_updated": "2025-10-16T00:00:00Z",
  "websites": [
    {
      "id": "college_of_policing",
      "name": "College of Policing - App Portal",
      "url": "https://www.college.police.uk/app",
      "enabled": true,
      "description": "College of Policing app portal",
      "document_types": ["pdf", "doc", "docx", "xml"],
      "crawl_depth": "deep",
      "priority": "high",
      "multi_level": false,
      "max_depth": 1
    },
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
    },
    {
      "id": "legislation_test_working",
      "name": "UK Legislation (Test - Working)",
      "url": "https://www.legislation.gov.uk/uksi/2024/1052/contents",
      "enabled": true,
      "description": "UK legislation test site",
      "document_types": ["pdf", "xml"],
      "crawl_depth": "single",
      "priority": "baseline",
      "multi_level": false,
      "max_depth": 1
    },
    {
      "id": "npcc_publications",
      "name": "NPCC Publications - All Publications",
      "url": "https://www.npcc.police.uk/publications/All-publications/",
      "enabled": true,
      "description": "NPCC All Publications page",
      "document_types": ["pdf", "doc", "docx", "xml"],
      "crawl_depth": "deep",
      "priority": "high",
      "multi_level": true,
      "max_depth": 2
    },
    {
      "id": "uk_legislation_future",
      "name": "UK Public General Acts",
      "url": "https://www.legislation.gov.uk/ukpga",
      "enabled": true,
      "description": "UK Public General Acts from all years",
      "document_types": ["pdf", "xml", "html"],
      "crawl_depth": "deep",
      "priority": "high",
      "multi_level": true,
      "max_depth": 2
    },
    {
      "id": "npcc_future",
      "name": "National Police Chiefs' Council",
      "url": "https://www.npcc.police.uk/",
      "enabled": false,
      "description": "NPCC guidance - disabled for now",
      "document_types": ["pdf", "doc", "docx", "xml"],
      "crawl_depth": "deep",
      "priority": "high",
      "multi_level": false,
      "max_depth": 1
    },
    {
      "id": "cps_future",
      "name": "Crown Prosecution Service",
      "url": "https://www.cps.gov.uk/",
      "enabled": false,
      "description": "CPS legal guidance - disabled for now",
      "document_types": ["pdf", "doc", "docx", "xml"],
      "crawl_depth": "deep",
      "priority": "high",
      "multi_level": false,
      "max_depth": 1
    },
    {
      "id": "gov_uk_future",
      "name": "GOV.UK",
      "url": "https://www.gov.uk/",
      "enabled": false,
      "description": "UK government guidance and publications",
      "document_types": ["pdf", "doc", "docx", "csv", "xml"],
      "crawl_depth": "deep",
      "priority": "high",
      "multi_level": false,
      "max_depth": 1
    }
  ]
}
```

**Deployment Note**: This file should be:
1. Stored locally in the project root during development
2. Optionally uploaded to Azure Blob Storage for production (recommended)
3. Environment variable `WEBSITES_CONFIG_LOCATION` can specify: `local` or `blob`

---

### Phase 2: Code Refactoring

#### Step 2.1: Extract Core Crawler Logic
**Location**: `function_app.py`

**Action**: Create a standalone function that can be called by the activity function

**Current State**: The crawler logic is embedded in `scheduled_crawler()` timer function

**New Function**:
```python
def crawl_website_core(website_config: dict) -> dict:
    """
    Core crawler logic extracted for reuse by activity functions
    
    Args:
        website_config: Dictionary containing website configuration
            {
                "id": "site_id",
                "name": "Site Name",
                "url": "https://example.com",
                "enabled": true,
                "document_types": ["pdf", "xml"],
                "crawl_depth": "deep",
                "priority": "high",
                "multi_level": true,
                "max_depth": 2
            }
    
    Returns:
        Dictionary with crawl results:
            {
                "website_id": "site_id",
                "website_name": "Site Name",
                "website_url": "https://example.com",
                "success": true,
                "documents_found": 15,
                "new_documents": 3,
                "updated_documents": 1,
                "unchanged_documents": 11,
                "errors": [],
                "start_time": "2025-10-16T10:00:00Z",
                "end_time": "2025-10-16T10:05:23Z",
                "duration_seconds": 323.45
            }
    """
    start_time = datetime.now(timezone.utc)
    
    try:
        # Step 1: Initialize result structure
        result = {
            "website_id": website_config["id"],
            "website_name": website_config["name"],
            "website_url": website_config["url"],
            "success": False,
            "documents_found": 0,
            "new_documents": 0,
            "updated_documents": 0,
            "unchanged_documents": 0,
            "errors": [],
            "start_time": start_time.isoformat()
        }
        
        # Step 2: Perform the actual crawl
        # (Insert existing crawler logic here - HTML parsing, document detection, etc.)
        # This will be the bulk of code from the current scheduled_crawler function
        
        # Step 3: Calculate duration
        end_time = datetime.now(timezone.utc)
        result["end_time"] = end_time.isoformat()
        result["duration_seconds"] = (end_time - start_time).total_seconds()
        result["success"] = True
        
        return result
        
    except Exception as e:
        logging.error(f'Crawler error for {website_config["name"]}: {str(e)}')
        end_time = datetime.now(timezone.utc)
        return {
            **result,
            "success": False,
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
            "errors": [str(e)]
        }
```

**Migration Checklist**:
- [ ] Extract HTML parsing logic
- [ ] Extract document detection logic
- [ ] Extract hash calculation logic
- [ ] Extract blob storage upload logic
- [ ] Extract change detection logic
- [ ] Add proper error handling
- [ ] Add logging statements
- [ ] Return structured results

---

#### Step 2.2: Create Configuration Reader Function
**Location**: `function_app.py`

**Action**: Replace hardcoded `get_enabled_websites()` with dynamic config reader

**New Function**:
```python
def load_websites_config(location: str = "local") -> list:
    """
    Load website configurations from file
    
    Args:
        location: Where to load from - "local" or "blob"
            - "local": Load from websites.json in project root
            - "blob": Load from Azure Blob Storage
    
    Returns:
        List of enabled website configurations
    """
    try:
        if location == "local":
            # Load from local file
            config_path = os.path.join(os.path.dirname(__file__), "websites.json")
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        
        elif location == "blob":
            # Load from Azure Blob Storage
            storage_account = os.environ.get("STORAGE_ACCOUNT_NAME", "stbtpuksprodcrawler01")
            container = "configuration"  # New container for config files
            filename = "websites.json"
            
            # Use Managed Identity to download
            access_token = get_managed_identity_token()
            url = f"https://{storage_account}.blob.core.windows.net/{container}/{filename}"
            
            request = urllib.request.Request(url)
            request.add_header('Authorization', f'Bearer {access_token}')
            request.add_header('x-ms-version', '2021-08-06')
            
            with urllib.request.urlopen(request) as response:
                config_data = json.loads(response.read().decode('utf-8'))
        
        else:
            raise ValueError(f"Unknown location: {location}")
        
        # Filter for enabled websites only
        enabled_websites = [
            site for site in config_data.get("websites", [])
            if site.get("enabled", False)
        ]
        
        logging.info(f'Loaded {len(enabled_websites)} enabled websites from {location}')
        return enabled_websites
        
    except Exception as e:
        logging.error(f'Failed to load websites config from {location}: {str(e)}')
        # Fallback to original hardcoded function
        return get_enabled_websites()
```

**Environment Variable**:
Add to `local.settings.json`:
```json
{
  "Values": {
    "WEBSITES_CONFIG_LOCATION": "local"
  }
}
```

---

### Phase 3: Durable Functions Implementation

#### Step 3.1: Create Activity Function
**Location**: `function_app.py`

**Action**: Add activity function that wraps the core crawler logic

**Code**:
```python
@app.activity_trigger(input_name="websiteConfig")
def crawl_website_activity(websiteConfig: dict) -> dict:
    """
    Activity function to crawl a single website
    
    This function is called by the orchestrator for each website
    It wraps the core crawler logic and returns structured results
    
    Args:
        websiteConfig: Website configuration dictionary
    
    Returns:
        Crawl result dictionary
    """
    logging.info(f'Activity: Starting crawl for {websiteConfig.get("name")}')
    
    try:
        # Call the core crawler logic
        result = crawl_website_core(websiteConfig)
        
        logging.info(
            f'Activity: Completed crawl for {websiteConfig.get("name")} - '
            f'Found {result.get("documents_found", 0)} documents'
        )
        
        return result
        
    except Exception as e:
        logging.error(f'Activity: Error crawling {websiteConfig.get("name")}: {str(e)}')
        return {
            "website_id": websiteConfig.get("id", "unknown"),
            "website_name": websiteConfig.get("name", "unknown"),
            "website_url": websiteConfig.get("url", "unknown"),
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
```

**Key Points**:
- Decorated with `@app.activity_trigger`
- Accepts website configuration as input
- Calls `crawl_website_core()` for actual work
- Returns structured results for orchestrator
- Has error handling and logging

---

#### Step 3.2: Create Orchestrator Function
**Location**: `function_app.py`

**Action**: Add the main orchestrator function

**Code**:
```python
import azure.durable_functions as df

@app.orchestration_trigger(context_name="context")
def crawler_orchestrator(context: df.DurableOrchestrationContext):
    """
    Orchestrator function to coordinate website crawls
    
    Flow:
    1. Load website configurations
    2. Fan-out: Start activity function for each enabled website
    3. Fan-in: Wait for all activities to complete
    4. Aggregate and store results
    5. Return summary
    """
    
    # Step 1: Get orchestration input (can include overrides)
    orchestration_input = context.get_input()
    config_location = orchestration_input.get("config_location", "local") if orchestration_input else "local"
    
    logging.info(f'Orchestrator: Starting web crawler orchestration')
    
    try:
        # Step 2: Load website configurations
        # Note: In orchestrators, we need to be careful about non-deterministic operations
        # We'll load this via an activity function to keep the orchestrator deterministic
        websites = yield context.call_activity("load_config_activity", config_location)
        
        logging.info(f'Orchestrator: Loaded {len(websites)} enabled websites')
        
        # Step 3: Fan-out - Create parallel tasks for each website
        parallel_tasks = []
        for website in websites:
            task = context.call_activity("crawl_website_activity", website)
            parallel_tasks.append(task)
        
        logging.info(f'Orchestrator: Starting {len(parallel_tasks)} parallel crawl tasks')
        
        # Step 4: Fan-in - Wait for all tasks to complete
        results = yield context.task_all(parallel_tasks)
        
        # Step 5: Aggregate results
        summary = {
            "orchestration_id": context.instance_id,
            "start_time": context.current_utc_datetime.isoformat(),
            "total_websites": len(websites),
            "successful_crawls": sum(1 for r in results if r.get("success", False)),
            "failed_crawls": sum(1 for r in results if not r.get("success", False)),
            "total_documents_found": sum(r.get("documents_found", 0) for r in results),
            "total_new_documents": sum(r.get("new_documents", 0) for r in results),
            "total_updated_documents": sum(r.get("updated_documents", 0) for r in results),
            "website_results": results
        }
        
        logging.info(
            f'Orchestrator: Completed - {summary["successful_crawls"]}/{summary["total_websites"]} successful, '
            f'{summary["total_new_documents"]} new documents found'
        )
        
        # Step 6: Store aggregated results (via activity to maintain determinism)
        yield context.call_activity("store_orchestration_results", summary)
        
        return summary
        
    except Exception as e:
        logging.error(f'Orchestrator: Fatal error: {str(e)}')
        return {
            "success": False,
            "error": str(e),
            "orchestration_id": context.instance_id
        }
```

**Orchestrator Best Practices Applied**:
- ✅ Deterministic: Uses activity functions for I/O operations
- ✅ Fan-out/Fan-in pattern: Parallel execution with aggregation
- ✅ Error handling: Graceful degradation
- ✅ Logging: Comprehensive tracking
- ✅ Returns structured results

---

#### Step 3.3: Create Supporting Activity Functions
**Location**: `function_app.py`

**Action**: Add helper activity functions for orchestrator

**Code**:
```python
@app.activity_trigger(input_name="configLocation")
def load_config_activity(configLocation: str) -> list:
    """
    Activity function to load website configurations
    
    This is separated into an activity to keep the orchestrator deterministic
    """
    logging.info(f'Activity: Loading website configurations from {configLocation}')
    
    websites = load_websites_config(configLocation)
    
    logging.info(f'Activity: Loaded {len(websites)} enabled websites')
    return websites


@app.activity_trigger(input_name="summary")
def store_orchestration_results(summary: dict) -> bool:
    """
    Activity function to store orchestration results
    
    Stores the aggregated crawl results to blob storage for history/audit
    """
    logging.info(f'Activity: Storing orchestration results for {summary.get("orchestration_id")}')
    
    try:
        storage_account = os.environ.get("STORAGE_ACCOUNT_NAME", "stbtpuksprodcrawler01")
        container = "documents"
        
        # Create filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"orchestration_results_{timestamp}_{summary.get('orchestration_id', 'unknown')}.json"
        
        # Upload to blob storage
        content = json.dumps(summary, indent=2).encode('utf-8')
        success = upload_to_blob_storage_real(content, filename, storage_account, container)
        
        if success:
            logging.info(f'Activity: Successfully stored orchestration results to {filename}')
        else:
            logging.error(f'Activity: Failed to store orchestration results')
        
        return success
        
    except Exception as e:
        logging.error(f'Activity: Error storing orchestration results: {str(e)}')
        return False
```

---

#### Step 3.4: Update Timer Trigger
**Location**: `function_app.py`

**Action**: Modify the existing timer trigger to start the orchestrator instead of running the crawler directly

**Current Code**:
```python
@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False)
def scheduled_crawler(mytimer: func.TimerRequest) -> None:
    """Scheduled multi-website document crawler - runs every 4 hours"""
    # ... existing crawler logic ...
```

**New Code**:
```python
@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False)
async def scheduled_crawler_trigger(mytimer: func.TimerRequest, starter: str) -> None:
    """
    Timer trigger to start the durable orchestration
    Runs every 4 hours at 12:00 AM, 4:00 AM, 8:00 AM, 12:00 PM, 4:00 PM, 8:00 PM
    """
    logging.info('Timer trigger: Starting scheduled web crawler orchestration')
    
    client = df.DurableOrchestrationClient(starter)
    
    # Start the orchestrator with configuration
    instance_id = await client.start_new(
        orchestration_function_name="crawler_orchestrator",
        client_input={
            "config_location": os.environ.get("WEBSITES_CONFIG_LOCATION", "local"),
            "trigger_type": "timer",
            "trigger_time": datetime.now(timezone.utc).isoformat()
        }
    )
    
    logging.info(f'Timer trigger: Started orchestration with ID: {instance_id}')
    
    # Optionally check status
    status = await client.get_status(instance_id)
    logging.info(f'Timer trigger: Orchestration status: {status.runtime_status}')
```

**Important Changes**:
- Function is now `async`
- Accepts `starter: str` parameter for durable client
- Creates `DurableOrchestrationClient`
- Starts new orchestration instance
- Logs instance ID for tracking

**Binding Configuration**:
The `starter` parameter is automatically bound by the Durable Functions framework when you:
1. Have `azure-functions-durable` installed
2. Have proper `host.json` configuration
3. Use Python v2 programming model

---

#### Step 3.5: Add HTTP Trigger for Manual Orchestration
**Location**: `function_app.py`

**Action**: Create HTTP endpoint to manually trigger orchestration

**Code**:
```python
@app.route(route="start_crawler", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def start_crawler_orchestration(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    """
    HTTP trigger to manually start the crawler orchestration
    
    POST /api/start_crawler
    Body (optional):
    {
        "config_location": "local" or "blob",
        "instance_id": "optional-custom-id"
    }
    """
    logging.info('HTTP trigger: Manual orchestration start requested')
    
    try:
        # Parse request body
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}
        
        config_location = req_body.get("config_location", 
                                       os.environ.get("WEBSITES_CONFIG_LOCATION", "local"))
        custom_instance_id = req_body.get("instance_id")
        
        # Create orchestration client
        client = df.DurableOrchestrationClient(starter)
        
        # Start orchestration
        instance_id = await client.start_new(
            orchestration_function_name="crawler_orchestrator",
            client_input={
                "config_location": config_location,
                "trigger_type": "manual_http",
                "trigger_time": datetime.now(timezone.utc).isoformat()
            },
            instance_id=custom_instance_id
        )
        
        logging.info(f'HTTP trigger: Started orchestration {instance_id}')
        
        # Get status
        status = await client.get_status(instance_id)
        
        # Create response with status check URL
        response = {
            "message": "Crawler orchestration started",
            "instance_id": instance_id,
            "runtime_status": status.runtime_status,
            "check_status_url": req.url.replace("/start_crawler", f"/orchestration_status/{instance_id}"),
            "config_location": config_location
        }
        
        return func.HttpResponse(
            json.dumps(response, indent=2),
            status_code=202,  # Accepted
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f'HTTP trigger: Error starting orchestration: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="orchestration_status/{instance_id}", methods=["GET"], 
          auth_level=func.AuthLevel.ANONYMOUS)
async def get_orchestration_status(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    """
    Get the status of a running orchestration
    
    GET /api/orchestration_status/{instance_id}
    """
    instance_id = req.route_params.get('instance_id')
    
    logging.info(f'HTTP trigger: Status check for orchestration {instance_id}')
    
    try:
        client = df.DurableOrchestrationClient(starter)
        status = await client.get_status(instance_id)
        
        if status:
            response = {
                "instance_id": instance_id,
                "runtime_status": status.runtime_status,
                "created_time": status.created_time.isoformat() if status.created_time else None,
                "last_updated_time": status.last_updated_time.isoformat() if status.last_updated_time else None,
                "output": status.output,
                "custom_status": status.custom_status
            }
            
            return func.HttpResponse(
                json.dumps(response, indent=2),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({"error": "Orchestration not found"}),
                status_code=404,
                mimetype="application/json"
            )
            
    except Exception as e:
        logging.error(f'HTTP trigger: Error getting orchestration status: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
```

---

### Phase 4: Testing and Validation

#### Step 4.1: Local Testing Setup

**Prerequisites**:
- [ ] Azurite running (Azure Storage Emulator)
- [ ] Python 3.9+ installed
- [ ] Azure Functions Core Tools v4
- [ ] All dependencies installed from `requirements.txt`

**Start Azurite** (PowerShell):
```powershell
# Install Azurite if not already installed
npm install -g azurite

# Start Azurite
azurite --silent --location c:\azurite --debug c:\azurite\debug.log
```

**Configure Local Settings**:
Ensure `local.settings.json` has:
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsFeatureFlags": "EnableWorkerIndexing",
    "WEBSITES_CONFIG_LOCATION": "local",
    "STORAGE_ACCOUNT_NAME": "",
    "MANAGED_IDENTITY_CLIENT_ID": ""
  }
}
```

**Start Function App**:
```powershell
func start
```

---

#### Step 4.2: Unit Testing Plan

**Test 1: Configuration Loading**
```powershell
# Test that websites.json can be loaded
# Expected: Return 5 enabled websites
```

**Test Approach**:
- Call `load_websites_config("local")`
- Verify count of enabled sites
- Verify structure of returned data

---

**Test 2: Activity Function - Single Website**
```powershell
# Test crawling a single website
# Expected: Return success with document counts
```

**Test Approach**:
- Create test website config for a simple site
- Call `crawl_website_activity` directly
- Verify return structure
- Check logs for errors

---

**Test 3: Orchestrator - Full Flow**
```bash
# Trigger orchestration via HTTP
curl -X POST http://localhost:7071/api/start_crawler \
  -H "Content-Type: application/json" \
  -d '{"config_location": "local"}'
```

**Expected Response**:
```json
{
  "message": "Crawler orchestration started",
  "instance_id": "abc123...",
  "runtime_status": "Running",
  "check_status_url": "http://localhost:7071/api/orchestration_status/abc123...",
  "config_location": "local"
}
```

**Verification Steps**:
1. Call the start endpoint
2. Note the `instance_id`
3. Poll the status endpoint
4. Verify status changes: Running → Completed
5. Check logs for each activity execution
6. Verify results in blob storage

---

**Test 4: Status Monitoring**
```bash
# Check orchestration status
curl http://localhost:7071/api/orchestration_status/{instance_id}
```

**Expected Response**:
```json
{
  "instance_id": "abc123...",
  "runtime_status": "Completed",
  "created_time": "2025-10-16T10:00:00Z",
  "last_updated_time": "2025-10-16T10:05:23Z",
  "output": {
    "orchestration_id": "abc123...",
    "total_websites": 5,
    "successful_crawls": 5,
    "failed_crawls": 0,
    "total_documents_found": 127,
    "total_new_documents": 5,
    "website_results": [...]
  }
}
```

---

**Test 5: Timer Trigger**
```powershell
# Manually trigger the timer function
# Note: With run_on_startup=False, you'll need to wait for scheduled time
# or temporarily set run_on_startup=True for testing
```

**Test Approach**:
- Temporarily change `run_on_startup=True`
- Restart function app
- Verify orchestration starts automatically
- Check logs for timer trigger execution

---

#### Step 4.3: Error Handling Tests

**Test 6: Invalid Website URL**
- Add a website with invalid URL to config
- Run orchestration
- Expected: Activity fails gracefully, orchestration continues

**Test 7: Network Timeout**
- Add a website that times out
- Expected: Activity handles timeout, returns error result

**Test 8: Missing Configuration File**
- Rename `websites.json`
- Run orchestration
- Expected: Fallback to hardcoded config

**Test 9: Storage Access Failure**
- Use invalid storage account
- Expected: Proper error logging, graceful degradation

---

### Phase 5: Deployment to Azure

#### Step 5.1: Pre-Deployment Checklist

**Code Preparation**:
- [ ] All tests passing locally
- [ ] Error handling verified
- [ ] Logging statements added
- [ ] Comments and documentation updated
- [ ] No sensitive data in code

**Configuration Files**:
- [ ] `requirements.txt` includes `azure-functions-durable`
- [ ] `host.json` updated with durable task configuration
- [ ] `websites.json` created and validated
- [ ] `local.settings.json` has all required variables

**Azure Resources**:
- [ ] Function App exists
- [ ] Storage Account accessible
- [ ] Managed Identity configured
- [ ] RBAC permissions assigned
- [ ] Application Insights enabled

---

#### Step 5.2: Deployment Steps

**Option A: VS Code Deployment**
1. Open VS Code
2. Install "Azure Functions" extension
3. Right-click on function project
4. Select "Deploy to Function App"
5. Choose existing Function App
6. Confirm deployment

**Option B: Azure Functions Core Tools**
```powershell
# Login to Azure
az login

# Deploy to existing Function App
func azure functionapp publish <function-app-name>
```

**Option C: GitHub Actions (Recommended for Production)**
Create `.github/workflows/deploy-function.yml`:
```yaml
name: Deploy Azure Function

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Deploy to Azure Functions
        uses: Azure/functions-action@v1
        with:
          app-name: '<function-app-name>'
          package: '.'
          publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

---

#### Step 5.3: Post-Deployment Configuration

**Upload websites.json to Blob Storage** (if using blob config):
```powershell
# Using Azure CLI
az storage blob upload `
  --account-name stbtpuksprodcrawler01 `
  --container-name configuration `
  --name websites.json `
  --file websites.json `
  --auth-mode login
```

**Set Application Settings**:
```powershell
# Set config location
az functionapp config appsettings set `
  --name <function-app-name> `
  --resource-group <resource-group> `
  --settings WEBSITES_CONFIG_LOCATION=blob

# Verify storage account name
az functionapp config appsettings set `
  --name <function-app-name> `
  --resource-group <resource-group> `
  --settings STORAGE_ACCOUNT_NAME=stbtpuksprodcrawler01
```

**Verify Managed Identity**:
```powershell
# Check system-assigned identity
az functionapp identity show `
  --name <function-app-name> `
  --resource-group <resource-group>

# Assign Storage Blob Data Contributor role
az role assignment create `
  --assignee <managed-identity-principal-id> `
  --role "Storage Blob Data Contributor" `
  --scope /subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.Storage/storageAccounts/stbtpuksprodcrawler01
```

---

#### Step 5.4: Deployment Verification

**Step 1: Check Function App Status**
```powershell
az functionapp show `
  --name <function-app-name> `
  --resource-group <resource-group> `
  --query state
```
Expected: `"Running"`

**Step 2: List Functions**
```powershell
az functionapp function list `
  --name <function-app-name> `
  --resource-group <resource-group>
```
Expected functions:
- `crawler_orchestrator`
- `crawl_website_activity`
- `load_config_activity`
- `store_orchestration_results`
- `scheduled_crawler_trigger`
- `start_crawler_orchestration`
- `get_orchestration_status`

**Step 3: Test Orchestration**
```bash
# Get function app URL
FUNCTION_APP_URL="https://<function-app-name>.azurewebsites.net"

# Get function key
FUNCTION_KEY="<your-function-key>"

# Start orchestration
curl -X POST "${FUNCTION_APP_URL}/api/start_crawler?code=${FUNCTION_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"config_location": "blob"}'
```

**Step 4: Monitor Execution**
- Open Azure Portal
- Navigate to Function App → Functions → `crawler_orchestrator`
- Click "Monitor"
- View recent invocations
- Check for errors

**Step 5: Verify Results**
- Open Storage Account → Containers → `documents`
- Look for `orchestration_results_*.json` files
- Download and verify structure
- Check for expected website results

---

### Phase 6: Monitoring and Maintenance

#### Step 6.1: Application Insights Queries

**Query 1: Orchestration Success Rate**
```kusto
traces
| where message contains "Orchestrator: Completed"
| summarize 
    TotalOrchestrations = count(),
    AvgWebsites = avg(toint(extract("(\\d+)/(\\d+) successful", 2, message))),
    AvgSuccessful = avg(toint(extract("(\\d+)/(\\d+) successful", 1, message)))
| extend SuccessRate = (AvgSuccessful / AvgWebsites) * 100
```

**Query 2: Document Discovery Metrics**
```kusto
traces
| where message contains "new documents found"
| extend NewDocs = toint(extract("(\\d+) new documents found", 1, message))
| summarize 
    TotalRuns = count(),
    TotalNewDocuments = sum(NewDocs),
    AvgNewDocsPerRun = avg(NewDocs)
| project TotalRuns, TotalNewDocuments, AvgNewDocsPerRun
```

**Query 3: Activity Duration Analysis**
```kusto
traces
| where message contains "Activity: Completed crawl"
| extend 
    Website = extract("for (.+?) -", 1, message),
    DocsFound = toint(extract("Found (\\d+) documents", 1, message))
| summarize 
    AvgDocs = avg(DocsFound),
    MinDocs = min(DocsFound),
    MaxDocs = max(DocsFound)
    by Website
| order by AvgDocs desc
```

**Query 4: Failure Analysis**
```kusto
traces
| where severityLevel >= 3  // Warning or Error
| where message contains "Activity:" or message contains "Orchestrator:"
| summarize FailureCount = count() by message
| order by FailureCount desc
```

---

#### Step 6.2: Alert Configuration

**Alert 1: Orchestration Failures**
- **Condition**: When orchestration fails
- **Query**:
  ```kusto
  traces
  | where message contains "Orchestrator: Fatal error"
  | count
  ```
- **Threshold**: > 0 in 5 minutes
- **Action**: Email to admin team

**Alert 2: Low Document Discovery**
- **Condition**: No new documents found in 24 hours
- **Query**:
  ```kusto
  traces
  | where timestamp > ago(24h)
  | where message contains "new documents found"
  | extend NewDocs = toint(extract("(\\d+) new documents", 1, message))
  | summarize TotalNew = sum(NewDocs)
  ```
- **Threshold**: TotalNew == 0
- **Action**: Email notification

**Alert 3: Activity Timeouts**
- **Condition**: Activity function exceeding 5 minutes
- **Metric**: Function execution duration
- **Threshold**: > 300 seconds
- **Action**: Log to monitoring dashboard

---

#### Step 6.3: Operational Procedures

**Adding New Websites**:
1. Edit `websites.json` (local or blob)
2. Add new website entry:
   ```json
   {
     "id": "new_website",
     "name": "New Website Name",
     "url": "https://example.com",
     "enabled": true,
     "description": "Description",
     "document_types": ["pdf"],
     "crawl_depth": "deep",
     "priority": "high",
     "multi_level": false,
     "max_depth": 1
   }
   ```
3. If using blob storage, re-upload:
   ```powershell
   az storage blob upload --account-name stbtpuksprodcrawler01 `
     --container-name configuration --name websites.json `
     --file websites.json --auth-mode login --overwrite
   ```
4. Next scheduled run will include the new website

**Disabling Websites**:
1. Edit `websites.json`
2. Set `"enabled": false`
3. Re-upload if using blob storage
4. No code deployment needed

**Adjusting Concurrency**:
1. Edit `host.json`
2. Modify `maxConcurrentActivityFunctions` value
3. Deploy updated `host.json`
4. Restart Function App

**Manual Trigger**:
```bash
# Trigger specific crawl
curl -X POST "https://<function-app>.azurewebsites.net/api/start_crawler?code=<key>" \
  -H "Content-Type: application/json" \
  -d '{"config_location": "blob"}'
```

---

### Phase 7: Rollback Plan

#### Step 7.1: Backup Current Version

**Before deploying new version**:
```powershell
# Create backup branch
git checkout -b backup-v2.2.0-before-durable-functions
git push origin backup-v2.2.0-before-durable-functions

# Tag current production version
git tag -a v2.2.0-stable -m "Stable version before Durable Functions migration"
git push origin v2.2.0-stable
```

**Create deployment slot** (recommended):
```powershell
# Create staging slot
az functionapp deployment slot create `
  --name <function-app-name> `
  --resource-group <resource-group> `
  --slot staging

# Deploy to staging first
func azure functionapp publish <function-app-name> --slot staging

# Test in staging
# Then swap to production
az functionapp deployment slot swap `
  --name <function-app-name> `
  --resource-group <resource-group> `
  --slot staging
```

---

#### Step 7.2: Rollback Procedure

**If issues arise after deployment**:

**Option 1: Slot Swap Rollback**
```powershell
# Swap back to previous version
az functionapp deployment slot swap `
  --name <function-app-name> `
  --resource-group <resource-group> `
  --slot staging
```

**Option 2: Redeploy Previous Version**
```powershell
# Checkout stable tag
git checkout v2.2.0-stable

# Redeploy
func azure functionapp publish <function-app-name>
```

**Option 3: Emergency Configuration Change**
```powershell
# If old timer trigger still exists, can disable new orchestrator
# and re-enable old crawler

# Stop function app
az functionapp stop --name <function-app-name> --resource-group <resource-group>

# Redeploy stable version
# Restart
az functionapp start --name <function-app-name> --resource-group <resource-group>
```

---

## Migration Strategy Recommendations

### Phased Approach (Recommended)

**Phase A: Parallel Running (Week 1-2)**
- Deploy Durable Functions alongside existing timer trigger
- Keep old `scheduled_crawler` running
- Run new orchestrator on different schedule (e.g., offset by 2 hours)
- Compare results from both systems
- Monitor for discrepancies

**Phase B: Canary Testing (Week 3)**
- Disable old timer trigger for 1-2 websites
- Route those through orchestrator only
- Monitor closely
- Validate document detection accuracy

**Phase C: Full Cutover (Week 4)**
- Disable old `scheduled_crawler` timer trigger
- Keep function code as backup
- Use orchestrator exclusively
- Monitor for one week

**Phase D: Cleanup (Week 5+)**
- After successful operation, remove old crawler code
- Update documentation
- Declare v3.0.0 stable

---

## Success Criteria

### Technical Metrics
- [ ] Orchestrator successfully starts on schedule
- [ ] All enabled websites are crawled in parallel
- [ ] Document detection accuracy matches old system (≥95%)
- [ ] No increase in false positives/negatives
- [ ] Results properly stored in blob storage
- [ ] Managed Identity authentication working
- [ ] Application Insights telemetry flowing

### Performance Metrics
- [ ] Total crawl time reduced (due to parallelization)
- [ ] Individual website crawl times unchanged
- [ ] No timeout issues
- [ ] Storage operations complete successfully
- [ ] Memory usage within acceptable limits

### Operational Metrics
- [ ] Zero critical errors in first week
- [ ] Alert system functioning
- [ ] Monitoring dashboards accurate
- [ ] Can add/remove websites without code changes
- [ ] Manual trigger works reliably

---

## Risk Assessment

### High Risk Items
1. **Breaking Change**: Timer trigger modification
   - **Mitigation**: Keep old function, parallel run
   
2. **Configuration Loading**: New file-based system
   - **Mitigation**: Fallback to hardcoded values

3. **Managed Identity Permissions**: Blob access
   - **Mitigation**: Test thoroughly in staging

### Medium Risk Items
1. **Parallel Execution**: Resource contention
   - **Mitigation**: Limit concurrent activities to 10

2. **Storage Account Limits**: Increased blob operations
   - **Mitigation**: Monitor throttling, implement backoff

3. **Durable Functions Learning Curve**: Team unfamiliar
   - **Mitigation**: Comprehensive documentation, training

### Low Risk Items
1. **Application Insights Costs**: More telemetry
   - **Mitigation**: Acceptable for better observability

2. **Code Complexity**: Orchestrator pattern
   - **Mitigation**: Well-documented, follows best practices

---

## Estimated Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Phase 1: Prerequisites** | 2 days | Install packages, update configs, create websites.json |
| **Phase 2: Refactoring** | 3 days | Extract core logic, create config reader |
| **Phase 3: Implementation** | 5 days | Create orchestrator, activities, update triggers |
| **Phase 4: Testing** | 3 days | Local testing, error scenarios, validation |
| **Phase 5: Deployment** | 2 days | Deploy to staging, configure Azure resources |
| **Phase 6: Monitoring Setup** | 2 days | Alerts, dashboards, queries |
| **Phase 7: Production Cutover** | 1 day | Final deployment, verification |
| **Buffer** | 2 days | Unexpected issues, refinements |
| **Total** | **20 days** | **~4 weeks** |

---

## Appendix

### A. Durable Functions Concepts

**Orchestrator Function**:
- Coordinates workflow
- Must be deterministic
- Uses `yield` for async operations
- Automatically checkpointed

**Activity Function**:
- Performs actual work
- Can be non-deterministic
- Called by orchestrator
- Supports retry policies

**Durable Orchestration Client**:
- Starts orchestrations
- Checks status
- Sends events
- Manages instances

**Fan-out/Fan-in Pattern**:
```
Orchestrator
    ├─> Activity 1 ─┐
    ├─> Activity 2 ─┤
    ├─> Activity 3 ─┼─> Aggregate Results
    └─> Activity N ─┘
```

---

### B. Required Dependencies

**Python Packages** (`requirements.txt`):
```
azure-functions>=1.18.0
azure-functions-durable>=1.2.9
requests>=2.31.0
```

**Azure Resources**:
- Azure Functions (Consumption or Premium plan)
- Azure Storage Account (for Durable Functions state)
- Application Insights (for monitoring)
- Managed Identity (for authentication)

---

### C. Configuration Reference

**Environment Variables**:
```
AzureWebJobsStorage=<connection-string>
FUNCTIONS_WORKER_RUNTIME=python
WEBSITES_CONFIG_LOCATION=local|blob
STORAGE_ACCOUNT_NAME=stbtpuksprodcrawler01
MANAGED_IDENTITY_CLIENT_ID=<client-id>
```

**Host.json Key Settings**:
```json
{
  "extensions": {
    "durableTask": {
      "hubName": "WebCrawlerHub",
      "maxConcurrentActivityFunctions": 10,
      "maxConcurrentOrchestratorFunctions": 5
    }
  }
}
```

---

### D. Troubleshooting Guide

**Issue: Orchestrator not starting**
- Check: `host.json` has correct durable task config
- Check: Extension bundle version `[4.*, 5.0.0)`
- Check: `AzureWebJobsStorage` is set correctly
- Check: Function app logs for errors

**Issue: Activities not executing**
- Check: Activity function names match orchestrator calls
- Check: Input serialization (JSON compatible)
- Check: Concurrency limits in `host.json`
- Check: Application Insights for exceptions

**Issue: Configuration not loading**
- Check: `websites.json` exists and is valid JSON
- Check: File path correct for local/blob
- Check: Managed Identity has Storage Blob Data Reader role
- Check: Container name is correct

**Issue: Slow execution**
- Check: Network timeouts on crawler requests
- Check: Increase `maxConcurrentActivityFunctions`
- Check: Storage account throttling
- Check: Application Insights sampling rate

---

### E. References

**Official Documentation**:
- [Azure Durable Functions for Python](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview)
- [Durable Functions Patterns](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview#application-patterns)
- [Fan-out/Fan-in Pattern](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview#fan-in-out)
- [Python V2 Programming Model](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)

**Best Practices**:
- [Durable Functions Checklist](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-checklist)
- [Performance and Scale](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-perf-and-scale)
- [Error Handling](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-error-handling)

---

## Summary

This implementation plan provides a comprehensive, step-by-step guide to migrate your web crawler from a simple timer-triggered function to a robust Durable Functions orchestrator pattern. The approach emphasizes:

1. **Minimal Breaking Changes**: Reusing existing logic where possible
2. **Incremental Migration**: Parallel running before full cutover
3. **Production-Ready**: Error handling, monitoring, rollback plans
4. **Maintainability**: Configuration-driven, well-documented
5. **Scalability**: Parallel execution, easy to extend

Follow this plan sequentially, testing at each phase, and you'll have a production-grade orchestrated web crawler that's easier to manage, monitor, and scale.

---

**Next Steps**:
1. Review this plan with stakeholders
2. Set up development environment
3. Begin Phase 1: Prerequisites
4. Create feature branch: `feature/durable-functions-orchestrator`
5. Implement incrementally with testing at each step

**Questions or Issues**:
- Document any deviations from this plan
- Update this document as you progress
- Track issues in version control

**Good luck with the implementation! 🚀**
