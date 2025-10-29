---
page_type: sample
languages:
- python
products:
- azure
- azure-functions
name: Azure Functions Python Web Crawler
description: Production-ready web crawler built with Azure Durable Functions and Python that extracts content from multiple websites in parallel.
---

# Azure Functions Python Web Crawler

A production-ready, scalable web crawler built with Azure Durable Functions that processes multiple websites in parallel. The crawler extracts content from legal guidance websites, generates unique filenames, and saves results to Azure Blob Storage with comprehensive monitoring and change detection.

[![Version](https://img.shields.io/badge/version-2.8.1-blue.svg)](VERSION-TRACKING.md)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Azure Functions](https://img.shields.io/badge/azure--functions-v2-blue.svg)](https://learn.microsoft.com/en-us/azure/azure-functions/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE.md)

## Overview

This Azure Function application automatically monitors and captures legal guidance documents and web content from multiple sources including:

- **Crown Prosecution Service (CPS)** - Prosecution guidance (HTML content, 200-300 pages)
- **College of Policing** - Authorised Professional Practice (APP) guidance (HTML content)
- **Sentencing Council** - Sentencing guidelines (downloadable documents)
- **Home Office** - Legislation and circulars (downloadable documents)

### Key Capabilities

- **Parallel Processing**: Crawl multiple websites simultaneously using Durable Functions orchestration
- **Smart Content Extraction**: Extract both downloadable documents (PDF, DOC, DOCX) and HTML web content
- **HTML Guidance Capture**: Intelligent extraction of web-based guidance with content filtering
- **Change Detection**: Hash-based monitoring to detect document updates automatically
- **Unique Filename Generation**: Collision-resistant naming with timestamp and content hash
- **Azure Blob Storage**: Organized storage with website-specific folders and metadata
- **Production Monitoring**: Real-time dashboard with statistics, validation, and health monitoring
- **Storage Validation**: Automated consistency checks between metadata and actual storage
- **AI Search Ready**: Metadata optimized for Azure AI Search integration

## Features

### Content Capture

- **Document Downloads**: Automatically download PDF, DOC, DOCX, and other document types
- **HTML Guidance Extraction**: Extract web-based guidance content with intelligent filtering
  - Detects guidance pages vs navigation pages
  - Extracts main content (excludes headers, footers, navigation)
  - Validates substantial content (>500 characters)
- **CPS Alphabetical Discovery**: Navigate A-Z subject indices to find all prosecution guidance
- **Multi-Level Crawling**: Follow links to discover all available documents

### Storage & Organization

- **Smart Folder Structure**: `{website-name}/{filename}` organization in Azure Blob Storage
- **Collision-Resistant Naming**: Timestamps + content hash ensure unique filenames
- **Rich Metadata**: Source, capture date, content type, file size, hash stored with each document
- **Change Detection**: Hash-based tracking identifies when documents are updated

### Monitoring & Validation

- **Real-Time Dashboard**: View crawl statistics, document counts, and system health
- **Storage Validation**: Automated consistency checks (Phase 2 validation)
- **Activity Tracking**: Monitor recent crawls, uploads, and detected changes
- **Error Logging**: Comprehensive error tracking with Application Insights integration

### Production Ready

### Production Ready

- **Managed Identity**: Secure authentication to Azure resources without connection strings
- **Error Handling**: Comprehensive try-catch blocks with detailed logging
- **Retry Logic**: Built-in retry for transient failures
- **Scalable Architecture**: Azure Durable Functions orchestration handles high workloads
- **CI/CD Ready**: GitHub Actions workflow for automated deployment

## Current Version: v2.8.1

**Recent Improvements:**

✅ **Dashboard Fix** - Storage Validation panel now displays correctly  
✅ **CPS Guidance Capture** - Complete alphabetical discovery (A-Z) for prosecution guidance  
✅ **HTML Content Extraction** - Enhanced extraction for legal guidance web pages  
✅ **Configuration Updates** - Optimized settings for CPS and College of Policing

See [VERSION-TRACKING.md](VERSION-TRACKING.md) for detailed release history and [CHANGELOG.md](CHANGELOG.md) for version notes.

## Architecture

This project uses Azure Durable Functions with the following components:

- **HTTP Trigger**: Initiates the crawl orchestration (`crawl_orchestrator_http`)
- **Orchestrator**: Manages parallel execution of crawl activities (`crawl_orchestrator`)
- **Activity Functions**: 
  - `crawl_activity`: Crawls individual websites
  - `save_to_blob_activity`: Saves content to Azure Blob Storage
- **Blob Output**: Stores crawled content in Azure Storage

For detailed architecture information, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Prerequisites

- Python 3.10 or higher
- Azure subscription
- Azure Function Core Tools 4.x
- Visual Studio Code (recommended)
- Azure Functions extension for VS Code

### For Local Development:
- Azurite (Azure Storage emulator)
- Postman or similar API testing tool

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/functions-python-web-crawler.git
cd functions-python-web-crawler
```

### 2. Set Up Python Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Local Settings

Create a `local.settings.json` file (ignored by git):

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsFeatureFlags": "EnableWorkerIndexing",
    "STORAGE_CONNECTION_STRING": "UseDevelopmentStorage=true"
  }
}
```

### 4. Configure Websites to Crawl

Edit `websites.json` to add your target websites:

```json
{
  "websites": [
    {
      "url": "https://example.com",
      "name": "Example Site"
    }
  ]
}
```

### 5. Run Locally

1. Start Azurite (Azure Storage emulator):
   - In VS Code: `View` → `Command Palette` → `Azurite: Start`

2. Run the function:
   ```bash
   func start
   ```

3. Test the endpoint:
   - URL: `http://localhost:7071/api/crawl_orchestrator_http`
   - Method: `POST`
   - No body required (uses websites.json)

## Deployment to Azure

### Quick Deploy (GitHub Actions - Recommended)

This project uses GitHub Actions for automated deployment:

1. **Push to main branch**:

   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **Monitor deployment**:
   - Visit: `https://github.com/YOUR-USERNAME/functions-python-web-crawler/actions`
   - Expected time: 3-5 minutes

3. **Verify function**:

   ```bash
   curl "https://YOUR-FUNCTION-APP.azurewebsites.net/api/dashboard"
   ```

### Manual Deployment (Azure CLI)

For manual deployments or initial setup:

1. **Create Azure Resources** (one-time setup):

   - Resource Group
   - Function App (Python 3.10+, Linux)
   - Storage Account
   - Application Insights (recommended)

2. **Create Resource Reference** (optional, for documentation):
   
   Copy `AZURE_RESOURCE_REFERENCE.md.template` to `AZURE_RESOURCE_REFERENCE.md` and fill in your resource names:

   ```markdown
   # Azure Resource Reference
   
   - Resource Group: `rg-your-resource-group`
   - Function App: `func-your-function-app`
   - Storage Account: `styourstorageaccount`
   - Subscription ID: `your-subscription-id`
   ```

   Note: This file is gitignored and used only for local reference.

3. **Deploy with Azure CLI**:

   ```bash
   # Create deployment package
   zip -r v2.8.1-deployment.zip . \
     -x "*.git*" -x "*.vscode*" -x "*__pycache__*" \
     -x "*.venv*" -x "*tests*" -x "*archive*" -x "*.zip"

   # Deploy to Azure
   az functionapp deployment source config-zip \
     --resource-group YOUR_RESOURCE_GROUP \
     --name YOUR_FUNCTION_APP \
     --src v2.8.1-deployment.zip \
     --subscription YOUR_SUBSCRIPTION_ID
   ```

4. **Configure Application Settings** (if using connection strings):

   ```bash
   az functionapp config appsettings set \
     --resource-group YOUR_RESOURCE_GROUP \
     --name YOUR_FUNCTION_APP \
     --settings STORAGE_CONNECTION_STRING="YOUR_CONNECTION_STRING"
   ```

   **Note**: Managed Identity is recommended over connection strings for production.

For detailed deployment instructions, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Usage

### API Endpoint

**POST** `/api/crawl_orchestrator_http`

Starts the web crawl orchestration for all websites defined in `websites.json`.

**Response**:
```json
{
  "id": "orchestration-instance-id",
  "statusQueryGetUri": "http://...",
  "sendEventPostUri": "http://...",
  "terminatePostUri": "http://...",
  "purgeHistoryDeleteUri": "http://..."
}
```

### Monitoring Progress

Use the `statusQueryGetUri` from the response to check orchestration status:

```bash
curl "https://your-function-app.azurewebsites.net/runtime/webhooks/durabletask/instances/{instanceId}"
```

## Project Structure

```
functions-python-web-crawler/
├── function_app.py          # Main application code
├── requirements.txt         # Python dependencies
├── host.json               # Function host configuration
├── websites.json           # Website configuration
├── local.settings.json     # Local settings (not in git)
├── .funcignore            # Files to ignore during deployment
├── .gitignore             # Git ignore rules
├── docs/                  # Documentation
│   ├── API.md            # API documentation
│   ├── ARCHITECTURE.md   # Architecture details
│   └── DEPLOYMENT.md     # Deployment guide
├── archive/               # Previous deployment artifacts
└── tests/                 # Test files (optional)
```

## Configuration

### Environment Variables

- `AzureWebJobsStorage`: Azure Storage connection string for Functions runtime
- `STORAGE_CONNECTION_STRING`: Azure Storage connection string for blob output
- `FUNCTIONS_WORKER_RUNTIME`: Set to `python`
- `AzureWebJobsFeatureFlags`: Set to `EnableWorkerIndexing`

### websites.json

Configure websites to crawl:

```json
{
  "websites": [
    {
      "url": "https://example.com",
      "name": "Example Site"
    },
    {
      "url": "https://another-example.com",
      "name": "Another Example"
    }
  ]
}
```

## Monitoring and Logging

The application includes comprehensive logging and integrates with Application Insights:

- All activities are logged with INFO level
- Errors are captured with ERROR level and full stack traces
- Orchestration progress can be monitored via Durable Functions status endpoints
- Application Insights provides detailed telemetry and diagnostics

## Development

### Running Tests

```bash
python tests/run_tests.py
```

### Code Style

This project follows PEP 8 conventions. Key guidelines:
- Use `snake_case` for functions and variables
- Use `PascalCase` for classes
- Include docstrings for all functions
- Use type hints where appropriate

## Troubleshooting

### Common Issues

1. **"No module named 'azure.durable_task'"**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

2. **"AzureWebJobsStorage not found"**
   - Check `local.settings.json` configuration
   - Ensure Azurite is running for local development

3. **"Failed to crawl website"**
   - Check website URL is accessible
   - Verify network connectivity
   - Review function logs for detailed error messages

For more troubleshooting tips, see [DEPLOYMENT.md](docs/DEPLOYMENT.md).

## API Documentation

For detailed API documentation, see [API.md](docs/API.md).

## Version History

See [CHANGELOG.md](CHANGELOG.md) for release notes and version history.

See [VERSION-TRACKING.md](VERSION-TRACKING.md) for deployment tracking.

## Resources

- [Azure Functions Python Developer Guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level&pivots=python-mode-decorators)
- [Azure Durable Functions](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview)
- [BeautifulSoup4 Documentation](https://beautiful-soup-4.readthedocs.io/en/latest/)
- [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

This project welcomes contributions and suggestions. Most contributions require you to agree to a Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us the rights to use your contribution.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide a CLA and decorate the PR appropriately. Simply follow the instructions provided by the bot.

## License

This project is licensed under the MIT License - see [LICENSE.md](LICENSE.md) for details.

## Support

For issues and questions:
- Create an issue in this repository
- Check existing documentation in the `docs/` folder
- Review the troubleshooting section above
