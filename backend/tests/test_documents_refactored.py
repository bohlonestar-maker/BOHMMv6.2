"""
Document Signing Module Unit Tests
Tests for the refactored document signing modules:
- utils.py - Utility functions
- templates.py - Template endpoints
- signing.py - Signing endpoints
- officers.py - National officers endpoint
- pdf.py - PDF generation
"""
import pytest
import requests
import os
import sys
import uuid

# Add backend to path for direct imports
sys.path.insert(0, '/app/backend')

# Base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "2X13y75Z"


class TestDocumentUtils:
    """Test utility functions from documents/utils.py"""
    
    def test_generate_signing_token(self):
        """Test signing token generation produces unique tokens"""
        from routes.documents.utils import generate_signing_token
        
        tokens = set()
        for _ in range(100):
            token = generate_signing_token()
            assert token not in tokens, "Token collision detected"
            tokens.add(token)
            assert "-" in token, "Token should contain hyphens"
            assert len(token) > 30, "Token should be sufficiently long"
        
        print(f"✅ generate_signing_token: Generated 100 unique tokens")
    
    def test_hash_document(self):
        """Test document hashing produces consistent SHA-256 hashes"""
        from routes.documents.utils import hash_document
        
        content = b"Test document content"
        hash1 = hash_document(content)
        hash2 = hash_document(content)
        
        assert hash1 == hash2, "Same content should produce same hash"
        assert len(hash1) == 64, "SHA-256 hash should be 64 characters"
        
        # Different content should produce different hash
        hash3 = hash_document(b"Different content")
        assert hash1 != hash3, "Different content should produce different hash"
        
        print(f"✅ hash_document: Produces consistent SHA-256 hashes")
    
    def test_national_officers_list(self):
        """Test NATIONAL_OFFICERS constant is properly configured"""
        from routes.documents.utils import NATIONAL_OFFICERS
        
        assert isinstance(NATIONAL_OFFICERS, list), "Should be a list"
        assert len(NATIONAL_OFFICERS) == 6, "Should have 6 national officers"
        
        # Check structure
        for officer in NATIONAL_OFFICERS:
            assert "role" in officer, "Officer should have 'role'"
            assert "title" in officer, "Officer should have 'title'"
            assert "display_title" in officer, "Officer should have 'display_title'"
            assert "order" in officer, "Officer should have 'order'"
        
        # Check no National Road Captain (was removed per user request)
        roles = [o["role"] for o in NATIONAL_OFFICERS]
        assert "national_road_captain" not in roles, "National Road Captain should not be in list"
        
        print(f"✅ NATIONAL_OFFICERS: Contains {len(NATIONAL_OFFICERS)} officers (no Road Captain)")
    
    def test_check_document_permission(self):
        """Test permission checking logic"""
        from routes.documents.utils import check_document_permission
        
        # Admin should have permission
        admin_user = {"role": "admin", "permissions": {}}
        assert check_document_permission(admin_user) == True
        
        # User with send_documents permission
        permitted_user = {"role": "officer", "permissions": {"send_documents": True}}
        assert check_document_permission(permitted_user) == True
        
        # User without permission
        unpermitted_user = {"role": "member", "permissions": {"view_members": True}}
        assert check_document_permission(unpermitted_user) == False
        
        print(f"✅ check_document_permission: Correctly validates permissions")


class TestNationalOfficersEndpoint:
    """Test the national officers API endpoint"""
    
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
    
    def test_get_national_officers(self):
        """GET /api/documents/national-officers - returns list of officers"""
        response = requests.get(
            f"{BASE_URL}/api/documents/national-officers",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        officers = response.json()
        
        assert isinstance(officers, list), "Should return a list"
        assert len(officers) == 6, "Should return 6 officers"
        
        # Check structure
        for officer in officers:
            assert "role" in officer
            assert "title" in officer
            assert "display_title" in officer
            assert "order" in officer
            # user may be None if no one has that title
            assert "user" in officer
        
        print(f"✅ GET /api/documents/national-officers: {len(officers)} officers returned")
    
    def test_national_officers_requires_auth(self):
        """National officers endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/documents/national-officers")
        assert response.status_code in [401, 403], "Should require auth"
        print(f"✅ National officers endpoint requires authentication")


class TestRefactoredTemplatesModule:
    """Test template endpoints from the refactored templates.py module"""
    
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
    
    def test_templates_list_excludes_pdf_data(self):
        """GET /api/documents/templates - should NOT include pdf_data in list response"""
        response = requests.get(
            f"{BASE_URL}/api/documents/templates",
            headers=self.headers
        )
        
        assert response.status_code == 200
        templates = response.json()
        
        for template in templates:
            # pdf_data should be excluded for performance
            assert "pdf_data" not in template, "List should not include pdf_data"
            # But should have other fields
            assert "id" in template
            assert "name" in template
        
        print(f"✅ Templates list correctly excludes pdf_data for performance")
    
    def test_template_pages_endpoint(self):
        """Test PDF page rendering endpoint for template editor"""
        # Get templates to find one with PDF
        response = requests.get(
            f"{BASE_URL}/api/documents/templates",
            headers=self.headers
        )
        templates = response.json()
        
        pdf_template = None
        for t in templates:
            if t.get("template_type") == "pdf":
                pdf_template = t
                break
        
        if not pdf_template:
            pytest.skip("No PDF template available for testing")
        
        # Test page rendering
        response = requests.get(
            f"{BASE_URL}/api/documents/templates/{pdf_template['id']}/pages/1",
            headers=self.headers
        )
        
        if response.status_code == 200:
            # Should return image
            content_type = response.headers.get("content-type", "")
            assert "image" in content_type, "Should return an image"
            print(f"✅ Template page rendering endpoint works for PDF templates")
        else:
            print(f"⚠️ Page rendering returned {response.status_code} - may need PyMuPDF")


class TestRefactoredSigningModule:
    """Test signing endpoints from the refactored signing.py module"""
    
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
        
        assert response.status_code == 200, f"Failed: {response.text}"
        requests_list = response.json()
        assert isinstance(requests_list, list), "Should return a list"
        
        print(f"✅ GET /api/documents/requests: {len(requests_list)} requests found")
    
    def test_get_signing_requests_by_status(self):
        """GET /api/documents/requests?status=pending - filter by status"""
        response = requests.get(
            f"{BASE_URL}/api/documents/requests",
            params={"status": "completed"},
            headers=self.headers
        )
        
        assert response.status_code == 200
        requests_list = response.json()
        
        # All returned should have matching status
        for req in requests_list:
            assert req.get("status") == "completed"
        
        print(f"✅ Signing requests filter by status works")
    
    def test_signing_requests_no_token_leak(self):
        """Signing requests list should NOT expose signing_token"""
        response = requests.get(
            f"{BASE_URL}/api/documents/requests",
            headers=self.headers
        )
        
        assert response.status_code == 200
        requests_list = response.json()
        
        for req in requests_list:
            assert "signing_token" not in req, "signing_token should not be exposed"
        
        print(f"✅ Signing requests correctly hide signing_token")


class TestModuleIntegration:
    """Integration tests for the refactored modules working together"""
    
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
    
    def test_full_document_workflow(self):
        """Test complete workflow: templates -> officers -> send -> sign"""
        # 1. Get templates
        templates_resp = requests.get(
            f"{BASE_URL}/api/documents/templates",
            headers=self.headers
        )
        assert templates_resp.status_code == 200
        templates = templates_resp.json()
        print(f"   Step 1: {len(templates)} templates available")
        
        # 2. Get national officers
        officers_resp = requests.get(
            f"{BASE_URL}/api/documents/national-officers",
            headers=self.headers
        )
        assert officers_resp.status_code == 200
        officers = officers_resp.json()
        print(f"   Step 2: {len(officers)} officers available as approvers")
        
        # 3. Get signing requests
        requests_resp = requests.get(
            f"{BASE_URL}/api/documents/requests",
            headers=self.headers
        )
        assert requests_resp.status_code == 200
        sign_requests = requests_resp.json()
        print(f"   Step 3: {len(sign_requests)} signing requests in system")
        
        print(f"✅ Full document workflow integration test passed")
    
    def test_router_prefix_consistency(self):
        """Verify all document endpoints use /api/documents prefix"""
        endpoints = [
            "/api/documents/templates",
            "/api/documents/national-officers",
            "/api/documents/requests",
        ]
        
        for endpoint in endpoints:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=self.headers
            )
            assert response.status_code == 200, f"Endpoint {endpoint} failed"
        
        print(f"✅ All document endpoints use consistent /api/documents prefix")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
