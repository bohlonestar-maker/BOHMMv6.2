"""
Test Suite for Square Subscription Integration Endpoints
Tests: GET /api/dues/subscriptions, POST /api/dues/sync-subscriptions, 
       GET /api/dues/all-members-for-linking, POST /api/dues/link-subscription
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - user with SEC title (Secretary) can access subscription endpoints
TEST_CREDENTIALS = {
    "username": "Lonestar",
    "password": "boh2158tc"
}


class TestSubscriptionEndpoints:
    """Test Square subscription integration endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
    
    def test_01_login_success(self):
        """Test that login works with provided credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert data.get("username") == TEST_CREDENTIALS["username"]
        print(f"✓ Login successful for user: {data.get('username')}")
    
    def test_02_get_subscriptions_returns_expected_fields(self):
        """Test GET /api/dues/subscriptions returns match_score, match_type, customer_fetch_method"""
        response = self.session.get(f"{BASE_URL}/api/dues/subscriptions")
        
        assert response.status_code == 200, f"Failed to get subscriptions: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total" in data, "Missing 'total' field"
        assert "matched" in data, "Missing 'matched' field"
        assert "unmatched" in data, "Missing 'unmatched' field"
        assert "customer_fetch_method" in data, "Missing 'customer_fetch_method' field"
        
        # Verify batch API is being used
        assert data["customer_fetch_method"] == "batch", f"Expected 'batch' but got '{data['customer_fetch_method']}'"
        
        print(f"✓ Subscriptions endpoint returned {data['total']} total subscriptions")
        print(f"  - Matched: {len(data['matched'])}")
        print(f"  - Unmatched: {len(data['unmatched'])}")
        print(f"  - Customer fetch method: {data['customer_fetch_method']}")
        
        # Verify matched subscriptions have required fields
        if data["matched"]:
            first_matched = data["matched"][0]
            assert "match_score" in first_matched, "Missing 'match_score' in matched subscription"
            assert "match_type" in first_matched, "Missing 'match_type' in matched subscription"
            assert "matched_member_handle" in first_matched, "Missing 'matched_member_handle'"
            
            # Verify match_type is one of expected values
            valid_match_types = ["manual_link", "exact_name", "exact_handle", "fuzzy_name", "fuzzy_handle", "partial_name"]
            assert first_matched["match_type"] in valid_match_types, f"Invalid match_type: {first_matched['match_type']}"
            
            print(f"  - First matched: {first_matched['customer_name']} -> {first_matched['matched_member_handle']} ({first_matched['match_type']}, score: {first_matched['match_score']})")
    
    def test_03_get_subscriptions_match_types(self):
        """Test that subscriptions have various match types (manual, exact, fuzzy)"""
        response = self.session.get(f"{BASE_URL}/api/dues/subscriptions")
        assert response.status_code == 200
        data = response.json()
        
        match_types_found = set()
        for sub in data.get("matched", []):
            match_types_found.add(sub.get("match_type"))
        
        print(f"✓ Match types found: {match_types_found}")
        
        # At least one match type should be present
        assert len(match_types_found) > 0, "No match types found in matched subscriptions"
    
    def test_04_get_all_members_for_linking(self):
        """Test GET /api/dues/all-members-for-linking returns member list"""
        response = self.session.get(f"{BASE_URL}/api/dues/all-members-for-linking")
        
        assert response.status_code == 200, f"Failed to get members for linking: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list), "Response should be a list"
        
        # Should have members
        assert len(data) > 0, "No members returned for linking"
        
        # Verify member structure
        first_member = data[0]
        assert "id" in first_member, "Missing 'id' field"
        assert "name" in first_member, "Missing 'name' field"
        assert "handle" in first_member, "Missing 'handle' field"
        assert "chapter" in first_member, "Missing 'chapter' field"
        
        print(f"✓ Members for linking endpoint returned {len(data)} members")
        print(f"  - Sample: {first_member['handle']} - {first_member['name']} ({first_member['chapter']})")
    
    def test_05_sync_subscriptions(self):
        """Test POST /api/dues/sync-subscriptions syncs subscriptions"""
        response = self.session.post(f"{BASE_URL}/api/dues/sync-subscriptions")
        
        assert response.status_code == 200, f"Failed to sync subscriptions: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "message" in data, "Missing 'message' field"
        assert "synced" in data, "Missing 'synced' field"
        assert "total_subscriptions" in data, "Missing 'total_subscriptions' field"
        assert "valid_for_month" in data, "Missing 'valid_for_month' field"
        assert "month" in data, "Missing 'month' field"
        
        print(f"✓ Sync subscriptions completed:")
        print(f"  - Message: {data['message']}")
        print(f"  - Synced: {data['synced']}")
        print(f"  - Total subscriptions: {data['total_subscriptions']}")
        print(f"  - Valid for month: {data['valid_for_month']}")
        print(f"  - Month: {data['month']}")
        
        if data.get("errors"):
            print(f"  - Errors: {data['errors']}")
    
    def test_06_link_subscription_validation(self):
        """Test POST /api/dues/link-subscription validates input"""
        # Test with missing fields
        response = self.session.post(
            f"{BASE_URL}/api/dues/link-subscription",
            json={}
        )
        # Should fail validation (422 Unprocessable Entity)
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"
        print("✓ Link subscription validates required fields")
    
    def test_07_link_subscription_invalid_member(self):
        """Test POST /api/dues/link-subscription with invalid member ID"""
        response = self.session.post(
            f"{BASE_URL}/api/dues/link-subscription",
            json={
                "member_id": "invalid-member-id-12345",
                "square_customer_id": "test-customer-id"
            }
        )
        # Should return 404 for member not found
        assert response.status_code == 404, f"Expected 404 for invalid member, got {response.status_code}"
        print("✓ Link subscription returns 404 for invalid member")
    
    def test_08_subscriptions_unauthorized_access(self):
        """Test that subscriptions endpoint requires authentication"""
        # Create new session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        response = unauth_session.get(f"{BASE_URL}/api/dues/subscriptions")
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthorized, got {response.status_code}"
        print("✓ Subscriptions endpoint requires authentication")
    
    def test_09_verify_fuzzy_matching_threshold(self):
        """Test that fuzzy matching uses 75% threshold"""
        response = self.session.get(f"{BASE_URL}/api/dues/subscriptions")
        assert response.status_code == 200
        data = response.json()
        
        # Check that all fuzzy matches have score >= 75
        for sub in data.get("matched", []):
            if sub.get("match_type") in ["fuzzy_name", "fuzzy_handle"]:
                score = sub.get("match_score", 0)
                assert score >= 75, f"Fuzzy match score {score} is below 75% threshold"
        
        print("✓ All fuzzy matches meet 75% threshold")
    
    def test_10_verify_batch_api_performance(self):
        """Test that batch API is used (customer_fetch_method='batch')"""
        response = self.session.get(f"{BASE_URL}/api/dues/subscriptions")
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("customer_fetch_method") == "batch", "Batch API not being used"
        print(f"✓ Batch API confirmed: {data['customer_fetch_method']}")


class TestSubscriptionLinkingFlow:
    """Test the complete manual linking flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
    
    def test_linking_flow_get_unmatched(self):
        """Test getting unmatched subscriptions for linking"""
        response = self.session.get(f"{BASE_URL}/api/dues/subscriptions")
        assert response.status_code == 200
        data = response.json()
        
        unmatched = data.get("unmatched", [])
        print(f"✓ Found {len(unmatched)} unmatched subscriptions")
        
        if unmatched:
            for sub in unmatched[:3]:  # Show first 3
                print(f"  - {sub.get('customer_name', 'Unknown')} ({sub.get('customer_email', 'No email')})")
    
    def test_linking_flow_get_members(self):
        """Test getting members list for linking dropdown"""
        response = self.session.get(f"{BASE_URL}/api/dues/all-members-for-linking")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) > 0, "No members available for linking"
        print(f"✓ {len(data)} members available for linking")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
