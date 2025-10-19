# 🚀 QUICK DEPLOY - GitHub Actions

## Deploy v2.5.0 in 3 Commands

All your fixes are ready in the code. Just commit and push:

```bash
# 1. Stage changes
git add .

# 2. Commit with version tag
git commit -m "v2.5.0: Fix functions not appearing in portal"

# 3. Push to deploy
git push origin main
```

## What Happens Next

1. ⚙️ **GitHub Actions triggers** (automatic)
2. 🔨 **Build job runs** (1-2 minutes)
3. 🚀 **Deploy job runs** (2-3 minutes)
4. ✅ **Functions appear in portal** (2-3 minutes after deploy)

## Monitor Deployment

Watch it happen:
```
https://github.com/Russ-Holloway/functions-python-web-crawler/actions
```

## Verify It Worked

After ~5-8 minutes total:

```bash
# Test health
curl https://func-btp-uks-prod-doc-crawler-01.azurewebsites.net/api/ping
```

Then check Azure Portal → Functions → Should see 20+ functions!

---

**That's it!** GitHub Actions handles everything automatically.

For details, see: `GITHUB-ACTIONS-DEPLOYMENT.md`
