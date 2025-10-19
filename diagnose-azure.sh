#!/bin/bash
# Azure Functions Diagnostic Script
# Run this in Azure CLI Bash to diagnose why functions aren't appearing

SUBSCRIPTION="96726562-1726-4984-88c6-2e4f28878873"
RG="rg-btp-uks-prod-doc-mon-01"
FUNCAPP="func-btp-uks-prod-doc-crawler-01"

echo "=========================================="
echo "Azure Functions Diagnostic Report"
echo "Function App: $FUNCAPP"
echo "=========================================="
echo ""

echo "1️⃣ CHECKING APP SETTINGS..."
echo "Looking for critical Python v2 settings..."
az functionapp config appsettings list \
  --resource-group $RG \
  --name $FUNCAPP \
  --subscription $SUBSCRIPTION \
  --query "[?name=='AzureWebJobsFeatureFlags' || name=='FUNCTIONS_WORKER_RUNTIME' || name=='WEBSITE_RUN_FROM_PACKAGE' || name=='FUNCTIONS_EXTENSION_VERSION'].{Name:name, Value:value}" \
  --output table

echo ""
echo "2️⃣ CHECKING FUNCTION APP STATUS..."
az functionapp show \
  --resource-group $RG \
  --name $FUNCAPP \
  --subscription $SUBSCRIPTION \
  --query "{State:state, Enabled:enabled, DefaultHostName:defaultHostName, PythonVersion:siteConfig.linuxFxVersion}" \
  --output json

echo ""
echo "3️⃣ CHECKING DEPLOYMENT STATUS..."
az webapp deployment source show \
  --resource-group $RG \
  --name $FUNCAPP \
  --subscription $SUBSCRIPTION 2>/dev/null || echo "No deployment source configured"

echo ""
echo "4️⃣ LISTING FUNCTIONS (if visible)..."
az functionapp function list \
  --resource-group $RG \
  --name $FUNCAPP \
  --subscription $SUBSCRIPTION \
  --query "[].{Name:name, IsDisabled:config.disabled}" \
  --output table 2>/dev/null || echo "⚠️  No functions found!"

echo ""
echo "5️⃣ CHECKING RECENT LOGS..."
echo "Looking for errors in the last 100 log entries..."
az monitor app-insights query \
  --app func-btp-uks-prod-doc-crawler-01 \
  --analytics-query "traces | where timestamp > ago(1h) | where message contains 'error' or message contains 'fail' | project timestamp, message | take 10" \
  --subscription $SUBSCRIPTION 2>/dev/null || echo "App Insights not available or not configured"

echo ""
echo "=========================================="
echo "✅ DIAGNOSTIC COMPLETE"
echo "=========================================="
echo ""
echo "NEXT STEPS:"
echo "1. If AzureWebJobsFeatureFlags != 'EnableWorkerIndexing' → Run fix script"
echo "2. If FUNCTIONS_WORKER_RUNTIME != 'python' → Run fix script"
echo "3. If no functions listed → Check logs and redeploy"
echo ""
