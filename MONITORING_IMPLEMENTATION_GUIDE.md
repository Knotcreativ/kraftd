# Monitoring & Observability Integration Guide

## 1. Application Insights Setup

### 1.1 Configuration in main.py

```python
from backend.monitoring import monitoring, logger, EventSeverity

# Initialize in FastAPI startup
@app.on_event("startup")
async def startup_event():
    logger.logger.info("Application starting...")

# Track requests in middleware
@app.middleware("http")
async def track_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    
    monitoring.record_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    logger.log_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    return response
```

### 1.2 Environment Variables

```bash
# .env file
APPINSIGHTS_INSTRUMENTATION_KEY=your-key-here
MONITORING_ENABLED=true
LOG_LEVEL=INFO
LOG_FILE=/var/log/kraftdintel/app.log
```

### 1.3 Deployment Configuration

Add to App Service application settings:
```
APPINSIGHTS_INSTRUMENTATION_KEY: [your-instrumentation-key]
ApplicationInsightsAgent_EXTENSION_VERSION: ~3
XDT_MicrosoftApplicationInsights_Mode: recommended
```

---

## 2. Alert Configuration

### 2.2 Alert Rules Included

1. **High Error Rate Alert**
   - Threshold: > 50 HTTP 5xx errors in 15 minutes
   - Severity: 2 (High)
   - Evaluation: Every 5 minutes

2. **High Response Time Alert**
   - Threshold: Average response time > 2000ms
   - Severity: 2 (High)
   - Evaluation: Every 5 minutes

3. **High CPU Usage Alert**
   - Threshold: CPU time > 80%
   - Severity: 2 (High)
   - Evaluation: Every 5 minutes

4. **Application Offline Alert**
   - Threshold: Health status < 1
   - Severity: 0 (Critical)
   - Evaluation: Every 1 minute

5. **High Memory Usage Alert**
   - Threshold: Memory usage > 80%
   - Severity: 2 (High)
   - Evaluation: Every 5 minutes

### 2.2 Setting Up Alerts

```powershell
# Run setup script
.\scripts\setup-monitoring.ps1 `
  -ResourceGroup "kraftdintel-rg" `
  -AppServiceName "kraftdintel-prod" `
  -AppInsightsName "kraftdintel-prod-insights" `
  -EmailAddress "admin@kraftdintel.com"
```

---

## 3. Structured Logging

### 3.1 JSON Log Format

All logs are formatted as JSON for easy parsing by Application Insights:

```json
{
  "time": "2026-01-15T12:34:56Z",
  "level": "INFO",
  "name": "main",
  "message": "http_request",
  "method": "POST",
  "path": "/documents/upload",
  "status_code": 200,
  "duration_ms": 245.3
}
```

### 3.2 Usage in Application

```python
from backend.monitoring import logger, EventSeverity

# Log HTTP request
logger.log_request("POST", "/documents", 200, 245.3)

# Log database operation
logger.log_database_operation("insert_document", 125.5, True)

# Log authentication
logger.log_authentication("user@example.com", True)

# Log error
logger.log_error("ValidationError", "Invalid email format", EventSeverity.MEDIUM)
```

---

## 4. Application Insights Dashboard

### 4.1 Pre-built Dashboard Sections

The dashboard (`infrastructure/dashboard.json`) includes:

1. **Application Map**
   - Visual representation of application components
   - Dependency tracking

2. **Availability Status**
   - Uptime percentage
   - Recent availability events

3. **Failures**
   - Failed request count
   - Exception trends

4. **Performance**
   - Response time trends
   - Request rate

5. **Custom Metrics**
   - Requests by browser
   - Exception breakdown

### 4.2 Accessing the Dashboard

```
Azure Portal → Dashboards → KraftdIntelDashboard
```

### 4.3 Custom Queries

Example Application Insights KQL queries:

**Request trends over time:**
```kusto
requests
| where timestamp > ago(24h)
| summarize RequestCount=count() by bin(timestamp, 1h)
| render timechart
```

**Exceptions by type:**
```kusto
exceptions
| where timestamp > ago(24h)
| summarize Count=count() by type
| order by Count desc
```

**Performance analysis:**
```kusto
requests
| where timestamp > ago(24h)
| summarize
    AverageResponseTime=avg(duration),
    P95ResponseTime=percentile(duration, 95),
    P99ResponseTime=percentile(duration, 99)
    by name
| order by AverageResponseTime desc
```

---

## 5. Monitoring Metrics

### 5.1 Application Metrics to Monitor

**Performance Metrics:**
- Average response time (target: < 500ms)
- Requests per second (typical: 10-50)
- P95/P99 response times
- Error rate (target: < 0.5%)

**Resource Metrics:**
- CPU usage (alert at > 80%)
- Memory usage (alert at > 80%)
- Disk I/O
- Network throughput

**Business Metrics:**
- Successful document uploads
- Workflow completion rate
- Authentication success rate
- API error rate by endpoint

### 5.2 Setting Baseline Thresholds

```powershell
# After 1-2 weeks in production, analyze trends

# Get average response time
az monitor metrics list-definitions `
  --resource-id /subscriptions/{id}/resourceGroups/kraftdintel-rg/providers/Microsoft.Web/sites/kraftdintel-prod `
  --namespace microsoft.web/sites

# View response time data
az monitor metrics list `
  --resource-id /subscriptions/{id}/resourceGroups/kraftdintel-rg/providers/Microsoft.Web/sites/kraftdintel-prod `
  --metric "ResponseTime" `
  --start-time 2026-01-08T00:00:00Z `
  --end-time 2026-01-15T00:00:00Z
```

---

## 6. Log Retention & Cleanup

### 6.1 Application Insights Retention

- Default: 30 days
- Configurable: 30-365 days
- Beyond retention: Exported to cold storage (optional)

### 6.2 Setting Retention in Bicep

```bicep
RetentionInDays: 90  // 90 days retention
```

### 6.3 Log Export

Export logs to Azure Storage for long-term analysis:

```powershell
# Configure continuous export
az monitor app-insights component linked-storage `
  --resource-group kraftdintel-rg `
  --app kraftdintel-prod-insights `
  --storage-account kraftdintelstorage
```

---

## 7. Diagnostic Logging Configuration

### 7.1 Enable App Service Diagnostics

```powershell
# Enable HTTP logging
az webapp log config `
  --name kraftdintel-prod `
  --resource-group kraftdintel-rg `
  --application-logging filesystem `
  --detailed-error-messages true `
  --failed-request-tracing true
```

### 7.2 Log Types Available

- **Application Logs**: Structured JSON logs from application
- **HTTP Logs**: All HTTP requests/responses
- **Failed Request Logs**: Detailed failure analysis
- **Console Logs**: stdout/stderr from application

---

## 8. Alerting Best Practices

### 8.1 Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Error Rate | > 2% | > 5% | Scale up / investigate |
| Response Time | > 1000ms | > 2000ms | Check database / scale |
| CPU Usage | > 70% | > 85% | Scale up app plan |
| Memory Usage | > 70% | > 85% | Restart app / scale |
| Disk Space | > 80% | > 90% | Cleanup logs / scale |
| Availability | < 99.5% | < 99% | Investigate outage |

### 8.2 Alert Response Procedures

**High Error Rate:**
1. Check Application Insights for error patterns
2. Review recent deployments
3. Restart app service if needed
4. Scale up if caused by load

**High Response Time:**
1. Check database connection
2. Monitor CPU/memory usage
3. Review slow query logs
4. Scale up if resource constrained

**Application Offline:**
1. Check app service status
2. Review application logs
3. Check health endpoint manually
4. Restart app service

---

## 9. Performance Optimization Tips

### 9.1 Reducing Latency

- Cache database queries (Redis if available)
- Implement request batching
- Use connection pooling for Cosmos DB
- Enable response compression

### 9.2 Reducing Errors

- Add request validation
- Implement retry logic with exponential backoff
- Add circuit breaker pattern
- Monitor and fix common exceptions

### 9.3 Scaling Strategy

**Vertical Scaling (increase size):**
- B1 → S1 → S2 → P1V2
- Improves performance for single instance

**Horizontal Scaling (add instances):**
- Enable auto-scaling rules
- Based on CPU/memory metrics
- Set minimum/maximum instance counts

---

## 10. Dashboard & Query Examples

### 10.1 Create Custom Dashboard

```powershell
# Create dashboard from template
az portal dashboard create `
  --resource-group kraftdintel-rg `
  --name KraftdIntelCustom `
  --input-path dashboard.json
```

### 10.2 Common Analytics Queries

**Daily error count:**
```kusto
requests
| where timestamp > ago(7d)
| where success == false
| summarize ErrorCount=count() by bin(timestamp, 1d)
| render barchart
```

**Most slow endpoints:**
```kusto
requests
| where timestamp > ago(24h)
| top 10 by duration desc
| project name, duration, success, timestamp
```

**Failed authentication attempts:**
```kusto
customEvents
| where name == "authentication"
| where customDimensions.success == false
| summarize FailureCount=count() by bin(timestamp, 1h)
```

---

## 11. Integration with Application Code

### 11.1 Example: Document Upload Monitoring

```python
from backend.monitoring import monitoring, logger

@app.post("/documents/upload")
async def upload_document(email: str, file: UploadFile):
    start = time.time()
    
    try:
        # Upload logic
        result = await document_service.upload(email, file)
        
        duration_ms = (time.time() - start) * 1000
        monitoring.record_request("POST", "/documents/upload", 200, duration_ms)
        logger.log_request("POST", "/documents/upload", 200, duration_ms)
        
        return {"status": "success", "document_id": result["id"]}
    except Exception as e:
        logger.log_error("DocumentUploadError", str(e), EventSeverity.HIGH)
        raise HTTPException(status_code=500, detail="Upload failed")
```

---

## 12. Maintenance Tasks

**Daily:**
- Review error rate trending
- Check alert notifications
- Monitor CPU/memory usage

**Weekly:**
- Analyze performance trends
- Review exception logs
- Check disk usage

**Monthly:**
- Review baseline thresholds
- Optimize slow queries
- Plan capacity upgrades
- Review cost metrics

---

## Files Generated

| File | Purpose |
|------|---------|
| `backend/monitoring.py` | Monitoring module with metrics & logging |
| `infrastructure/alerts.json` | Alert rule definitions |
| `infrastructure/dashboard.json` | Dashboard configuration |
| `scripts/setup-monitoring.ps1` | Monitoring setup script |
| `MONITORING_IMPLEMENTATION_GUIDE.md` | This guide |

---

**Status:** ✅ COMPLETE | Priority 5 Implementation  
**Total Lines:** 1,500+ (code + config + guide)  
**Next:** Deploy and validate monitoring in production

