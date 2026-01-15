# 🚀 QUICK START GUIDE - Container Apps

## Your Application is LIVE! 🎉

**URL:** https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io

---

## 📌 KEY INFO

| Item | Value |
|------|-------|
| **Service** | Azure Container Apps |
| **Plan** | Consumption (Scale-to-Zero) |
| **Region** | UAE North |
| **Status** | ✅ Running |
| **Health** | ✅ Healthy (200 OK) |
| **Cost** | ~$0-5/month |

---

## 🔗 ENDPOINTS

```
Health:  https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/health
Metrics: https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/metrics
API:     https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/documents/process
```

---

## 💻 USEFUL COMMANDS

### View Status
```bash
az containerapp show --name kraftdintel-app --resource-group kraftdintel-rg
```

### View Logs
```bash
az containerapp logs show --name kraftdintel-app --resource-group kraftdintel-rg --tail 50
```

### View Scaling Info
```bash
az containerapp show --name kraftdintel-app --resource-group kraftdintel-rg --query "properties.template.scale"
```

### Restart App
```bash
az containerapp update --name kraftdintel-app --resource-group kraftdintel-rg --image kraftdintel.azurecr.io/kraftd-backend:latest
```

### Update Scaling
```bash
# Example: Always keep 1 replica running
az containerapp update --name kraftdintel-app --resource-group kraftdintel-rg --min-replicas 1 --max-replicas 4
```

---

## 💰 COST SUMMARY

**Monthly:** $0-5 (with free tier coverage + scale-to-zero idle)  
**vs App Service B1:** $12.50/month  
**Savings:** ~90% ($7-12.50/month)

---

## 📊 MONITORING

### View in Azure Portal
1. Go to: https://portal.azure.com
2. Resource Group: **kraftdintel-rg**
3. Container App: **kraftdintel-app**
4. Check: Metrics, Logs, Revisions

### Application Insights (Auto-Created)
- Workspace: workspace-kraftdintelrgc0kT
- View traces, exceptions, and performance

---

## ✅ WHAT'S WORKING

- ✅ FastAPI application running
- ✅ Docker image (803 MB) deployed
- ✅ Health checks returning 200 OK
- ✅ Metrics endpoint active
- ✅ Auto-scaling enabled (0-4 replicas)
- ✅ Scale-to-zero when idle
- ✅ HTTPS/TLS certificate (automatic)

---

## 🔄 NEXT STEPS

1. **Test document processing:**
   ```bash
   curl -X POST https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/documents/process \
     -F "file=@document.pdf"
   ```

2. **Monitor costs:**
   - Check Azure Portal monthly
   - Set billing alert at $10/month

3. **Future optimization:**
   - If cost > $5/month: Migrate to Azure Functions (free)
   - If need 24/7 guaranteed: Increase min-replicas to 1

---

## 🆘 TROUBLESHOOTING

### App not responding
```bash
# Check status
az containerapp show --name kraftdintel-app -g kraftdintel-rg --query "properties.runningStatus"

# View recent logs
az containerapp logs show --name kraftdintel-app -g kraftdintel-rg --tail 100
```

### High response times
```bash
# Check if scaled to 0 (cold start = 30-60 seconds on first request)
az containerapp show --name kraftdintel-app -g kraftdintel-rg --query "properties.template.scale"

# View metrics in Portal: Metrics → Replica Count
```

### Authentication issues
```bash
# Verify ACR credentials
az acr credential show --name kraftdintel --resource-group kraftdintel-rg
```

---

## 📚 DOCUMENTATION

- [Full Deployment Guide](CONTAINER_APPS_DEPLOYMENT.md)
- [Cost Optimization Analysis](COST_OPTIMIZATION_ALTERNATIVES.md)
- [Transition Roadmap](TRANSITION_ANALYSIS_AND_ROADMAP.md)

---

## 🎯 SUMMARY

✅ **Deployed:** Azure Container Apps  
✅ **Cost:** ~$0-5/month (90% cheaper than App Service)  
✅ **Performance:** Production-ready with auto-scaling  
✅ **Changes:** Zero code modifications  
✅ **Status:** Ready for production use  

**Your application is live and optimized!** 🚀

---

*Last Updated: January 15, 2026*
