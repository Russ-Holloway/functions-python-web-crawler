# Complete Automated Deployment Script
# Durable Functions Web Crawler v3.0.0-alpha
# Deploys to Azure using ZIP method with all BTP resources

param(
    [Parameter(Mandatory=$false)]
    [switch]$SkipValidation
)

# ============================================================================
# AZURE RESOURCE CONFIGURATION (from AZURE_RESOURCE_REFERENCE.md)
# ============================================================================

$FUNCTION_APP_NAME = "func-btp-uks-prod-doc-crawler-01"
$RESOURCE_GROUP = "rg-btp-uks-prod-doc-mon-01"
$SUBSCRIPTION_ID = "96726562-1726-4984-88c6-2e4f28878873"
$STORAGE_ACCOUNT = "stbtpuksprodcrawler01"
$REGION = "uksouth"

# ============================================================================
# COLOR OUTPUT FUNCTIONS
# ============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║ $Message" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
}

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

function Write-Progress {
    param([string]$Message)
    Write-Host "⏳ $Message..." -ForegroundColor Yellow
}

# ============================================================================
# MAIN DEPLOYMENT SCRIPT
# ============================================================================

try {
    Write-Host "`n" -NoNewline
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║                                                            ║" -ForegroundColor Magenta
    Write-Host "║     DURABLE FUNCTIONS WEB CRAWLER - AUTO DEPLOYMENT       ║" -ForegroundColor Magenta
    Write-Host "║              Version 3.0.0-alpha                           ║" -ForegroundColor Magenta
    Write-Host "║                                                            ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""

    # Display configuration
    Write-Info "Deployment Configuration:"
    Write-Host "  Function App:    $FUNCTION_APP_NAME" -ForegroundColor Gray
    Write-Host "  Resource Group:  $RESOURCE_GROUP" -ForegroundColor Gray
    Write-Host "  Subscription:    $SUBSCRIPTION_ID" -ForegroundColor Gray
    Write-Host "  Storage Account: $STORAGE_ACCOUNT" -ForegroundColor Gray
    Write-Host "  Region:          $REGION" -ForegroundColor Gray
    Write-Host ""

    # ========================================================================
    # STEP 1: PRE-DEPLOYMENT VALIDATION
    # ========================================================================
    
    Write-Step "STEP 1: Pre-Deployment Validation"

    # Check Azure CLI
    Write-Progress "Checking Azure CLI"
    $azVersion = az --version 2>&1 | Select-String "azure-cli"
    if ($azVersion) {
        Write-Success "Azure CLI installed: $azVersion"
    } else {
        Write-Error "Azure CLI not found. Please install from: https://aka.ms/installazurecli"
        exit 1
    }

    # Check Azure login
    Write-Progress "Verifying Azure login"
    $account = az account show 2>&1 | ConvertFrom-Json
    if ($account) {
        Write-Success "Logged in as: $($account.user.name)"
        Write-Info "  Subscription: $($account.name) ($($account.id))"
    } else {
        Write-Warning "Not logged in to Azure. Initiating login..."
        az login --use-device-code
        $account = az account show 2>&1 | ConvertFrom-Json
    }

    # Set correct subscription
    Write-Progress "Setting subscription"
    az account set --subscription $SUBSCRIPTION_ID 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Subscription set to: $SUBSCRIPTION_ID"
    } else {
        Write-Error "Failed to set subscription"
        exit 1
    }

    # Verify Function App exists
    Write-Progress "Verifying Function App exists"
    $functionApp = az functionapp show `
        --name $FUNCTION_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        2>&1 | ConvertFrom-Json
    
    if ($functionApp) {
        Write-Success "Function App found: $FUNCTION_APP_NAME"
        Write-Info "  State: $($functionApp.state)"
        Write-Info "  Location: $($functionApp.location)"
        Write-Info "  Default Hostname: $($functionApp.defaultHostName)"
    } else {
        Write-Error "Function App not found: $FUNCTION_APP_NAME"
        exit 1
    }

    # Run system validation (unless skipped)
    if (-not $SkipValidation) {
        Write-Progress "Running system validation"
        if (Test-Path "tests\validate_system.py") {
            try {
                $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
                if ($pythonCmd) {
                    python tests\validate_system.py
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "System validation passed"
                    } else {
                        Write-Warning "Validation found issues"
                        $response = Read-Host "Continue anyway? (y/n)"
                        if ($response -ne 'y') {
                            Write-Error "Deployment cancelled"
                            exit 1
                        }
                    }
                } else {
                    Write-Warning "Python not found, skipping validation"
                }
            } catch {
                Write-Warning "Could not run validation: $_"
            }
        } else {
            Write-Warning "Validation script not found, skipping"
        }
    }

    # ========================================================================
    # STEP 2: CREATE DEPLOYMENT PACKAGE
    # ========================================================================
    
    Write-Step "STEP 2: Creating Deployment Package"

    # Verify required files
    $requiredFiles = @(
        "function_app.py",
        "host.json",
        "requirements.txt",
        "websites.json"
    )

    Write-Info "Checking required files..."
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            $fileInfo = Get-Item $file
            Write-Success "$file ($('{0:N0}' -f $fileInfo.Length) bytes)"
        } else {
            Write-Error "Required file not found: $file"
            exit 1
        }
    }

    # Remove old deployment zip
    if (Test-Path "deploy.zip") {
        Write-Info "Removing old deploy.zip"
        Remove-Item "deploy.zip" -Force
    }

    # Create deployment package
    Write-Progress "Creating deployment ZIP package"
    try {
        Compress-Archive -Path $requiredFiles -DestinationPath "deploy.zip" -Force
        $zipSize = (Get-Item "deploy.zip").Length
        Write-Success "Deployment package created: deploy.zip ($('{0:N0}' -f $zipSize) bytes)"
        
        # Verify ZIP contents
        Write-Info "Verifying ZIP contents..."
        Expand-Archive -Path "deploy.zip" -DestinationPath "temp_verify" -Force
        $zipContents = Get-ChildItem "temp_verify"
        foreach ($item in $zipContents) {
            Write-Info "  ✓ $($item.Name)"
        }
        Remove-Item "temp_verify" -Recurse -Force
        
    } catch {
        Write-Error "Failed to create deployment package: $_"
        exit 1
    }

    # ========================================================================
    # STEP 3: DEPLOY TO AZURE
    # ========================================================================
    
    Write-Step "STEP 3: Deploying to Azure Function App"

    Write-Progress "Uploading deployment package to Azure"
    Write-Warning "This may take 2-3 minutes..."
    
    az functionapp deployment source config-zip `
        --resource-group $RESOURCE_GROUP `
        --name $FUNCTION_APP_NAME `
        --subscription $SUBSCRIPTION_ID `
        --src "deploy.zip" `
        --build-remote true `
        2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Deployment successful!"
    } else {
        Write-Error "Deployment failed with exit code $LASTEXITCODE"
        Write-Info "Checking deployment logs..."
        az functionapp log deployment show `
            --name $FUNCTION_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            2>&1
        exit 1
    }

    # ========================================================================
    # STEP 4: CONFIGURE APPLICATION SETTINGS
    # ========================================================================
    
    Write-Step "STEP 4: Configuring Application Settings"

    # Set WEBSITES_CONFIG_LOCATION
    Write-Progress "Setting WEBSITES_CONFIG_LOCATION=local"
    az functionapp config appsettings set `
        --name $FUNCTION_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --subscription $SUBSCRIPTION_ID `
        --settings "WEBSITES_CONFIG_LOCATION=local" `
        --output none

    if ($LASTEXITCODE -eq 0) {
        Write-Success "WEBSITES_CONFIG_LOCATION set to 'local'"
    }

    # Set STORAGE_ACCOUNT_NAME
    Write-Progress "Setting STORAGE_ACCOUNT_NAME"
    az functionapp config appsettings set `
        --name $FUNCTION_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --subscription $SUBSCRIPTION_ID `
        --settings "STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT" `
        --output none

    if ($LASTEXITCODE -eq 0) {
        Write-Success "STORAGE_ACCOUNT_NAME set to '$STORAGE_ACCOUNT'"
    }

    # Verify settings
    Write-Progress "Verifying application settings"
    $settings = az functionapp config appsettings list `
        --name $FUNCTION_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --subscription $SUBSCRIPTION_ID `
        --query "[?name=='WEBSITES_CONFIG_LOCATION' || name=='STORAGE_ACCOUNT_NAME'].{Name:name, Value:value}" `
        2>&1 | ConvertFrom-Json

    if ($settings) {
        Write-Success "Application settings configured:"
        foreach ($setting in $settings) {
            Write-Info "  $($setting.Name) = $($setting.Value)"
        }
    }

    # ========================================================================
    # STEP 5: VERIFY MANAGED IDENTITY
    # ========================================================================
    
    Write-Step "STEP 5: Verifying Managed Identity"

    Write-Progress "Checking system-assigned identity"
    $identity = az functionapp identity show `
        --name $FUNCTION_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --subscription $SUBSCRIPTION_ID `
        2>&1 | ConvertFrom-Json

    if ($identity.principalId) {
        Write-Success "Managed Identity enabled"
        Write-Info "  Principal ID: $($identity.principalId)"
        
        # Check role assignments
        Write-Progress "Checking role assignments"
        $roles = az role assignment list `
            --assignee $identity.principalId `
            --subscription $SUBSCRIPTION_ID `
            2>&1 | ConvertFrom-Json

        if ($roles -and $roles.Count -gt 0) {
            Write-Success "Found $($roles.Count) role assignment(s):"
            foreach ($role in $roles) {
                Write-Info "  ✓ $($role.roleDefinitionName)"
            }
            
            # Check if Storage Blob Data Contributor is assigned
            $hasStorageRole = $roles | Where-Object { $_.roleDefinitionName -eq "Storage Blob Data Contributor" }
            if (-not $hasStorageRole) {
                Write-Warning "Storage Blob Data Contributor role not found"
                Write-Info "You may need to assign it manually using:"
                Write-Host "  az role assignment create --assignee $($identity.principalId) --role 'Storage Blob Data Contributor' --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT" -ForegroundColor Gray
            }
        } else {
            Write-Warning "No role assignments found"
            Write-Info "Managed Identity is enabled but has no role assignments"
        }
    } else {
        Write-Warning "Managed Identity not enabled"
        Write-Info "Enabling system-assigned identity..."
        az functionapp identity assign `
            --name $FUNCTION_APP_NAME `
            --resource-group $RESOURCE_GROUP `
            --subscription $SUBSCRIPTION_ID `
            --output none
        Write-Success "Managed Identity enabled"
    }

    # ========================================================================
    # STEP 6: VERIFY DEPLOYED FUNCTIONS
    # ========================================================================
    
    Write-Step "STEP 6: Verifying Deployed Functions"

    Write-Progress "Listing deployed functions"
    Start-Sleep -Seconds 5  # Give Azure time to sync

    $functions = az functionapp function list `
        --name $FUNCTION_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --subscription $SUBSCRIPTION_ID `
        2>&1 | ConvertFrom-Json

    if ($functions) {
        Write-Success "Found $($functions.Count) function(s):"
        foreach ($func in $functions) {
            Write-Info "  ✓ $($func.name)"
        }

        # Check for expected functions
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

        $missingFunctions = @()
        foreach ($expected in $expectedFunctions) {
            if ($functions.name -notcontains $expected) {
                $missingFunctions += $expected
            }
        }

        if ($missingFunctions.Count -eq 0) {
            Write-Success "All expected functions deployed successfully!"
        } else {
            Write-Warning "Missing functions:"
            foreach ($missing in $missingFunctions) {
                Write-Warning "  ✗ $missing"
            }
        }
    } else {
        Write-Warning "Could not retrieve function list"
    }

    # ========================================================================
    # STEP 7: GET FUNCTION KEY
    # ========================================================================
    
    Write-Step "STEP 7: Retrieving Function Key"

    Write-Progress "Getting function key"
    $keys = az functionapp keys list `
        --name $FUNCTION_APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --subscription $SUBSCRIPTION_ID `
        2>&1 | ConvertFrom-Json

    if ($keys) {
        $functionKey = $keys.functionKeys.default
        Write-Success "Function key retrieved"
        Write-Info "  Key: $functionKey"
        
        # Save to environment variable for testing
        $env:FUNCTION_KEY = $functionKey
    } else {
        Write-Warning "Could not retrieve function key"
    }

    # ========================================================================
    # STEP 8: TEST DEPLOYMENT
    # ========================================================================
    
    Write-Step "STEP 8: Testing Deployment"

    $functionAppUrl = "https://$FUNCTION_APP_NAME.azurewebsites.net"
    
    if ($functionKey) {
        Write-Info "Testing orchestration endpoint..."
        Write-Progress "Starting test orchestration"
        
        try {
            $body = @{
                config_location = "local"
            } | ConvertTo-Json

            $startUrl = "$functionAppUrl/api/start_web_crawler_orchestration?code=$functionKey"
            
            $response = Invoke-RestMethod -Uri $startUrl -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
            
            Write-Success "Orchestration started successfully!"
            Write-Info "  Instance ID: $($response.id)"
            
            if ($response.statusQueryGetUri) {
                Write-Info "  Status URL: $($response.statusQueryGetUri)"
                
                # Poll status
                Write-Progress "Checking orchestration status"
                Start-Sleep -Seconds 5
                
                try {
                    $status = Invoke-RestMethod -Uri $response.statusQueryGetUri -Method GET -ErrorAction Stop
                    Write-Success "Orchestration Status: $($status.runtimeStatus)"
                    
                    if ($status.runtimeStatus -eq "Running" -or $status.runtimeStatus -eq "Pending") {
                        Write-Info "Orchestration is running. Check status later using:"
                        Write-Host "  Invoke-RestMethod -Uri '$($response.statusQueryGetUri)' | ConvertTo-Json -Depth 10" -ForegroundColor Gray
                    } elseif ($status.runtimeStatus -eq "Completed") {
                        Write-Success "Orchestration completed!"
                        if ($status.output) {
                            Write-Info "Results:"
                            Write-Host ($status.output | ConvertTo-Json -Depth 5) -ForegroundColor Gray
                        }
                    }
                } catch {
                    Write-Warning "Could not get status: $_"
                }
            }
            
        } catch {
            Write-Warning "Could not start orchestration: $_"
            Write-Info "You can test manually using:"
            Write-Host "  Invoke-RestMethod -Uri '$startUrl' -Method POST -Body '{`"config_location`":`"local`"}' -ContentType 'application/json'" -ForegroundColor Gray
        }
    } else {
        Write-Warning "Skipping test (no function key)"
    }

    # ========================================================================
    # DEPLOYMENT COMPLETE
    # ========================================================================
    
    Write-Host "`n" -NoNewline
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                                                            ║" -ForegroundColor Green
    Write-Host "║              DEPLOYMENT COMPLETED SUCCESSFULLY!            ║" -ForegroundColor Green
    Write-Host "║                                                            ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""

    # Summary
    Write-Info "Deployment Summary:"
    Write-Host "  Function App:     $FUNCTION_APP_NAME" -ForegroundColor Gray
    Write-Host "  URL:              $functionAppUrl" -ForegroundColor Gray
    Write-Host "  Functions:        $($functions.Count) deployed" -ForegroundColor Gray
    Write-Host "  Config Location:  local (websites.json in ZIP)" -ForegroundColor Gray
    Write-Host ""

    Write-Info "Next Steps:"
    Write-Host "  1. Monitor execution in Azure Portal:" -ForegroundColor Gray
    Write-Host "     https://portal.azure.com/#resource/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$FUNCTION_APP_NAME" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. View logs:" -ForegroundColor Gray
    Write-Host "     az functionapp log tail --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. Manually trigger orchestration:" -ForegroundColor Gray
    if ($functionKey) {
        Write-Host "     Invoke-RestMethod -Uri '$functionAppUrl/api/start_web_crawler_orchestration?code=$functionKey' -Method POST -Body '{`"config_location`":`"local`"}' -ContentType 'application/json'" -ForegroundColor Gray
    } else {
        Write-Host "     (Get function key first using: az functionapp keys list --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP)" -ForegroundColor Gray
    }
    Write-Host ""

    Write-Success "Deployment completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host ""

} catch {
    Write-Host "`n" -NoNewline
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║                                                            ║" -ForegroundColor Red
    Write-Host "║                  DEPLOYMENT FAILED!                        ║" -ForegroundColor Red
    Write-Host "║                                                            ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Error "Error: $_"
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}
