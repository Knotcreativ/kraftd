# 📊 PRODUCTION MONITORING & OBSERVABILITY SETUP

**Status:** Ready to Configure  
**Date:** January 20, 2026  
**Duration:** 15 minutes to activate

---

## 🎯 Monitoring Strategy

KRAFTD uses multi-layered monitoring across:
1. **Application Insights** (Azure) - APM & logs
2. **Custom Metrics** - Business KPIs
3. **Alerts** - Proactive issue detection
4. **Dashboards** - Real-time visibility
5. **Logs** - Troubleshooting & audit

---

## 📈 KEY PERFORMANCE INDICATORS (KPIs)

### User Experience KPIs
| Metric | Target | Alert Threshold | Check Frequency |
|--------|--------|-----------------|-----------------|
| API Response Time (p99) | <2s | >3s | 1 minute |
| Frontend Load Time | <3s | >5s | 5 minutes |
| Error Rate | <0.5% | >1% | 1 minute |
| Uptime | 99.5% | <99% | 5 minutes |
| Feature Availability | 100% | <99% | 1 minute |

### Infrastructure KPIs
| Metric | Target | Alert Threshold | Check Frequency |
|--------|--------|-----------------|-----------------|
| CPU Usage | <70% | >85% | 1 minute |
| Memory Usage | <80% | >90% | 1 minute |
| Disk Space | >10% free | <5% free | 5 minutes |
| Database Connections | <80% max | >90% max | 1 minute |
| Request Rate | <100/sec | >200/sec | 1 minute |

### Business KPIs
| Metric | Target | Alert Threshold | Check Frequency |
|--------|--------|-----------------|-----------------|
| Successful Uploads | >99% | <95% | 5 minutes |
| Extraction Accuracy | >94% | <90% | 1 hour |
| Export Success Rate | >99% | <95% | 5 minutes |
| User Registration | >10/day | <5/day | 1 hour |
| Active Users | +5%/week | Trend analysis | 1 hour |

---

## 🔧 MONITORING COMPONENTS SETUP

### 1. Application Insights Configuration

**Status:** ✅ Configured

```python
# backend/.env.production
APPINSIGHTS_INSTRUMENTATION_KEY=<from Azure Key Vault>
```

**Monitored Components:**
- [ ] API request/response times
- [ ] Exception tracking
- [ ] Performance counters
- [ ] Dependency calls
- [ ] Custom events
- [ ] Traces

**Verification:**
```bash
# Test that Application Insights is receiving data
az monitor app-insights metrics show \
  --app kraftd-backend \
  --resource-group ProjectCatalyst \
  --metric requests/count
```

### 2. Custom Metrics Setup

**Application-Level Metrics:**

```python
# backend/monitoring/metrics.py
from opencensus.ext.azure import metrics_exporter

# Document Processing Metrics
documents_uploaded_total = Counter("documents_uploaded_total", "Total documents uploaded")
documents_processed_total = Counter("documents_processed_total", "Total documents processed")
document_extraction_duration = Histogram("document_extraction_duration_ms", "Time to extract document")
extraction_accuracy = Gauge("extraction_accuracy_percent", "AI extraction accuracy %")

# API Metrics
api_request_duration = Histogram("api_request_duration_ms", "API request duration")
api_error_total = Counter("api_error_total", "Total API errors")
auth_failures_total = Counter("auth_failures_total", "Total authentication failures")

# Database Metrics
db_query_duration = Histogram("db_query_duration_ms", "Database query duration")
db_connection_pool_size = Gauge("db_connection_pool_size", "Active DB connections")
db_transaction_duration = Histogram("db_transaction_duration_ms", "Transaction duration")
```

**Verification:**
```bash
# Metrics should be visible in Azure Monitor
# Custom Metrics > Select metric > Verify data points appearing
```

### 3. Logging Configuration

**Log Levels for Production:**
- ERROR: System failures, unrecoverable errors
- WARNING: Degraded performance, security events, high error rates
- INFO: Deployment events, business milestones
- DEBUG: Disabled in production (performance)

**Structured Logging Format:**
```json
{
  "timestamp": "2026-01-20T10:15:30.123Z",
  "level": "ERROR",
  "service": "backend",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "message": "Document extraction failed",
  "error": {
    "type": "ExtractionException",
    "message": "AI model inference timed out",
    "stack_trace": "..."
  },
  "context": {
    "document_id": "doc_12345",
    "user_id": "user_789",
    "request_id": "req_456"
  },
  "performance": {
    "duration_ms": 31500,
    "cpu_ms": 2800,
    "memory_mb": 450
  }
}
```

**Configuration:**
```python
# backend/logging_config.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(timestamp)s %(level)s %(service)s %(trace_id)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "WARNING"  # Only WARNING+ in production
        },
        "application_insights": {
            "class": "opencensus.ext.azure.log_exporter.AzureLogHandler",
            "instrumentation_key": os.getenv("APPINSIGHTS_INSTRUMENTATION_KEY")
        }
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console", "application_insights"]
    }
}
```

**Verification:**
```bash
# Check logs in Application Insights
az monitor app-insights query \
  --app kraftd-backend \
  --resource-group ProjectCatalyst \
  --analytics-query "traces | where severityLevel >= 1 | take 10"
```

### 4. Alerting Rules

**Alert 1: High Error Rate**
```
Name: API Error Rate High
Condition: Error rate > 1% over 5 minutes
Severity: Critical (P1)
Action: Page on-call engineer, Slack #incidents
Runbook: See troubleshooting guide > API Errors
```

**Alert 2: High Latency**
```
Name: API Latency High
Condition: Response time (p99) > 3 seconds over 5 minutes
Severity: Warning (P2)
Action: Notify backend team, Slack #performance
Runbook: See troubleshooting guide > Performance
```

**Alert 3: Low Disk Space**
```
Name: Disk Space Critical
Condition: Free space < 5% on /
Severity: Critical (P1)
Action: Page on-call engineer immediately
Runbook: See troubleshooting guide > Disk Space
```

**Alert 4: Database Connection Pool Exhausted**
```
Name: DB Connection Pool High
Condition: Active connections > 90% of max over 2 minutes
Severity: Critical (P1)
Action: Page DBA, Slack #incidents
Runbook: Database connection troubleshooting
```

**Alert 5: Authentication Failures Spike**
```
Name: Auth Failures Spike
Condition: Failed login attempts > 20 in 1 minute
Severity: Warning (P2)
Action: Slack #security, review logs
Runbook: Security incident response > Brute force
```

**Alert 6: Document Extraction Failures**
```
Name: Document Extraction Failure Rate
Condition: Extraction failure % > 5% over 1 hour
Severity: Warning (P2)
Action: Slack #ai-ml, alert data science team
Runbook: AI/ML troubleshooting
```

**Alert 7: Feature Degradation**
```
Name: Feature Unavailable
Condition: Feature availability < 99% for 5 minutes
Severity: Critical (P1)
Action: Page feature owner, Slack #incidents
Runbook: Feature troubleshooting
```

### 5. Dashboards

**Main Operations Dashboard** (Real-time)
```
Layout: 4x3 grid
┌─────────────────────────────────────────┐
│ System Health     │ API Metrics         │
├─────────────────────────────────────────┤
│ Active Users      │ Error Rate          │
├─────────────────────────────────────────┤
│ Database Health   │ Recent Errors       │
├─────────────────────────────────────────┤
│ Resource Usage    │ Performance Trend   │
└─────────────────────────────────────────┘

Panels:
1. System Health (overall status)
2. API Response Time (p50, p95, p99 over last hour)
3. Active Users (real-time count)
4. Error Rate (%) trending
5. Database Connection Usage (%)
6. Recent Errors (last 10)
7. CPU/Memory/Disk Usage
8. Request Volume (requests/sec)
9. Failed Requests (by type)
10. Feature Availability (% online)
11. Deployment History (last 5 deploys)
12. Alerts (active)
```

**Feature-Specific Dashboard** (Product metrics)
```
1. Document Upload Volume (daily trending)
2. Extraction Accuracy (% correct extractions)
3. Export Success Rate (%)
4. User Signup Rate (daily)
5. User Retention (weekly cohort)
6. Feature Usage Distribution
7. Common Error Types
8. Performance by Feature
```

**Team Dashboards:**
- **Engineering:** Performance, errors, deployment status
- **DevOps:** Infrastructure, resource usage, scaling
- **Product:** User metrics, feature usage, KPIs
- **Security:** Auth failures, suspicious activity, policy violations

---

## 🔔 ALERTING CHANNELS

### Channels Configuration

**Critical (P1) - Immediate Page**
- [ ] PagerDuty integration
- [ ] Phone call to on-call engineer
- [ ] Slack #incidents (critical)
- [ ] Email to leadership

**Warning (P2) - Slack Notification**
- [ ] Slack #engineering
- [ ] Email to team lead
- [ ] No immediate page

**Info (P3) - Background**
- [ ] Slack #monitoring
- [ ] Daily digest email
- [ ] No immediate notification

### Escalation Paths

| Issue | P1 Response | Escalation |
|-------|-------------|------------|
| Service Down | 15 min | VP Engineering (30 min) |
| High Error Rate | 30 min | VP Engineering (60 min) |
| Performance | 1 hour | VP Engineering (2 hours) |
| Security | Immediate | CISO (15 min) |

---

## 📊 DASHBOARD ACCESS

### Monitoring URLs

**Application Insights Dashboard:**
```
https://portal.azure.com/#resource/subscriptions/{sub-id}/resourceGroups/ProjectCatalyst/providers/microsoft.insights/components/kraftd-backend/overview
```

**Grafana Dashboard:**
```
http://grafana.kraftd.internal:3000
Login: admin / (from Key Vault)
```

**Custom Application Dashboard:**
```
https://monitoring.kraftd.internal/dashboard
```

### Team Access

```
Database: Azure CosmosDB
Role: Viewer (default)
Write Access: DevOps team only
Backup Access: DBA team + DevOps lead
```

---

## 🧪 MONITORING VALIDATION

### Pre-Launch Verification Checklist

- [ ] Application Insights receiving data (>100 events/min)
- [ ] Custom metrics appearing in Azure Monitor
- [ ] All alerts configured and tested
- [ ] Alert routing verified (Slack, email, PagerDuty)
- [ ] Dashboards displaying real-time data
- [ ] Log aggregation working
- [ ] Team can access monitoring tools
- [ ] On-call rotation has access
- [ ] Documentation links in runbooks updated
- [ ] Baseline metrics captured

### Test Alert Triggering

```bash
# Generate test alert
# Example: Simulate high error rate
ab -n 1000 -c 10 https://api.kraftd.io/api/v1/test/error

# Verify alert fires within 5 minutes
# Check: PagerDuty, Slack, email
```

---

## 🚨 INCIDENT RESPONSE INTEGRATION

### On-Call Responsibilities

**On-Call Engineer** checks monitoring tools:
1. Application Insights for errors
2. Custom dashboards for trends
3. Alert history for patterns
4. Logs for root cause

**Response Time SLAs:**
- P1 (Critical): 15 minutes response
- P2 (Warning): 1 hour response
- P3 (Info): 24 hours response

### Handoff Procedures

```
Day-of-Call Engineer:
- 9 AM: Check overnight alerts and trends
- Identify any developing issues
- Discuss with previous on-call
- Brief engineering team on status

Night-of-Call Engineer:
- Receive handoff summary
- Verify monitoring alerts working
- Check system health before bed
- Maintain pager during sleep
```

---

## 📅 MONITORING SCHEDULE

### Daily Reviews (9 AM)
- [ ] Check overnight error logs
- [ ] Review alert history
- [ ] Verify all systems healthy
- [ ] Note any concerning trends

### Weekly Reviews (Monday 10 AM)
- [ ] Review SLA metrics
- [ ] Discuss alert tuning
- [ ] Plan capacity based on growth
- [ ] Review on-call rotation

### Monthly Reviews (First Monday 2 PM)
- [ ] Full metrics analysis
- [ ] Performance trending
- [ ] Scaling recommendations
- [ ] Tool effectiveness review

### Quarterly Reviews (Jan/Apr/Jul/Oct)
- [ ] Monitoring architecture review
- [ ] New metrics to track?
- [ ] Tool upgrades needed?
- [ ] Team training on new features

---

## 🔄 CONTINUOUS IMPROVEMENT

### Metrics Refinement

**Monthly Checklist:**
- Are we tracking the right metrics?
- Are alerts noisy (too many false positives)?
- Are we missing important signals?
- Do dashboards tell the right story?
- Can we respond faster to issues?

**Quarterly Refinement:**
- Remove metrics no longer useful
- Add metrics for new features
- Update alert thresholds based on baseline
- Reorganize dashboards for clarity
- Train team on updated procedures

---

## 🎯 SUCCESS CRITERIA

✅ **Monitoring is successful when:**
- Team is alerted to issues before customers notice
- Root cause can be identified within 15 minutes
- Alert noise is <5% false positive rate
- All critical issues have runbooks
- Dashboards provide clear visibility
- Trends are visible (capacity planning)
- Compliance/audit requirements met

---

## 📞 SUPPORT & ESCALATION

**Questions about monitoring setup?**
- Platform Team (monitoring infrastructure)
- DevOps Lead (configuration)
- On-Call Engineer (incident response)

---

## STATUS: READY FOR ACTIVATION ✅

All monitoring components configured. Ready to activate upon Phase 3 test completion.

**Next Step:** Execute Phase 3 integration tests, then activate production monitoring.

---

*Last Updated: January 20, 2026*  
*Next Update: Post-launch optimization review*
