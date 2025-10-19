#!/bin/bash
# Fix Storage Account Permissions for Function App Managed Identity
# This script assigns the necessary RBAC role for the function app to access blob storage

set -e

# Azure resource details
SUBSCRIPTION_ID="96726562-1726-4984-88c6-2e4f28878873"
RESOURCE_GROUP="rg-btp-uks-prod-doc-mon-01"
FUNCTION_APP_NAME="func-btp-uks-prod-doc-crawler-01"
STORAGE_ACCOUNT_NAME="stbtpuksprodcrawler01"

echo "=========================================="
echo "Fixing Storage Permissions for Function App"
echo "=========================================="
echo ""
echo "Function App: $FUNCTION_APP_NAME"
echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo "Subscription: $SUBSCRIPTION_ID"
echo ""

# Step 1: Get the Function App's managed identity principal ID
echo "Step 1: Getting Function App's managed identity..."
PRINCIPAL_ID=$(az functionapp identity show \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --subscription $SUBSCRIPTION_ID \
  --query principalId \
  --output tsv)

if [ -z "$PRINCIPAL_ID" ]; then
  echo "❌ ERROR: Could not get managed identity principal ID"
  echo "The Function App might not have a system-assigned managed identity enabled."
  echo ""
  echo "Enabling system-assigned managed identity..."
  az functionapp identity assign \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --subscription $SUBSCRIPTION_ID
  
  echo "Waiting 10 seconds for identity to propagate..."
  sleep 10
  
  PRINCIPAL_ID=$(az functionapp identity show \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --subscription $SUBSCRIPTION_ID \
    --query principalId \
    --output tsv)
fi

echo "✓ Managed Identity Principal ID: $PRINCIPAL_ID"
echo ""

# Step 2: Get the storage account resource ID
echo "Step 2: Getting Storage Account resource ID..."
STORAGE_ID=$(az storage account show \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --subscription $SUBSCRIPTION_ID \
  --query id \
  --output tsv)

echo "✓ Storage Account ID: $STORAGE_ID"
echo ""

# Step 3: Assign "Storage Blob Data Contributor" role
echo "Step 3: Assigning 'Storage Blob Data Contributor' role..."
echo "This allows the Function App to read, write, and delete blobs."
echo ""

az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope $STORAGE_ID \
  --subscription $SUBSCRIPTION_ID

echo ""
echo "✓ Role assignment complete!"
echo ""

# Step 4: Verify the role assignment
echo "Step 4: Verifying role assignment..."
ROLE_CHECK=$(az role assignment list \
  --assignee $PRINCIPAL_ID \
  --scope $STORAGE_ID \
  --subscription $SUBSCRIPTION_ID \
  --query "[?roleDefinitionName=='Storage Blob Data Contributor'].roleDefinitionName" \
  --output tsv)

if [ "$ROLE_CHECK" == "Storage Blob Data Contributor" ]; then
  echo "✓ Verification successful! Role assignment confirmed."
else
  echo "⚠ Warning: Could not verify role assignment immediately."
  echo "This is normal - role assignments can take a few minutes to propagate."
fi

echo ""
echo "=========================================="
echo "✅ Permission Fix Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Wait 1-2 minutes for role assignment to propagate"
echo "2. Refresh the dashboard in your browser"
echo "3. The storage error should be resolved"
echo ""
echo "If you still see errors, restart the Function App:"
echo "  az functionapp restart --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP --subscription $SUBSCRIPTION_ID"
echo ""
