# Test Deployment Script
# Quick script to test deployed Azure Function
# Durable Functions Web Crawler v3.0.0-alpha

param(
    [Parameter(Mandatory=$true)]
    [string]$FunctionAppName,
    
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$false)]
    [string]$FunctionKey = ""
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

try {
    Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   AZURE FUNCTION DEPLOYMENT TEST                         ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

    # Get function key if not provided
    if (-not $FunctionKey) {
        Write-Info "Retrieving function key..."
        $keys = az functionapp keys list --name $FunctionAppName --resource-group $ResourceGroup | ConvertFrom-Json
        $FunctionKey = $keys.functionKeys.default
        if ($FunctionKey) {
            Write-Success "Function key retrieved"
        } else {
            Write-Error "Failed to retrieve function key"
            exit 1
        }
    }

    # Construct URLs
    $functionAppUrl = "https://$FunctionAppName.azurewebsites.net"
    $startUrl = "$functionAppUrl/api/start_web_crawler_orchestration?code=$FunctionKey"

    Write-Info "Function App URL: $functionAppUrl"
    Write-Info ""

    # Test 1: Start orchestration
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host " TEST 1: Starting Orchestration" -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════`n" -ForegroundColor Yellow

    Write-Info "Sending POST request to start orchestration..."
    
    $body = @{
        config_location = "blob"
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri $startUrl -Method POST -Body $body -ContentType "application/json"
        
        Write-Success "Orchestration started successfully!`n"
        Write-Host "Response:" -ForegroundColor Cyan
        $response | ConvertTo-Json -Depth 10 | Write-Host
        
        $instanceId = $response.id
        $statusQueryGetUri = $response.statusQueryGetUri
        
    } catch {
        Write-Error "Failed to start orchestration"
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }

    # Test 2: Check status
    Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host " TEST 2: Checking Orchestration Status" -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════`n" -ForegroundColor Yellow

    Write-Info "Instance ID: $instanceId"
    Write-Info "Waiting 5 seconds before checking status..."
    Start-Sleep -Seconds 5

    Write-Info "Polling status endpoint..."
    $maxAttempts = 12  # 1 minute total (5 second intervals)
    $attempt = 0
    $completed = $false

    while ($attempt -lt $maxAttempts -and -not $completed) {
        $attempt++
        Write-Info "Attempt $attempt of $maxAttempts..."
        
        try {
            $statusResponse = Invoke-RestMethod -Uri $statusQueryGetUri -Method GET
            
            $runtimeStatus = $statusResponse.runtimeStatus
            Write-Info "Status: $runtimeStatus"
            
            if ($runtimeStatus -eq "Completed") {
                $completed = $true
                Write-Success "`nOrchestration completed!`n"
                Write-Host "Final Output:" -ForegroundColor Cyan
                $statusResponse.output | ConvertTo-Json -Depth 10 | Write-Host
                
                # Display summary
                Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Green
                Write-Host " EXECUTION SUMMARY" -ForegroundColor Green
                Write-Host "═══════════════════════════════════════════════════════`n" -ForegroundColor Green
                
                $output = $statusResponse.output
                Write-Success "Total Websites: $($output.total_websites)"
                Write-Success "Successful Crawls: $($output.successful_crawls)"
                
                if ($output.failed_crawls -gt 0) {
                    Write-Warning "Failed Crawls: $($output.failed_crawls)"
                } else {
                    Write-Success "Failed Crawls: $($output.failed_crawls)"
                }
                
                Write-Success "Total Documents: $($output.total_documents)"
                Write-Success "New Documents: $($output.new_documents)"
                Write-Success "Updated Documents: $($output.updated_documents)"
                
                $duration = [DateTime]::Parse($output.end_time) - [DateTime]::Parse($output.start_time)
                Write-Success "Duration: $($duration.TotalSeconds) seconds"
                
            } elseif ($runtimeStatus -eq "Failed") {
                Write-Error "`nOrchestration failed!`n"
                Write-Host "Error Output:" -ForegroundColor Red
                $statusResponse.output | ConvertTo-Json -Depth 10 | Write-Host
                break
            } elseif ($runtimeStatus -eq "Running" -or $runtimeStatus -eq "Pending") {
                Write-Info "Still running... waiting 5 seconds"
                Start-Sleep -Seconds 5
            } else {
                Write-Warning "Unexpected status: $runtimeStatus"
                break
            }
            
        } catch {
            Write-Error "Failed to get status"
            Write-Host $_.Exception.Message -ForegroundColor Red
            break
        }
    }

    if (-not $completed -and $attempt -ge $maxAttempts) {
        Write-Warning "`nOrchestration still running after $($maxAttempts * 5) seconds"
        Write-Info "You can check status later using:"
        Write-Host "  Invoke-RestMethod -Uri '$statusQueryGetUri' -Method GET | ConvertTo-Json -Depth 10"
    }

    # Test 3: Verify blob storage
    Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host " TEST 3: Verifying Blob Storage" -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════`n" -ForegroundColor Yellow

    Write-Info "Checking for recent documents..."
    
    $storageAccount = "stbtpuksprodcrawler01"
    $documentsContainer = "documents"
    
    try {
        $recentBlobs = az storage blob list `
            --account-name $storageAccount `
            --container-name $documentsContainer `
            --auth-mode login `
            --num-results 10 `
            | ConvertFrom-Json
        
        if ($recentBlobs) {
            Write-Success "Found $($recentBlobs.Count) recent blob(s)"
            foreach ($blob in $recentBlobs) {
                Write-Info "  - $($blob.name) ($(([DateTime]$blob.properties.lastModified).ToString('yyyy-MM-dd HH:mm')))"
            }
        } else {
            Write-Warning "No blobs found in documents container"
        }
        
    } catch {
        Write-Warning "Could not access blob storage (may need login or permissions)"
        Write-Info $_.Exception.Message
    }

    # Summary
    Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║   DEPLOYMENT TEST COMPLETE                               ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

    Write-Info "View detailed logs in Azure Portal:"
    Write-Host "  https://portal.azure.com/#resource/subscriptions/<sub-id>/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$FunctionAppName/logStream`n"

    Write-Info "Monitor Application Insights:"
    Write-Host "  Navigate to Function App -> Application Insights -> Live Metrics`n"

    Write-Success "Test completed successfully!"

} catch {
    Write-Error "Test failed: $_"
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
