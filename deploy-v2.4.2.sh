#!/bin/bash
# Azure Functions Deployment Script - v2.4.2
# CRITICAL: Functions Not Appearing Fix
# Run this in Azure CLI Bash (NOT PowerShell)

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Azure Resource Details
RESOURCE_GROUP="rg-btp-uks-prod-doc-mon-01"
FUNCTION_APP="func-btp-uks-prod-doc-crawler-01"
SUBSCRIPTION="96726562-1726-4984-88c6-2e4f28878873"
DEPLOYMENT_ZIP="v2.4.2-deployment.zip"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Azure Functions Deployment - v2.4.2${NC}"
echo -e "${YELLOW}Function Registration Fix${NC}"
echo -e "${YELLOW}========================================${NC}\n"

# Step 1: Configure App Settings
echo -e "${GREEN}Step 1: Configuring Azure App Settings...${NC}"
echo "Setting AzureWebJobsFeatureFlags=EnableWorkerIndexing..."

az functionapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" \
  --subscription "$SUBSCRIPTION" \
  --settings AzureWebJobsFeatureFlags=EnableWorkerIndexing \
  --output none

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ App settings configured${NC}\n"
else
    echo -e "${RED}❌ Failed to configure app settings${NC}"
    exit 1
fi

# Step 2: Verify deployment package exists
echo -e "${GREEN}Step 2: Verifying deployment package...${NC}"
if [ ! -f "$DEPLOYMENT_ZIP" ]; then
    echo -e "${RED}❌ Deployment package not found: $DEPLOYMENT_ZIP${NC}"
    echo "Please create the package first using:"
    echo "  Compress-Archive -Path function_app.py,host.json,requirements.txt,websites.json -DestinationPath v2.4.2-deployment.zip -Force"
    exit 1
fi
echo -e "${GREEN}✅ Package found: $DEPLOYMENT_ZIP${NC}\n"

# Step 3: Deploy to Azure
echo -e "${GREEN}Step 3: Deploying to Azure Function App...${NC}"
echo "This may take 2-3 minutes..."

az functionapp deployment source config-zip \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" \
  --subscription "$SUBSCRIPTION" \
  --src "$DEPLOYMENT_ZIP"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment successful${NC}\n"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

# Step 4: Restart Function App
echo -e "${GREEN}Step 4: Restarting Function App...${NC}"
echo "This is CRITICAL for function discovery..."

az functionapp restart \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" \
  --subscription "$SUBSCRIPTION" \
  --output none

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Function app restarted${NC}\n"
else
    echo -e "${RED}❌ Restart failed${NC}"
    exit 1
fi

# Wait for startup
echo -e "${YELLOW}Waiting 60 seconds for function app to initialize...${NC}"
for i in {60..1}; do
    echo -ne "\rTime remaining: ${i}s "
    sleep 1
done
echo -e "\n"

# Step 5: Test deployment
echo -e "${GREEN}Step 5: Testing deployment...${NC}"
echo "Testing ping endpoint..."

RESPONSE=$(curl -s -w "\n%{http_code}" "https://${FUNCTION_APP}.azurewebsites.net/api/ping")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Ping endpoint working!${NC}"
    echo "Response: $BODY"
else
    echo -e "${YELLOW}⚠️  Ping endpoint returned: HTTP $HTTP_CODE${NC}"
    echo "Response: $BODY"
fi
echo ""

# Step 6: Verify app settings
echo -e "${GREEN}Step 6: Verifying critical app settings...${NC}"

SETTINGS=$(az functionapp config appsettings list \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" \
  --subscription "$SUBSCRIPTION" \
  --query "[?name=='AzureWebJobsFeatureFlags' || name=='FUNCTIONS_WORKER_RUNTIME'].{name:name, value:value}" \
  --output table)

echo "$SETTINGS"
echo ""

# Final instructions
echo -e "${YELLOW}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${YELLOW}========================================${NC}\n"

echo -e "${GREEN}Next Steps:${NC}"
echo "1. Open Azure Portal: https://portal.azure.com"
echo "2. Navigate to Function App: $FUNCTION_APP"
echo "3. Click 'Functions' in the left menu"
echo "4. Wait 30-60 seconds for function list to populate"
echo ""
echo -e "${GREEN}You should see these functions:${NC}"
echo "  - ping (HTTP GET) - Test endpoint"
echo "  - dashboard (HTTP GET)"
echo "  - websites (HTTP GET)"
echo "  - manual_crawl (HTTP POST)"
echo "  - scheduled_crawler (Timer)"
echo "  - scheduled_crawler_orchestrated (Timer)"
echo "  - web_crawler_orchestrator (Orchestration)"
echo "  - 6 activity functions"
echo "  - Additional HTTP triggers"
echo ""
echo -e "${GREEN}Test URLs:${NC}"
echo "  Ping: https://${FUNCTION_APP}.azurewebsites.net/api/ping"
echo "  Dashboard: https://${FUNCTION_APP}.azurewebsites.net/api/dashboard"
echo "  Websites: https://${FUNCTION_APP}.azurewebsites.net/api/websites"
echo ""
echo -e "${YELLOW}If functions still don't appear:${NC}"
echo "  1. Check Application Insights logs in Azure Portal"
echo "  2. Look for errors in the Log stream"
echo "  3. See COMPLETE-FIX-FUNCTIONS-NOT-APPEARING.md"
echo ""
echo -e "${GREEN}Deployment script completed successfully!${NC}"
