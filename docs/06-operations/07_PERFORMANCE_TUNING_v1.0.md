# Performance Tuning v1.0

**Document**: System Optimization Guide  
**Version**: 1.0  
**Last Updated**: January 2026  
**Audience**: DevOps Engineers, Senior Engineers, Performance Team

---

## Overview

This guide explains how to identify performance bottlenecks and optimize the system. Use when response times are slow or throughput is low.

---

## 1. Performance Baselines

### Expected Performance Targets

**API Response Times**:
```
GET  /api/v1/health              < 50ms     (p99)
GET  /api/v1/auth/profile        < 100ms    (p99)
POST /api/v1/auth/login          < 500ms    (p99)
POST /api/v1/auth/register       < 1000ms   (p99)
POST /api/v1/documents/upload    < 2000ms   (p99)
POST /api/v1/documents/convert   < 5000ms   (p99)
POST /api/v1/exports             < 3000ms   (p99)
```

**Frontend Performance**:
```
Page Load (First Paint)         < 1000ms   (p95)
Page Load (Interactive)         < 2000ms   (p95)
Script Bundle Size              < 500KB
CSS Bundle Size                 < 100KB
API Response Time               < 500ms    (p95)
```

**Database Performance**:
```
Query Latency (p99)            < 20ms
Connection Pool Utilization    < 80%
RU/s Utilization              < 80%
Throttle Rate                  0%
```

**System Metrics**:
```
CPU Usage (avg)                < 50%
CPU Usage (peak)               < 80%
Memory Usage                   < 500MB
Disk Space Usage               < 80%
Network Latency               < 10ms (to Azure)
```

---

## 2. Performance Monitoring

### Azure Application Insights

**Key Metrics to Watch**:

```kusto
// Average response time by endpoint
requests
| where timestamp > ago(1h)
| summarize AvgDuration = avg(duration) by name
| sort by AvgDuration desc

// P99 response time
requests
| where timestamp > ago(1h)
| summarize P99Duration = percentile(duration, 99) by name
| where P99Duration > 2000  // Alert if > 2 seconds

// Failed requests by endpoint
requests
| where timestamp > ago(1h)
| where success == false
| summarize FailureCount = count() by name
| sort by FailureCount desc
```

### Cosmos DB Metrics

**Location**: Azure Portal → Cosmos DB → Metrics

**Key Charts**:
1. **RU Consumption**: Should be < 80% of provisioned
2. **Latency (p99)**: Should be < 20ms
3. **Throttled Requests**: Should be 0
4. **Replication Lag**: Should be < 100ms

---

## 3. Identifying Bottlenecks

### Slow API Endpoint Analysis

**If API is slow** (> 2 seconds):

1. **Check Application Insights**:
   ```kusto
   // Find slow requests
   requests
   | where name == "/api/v1/documents/convert"
   | where duration > 2000
   | project name, duration, customMeasurements
   | sort by duration desc
   | limit 20
   ```

2. **Identify dependency latency**:
   ```kusto
   // Check if database is slow
   dependencies
   | where operation_Name == "POST /api/v1/documents/convert"
   | summarize AvgDuration = avg(duration) by name
   ```

3. **Check for exceptions**:
   ```kusto
   exceptions
   | where operation_Name == "POST /api/v1/documents/convert"
   | summarize count() by type
   ```

### High CPU Usage

**If CPU > 80%**:

1. **Check running processes**:
   ```powershell
   Get-Process | Sort-Object CPU -Descending | Select-Object -First 5
   ```

2. **Check backend process**:
   ```powershell
   # If Python using > 80% CPU
   # Either processing heavy request or memory leak
   ```

3. **Solutions**:
   - Restart backend (clears caches)
   - Identify long-running request
   - Optimize algorithm
   - Move to background job

### High Memory Usage

**If Memory > 500MB**:

1. **Check process memory**:
   ```powershell
   Get-Process python | Select-Object ProcessName, @{
     Name="MemoryMB"; Expression={$_.WorkingSet/1MB}
   }
   ```

2. **Possible causes**:
   - Memory leak in code
   - Large file in memory
   - Unbounded cache
   - Database connection leak

3. **Solutions**:
   - Restart backend service
   - Implement maximum memory limits
   - Stream large files instead of loading
   - Implement cache size limits

### Database Throttling (429 Errors)

**If seeing 429 errors**:

1. **Check RU consumption**:
   ```
   Azure Portal → Cosmos DB → Metrics →
   Normalized RU Consumption by Partition Key
   ```

2. **If > 90% utilized**:
   - Increase RU/s (manual or auto-scale)
   - Optimize queries to use fewer RUs
   - Implement request batching

3. **Increase RU/s**:
   ```
   Azure Portal → Cosmos DB → Scale & Settings →
   Select container → Increase RU/s
   Recommend: Auto-scale 400-4000 RU/s
   ```

---

## 4. Optimization Techniques

### Database Query Optimization

**Example: Slow Document Search**

**Before** (expensive query):
```python
# Gets all documents, filters in code
documents = list(container.query_items(
    query="SELECT * FROM c WHERE c.type = 'Invoice'"
))
# RU cost: Scans entire container
```

**After** (optimized query):
```python
# Filters at database level using partition key
documents = list(container.query_items(
    query="SELECT * FROM c WHERE c.type = 'Invoice'",
    partition_key="email"  # Use partition key
))
# RU cost: Much lower, scans single partition
```

**Optimization Tips**:
1. Always use partition key in WHERE clause
2. Project only needed fields (SELECT c.id, c.name instead of SELECT *)
3. Use TOP to limit results
4. Avoid joins if possible
5. Create indexes for frequently queried fields

### API Response Optimization

**Before** (N+1 problem):
```python
# Gets 100 documents, then loops to get user for each
documents = list(container.query_items(...))
for doc in documents:
    user = get_user(doc.user_id)  # 100 separate queries
    doc.user = user
```

**After** (batch query):
```python
# Gets all documents and users in 2 queries
documents = list(container.query_items(...))
user_ids = [d.user_id for d in documents]
users = get_users_batch(user_ids)  # 1 query for all
user_map = {u.id: u for u in users}
for doc in documents:
    doc.user = user_map[doc.user_id]
```

### Frontend Performance Optimization

**Code Splitting**:
```javascript
// Before: One large bundle
import { Dashboard, Documents, Settings } from './pages'

// After: Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Documents = lazy(() => import('./pages/Documents'))
const Settings = lazy(() => import('./pages/Settings'))
```

**Image Optimization**:
```javascript
// Use WebP format with fallback
<picture>
  <source srcSet="image.webp" type="image/webp" />
  <img src="image.png" alt="..." />
</picture>

// Compress images
// Before: 500KB
// After: 50KB (90% reduction)
```

**Caching**:
```javascript
// Cache API responses
const cache = new Map()

async function getDocuments() {
  if (cache.has('documents')) {
    return cache.get('documents')
  }
  const docs = await api.getDocuments()
  cache.set('documents', docs)
  return docs
}
```

### Scaling Strategies

**Vertical Scaling** (more powerful machine):
- Increase RU/s for Cosmos DB
- Move to larger VM for backend
- More memory/CPU available

**Horizontal Scaling** (multiple machines):
- Add API servers (load balanced)
- Add document processing workers
- Use message queue for async jobs

**Both** (recommended):
- Start with vertical scaling
- Move expensive operations to background jobs
- Add horizontal scaling when needed

---

## 5. Performance Tuning Checklist

### Quick Wins (< 1 hour)

- [ ] Enable API response caching (HTTP caching headers)
- [ ] Enable gzip compression on responses
- [ ] Optimize database indexes
- [ ] Update slow queries to use partition keys
- [ ] Implement connection pooling

### Medium Effort (1-4 hours)

- [ ] Implement query result caching
- [ ] Lazy load pages on frontend
- [ ] Move heavy operations to background jobs
- [ ] Implement request batching
- [ ] Add CDN for static files

### Major Changes (> 4 hours)

- [ ] Implement horizontal scaling
- [ ] Add database read replicas
- [ ] Implement full-text search
- [ ] Move to message queue architecture
- [ ] Implement distributed caching (Redis)

---

## 6. Performance Tuning by Component

### Backend API Server

**Current Configuration**:
- Python 3.9
- FastAPI framework
- Uvicorn server
- Single process

**Optimization Options**:

1. **Increase workers**:
   ```
   # Current: 1 worker
   # Changed to: 4 workers
   uvicorn main:app --workers 4 --port 8000
   ```

2. **Enable compression**:
   ```python
   from fastapi.middleware.gzip import GZIPMiddleware
   app.add_middleware(GZIPMiddleware, minimum_size=1000)
   ```

3. **Add response caching**:
   ```python
   from fastapi_cache2 import FastAPICache2
   
   @cached(expire=300)  # Cache for 5 minutes
   async def get_documents():
       return documents
   ```

### Cosmos DB

**Current Configuration**:
- Manual RU/s provisioning
- Single region
- Standard (not multi-master)

**Optimization Options**:

1. **Enable auto-scale**:
   ```
   Recommended: Auto-scale 400-4000 RU/s
   Pay only for what you use
   Cost: Same or lower than fixed
   ```

2. **Add read replicas**:
   ```
   If doing heavy reads, replicate to second region
   Reduces latency for local reads
   ```

3. **Enable TTL**:
   ```python
   # Delete old data automatically
   container.update_item(
       item, 
       ttl=2592000  # 30 days
   )
   ```

### Frontend

**Current Configuration**:
- React with Vite bundler
- Single page app
- No lazy loading

**Optimization Options**:

1. **Code splitting**:
   ```javascript
   Lazy load pages: Reduces initial load from 500KB → 150KB
   ```

2. **Image optimization**:
   ```javascript
   Use modern formats (WebP)
   Compress aggressively
   Use responsive images
   ```

3. **Browser caching**:
   ```javascript
   Cache API responses (5 min)
   Cache static files (1 day)
   Use service worker
   ```

---

## 7. Load Testing

### Run Load Test Before Production

**Objective**: Verify system can handle peak load

**Tools**:
- Apache JMeter
- Locust
- Azure Load Testing

**Simple Test Script**:
```python
import requests
import concurrent.futures

def login_request():
    response = requests.post(
        'http://127.0.0.1:8000/api/v1/auth/login',
        json={
            'email': 'user@example.com',
            'password': 'password123'
        }
    )
    return response.status_code == 200

# Simulate 100 concurrent users
with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
    results = list(executor.map(lambda _: login_request(), range(100)))
    success_rate = sum(results) / len(results)
    print(f"Success rate: {success_rate*100}%")
```

**Expected Results**:
- 100 concurrent users: 95%+ success
- Response time < 1 second average
- No 429 throttling errors
- No 500 server errors

---

## 8. Performance Monitoring Dashboard

### Create Custom Dashboard

**Metrics to Include**:
1. API Response Time (avg, p95, p99)
2. Error Rate (%)
3. RU Consumption (%)
4. Database Latency (p99)
5. CPU Usage
6. Memory Usage
7. Request Volume
8. Active Users

**Setup**:
```
Azure Portal → Application Insights →
Workbooks → Create New →
Add all metrics above
Share with team
```

---

## 9. Continuous Performance Improvement

### Monthly Performance Review

**Process**:
1. Collect metrics (last 30 days)
2. Identify slowest endpoints
3. Compare to baseline
4. Set optimization targets
5. Assign improvements
6. Track progress

### Quarterly Goals

**Example**:
- Q1: Reduce API latency by 20%
- Q2: Add lazy loading (reduce bundle size)
- Q3: Implement caching layer
- Q4: Add database read replicas

---

## 10. Performance Standards

### SLA Commitments

**Availability**: 99.5% uptime
**Response Time**: P99 < 2 seconds
**Error Rate**: < 1%
**Data Loss**: < 1 hour

### Performance Targets

| Metric | Target | Warn | Alert |
|--------|--------|------|-------|
| API Latency (p99) | < 500ms | 500-1000ms | > 1000ms |
| Database Latency (p99) | < 20ms | 20-100ms | > 100ms |
| Error Rate | < 1% | 1-5% | > 5% |
| RU Utilization | < 80% | 80-95% | > 95% |
| CPU Usage | < 50% | 50-80% | > 80% |
| Memory Usage | < 400MB | 400-500MB | > 500MB |

---

## Quick Reference

**Slow API Endpoint?**
1. Check database latency
2. Check for N+1 queries
3. Check response size
4. Implement caching

**High CPU?**
1. Check for infinite loops
2. Restart backend
3. Reduce batch size
4. Add more workers

**High Memory?**
1. Check for leaks
2. Limit cache size
3. Stream large files
4. Restart backend

**Database Throttling?**
1. Check RU consumption
2. Increase RU/s
3. Optimize queries
4. Implement request batching

---

**Document Complete** - Last updated January 2026

**Performance is never "done" - continuous improvement is key**
