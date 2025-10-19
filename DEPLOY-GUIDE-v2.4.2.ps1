# ⚠️ IMPORTANT: This PowerShell script guides you to use Azure CLI Bash
# Azure Functions deployment MUST be done from Azure CLI in Bash mode

Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "Azure Functions Deployment - v2.4.2" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Yellow

Write-Host "✅ Deployment package created: v2.4.2-deployment.zip" -ForegroundColor Green
Write-Host "`nThis package includes a new 'ping' test endpoint to verify deployment.`n" -ForegroundColor Cyan

Write-Host "⚠️  CRITICAL: You must deploy using Azure CLI in Bash mode`n" -ForegroundColor Red

Write-Host "HOW TO DEPLOY:`n" -ForegroundColor Yellow

Write-Host "Option 1: Use Windows Subsystem for Linux (WSL)" -ForegroundColor Cyan
Write-Host "  1. Open WSL / Ubuntu terminal"
Write-Host "  2. Navigate to this directory:"
Write-Host "     cd ""/mnt/c/Users/4530Holl/OneDrive - British Transport Police/_Open-Ai/Web-Crawler-Repo/functions-python-web-crawler/functions-python-web-crawler""" -ForegroundColor Gray
Write-Host "  3. Make script executable:"
Write-Host "     chmod +x deploy-v2.4.2.sh" -ForegroundColor Gray
Write-Host "  4. Run deployment:"
Write-Host "     ./deploy-v2.4.2.sh" -ForegroundColor Gray
Write-Host ""

Write-Host "Option 2: Use Git Bash" -ForegroundColor Cyan
Write-Host "  1. Open Git Bash terminal"
Write-Host "  2. Navigate to this directory:"
Write-Host "     cd '/c/Users/4530Holl/OneDrive - British Transport Police/_Open-Ai/Web-Crawler-Repo/functions-python-web-crawler/functions-python-web-crawler'" -ForegroundColor Gray
Write-Host "  3. Run deployment:"
Write-Host "     bash deploy-v2.4.2.sh" -ForegroundColor Gray
Write-Host ""

Write-Host "Option 3: Use Azure Cloud Shell (Recommended)" -ForegroundColor Cyan
Write-Host "  1. Open https://portal.azure.com" -ForegroundColor Gray
Write-Host "  2. Click the Cloud Shell icon (>_) at the top" -ForegroundColor Gray
Write-Host "  3. Upload v2.4.2-deployment.zip using the upload button" -ForegroundColor Gray
Write-Host "  4. Run these commands:" -ForegroundColor Gray
Write-Host ""
Write-Host "     # Set the critical app setting" -ForegroundColor DarkGray
Write-Host "     az functionapp config appsettings set \" -ForegroundColor Gray
Write-Host "       --resource-group rg-btp-uks-prod-doc-mon-01 \" -ForegroundColor Gray
Write-Host "       --name func-btp-uks-prod-doc-crawler-01 \" -ForegroundColor Gray
Write-Host "       --subscription 96726562-1726-4984-88c6-2e4f28878873 \" -ForegroundColor Gray
Write-Host "       --settings AzureWebJobsFeatureFlags=EnableWorkerIndexing" -ForegroundColor Gray
Write-Host ""
Write-Host "     # Deploy the package" -ForegroundColor DarkGray
Write-Host "     az functionapp deployment source config-zip \" -ForegroundColor Gray
Write-Host "       --resource-group rg-btp-uks-prod-doc-mon-01 \" -ForegroundColor Gray
Write-Host "       --name func-btp-uks-prod-doc-crawler-01 \" -ForegroundColor Gray
Write-Host "       --subscription 96726562-1726-4984-88c6-2e4f28878873 \" -ForegroundColor Gray
Write-Host "       --src v2.4.2-deployment.zip" -ForegroundColor Gray
Write-Host ""
Write-Host "     # Restart the function app (CRITICAL)" -ForegroundColor DarkGray
Write-Host "     az functionapp restart \" -ForegroundColor Gray
Write-Host "       --resource-group rg-btp-uks-prod-doc-mon-01 \" -ForegroundColor Gray
Write-Host "       --name func-btp-uks-prod-doc-crawler-01 \" -ForegroundColor Gray
Write-Host "       --subscription 96726562-1726-4984-88c6-2e4f28878873" -ForegroundColor Gray
Write-Host ""

Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "After Deployment:" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Yellow

Write-Host "1. Wait 2-3 minutes for function app to initialize" -ForegroundColor Cyan
Write-Host "2. Test the ping endpoint:" -ForegroundColor Cyan
Write-Host "   https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/ping`n" -ForegroundColor Gray

Write-Host "3. Check Azure Portal:" -ForegroundColor Cyan
Write-Host "   - Navigate to Function App: func-btp-uks-prod-doc-crawler-01" -ForegroundColor Gray
Write-Host "   - Click 'Functions' in left menu" -ForegroundColor Gray
Write-Host "   - You should see all 20 functions (including new 'ping' function)`n" -ForegroundColor Gray

Write-Host "========================================`n" -ForegroundColor Yellow

# Optionally test if we can reach the endpoint
Write-Host "Testing if function app is reachable..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Function app is online (HTTP $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Function app status: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   This is normal if not yet deployed or app is stopped" -ForegroundColor DarkGray
}

Write-Host "`nReady to deploy! Choose one of the options above.`n" -ForegroundColor Green
