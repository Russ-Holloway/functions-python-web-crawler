# 🚀 QUICK START - Deploy v2.5.0 Now

## COPY AND PASTE THESE COMMANDS:

### 1. Deploy the package:
```bash
az functionapp deployment source config-zip \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --src v2.5.0-deployment.zip \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

### 2. Restart the Function App (CRITICAL!):
```bash
az functionapp restart \
  --resource-group rg-btp-uks-prod-doc-mon-01 \
  --name func-btp-uks-prod-doc-crawler-01 \
  --subscription 96726562-1726-4984-88c6-2e4f28878873
```

### 3. Test it works:
```bash
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/ping
```

## That's it! 

Check the Azure Portal in 2-3 minutes to see all functions appear.

For detailed instructions, see: DEPLOYMENT-v2.5.0.md
