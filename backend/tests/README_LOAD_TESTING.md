# KraftdIntel Load Testing Configuration

# This directory contains load testing scripts and configurations for production readiness validation.

## Prerequisites
# 1. Install Locust: pip install locust
# 2. Set environment variables:
#    - TEST_JWT_TOKEN: Valid JWT token for API authentication
#    - TEST_DOCUMENT_PATH: Path to test document (default: test_document.pdf)

## Running Load Tests

### Local Development Testing
```bash
# Basic load test
locust -f backend/tests/load_test.py --host http://localhost:8000

# With specific user count and spawn rate
locust -f backend/tests/load_test.py KraftdIntelUser -u 10 -r 2 --host http://localhost:8000
```

### Production Environment Testing
```bash
# Test against production Container App
locust -f backend/tests/load_test.py --host https://kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io
```

### Specialized Load Scenarios

#### Email Load Testing
```bash
# Focus on email verification endpoints
locust -f backend/tests/load_test.py EmailLoadUser -u 50 -r 5 --host http://localhost:8000
```

#### Document Processing Load Testing
```bash
# Focus on document upload and processing
locust -f backend/tests/load_test.py DocumentLoadUser -u 20 -r 3 --host http://localhost:8000
```

#### Heavy Load Testing
```bash
# Aggressive load testing
locust -f backend/tests/load_test.py HeavyLoadUser -u 100 -r 10 --host http://localhost:8000
```

## Load Testing Scenarios

### 1. Normal Production Load
- Users: 50-100 concurrent
- Spawn rate: 5-10 users/second
- Duration: 10-15 minutes
- Expected: <5% error rate, <2s response time

### 2. Peak Load Testing
- Users: 200-500 concurrent
- Spawn rate: 20-50 users/second
- Duration: 5-10 minutes
- Expected: <10% error rate, <5s response time

### 3. Stress Testing
- Users: 1000+ concurrent
- Spawn rate: 50-100 users/second
- Duration: 3-5 minutes
- Expected: System stability under extreme load

### 4. Email Throughput Testing
- Users: 100-200 concurrent
- Focus: Email verification endpoints
- Duration: 5-10 minutes
- Expected: 50-100 emails/second throughput

## Monitoring During Load Tests

Monitor these metrics during load testing:
- Container App CPU/Memory usage
- Application Insights telemetry
- ACS API request rates
- Database connection pools
- Response times and error rates

## Test Results Interpretation

### Success Criteria
- ✅ <5% error rate for normal load
- ✅ <2 second average response time
- ✅ No memory leaks or CPU spikes
- ✅ Proper scaling behavior
- ✅ Email delivery success rate >99%

### Failure Indicators
- ❌ >10% error rate
- ❌ >5 second response times
- ❌ Memory/CPU utilization >90%
- ❌ Container App restarts
- ❌ Database connection exhaustion

## Azure Load Testing Integration

For production-scale load testing, consider using Azure Load Testing service:

```bash
# Create Azure Load Testing resource
az load create --name kraftd-load-test --resource-group KraftdRG --location uaenorth

# Run JMeter-based tests
az load test create --name api-load-test --resource-group KraftdRG --load-test-resource kraftd-load-test --test-plan backend/tests/load_test.jmx --display-name "API Load Test"
```