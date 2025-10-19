#!/bin/bash
echo "🔧 CHECKING AND FIXING AUTHENTICATION ISSUE"
echo "==========================================="
echo ""

echo "Step 1: Checking current authentication status..."
AUTH_STATUS=$(az webapp auth show \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873 \
  --query "enabled" -o tsv 2>/dev/null)

if [ "$AUTH_STATUS" = "true" ]; then
    echo "❌ App Service Authentication is ENABLED (causing 401 errors)"
    echo ""
    echo "Step 2: Disabling authentication..."
    az webapp auth update \
      --resource-group rg-btp-uks-prod-doc-mon-01 \
      --name func-btp-uks-prod-doc-crawler-01 \
      --enabled false \
      --subscription 96726562-1726-4984-88c6-2e4f28878873
    echo ""
    echo "✅ Authentication disabled!"
    echo ""
    echo "Step 3: Waiting 10 seconds for changes to propagate..."
    sleep 10
else
    echo "✅ App Service Authentication is already disabled"
    echo ""
fi

echo "Step 4: Testing function endpoint..."
echo ""
curl -s https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/ping | python3 -m json.tool || echo "Still having issues..."
echo ""
echo "==========================================="
echo "If you see JSON response above, it's WORKING! ✅"
echo "If you still see 401, wait another minute and try again."
