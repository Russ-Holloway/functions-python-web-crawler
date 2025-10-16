# Azure Function Deployment Script
# Durable Functions Web Crawler
# Version: 3.0.0-alpha

param(
    [Parameter(Mandatory=$true)]
    [string]$FunctionAppName,
    
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$false)]
    [string]$StorageAccountName = "stbtpuksprodcrawler01",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("local", "blob")]
    [string]$ConfigLocation = "blob",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipTests
)

# Color output functions
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Blue
    Write-Host " $Message" -ForegroundColor Blue
    Write-Host "═══════════════════════════════════════════════════════`n" -ForegroundColor Blue
}

# Main deployment script
try {
    Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   AZURE FUNCTIONS DEPLOYMENT - DURABLE WEB CRAWLER       ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

    # Step 1: Pre-deployment checks
    Write-Step "Step 1: Pre-Deployment Validation"

    # Check if Azure CLI is installed
    Write-Info "Checking Azure CLI..."
    $azVersion = az --version 2>&1 | Select-String "azure-cli"
    if ($azVersion) {
        Write-Success "Azure CLI installed: $azVersion"
    } else {
        Write-Error "Azure CLI not found. Please install Azure CLI."
        exit 1
    }

    # Check if logged in to Azure
    Write-Info "Checking Azure login status..."
    $account = az account show 2>&1 | ConvertFrom-Json
    if ($account) {
        Write-Success "Logged in as: $($account.user.name)"
        Write-Success "Subscription: $($account.name)"
    } else {
        Write-Warning "Not logged in to Azure. Initiating login..."
        az login
    }

    # Check if Functions Core Tools is installed
    Write-Info "Checking Azure Functions Core Tools..."
    $funcVersion = func --version 2>&1
    if ($funcVersion) {
        Write-Success "Functions Core Tools version: $funcVersion"
    } else {
        Write-Error "Azure Functions Core Tools not found. Please install from: https://aka.ms/func-cli"
        exit 1
    }

    # Verify Function App exists
    Write-Info "Verifying Function App exists..."
    $functionApp = az functionapp show --name $FunctionAppName --resource-group $ResourceGroup 2>&1 | ConvertFrom-Json
    if ($functionApp) {
        Write-Success "Function App found: $FunctionAppName"
        Write-Info "  Location: $($functionApp.location)"
        Write-Info "  State: $($functionApp.state)"
        Write-Info "  Runtime: $($functionApp.kind)"
    } else {
        Write-Error "Function App '$FunctionAppName' not found in resource group '$ResourceGroup'"
        exit 1
    }

    # Run validation script (unless skipped)
    if (-not $SkipTests) {
        Write-Info "Running system validation..."
        python tests\validate_system.py
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Validation found issues. Continue anyway? (y/n)"
            $response = Read-Host
            if ($response -ne 'y') {
                Write-Error "Deployment cancelled."
                exit 1
            }
        } else {
            Write-Success "System validation passed"
        }
    }

    # Step 2: Prepare deployment
    Write-Step "Step 2: Preparing Deployment"

    # Ensure we're in the correct directory
    $projectRoot = Split-Path -Parent $PSScriptRoot
    if (-not (Test-Path "$projectRoot\function_app.py")) {
        Write-Error "function_app.py not found. Are you in the correct directory?"
        exit 1
    }
    Write-Success "Project root: $projectRoot"

    # Step 3: Deploy Function App
    Write-Step "Step 3: Deploying Function App to Azure"

    Write-Info "Starting deployment to '$FunctionAppName'..."
    Write-Warning "This may take several minutes..."

    # Deploy using func CLI
    Push-Location $projectRoot
    func azure functionapp publish $FunctionAppName --python
    $deployResult = $LASTEXITCODE
    Pop-Location

    if ($deployResult -eq 0) {
        Write-Success "Function App deployed successfully"
    } else {
        Write-Error "Deployment failed with exit code $deployResult"
        exit 1
    }

    # Step 4: Upload configuration to blob storage (if using blob config)
    if ($ConfigLocation -eq "blob") {
        Write-Step "Step 4: Uploading Configuration to Blob Storage"

        Write-Info "Uploading websites.json to blob storage..."
        az storage blob upload `
            --account-name $StorageAccountName `
            --container-name configuration `
            --name websites.json `
            --file "$projectRoot\websites.json" `
            --auth-mode login `
            --overwrite `
            2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Configuration uploaded to blob storage"
        } else {
            Write-Warning "Failed to upload configuration to blob storage"
            Write-Info "You may need to upload manually or check permissions"
        }
    } else {
        Write-Step "Step 4: Configuration Upload (Skipped - using local config)"
        Write-Info "Configuration location set to 'local'"
    }

    # Step 5: Configure Application Settings
    Write-Step "Step 5: Configuring Application Settings"

    Write-Info "Setting WEBSITES_CONFIG_LOCATION..."
    az functionapp config appsettings set `
        --name $FunctionAppName `
        --resource-group $ResourceGroup `
        --settings "WEBSITES_CONFIG_LOCATION=$ConfigLocation" `
        --output none

    Write-Info "Setting STORAGE_ACCOUNT_NAME..."
    az functionapp config appsettings set `
        --name $FunctionAppName `
        --resource-group $ResourceGroup `
        --settings "STORAGE_ACCOUNT_NAME=$StorageAccountName" `
        --output none

    Write-Success "Application settings configured"

    # Step 6: Verify Managed Identity
    Write-Step "Step 6: Verifying Managed Identity"

    Write-Info "Checking system-assigned identity..."
    $identity = az functionapp identity show `
        --name $FunctionAppName `
        --resource-group $ResourceGroup `
        2>&1 | ConvertFrom-Json

    if ($identity.principalId) {
        Write-Success "Managed Identity enabled"
        Write-Info "  Principal ID: $($identity.principalId)"

        # Check role assignments
        Write-Info "Checking role assignments..."
        $roles = az role assignment list `
            --assignee $identity.principalId `
            --output json `
            2>&1 | ConvertFrom-Json

        if ($roles.Count -gt 0) {
            Write-Success "Found $($roles.Count) role assignment(s):"
            foreach ($role in $roles) {
                Write-Info "  - $($role.roleDefinitionName) on $($role.scope)"
            }
        } else {
            Write-Warning "No role assignments found"
            Write-Info "You may need to assign 'Storage Blob Data Contributor' role manually"
        }
    } else {
        Write-Warning "Managed Identity not enabled"
        Write-Info "Enabling system-assigned identity..."
        az functionapp identity assign `
            --name $FunctionAppName `
            --resource-group $ResourceGroup `
            --output none
        Write-Success "Managed Identity enabled"
    }

    # Step 7: Post-deployment verification
    Write-Step "Step 7: Post-Deployment Verification"

    Write-Info "Listing deployed functions..."
    $functions = az functionapp function list `
        --name $FunctionAppName `
        --resource-group $ResourceGroup `
        2>&1 | ConvertFrom-Json

    if ($functions) {
        Write-Success "Found $($functions.Count) function(s):"
        foreach ($func in $functions) {
            Write-Info "  - $($func.name)"
        }

        # Verify expected functions
        $expectedFunctions = @(
            "web_crawler_orchestrator",
            "get_configuration_activity",
            "get_document_hashes_activity",
            "crawl_single_website_activity",
            "store_document_hashes_activity",
            "store_crawl_history_activity",
            "start_web_crawler_orchestration",
            "get_orchestration_status",
            "terminate_orchestration",
            "scheduled_crawler_orchestrated"
        )

        $missingFunctions = $expectedFunctions | Where-Object { $functions.name -notcontains $_ }
        if ($missingFunctions.Count -eq 0) {
            Write-Success "All expected functions deployed"
        } else {
            Write-Warning "Missing functions: $($missingFunctions -join ', ')"
        }
    }

    # Step 8: Display next steps
    Write-Step "Step 8: Deployment Complete!"

    Write-Success "Deployment completed successfully!`n"

    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host " NEXT STEPS" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════`n" -ForegroundColor Green

    $functionAppUrl = "https://$FunctionAppName.azurewebsites.net"
    Write-Info "1. Get your function key:"
    Write-Host "   az functionapp keys list --name $FunctionAppName --resource-group $ResourceGroup`n"

    Write-Info "2. Test the deployment:"
    Write-Host "   Invoke-RestMethod -Uri '$functionAppUrl/api/start_web_crawler_orchestration?code=<KEY>' -Method POST`n"

    Write-Info "3. Monitor in Azure Portal:"
    Write-Host "   https://portal.azure.com/#resource/subscriptions/<sub-id>/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$FunctionAppName`n"

    Write-Info "4. View logs:"
    Write-Host "   func azure functionapp logstream $FunctionAppName`n"

    Write-Success "Deployment guide: See DEPLOYMENT-GUIDE.md for detailed testing and monitoring instructions"

} catch {
    Write-Error "Deployment failed: $_"
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}
