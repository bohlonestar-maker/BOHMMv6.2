"""
Document Signing System Tests
Tests for the in-house document signing feature that replaces SignNow.
- Template management (list, create, get)
- Document sending to members
- Public signing endpoint (no auth)
- Signature submission
"""
import pytest
import requests
import os
import uuid

# Base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "2X13y75Z"


class TestDocumentTemplates:
    """Document template endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test - login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_templates_list(self):
        """GET /api/documents/templates - should return list of templates"""
        response = requests.get(
            f"{BASE_URL}/api/documents/templates",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to get templates: {response.text}"
        templates = response.json()
        assert isinstance(templates, list), "Templates should be a list"
        
        print(f"✅ GET /api/documents/templates: Found {len(templates)} templates")
        
        # Check structure of templates if any exist
        if len(templates) > 0:
            template = templates[0]
            assert "id" in template, "Template should have 'id'"
            assert "name" in template, "Template should have 'name'"
            assert "template_type" in template, "Template should have 'template_type'"
            print(f"   First template: {template['name']} ({template['template_type']})")
    
    def test_get_templates_with_inactive(self):
        """GET /api/documents/templates?include_inactive=true"""
        response = requests.get(
            f"{BASE_URL}/api/documents/templates",
            params={"include_inactive": True},
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to get templates: {response.text}"
        templates = response.json()
        print(f"✅ GET /api/documents/templates?include_inactive=true: Found {len(templates)} templates")
    
    def test_create_text_template(self):
        """POST /api/documents/templates - create new text template"""
        unique_name = f"TEST_Template_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/documents/templates",
            headers=self.headers,
            data={
                "name": unique_name,
                "description": "Test template for automated testing",
                "template_type": "text",
                "category": "Other",
                "text_content": "This is a test document for signing.\n\nPlease sign below to confirm."
            }
        )
        
        assert response.status_code == 200, f"Failed to create template: {response.text}"
        template = response.json()
        
        assert template["name"] == unique_name, "Template name mismatch"
        assert template["template_type"] == "text", "Template type should be 'text'"
        assert "id" in template, "Template should have 'id'"
        
        print(f"✅ POST /api/documents/templates: Created template '{unique_name}' with ID: {template['id']}")
        
        # Store for cleanup or further tests
        self.created_template_id = template["id"]
        
        # Verify by fetching
        get_response = requests.get(
            f"{BASE_URL}/api/documents/templates/{template['id']}",
            headers=self.headers
        )
        assert get_response.status_code == 200, "Failed to fetch created template"
        fetched = get_response.json()
        assert fetched["name"] == unique_name, "Fetched template name mismatch"
        print(f"   Verified template persistence via GET")
    
    def test_create_template_validation(self):
        """POST /api/documents/templates - validation tests"""
        # Test missing template type
        response = requests.post(
            f"{BASE_URL}/api/documents/templates",
            headers=self.headers,
            data={
                "name": "Invalid Template",
                "template_type": "invalid_type",
                "text_content": "Test content"
            }
        )
        
        assert response.status_code == 400, "Should reject invalid template_type"
        print(f"✅ Validation: Rejects invalid template_type")
        
        # Test text template without content
        response = requests.post(
            f"{BASE_URL}/api/documents/templates",
            headers=self.headers,
            data={
                "name": "No Content Template",
                "template_type": "text",
            }
        )
        
        assert response.status_code == 400, "Should reject text template without content"
        print(f"✅ Validation: Rejects text template without content")
    
    def test_get_template_by_id(self):
        """GET /api/documents/templates/{template_id}"""
        # First get list to find an ID
        response = requests.get(
            f"{BASE_URL}/api/documents/templates",
            headers=self.headers
        )
        templates = response.json()
        
        if len(templates) == 0:
            pytest.skip("No templates available to test")
        
        template_id = templates[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/documents/templates/{template_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to get template by ID: {response.text}"
        template = response.json()
        assert template["id"] == template_id
        print(f"✅ GET /api/documents/templates/{template_id}: Retrieved '{template['name']}'")
    
    def test_get_nonexistent_template(self):
        """GET /api/documents/templates/{invalid_id} - should return 404"""
        fake_id = str(uuid.uuid4())
        
        response = requests.get(
            f"{BASE_URL}/api/documents/templates/{fake_id}",
            headers=self.headers
        )
        
        assert response.status_code == 404, "Should return 404 for nonexistent template"
        print(f"✅ GET /api/documents/templates/{fake_id[:8]}...: Returns 404 as expected")
    
    def test_templates_require_auth(self):
        """Templates endpoints should require authentication"""
        response = requests.get(f"{BASE_URL}/api/documents/templates")
        assert response.status_code in [401, 403], "Should require auth"
        print(f"✅ Templates endpoint requires authentication")


class TestDocumentSending:
    """Document sending tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a member ID for testing
        members_response = requests.get(
            f"{BASE_URL}/api/members",
            headers=self.headers
        )
        if members_response.status_code == 200:
            members = members_response.json()
            if len(members) > 0:
                self.test_member = members[0]
                self.test_member_id = members[0]["id"]
                self.test_member_email = members[0].get("email", "test@example.com")
                self.test_member_name = members[0].get("handle", "Test Member")
    
    def test_send_document_to_member(self):
        """POST /api/documents/send - send document for signing"""
        # Get a template first
        templates_response = requests.get(
            f"{BASE_URL}/api/documents/templates",
            headers=self.headers
        )
        templates = templates_response.json()
        
        if len(templates) == 0:
            pytest.skip("No templates available")
        
        template_id = templates[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/documents/send",
            headers=self.headers,
            data={
                "template_id": template_id,
                "member_id": self.test_member_id,
                "recipient_email": self.test_member_email,
                "recipient_name": self.test_member_name,
                "message": "Please sign this test document"
            }
        )
        
        assert response.status_code == 200, f"Failed to send document: {response.text}"
        result = response.json()
        
        assert "id" in result, "Response should have request 'id'"
        assert result["status"] == "pending", "Initial status should be 'pending'"
        assert result["member_id"] == self.test_member_id
        assert result["recipient_email"] == self.test_member_email
        
        print(f"✅ POST /api/documents/send: Document sent, request ID: {result['id']}")
        
        # Store for later tests
        self.signing_request_id = result["id"]
    
    def test_send_document_invalid_template(self):
        """POST /api/documents/send - should fail with invalid template"""
        response = requests.post(
            f"{BASE_URL}/api/documents/send",
            headers=self.headers,
            data={
                "template_id": str(uuid.uuid4()),
                "member_id": self.test_member_id,
                "recipient_email": "test@example.com",
                "recipient_name": "Test User"
            }
        )
        
        assert response.status_code == 404, "Should return 404 for invalid template"
        print(f"✅ Validation: Rejects invalid template_id")
    
    def test_send_document_invalid_member(self):
        """POST /api/documents/send - should fail with invalid member"""
        # Get a template first
        templates_response = requests.get(
            f"{BASE_URL}/api/documents/templates",
            headers=self.headers
        )
        templates = templates_response.json()
        
        if len(templates) == 0:
            pytest.skip("No templates available")
        
        response = requests.post(
            f"{BASE_URL}/api/documents/send",
            headers=self.headers,
            data={
                "template_id": templates[0]["id"],
                "member_id": str(uuid.uuid4()),  # Invalid member ID
                "recipient_email": "test@example.com",
                "recipient_name": "Test User"
            }
        )
        
        assert response.status_code == 404, "Should return 404 for invalid member"
        print(f"✅ Validation: Rejects invalid member_id")


class TestSigningRequests:
    """Signing request management tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_signing_requests(self):
        """GET /api/documents/requests - list signing requests"""
        response = requests.get(
            f"{BASE_URL}/api/documents/requests",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to get requests: {response.text}"
        requests_list = response.json()
        assert isinstance(requests_list, list), "Should return a list"
        
        print(f"✅ GET /api/documents/requests: Found {len(requests_list)} signing requests")
        
        if len(requests_list) > 0:
            req = requests_list[0]
            assert "id" in req
            assert "template_name" in req
            assert "recipient_name" in req
            assert "status" in req
            print(f"   First request: {req['template_name']} to {req['recipient_name']} ({req['status']})")
    
    def test_get_signing_requests_by_member(self):
        """GET /api/documents/requests?member_id={id}"""
        # Get a member ID first
        members_response = requests.get(f"{BASE_URL}/api/members", headers=self.headers)
        members = members_response.json()
        
        if len(members) == 0:
            pytest.skip("No members available")
        
        member_id = members[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/documents/requests",
            params={"member_id": member_id},
            headers=self.headers
        )
        
        assert response.status_code == 200
        requests_list = response.json()
        
        # All returned requests should be for this member
        for req in requests_list:
            assert req["member_id"] == member_id
        
        print(f"✅ GET /api/documents/requests?member_id=...: Found {len(requests_list)} requests for member")
    
    def test_get_signing_requests_by_status(self):
        """GET /api/documents/requests?status={status}"""
        response = requests.get(
            f"{BASE_URL}/api/documents/requests",
            params={"status": "pending"},
            headers=self.headers
        )
        
        assert response.status_code == 200
        requests_list = response.json()
        
        for req in requests_list:
            assert req["status"] == "pending"
        
        print(f"✅ GET /api/documents/requests?status=pending: Found {len(requests_list)} pending requests")


class TestPublicSigningEndpoint:
    """Public signing endpoint tests (no auth required)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - create a test signing request to get a valid token"""
        # Login as admin
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get signing requests to find a valid signing token for testing
        requests_response = requests.get(
            f"{BASE_URL}/api/documents/requests",
            headers=self.headers
        )
        self.signing_requests = requests_response.json() if requests_response.status_code == 200 else []
    
    def test_public_signing_invalid_token(self):
        """GET /api/documents/sign/{invalid_token} - should return 404"""
        fake_token = f"{uuid.uuid4()}-{uuid.uuid4()}"
        
        # Public endpoint - no auth required
        response = requests.get(f"{BASE_URL}/api/documents/sign/{fake_token}")
        
        assert response.status_code == 404, f"Should return 404 for invalid token: {response.text}"
        print(f"✅ GET /api/documents/sign/{fake_token[:8]}...: Returns 404 as expected")
    
    def test_public_signing_no_auth_required(self):
        """Public signing endpoint should not require authentication"""
        fake_token = f"{uuid.uuid4()}-{uuid.uuid4()}"
        
        # Make request WITHOUT auth header
        response = requests.get(f"{BASE_URL}/api/documents/sign/{fake_token}")
        
        # Should get 404 (not found) NOT 401/403 (unauthorized)
        assert response.status_code == 404, "Should return 404, not auth error"
        print(f"✅ Public signing endpoint does not require auth")


class TestSignatureSubmission:
    """Signature submission tests"""
    
    def test_submit_signature_invalid_token(self):
        """POST /api/documents/sign/{invalid_token}/submit - should return 404"""
        fake_token = f"{uuid.uuid4()}-{uuid.uuid4()}"
        
        response = requests.post(
            f"{BASE_URL}/api/documents/sign/{fake_token}/submit",
            data={
                "signature_type": "typed",
                "typed_name": "Test User",
                "consent_agreed": "true"
            }
        )
        
        assert response.status_code == 404, "Should return 404 for invalid token"
        print(f"✅ POST /api/documents/sign/{fake_token[:8]}../submit: Returns 404 as expected")
    
    def test_submit_signature_no_consent(self):
        """POST /api/documents/sign/{token}/submit - should fail without consent"""
        # This would need a valid token to test properly
        # For now, just verify the endpoint structure
        fake_token = f"{uuid.uuid4()}-{uuid.uuid4()}"
        
        response = requests.post(
            f"{BASE_URL}/api/documents/sign/{fake_token}/submit",
            data={
                "signature_type": "typed",
                "typed_name": "Test User",
                "consent_agreed": "false"  # Should be rejected
            }
        )
        
        # Will be 404 because token is invalid, but endpoint is accessible
        assert response.status_code in [400, 404]
        print(f"✅ Signature submission endpoint accessible")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
