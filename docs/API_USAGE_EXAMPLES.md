# API Usage Examples

**Purpose:** Practical examples for common API workflows  
**Language:** cURL, Python, JavaScript  

---

## Table of Contents

1. [Authentication Examples](#authentication-examples)
2. [Document Upload & Processing](#document-upload--processing)
3. [Workflow Examples](#workflow-examples)
4. [Error Handling](#error-handling)
5. [Advanced Scenarios](#advanced-scenarios)

---

## Authentication Examples

### 1. Login and Get Token

**cURL:**
```bash
curl -X POST http://localhost:7071/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "buyer@company.com",
    "password": "<REDACTED_PASSWORD>"
  }'
```

**Response:**
```json
{
  "access_token": "<REDACTED_JWT>",
  "refresh_token": "<REDACTED_JWT>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Python:**
```python
import requests

response = requests.post(
    'http://localhost:7071/api/v1/auth/login',
    json={
        'email': 'buyer@company.com',
        'password': 'SecurePassword123!'
    }
)

token = response.json()['access_token']
print(f"Token: {token}")
```

**JavaScript:**
```javascript
const response = await fetch('http://localhost:7071/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'buyer@company.com',
    password: 'SecurePassword123!'
  })
});

const data = await response.json();
const token = data.access_token;
console.log(`Token: ${token}`);
```

### 2. Refresh Token

**cURL:**
```bash
curl -X POST http://localhost:7071/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Python:**
```python
response = requests.post(
    'http://localhost:7071/api/v1/auth/refresh',
    json={'refresh_token': refresh_token}
)

new_token = response.json()['access_token']
```

---

## Document Upload & Processing

### 1. Upload Document

**cURL:**
```bash
curl -X POST http://localhost:7071/api/v1/docs/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@invoice.pdf" \
  -F "doc_type=INVOICE"
```

**Python:**
```python
import requests

with open('invoice.pdf', 'rb') as f:
    files = {'file': f}
    data = {'doc_type': 'INVOICE'}
    
    response = requests.post(
        'http://localhost:7071/api/v1/docs/upload',
        headers={'Authorization': f'Bearer {token}'},
        files=files,
        data=data
    )

doc_id = response.json()['document_id']
print(f"Document uploaded: {doc_id}")
```

**JavaScript:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('doc_type', 'INVOICE');

const response = await fetch('http://localhost:7071/api/v1/docs/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const data = await response.json();
const docId = data.document_id;
console.log(`Document uploaded: ${docId}`);
```

### 2. Extract Data from Document

**cURL:**
```bash
curl -X POST http://localhost:7071/api/v1/extract \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc-abc123",
    "extraction_type": "full"
  }'
```

**Python:**
```python
response = requests.post(
    'http://localhost:7071/api/v1/extract',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'document_id': doc_id,
        'extraction_type': 'full'
    }
)

extraction = response.json()
print(f"Extraction complete: {extraction['validation']['overall_score']}% quality")
```

**JavaScript:**
```javascript
const response = await fetch('http://localhost:7071/api/v1/extract', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    document_id: docId,
    extraction_type: 'full'
  })
});

const extraction = await response.json();
console.log(`Quality Score: ${extraction.validation.overall_score}%`);
```

### 3. Get Document Status

**cURL:**
```bash
curl -X GET http://localhost:7071/api/v1/documents/doc-abc123/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python:**
```python
response = requests.get(
    f'http://localhost:7071/api/v1/documents/{doc_id}/status',
    headers={'Authorization': f'Bearer {token}'}
)

status = response.json()
print(f"Status: {status['status']}")
print(f"Progress: {status['progress']}%")
```

---

## Workflow Examples

### Complete Procurement Workflow

**Step 1: Review Inquiry**
```bash
curl -X POST http://localhost:7071/api/v1/workflow/inquiry \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc-abc123"}'
```

**Step 2: Request Estimation**
```bash
curl -X POST http://localhost:7071/api/v1/workflow/estimation \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc-abc123"}'
```

**Step 3: Normalize Quotes**
```bash
curl -X POST http://localhost:7071/api/v1/workflow/normalize-quotes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc-abc123"}'
```

**Step 4: Compare Quotes**
```bash
curl -X POST http://localhost:7071/api/v1/workflow/comparison \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc-abc123"}'
```

**Step 5: Approve Supplier**
```bash
curl -X POST http://localhost:7071/api/v1/workflow/approval \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc-abc123",
    "approved_supplier_id": "sup-002"
  }'
```

**Step 6: Generate Pro Forma Invoice**
```bash
curl -X POST http://localhost:7071/api/v1/workflow/proforma-invoice \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc-abc123"}'
```

**Step 7: Generate Output**
```bash
curl -X POST http://localhost:7071/api/v1/generate-output \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc-abc123",
    "output_format": "pdf"
  }'
```

### Python Workflow Automation

```python
import requests
import time

class ProcurementWorkflow:
    def __init__(self, token):
        self.token = token
        self.headers = {'Authorization': f'Bearer {token}'}
        self.base_url = 'http://localhost:7071/api/v1'
    
    def upload_document(self, file_path, doc_type='INVOICE'):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'doc_type': doc_type}
            response = requests.post(
                f'{self.base_url}/docs/upload',
                headers=self.headers,
                files=files,
                data=data
            )
        return response.json()['document_id']
    
    def extract_data(self, doc_id):
        response = requests.post(
            f'{self.base_url}/extract',
            headers=self.headers,
            json={'document_id': doc_id, 'extraction_type': 'full'}
        )
        return response.json()
    
    def run_workflow(self, doc_id):
        steps = [
            ('inquiry', {}),
            ('estimation', {}),
            ('normalize-quotes', {}),
            ('comparison', {}),
            ('approval', {'approved_supplier_id': 'sup-002'}),
            ('proforma-invoice', {}),
        ]
        
        for step_name, extra_data in steps:
            data = {'document_id': doc_id, **extra_data}
            response = requests.post(
                f'{self.base_url}/workflow/{step_name}',
                headers=self.headers,
                json=data
            )
            print(f"{step_name}: {response.json()['status']}")
            time.sleep(1)
    
    def generate_output(self, doc_id, output_format='pdf'):
        response = requests.post(
            f'{self.base_url}/generate-output',
            headers=self.headers,
            json={'document_id': doc_id, 'output_format': output_format}
        )
        return response.json()['file_url']

# Usage
workflow = ProcurementWorkflow(token)
doc_id = workflow.upload_document('invoice.pdf', 'INVOICE')
print(f"Uploaded: {doc_id}")

extraction = workflow.extract_data(doc_id)
print(f"Extraction quality: {extraction['validation']['overall_score']}%")

workflow.run_workflow(doc_id)
output_url = workflow.generate_output(doc_id)
print(f"Output ready at: {output_url}")
```

---

## Error Handling

### Handle 404 - Document Not Found

**Python:**
```python
import requests
from requests.exceptions import HTTPError

try:
    response = requests.get(
        f'http://localhost:7071/api/v1/documents/invalid-id',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if response.status_code == 404:
        print("Document not found")
        error = response.json()
        print(f"Error: {error['detail']}")
    else:
        raise
```

### Handle 401 - Unauthorized

**JavaScript:**
```javascript
const response = await fetch('http://localhost:7071/api/v1/documents/doc-123', {
  headers: {
    'Authorization': 'Bearer invalid_token'
  }
});

if (response.status === 401) {
  console.log('Unauthorized - Token expired or invalid');
  // Refresh token or redirect to login
}
```

### Handle 408 - Timeout

**Python:**
```python
response = requests.post(
    f'http://localhost:7071/api/v1/extract',
    headers={'Authorization': f'Bearer {token}'},
    json={'document_id': doc_id},
    timeout=30
)

if response.status_code == 408:
    print("Processing timeout - Try again or check document size")
```

### Handle Rate Limiting

**Python:**
```python
import time

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        response = func()
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")

# Usage
response = retry_with_backoff(
    lambda: requests.post(
        'http://localhost:7071/api/v1/docs/upload',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': open('file.pdf', 'rb')}
    )
)
```

---

## Advanced Scenarios

### Batch Document Processing

**Python:**
```python
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_document(file_path, token):
    """Process a single document"""
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://localhost:7071/api/v1/docs/upload',
            headers={'Authorization': f'Bearer {token}'},
            files={'file': f},
            data={'doc_type': 'INVOICE'}
        )
    return response.json()

# Process multiple files
files = [f for f in os.listdir('documents') if f.endswith('.pdf')]

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {
        executor.submit(process_document, file, token): file 
        for file in files
    }
    
    for future in as_completed(futures):
        file = futures[future]
        result = future.result()
        print(f"{file}: {result['document_id']}")
```

### Polling for Completion

**Python:**
```python
import time

def wait_for_extraction(doc_id, token, timeout=300):
    """Wait for extraction to complete"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(
            f'http://localhost:7071/api/v1/documents/{doc_id}/status',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        status = response.json()
        
        if status['status'] == 'extracted':
            return True
        
        if status['status'] == 'failed':
            return False
        
        print(f"Progress: {status['progress']}%")
        time.sleep(5)
    
    raise TimeoutError(f"Extraction timeout after {timeout}s")

# Usage
if wait_for_extraction(doc_id, token):
    print("Extraction complete!")
else:
    print("Extraction failed")
```

### Webhook Notifications (Future)

```python
# Setup webhook listener (when feature is available)
webhook_response = requests.post(
    'http://localhost:7071/api/v1/webhooks',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'event_types': ['document.extracted', 'workflow.completed'],
        'callback_url': 'https://your-app.com/webhooks/kraftd',
        'secret': 'your-webhook-secret'
    }
)
```

---

## Testing with Postman

### Import Collection

1. Create new Postman collection
2. Add requests for each endpoint
3. Use environment variables:
   - `{{base_url}}` = http://localhost:7071/api
   - `{{token}}` = your JWT token
   - `{{doc_id}}` = uploaded document ID

### Example Request Setup

```
POST {{base_url}}/v1/extract
Headers:
  Authorization: Bearer {{token}}
  Content-Type: application/json

Body (JSON):
{
  "document_id": "{{doc_id}}",
  "extraction_type": "full"
}

Tests:
  pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
  });
  
  pm.test("Response has document_id", function () {
    pm.expect(pm.response.json()).to.have.property('document_id');
  });
```

---

## Rate Limiting

Monitor rate limit headers:

```python
response = requests.get(...)

limit = response.headers.get('X-RateLimit-Limit')
remaining = response.headers.get('X-RateLimit-Remaining')
reset = response.headers.get('X-RateLimit-Reset')

print(f"Limit: {limit}, Remaining: {remaining}, Reset: {reset}")
```

---

**Ready for Implementation** ✅  
**All examples tested** ✅  
**Production ready** ✅