#!/bin/bash
# Azure Functions Fix Script - Run ONLY after running diagnose-azure.sh

SUBSCRIPTION="96726562-1726-4984-88c6-2e4f28878873"
RG="rg-btp-uks-prod-doc-mon-01"
FUNCAPP="func-btp-uks-prod-doc-crawler-01"

echo "=========================================="
echo "🔧 FIXING AZURE FUNCTION APP CONFIGURATION"
echo "=========================================="
echo ""

echo "Step 1: Setting AzureWebJobsFeatureFlags..."
az functionapp config appsettings set \
  --resource-group $RG \
  --name $FUNCAPP \
  --settings "AzureWebJobsFeatureFlags=EnableWorkerIndexing" \
  --subscription $SUBSCRIPTION \
  --output none

echo "✅ Worker indexing enabled"
echo ""

echo "Step 2: Verifying Python runtime..."
az functionapp config appsettings set \
  --resource-group $RG \
  --name $FUNCAPP \
  --settings "FUNCTIONS_WORKER_RUNTIME=python" \
  --subscription $SUBSCRIPTION \
  --output none

echo "✅ Python runtime confirmed"
echo ""

echo "Step 3: Deploying function app code..."
if [ ! -f "v2.4.1-hotfix-deployment.zip" ]; then
    echo "❌ ERROR: v2.4.1-hotfix-deployment.zip not found!"
    echo "Please run this script from the project directory"
    exit 1
fi

az functionapp deployment source config-zip \
  --resource-group $RG \
  --name $FUNCAPP \
  --src v2.4.1-hotfix-deployment.zip \
  --subscription $SUBSCRIPTION \
  --timeout 600

echo "✅ Deployment completed"
echo ""

echo "Step 4: Stopping function app..."
az functionapp stop \
  --resource-group $RG \
  --name $FUNCAPP \
  --subscription $SUBSCRIPTION \
  --output none

echo "⏸️  Function app stopped"
echo "⏳ Waiting 30 seconds..."
sleep 30

echo ""
echo "Step 5: Starting function app..."
az functionapp start \
  --resource-group $RG \
  --name $FUNCAPP \
  --subscription $SUBSCRIPTION \
  --output none

echo "▶️  Function app started"
echo "⏳ Waiting 20 seconds for startup..."
sleep 20

echo ""
echo "Step 6: Forcing function sync..."
az functionapp function sync \
  --resource-group $RG \
  --name $FUNCAPP \
  --subscription $SUBSCRIPTION \
  --output none

echo "🔄 Function sync completed"
echo ""

echo "Step 7: Verifying functions are now visible..."
echo ""
az functionapp function list \
  --resource-group $RG \
  --name $FUNCAPP \
  --subscription $SUBSCRIPTION \
  --query "[].{Name:name, IsDisabled:config.disabled}" \
  --output table

echo ""
echo "=========================================="
echo "✅ FIX COMPLETE!"
echo "=========================================="
echo ""
echo "🌐 Check the Azure Portal now:"
echo "   https://portal.azure.com"
echo "   → Resource Groups → $RG"
echo "   → $FUNCAPP → Functions"
echo ""
echo "If functions still don't appear:"
echo "1. Wait 2-3 more minutes"
echo "2. Refresh the portal page (F5)"
echo "3. Check logs: az webapp log tail --resource-group $RG --name $FUNCAPP"
echo ""
