# KraftdIntel Load Testing Suite

This directory contains comprehensive load testing tools for validating KraftdIntel's production readiness across different scenarios and tools.

## Files Overview

### Locust Scripts
- `load_test.py` - Main Locust load testing script with multiple user scenarios
- `README_LOAD_TESTING.md` - Detailed documentation for Locust-based testing

### JMeter Integration
- `load_test.jmx` - JMeter test plan for advanced load testing scenarios
- Compatible with Apache JMeter and Azure Load Testing service

### Azure Load Testing
- `azure_load_test_config.yaml` - Configuration for Azure Load Testing service
- `run_azure_load_test.ps1` - PowerShell script to execute Azure load tests

## Quick Start

### Local Locust Testing

1. **Install Locust** (if not already installed):
   ```bash
   pip install locust
   ```

2. **Run basic load test**:
   ```bash
   locust -f backend/tests/load_test.py --host http://localhost:8000
   ```

3. **Run with web UI**:
   ```bash
   locust -f backend/tests/load_test.py --host http://localhost:8000 --web-host 127.0.0.1 --web-port 8089
   ```

4. **Run headless with specific parameters**:
   ```bash
   locust -f backend/tests/load_test.py --host http://localhost:8000 --no-web -u 10 -r 2 --run-time 1m
   ```

### Production Load Testing

1. **Using Azure Load Testing Service**:
   ```powershell
   # Set your Azure subscription
   $env:AZURE_SUBSCRIPTION_ID = "your-subscription-id"

   # Run the Azure load test
   .\backend\tests\run_azure_load_test.ps1 -ResourceGroup "KraftdRG" -LoadTestName "kraftdintel-loadtest"
   ```

2. **Using JMeter directly**:
   - Download Apache JMeter from https://jmeter.apache.org/
   - Open `load_test.jmx` in JMeter GUI
   - Configure HOST and TOKEN variables
   - Run the test plan

## Test Scenarios

### Locust User Classes

1. **KraftdIntelUser** (Base class)
   - Health checks and basic API validation
   - Weight: 30%

2. **LightLoadUser**
   - Minimal load testing with authentication
   - Weight: 20%

3. **HeavyLoadUser**
   - Intensive API load with complex operations
   - Weight: 10%

4. **EmailLoadUser**
   - Email service load testing
   - Weight: 20%

5. **DocumentLoadUser**
   - Document processing load testing
   - Weight: 20%

### JMeter Test Plan

- **Health Check**: GET /health
- **Get Documents**: GET /api/documents (authenticated)
- **Send Verification Email**: POST /api/auth/send-verification (authenticated)

## Configuration

### Environment Variables

For production testing, set these environment variables:

```bash
# For Locust
export API_HOST="https://kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io"
export AUTH_TOKEN="Bearer your-jwt-token"

# For JMeter/Azure Load Testing
HOST=kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io
TOKEN=Bearer your-jwt-token
```

### Azure Load Testing Setup

1. **Create Azure Load Testing resource**:
   ```bash
   az load test create --name kraftdintel-loadtest --resource-group KraftdRG --location uaenorth
   ```

2. **Configure secrets in Key Vault**:
   - Add `AZURE_LOAD_TEST_TOKEN` secret with your JWT token

3. **Update configuration file**:
   - Modify `azure_load_test_config.yaml` with your resource IDs

## Performance Benchmarks

### Target Metrics

- **Response Time (P95)**: < 5000ms
- **Error Rate**: < 5%
- **Concurrent Users**: 50-100
- **Requests/Second**: 10-20

### Test Scenarios

1. **Smoke Test**: 1 user, 1 iteration
2. **Load Test**: 50 users, 30s ramp-up, 10 iterations
3. **Stress Test**: 100 users, 60s ramp-up, continuous
4. **Spike Test**: Sudden increase to 200 users

## Monitoring Integration

Load tests integrate with Azure Application Insights and Azure Monitor:

- **CPU Usage**: Container App CPU utilization
- **Memory Usage**: Container App memory consumption
- **Request Rate**: API requests per second
- **Response Time**: End-to-end response times
- **Error Rate**: Application error percentages

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Ensure JWT token is valid and not expired
   - Check token scope includes required API permissions

2. **Connection Timeouts**:
   - Verify Azure Container App is running
   - Check network connectivity and firewall rules

3. **High Error Rates**:
   - Review Application Insights for error details
   - Check Cosmos DB throttling and RU consumption

4. **Resource Limits**:
   - Monitor Azure Container App scaling limits
   - Check Azure subscription quotas

### Debugging Commands

```bash
# Check Container App status
az containerapp show --name kraftd-api --resource-group KraftdRG

# View Application Insights metrics
az monitor metrics list --resource /subscriptions/.../kraftd-api --metric "Requests"

# Check Azure Load Testing status
az load test run show --load-test-name kraftdintel-loadtest --resource-group KraftdRG --test-run-id <run-id>
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Load Tests
  run: |
    locust -f backend/tests/load_test.py \
           --host ${{ secrets.API_HOST }} \
           --no-web \
           -u 20 \
           -r 2 \
           --run-time 2m \
           --csv results
```

### Azure DevOps Pipeline

```yaml
- task: AzureLoadTest@1
  inputs:
    azureSubscription: 'azure-subscription'
    loadTestConfigFile: 'backend/tests/azure_load_test_config.yaml'
    loadTestResource: 'kraftdintel-loadtest'
    resourceGroup: 'KraftdRG'
```

## Best Practices

1. **Test Environment**: Always test in staging before production
2. **Gradual Load**: Start with low concurrency and gradually increase
3. **Monitor Resources**: Watch CPU, memory, and database metrics
4. **Baseline Measurements**: Establish normal operation baselines
5. **Failure Analysis**: Analyze failures to identify bottlenecks
6. **Regular Testing**: Include load testing in CI/CD pipelines

## Support

For issues or questions:
- Check Application Insights logs
- Review Azure Monitor alerts
- Consult Azure Load Testing documentation
- Review KraftdIntel deployment guide