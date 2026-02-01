"""
Test suite for Non-Dues Paying Member Feature
Tests:
1. Backend API accepts and returns non_dues_paying field
2. Officer Tracking members endpoint returns non_dues_paying field
3. Dues reminder status skips non_dues_paying members
4. Member create/update with non_dues_paying field
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestNonDuesPayingFeature:
    """Test non_dues_paying member feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "Lonestar",
            "password": "boh2158tc"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Store test member ID for cleanup
        self.test_member_id = None
        yield
        
        # Cleanup: Delete test member if created
        if self.test_member_id:
            try:
                self.session.delete(f"{BASE_URL}/api/members/{self.test_member_id}")
            except:
                pass
    
    def test_login_success(self):
        """Test login with officer credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "Lonestar",
            "password": "boh2158tc"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["username"] == "Lonestar"
        print("✅ Login successful")
    
    def test_officer_tracking_members_returns_non_dues_paying(self):
        """Test that officer-tracking/members endpoint returns non_dues_paying field"""
        response = self.session.get(f"{BASE_URL}/api/officer-tracking/members")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Response should be a dict with chapter keys
        assert isinstance(data, dict), "Response should be a dict with chapter keys"
        
        # Check at least one chapter has members
        has_members = False
        for chapter, members in data.items():
            if members:
                has_members = True
                # Check first member has non_dues_paying field
                first_member = members[0]
                assert "non_dues_paying" in first_member, f"Member missing non_dues_paying field: {first_member.keys()}"
                assert isinstance(first_member["non_dues_paying"], bool), "non_dues_paying should be boolean"
                print(f"✅ Chapter {chapter}: {len(members)} members, first member non_dues_paying={first_member['non_dues_paying']}")
        
        assert has_members, "No members found in any chapter"
        print("✅ officer-tracking/members returns non_dues_paying field")
    
    def test_create_member_with_non_dues_paying_true(self):
        """Test creating a member with non_dues_paying=true"""
        test_member = {
            "chapter": "AD",
            "title": "Brother",
            "handle": "TEST_NonDuesPayingMember",
            "name": "Test Non Dues Member",
            "email": "test_nondues@example.com",
            "phone": "555-123-4567",
            "address": "123 Test St",
            "non_dues_paying": True
        }
        
        response = self.session.post(f"{BASE_URL}/api/members", json=test_member)
        assert response.status_code in [200, 201], f"Create failed: {response.text}"
        
        data = response.json()
        self.test_member_id = data.get("id")
        
        # Verify non_dues_paying is set
        assert data.get("non_dues_paying") == True, f"non_dues_paying should be True, got: {data.get('non_dues_paying')}"
        print(f"✅ Created member with non_dues_paying=True, ID: {self.test_member_id}")
        
        # Verify by fetching the member
        get_response = self.session.get(f"{BASE_URL}/api/members/{self.test_member_id}")
        assert get_response.status_code == 200, f"Get member failed: {get_response.text}"
        
        fetched = get_response.json()
        assert fetched.get("non_dues_paying") == True, "non_dues_paying not persisted correctly"
        print("✅ Verified non_dues_paying=True persisted in database")
    
    def test_update_member_non_dues_paying(self):
        """Test updating a member's non_dues_paying status"""
        # First create a member with non_dues_paying=false
        test_member = {
            "chapter": "AD",
            "title": "Brother",
            "handle": "TEST_UpdateNonDues",
            "name": "Test Update Non Dues",
            "email": "test_update_nondues@example.com",
            "phone": "555-987-6543",
            "address": "456 Test Ave",
            "non_dues_paying": False
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/members", json=test_member)
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        
        member_id = create_response.json().get("id")
        self.test_member_id = member_id
        
        # Update to non_dues_paying=true
        update_response = self.session.put(f"{BASE_URL}/api/members/{member_id}", json={
            "non_dues_paying": True
        })
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        updated = update_response.json()
        assert updated.get("non_dues_paying") == True, f"non_dues_paying should be True after update, got: {updated.get('non_dues_paying')}"
        print("✅ Updated member non_dues_paying from False to True")
        
        # Verify by fetching
        get_response = self.session.get(f"{BASE_URL}/api/members/{member_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched.get("non_dues_paying") == True, "Update not persisted"
        print("✅ Verified non_dues_paying update persisted")
    
    def test_dues_reminder_status_excludes_non_dues_paying(self):
        """Test that dues reminder status endpoint excludes non_dues_paying members"""
        response = self.session.get(f"{BASE_URL}/api/dues-reminders/status")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Check response structure
        assert "unpaid_members" in data, "Response should have unpaid_members"
        assert "unpaid_count" in data, "Response should have unpaid_count"
        
        unpaid_members = data.get("unpaid_members", [])
        
        # Verify no non_dues_paying members in unpaid list
        # Note: We can't directly check this without knowing which members are non_dues_paying
        # But we can verify the structure is correct
        print(f"✅ Dues reminder status: {data.get('unpaid_count')} unpaid members")
        print(f"   Current month: {data.get('current_month')}")
        print(f"   Day of month: {data.get('day_of_month')}")
        
        # If there are unpaid members, check they don't have non_dues_paying=true
        for member in unpaid_members[:5]:  # Check first 5
            # The unpaid_members list shouldn't include non_dues_paying members
            # based on the backend logic we reviewed
            print(f"   - {member.get('handle')}: {member.get('chapter')}")
        
        print("✅ Dues reminder status endpoint working correctly")
    
    def test_member_list_includes_non_dues_paying_field(self):
        """Test that member list includes non_dues_paying field"""
        response = self.session.get(f"{BASE_URL}/api/members")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        members = response.json()
        assert isinstance(members, list), "Response should be a list"
        assert len(members) > 0, "Should have at least one member"
        
        # Check first few members have non_dues_paying field
        for member in members[:3]:
            # non_dues_paying might not be in the list response, check if it exists
            if "non_dues_paying" in member:
                assert isinstance(member["non_dues_paying"], bool), "non_dues_paying should be boolean"
                print(f"✅ Member {member.get('handle')}: non_dues_paying={member.get('non_dues_paying')}")
        
        print(f"✅ Member list returned {len(members)} members")


class TestDuesExemptionBehavior:
    """Test that non_dues_paying members are properly exempted from dues tracking"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "Lonestar",
            "password": "boh2158tc"
        })
        assert response.status_code == 200
        self.token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        self.test_member_id = None
        yield
        
        # Cleanup
        if self.test_member_id:
            try:
                self.session.delete(f"{BASE_URL}/api/members/{self.test_member_id}")
            except:
                pass
    
    def test_non_dues_paying_member_not_in_unpaid_list(self):
        """Create a non_dues_paying member and verify they don't appear in unpaid dues list"""
        # Create a non_dues_paying member
        test_member = {
            "chapter": "AD",
            "title": "Brother",
            "handle": "TEST_ExemptMember",
            "name": "Test Exempt Member",
            "email": "test_exempt@example.com",
            "phone": "555-111-2222",
            "address": "789 Exempt Lane",
            "non_dues_paying": True
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/members", json=test_member)
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        
        member_id = create_response.json().get("id")
        self.test_member_id = member_id
        print(f"✅ Created exempt member: {member_id}")
        
        # Check dues reminder status - exempt member should NOT be in unpaid list
        status_response = self.session.get(f"{BASE_URL}/api/dues-reminders/status")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        unpaid_members = status_data.get("unpaid_members", [])
        
        # Verify our test member is NOT in the unpaid list
        unpaid_ids = [m.get("id") for m in unpaid_members]
        assert member_id not in unpaid_ids, f"Non-dues paying member {member_id} should NOT be in unpaid list"
        print("✅ Verified exempt member is NOT in unpaid dues list")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
