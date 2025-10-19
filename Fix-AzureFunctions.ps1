# IMMEDIATE FIX - Run this in PowerShell
# This checks and fixes your Azure Function App configuration

$subscription = "96726562-1726-4984-88c6-2e4f28878873"
$rg = "rg-btp-uks-prod-doc-mon-01"
$funcApp = "func-btp-uks-prod-doc-crawler-01"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "AZURE FUNCTIONS QUICK FIX" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Azure CLI is installed
Write-Host "Checking Azure CLI..." -ForegroundColor Yellow
try {
    az version | Out-Null
    Write-Host "✅ Azure CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI not found. Please install it first." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 1: Checking current app settings..." -ForegroundColor Yellow
$settings = az functionapp config appsettings list `
    --resource-group $rg `
    --name $funcApp `
    --subscription $subscription `
    --query "[?name=='AzureWebJobsFeatureFlags'].value" `
    --output tsv

if ($settings -ne "EnableWorkerIndexing") {
    Write-Host "⚠️  Worker indexing NOT enabled. Fixing..." -ForegroundColor Red
    az functionapp config appsettings set `
        --resource-group $rg `
        --name $funcApp `
        --settings "AzureWebJobsFeatureFlags=EnableWorkerIndexing" `
        --subscription $subscription `
        --output none
    Write-Host "✅ Worker indexing enabled" -ForegroundColor Green
} else {
    Write-Host "✅ Worker indexing already enabled" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 2: Deploying fixed function app..." -ForegroundColor Yellow

if (-not (Test-Path "v2.4.1-hotfix-deployment.zip")) {
    Write-Host "❌ Deployment package not found!" -ForegroundColor Red
    Write-Host "Creating deployment package now..." -ForegroundColor Yellow
    
    Compress-Archive -Path function_app.py,host.json,requirements.txt,websites.json,.funcignore `
        -DestinationPath "v2.4.1-hotfix-deployment.zip" -Force
    
    Write-Host "✅ Deployment package created" -ForegroundColor Green
}

az functionapp deployment source config-zip `
    --resource-group $rg `
    --name $funcApp `
    --src "v2.4.1-hotfix-deployment.zip" `
    --subscription $subscription `
    --timeout 600

Write-Host "✅ Deployment completed" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Restarting function app..." -ForegroundColor Yellow

az functionapp stop --resource-group $rg --name $funcApp --subscription $subscription --output none
Write-Host "⏸️  Stopped. Waiting 30 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

az functionapp start --resource-group $rg --name $funcApp --subscription $subscription --output none
Write-Host "▶️  Started. Waiting 20 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

Write-Host ""
Write-Host "Step 4: Syncing functions..." -ForegroundColor Yellow
az functionapp function sync --resource-group $rg --name $funcApp --subscription $subscription --output none

Write-Host ""
Write-Host "Step 5: Listing functions..." -ForegroundColor Yellow
az functionapp function list `
    --resource-group $rg `
    --name $funcApp `
    --subscription $subscription `
    --query "[].{Name:name}" `
    --output table

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "✅ FIX COMPLETE!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Check Azure Portal:" -ForegroundColor Cyan
Write-Host "   https://portal.azure.com" -ForegroundColor White
Write-Host "   → Resource Groups → $rg" -ForegroundColor White
Write-Host "   → $funcApp → Functions" -ForegroundColor White
Write-Host ""
Write-Host "If functions still don't appear in portal:" -ForegroundColor Yellow
Write-Host "1. Wait 2-3 more minutes" -ForegroundColor White
Write-Host "2. Hard refresh the portal (Ctrl+F5)" -ForegroundColor White
Write-Host "3. Check logs with: az webapp log tail --resource-group $rg --name $funcApp" -ForegroundColor White
Write-Host ""
