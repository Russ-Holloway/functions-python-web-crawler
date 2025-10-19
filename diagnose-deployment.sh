#!/bin/bash
# Diagnostic script for Function App deployment issues

echo "🔍 DIAGNOSING FUNCTION APP DEPLOYMENT"
echo "======================================"
echo ""

echo "📋 Step 1: Checking Function App existence and status..."
echo ""

# Check if app is reachable (without API path)
echo "Testing base URL..."
curl -I https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net 2>&1 | grep -E "HTTP|www-authenticate|server" | head -5
echo ""

echo "Testing with SCM (Kudu) endpoint..."
curl -I https://func-btp-uks-prod-doc-crawler-01.scm.azurewebsites.net 2>&1 | grep -E "HTTP|www-authenticate" | head -3
echo ""

echo "📋 Step 2: Testing known function endpoints..."
echo ""

# Test different endpoints
endpoints=(
    "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/ping"
    "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/websites"
    "https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/admin/functions"
)

for endpoint in "${endpoints[@]}"; do
    echo "Testing: $endpoint"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint" 2>&1)
    echo "  Status: $response"
    
    if [ "$response" = "404" ]; then
        echo "  ❌ Not found - Function may not be registered"
    elif [ "$response" = "401" ]; then
        echo "  ⚠️  Authentication required - Function might be there but protected"
    elif [ "$response" = "200" ]; then
        echo "  ✅ Success!"
    else
        echo "  ⚠️  Unexpected status"
    fi
    echo ""
done

echo "📋 Step 3: GitHub Actions Status"
echo ""
echo "Please check: https://github.com/Russ-Holloway/functions-python-web-crawler/actions"
echo ""
echo "Look for:"
echo "  1. Green checkmark = Deployment succeeded"
echo "  2. Red X = Deployment failed"
echo "  3. Yellow dot = Still running"
echo ""

echo "📋 Step 4: Common Issues"
echo ""
echo "If functions aren't appearing, common causes are:"
echo "  1. ⏰ Deployment still in progress (wait 5-8 minutes)"
echo "  2. 🔒 Authentication level set too high (should be ANONYMOUS)"
echo "  3. 🐍 Python version mismatch (workflow uses 3.11)"
echo "  4. 📦 Missing files in deployment package"
echo "  5. ⚙️  Function App needs restart after deployment"
echo ""

echo "📋 Step 5: Recommended Next Steps"
echo ""
echo "If deployment completed but functions still don't work:"
echo ""
echo "Option 1: Check if it's an auth issue"
echo "  - Functions may be protected by auth level"
echo "  - Need to use function keys to call them"
echo ""
echo "Option 2: Force restart Function App"
echo "  Run: az functionapp restart \\"
echo "       --resource-group rg-btp-uks-prod-doc-mon-01 \\"
echo "       --name func-btp-uks-prod-doc-crawler-01 \\"
echo "       --subscription 96726562-1726-4984-88c6-2e4f28878873"
echo ""
echo "Option 3: Check Function App logs"
echo "  Run: az functionapp logs tail \\"
echo "       --resource-group rg-btp-uks-prod-doc-mon-01 \\"
echo "       --name func-btp-uks-prod-doc-crawler-01 \\"
echo "       --subscription 96726562-1726-4984-88c6-2e4f28878873"
echo ""

echo "======================================"
echo "🔍 DIAGNOSIS COMPLETE"
