from locust import HttpUser, task, between, TaskSet
import os
import json
import uuid

class KraftdIntelUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8000"  # Default for local testing, override with --host

    def on_start(self):
        """Setup user session - get authentication token"""
        self.token = self.authenticate()

    def authenticate(self):
        """Simulate user authentication"""
        # For load testing, use a pre-generated token or mock auth
        return os.getenv('TEST_JWT_TOKEN', 'test-token')

    @task(3)
    def upload_document(self):
        """Test document upload endpoint"""
        if os.path.exists("test_document.pdf"):
            with open("test_document.pdf", "rb") as f:
                response = self.client.post("/api/v1/docs/upload",
                                          files={"file": ("test.pdf", f)},
                                          headers={"Authorization": f"Bearer {self.token}"})
                if response.status_code == 200:
                    # Store document ID for later retrieval
                    data = response.json()
                    self.document_id = data.get('id')

    @task(2)
    def get_document_details(self):
        """Test individual document retrieval"""
        if hasattr(self, 'document_id') and self.document_id:
            self.client.get(f"/api/v1/documents/{self.document_id}/output",
                           headers={"Authorization": f"Bearer {self.token}"})

    @task(1)
    def send_verification_email(self):
        """Test email verification endpoint"""
        email = f"test-user-{uuid.uuid4().hex[:8]}@example.com"
        self.client.post("/api/v1/auth/verify-email",
                        json={"email": email},
                        headers={"Authorization": f"Bearer {self.token}"})

    @task(1)
    def get_user_profile(self):
        """Test user profile endpoint"""
        self.client.get("/api/v1/auth/profile",
                       headers={"Authorization": f"Bearer {self.token}"})

    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        self.client.get("/api/v1/health")

# Configuration for different load scenarios
class LightLoadUser(KraftdIntelUser):
    """Light load scenario - fewer concurrent users"""
    wait_time = between(2, 5)

class HeavyLoadUser(KraftdIntelUser):
    """Heavy load scenario - more aggressive testing"""
    wait_time = between(0.5, 2)

class EmailLoadUser(KraftdIntelUser):
    """Email-focused load testing"""
    @task(5)
    def send_verification_email(self):
        email = f"load-test-{uuid.uuid4().hex[:8]}@example.com"
        self.client.post("/api/v1/auth/verify-email",
                        json={"email": email},
                        headers={"Authorization": f"Bearer {self.token}"})

class DocumentLoadUser(KraftdIntelUser):
    """Document processing focused load testing"""
    @task(5)
    def upload_document(self):
        if os.path.exists("test_document.pdf"):
            with open("test_document.pdf", "rb") as f:
                response = self.client.post("/api/v1/docs/upload",
                                          files={"file": ("test.pdf", f)},
                                          headers={"Authorization": f"Bearer {self.token}"})
                if response.status_code == 200:
                    data = response.json()
                    self.document_id = data.get('id')

    @task(3)
    def get_document_details(self):
        if hasattr(self, 'document_id') and self.document_id:
            self.client.get(f"/api/v1/documents/{self.document_id}/output",
                           headers={"Authorization": f"Bearer {self.token}"})

# To run different scenarios:
# locust -f backend/tests/load_test.py --host http://localhost:8000
# locust -f backend/tests/load_test.py --host https://kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io
# locust -f backend/tests/load_test.py KraftdIntelUser -u 10 -r 2 --host http://localhost:8000
# locust -f backend/tests/load_test.py EmailLoadUser -u 50 -r 5 --host http://localhost:8000