#!/bin/bash
# Complete fix for Azure Function App - Run this in Azure CLI Bash

# Azure resource details
SUBSCRIPTION="96726562-1726-4984-88c6-2e4f28878873"
RG="rg-btp-uks-prod-doc-mon-01"
FUNCAPP="func-btp-uks-prod-doc-crawler-01"

echo "🚀 Fixing Azure Function App: $FUNCAPP"
echo "=================================================="
echo ""

# Step 1: Enable Worker Indexing (CRITICAL!)
echo "Step 1: Enabling Worker Indexing..."
az functionapp config appsettings set \
  --resource-group $RG \
  --name $FUNCAPP \
  --settings "AzureWebJobsFeatureFlags=EnableWorkerIndexing" \
  --subscription $SUBSCRIPTION \
  --output none

echo "✅ Worker indexing enabled"
echo ""

# Step 2: Deploy the fixed code
echo "Step 2: Deploying fixed function app..."
az functionapp deployment source config-zip \
  --resource-group $RG \
  --name $FUNCAPP \
  --src v2.4.1-hotfix-deployment.zip \
  --subscription $SUBSCRIPTION

echo "✅ Deployment complete"
echo ""

# Step 3: Stop the function app
echo "Step 3: Stopping function app..."
az functionapp stop \
  --resource-group $RG \
  --name $FUNCAPP \
  --subscription $SUBSCRIPTION

echo "⏸️  Stopped. Waiting 30 seconds..."
sleep 30

# Step 4: Start the function app
echo ""
echo "Step 4: Starting function app..."
az functionapp start \
  --resource-group $RG \
  --name $FUNCAPP \
  --subscription $SUBSCRIPTION

echo "▶️  Started. Waiting 30 seconds for warm-up..."
sleep 30

# Step 5: Force function sync
echo ""
echo "Step 5: Syncing functions..."
az functionapp function sync \
  --resource-group $RG \
  --name $FUNCAPP \
  --subscription $SUBSCRIPTION

echo "✅ Function sync complete"
echo ""

# Step 6: List functions
echo "Step 6: Verifying functions are visible..."
echo ""
az functionapp function list \
  --resource-group $RG \
  --name $FUNCAPP \
  --subscription $SUBSCRIPTION \
  --query "[].name" \
  --output table

echo ""
echo "=================================================="
echo "✅ FIX COMPLETE!"
echo "=================================================="
echo ""
echo "Go to Azure Portal and check:"
echo "https://portal.azure.com"
echo "→ Resource Groups → $RG → $FUNCAPP → Functions"
echo ""
echo "All functions should now be visible!"
echo ""
