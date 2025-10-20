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

A production-ready, scalable web crawler built with Azure Durable Functions that processes multiple websites in parallel. The crawler extracts content, generates unique filenames, and saves the results to Azure Blob Storage with comprehensive error handling and monitoring.

## Features

- **Parallel Processing**: Crawl multiple websites simultaneously using Azure Durable Functions orchestration
- **Smart Content Extraction**: Extract titles, metadata, and content from web pages
- **Unique Filename Generation**: Automatically generate collision-resistant filenames for crawled content
- **Azure Blob Storage**: Store crawled content with organized naming conventions
- **Production Error Handling**: Comprehensive error handling with detailed logging
- **Monitoring Ready**: Integration with Application Insights for monitoring and diagnostics
- **Configurable**: Easy website management through JSON configuration

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

### Prerequisites

1. **Create Azure Resources**:
   - Resource Group
   - Function App (Python 3.10+)
   - Storage Account

2. **Create Resource Reference File** (optional):
   
   Create `AZURE_RESOURCE_REFERENCE.md` in your local copy (ignored by git):
   ```markdown
   # Azure Resource Reference
   
   - Resource Group: `your-resource-group`
   - Function App: `your-function-app`
   - Storage Account: `your-storage-account`
   - Subscription ID: `your-subscription-id`
   ```

### Deployment Steps

1. **Create Deployment Package**:
   ```bash
   # Create deployment ZIP
   zip -r v1.0.0-deployment.zip . \
     -x "*.git*" -x "*.vscode*" -x "*__pycache__*" \
     -x "*.venv*" -x "*tests*" -x "*.zip"
   ```

2. **Deploy to Azure**:
   ```bash
   az functionapp deployment source config-zip \
     --resource-group YOUR_RESOURCE_GROUP \
     --name YOUR_FUNCTION_APP \
     --src v1.0.0-deployment.zip \
     --subscription YOUR_SUBSCRIPTION_ID
   ```

3. **Configure Application Settings**:
   ```bash
   az functionapp config appsettings set \
     --resource-group YOUR_RESOURCE_GROUP \
     --name YOUR_FUNCTION_APP \
     --settings STORAGE_CONNECTION_STRING="YOUR_STORAGE_CONNECTION_STRING"
   ```

For detailed deployment instructions, see [DEPLOYMENT.md](docs/DEPLOYMENT.md).

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
