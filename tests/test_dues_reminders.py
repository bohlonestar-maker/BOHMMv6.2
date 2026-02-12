"""
Test suite for Dues Reminders feature
Tests:
- GET /api/dues-reminders/templates - returns 3 email templates
- PUT /api/dues-reminders/templates/{template_id} - updates template
- GET /api/dues-reminders/status - returns unpaid members status
- POST /api/dues-reminders/run-check - processes unpaid members
- POST /api/dues-reminders/send-test - generates email preview
- Permission checks - non-authorized users get 403
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://member-manager-26.preview.emergentagent.com').rstrip('/')

# Test credentials
# Lonestar is National Prez - has full access to dues reminders
ADMIN_CREDENTIALS = {"username": "Lonestar", "password": "boh2158tc"}
# Note: The "admin" user provided is actually National SEC, so they ALSO have access
# For non-authorized testing, we would need a user from a different chapter or without Prez/VP/SEC/T title
# Since we don't have valid credentials for such a user, we'll skip unauthorized tests
NON_AUTHORIZED_CREDENTIALS = None  # No valid non-authorized credentials available


class TestDuesRemindersAuth:
    """Test authentication and authorization for dues reminders"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get token for authorized admin (National Prez/VP/SEC/T)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def non_authorized_token(self):
        """Get token for non-authorized user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=NON_AUTHORIZED_CREDENTIALS)
        assert response.status_code == 200, f"Non-authorized login failed: {response.text}"
        return response.json().get("token")
    
    def test_admin_login_success(self):
        """Test that admin credentials work"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data.get("username") == "Lonestar"
        print(f"✅ Admin login successful: {data.get('username')}")
    
    def test_non_authorized_login_success(self):
        """Test that non-authorized credentials work"""
        if NON_AUTHORIZED_CREDENTIALS is None:
            pytest.skip("No non-authorized credentials available for testing")
        response = requests.post(f"{BASE_URL}/api/auth/login", json=NON_AUTHORIZED_CREDENTIALS)
        # If this user doesn't exist or password is wrong, skip the unauthorized tests
        if response.status_code != 200:
            pytest.skip(f"Non-authorized user login failed: {response.status_code}")
        data = response.json()
        assert "token" in data
        print(f"✅ Non-authorized login successful: {data.get('username')}")


class TestDuesRemindersTemplates:
    """Test dues reminder templates endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get token for authorized admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def non_authorized_token(self):
        """Get token for non-authorized user"""
        if NON_AUTHORIZED_CREDENTIALS is None:
            pytest.skip("No non-authorized credentials available")
        response = requests.post(f"{BASE_URL}/api/auth/login", json=NON_AUTHORIZED_CREDENTIALS)
        if response.status_code != 200:
            pytest.skip("Non-authorized user login failed")
        return response.json().get("token")
    
    def test_get_templates_returns_3_templates(self, admin_token):
        """GET /api/dues-reminders/templates should return 3 email templates"""
        response = requests.get(
            f"{BASE_URL}/api/dues-reminders/templates",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to get templates: {response.text}"
        data = response.json()
        
        assert "templates" in data
        templates = data["templates"]
        assert len(templates) == 3, f"Expected 3 templates, got {len(templates)}"
        
        # Verify template structure
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "day_trigger" in template
            assert "subject" in template
            assert "body" in template
            assert "is_active" in template
        
        # Verify day triggers are 3, 8, 10
        day_triggers = [t["day_trigger"] for t in templates]
        assert 3 in day_triggers, "Day 3 template missing"
        assert 8 in day_triggers, "Day 8 template missing"
        assert 10 in day_triggers, "Day 10 template missing"
        
        print(f"✅ GET templates returned {len(templates)} templates with day triggers: {day_triggers}")
    
    def test_get_templates_unauthorized(self, non_authorized_token):
        """Non-authorized users should get 403 on templates endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/dues-reminders/templates",
            headers={"Authorization": f"Bearer {non_authorized_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✅ Non-authorized user correctly received 403 on GET templates")
    
    def test_get_templates_no_auth(self):
        """Unauthenticated requests should get 401/403"""
        response = requests.get(f"{BASE_URL}/api/dues-reminders/templates")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Unauthenticated request correctly rejected")
    
    def test_update_template_success(self, admin_token):
        """PUT /api/dues-reminders/templates/{id} should update template"""
        # First get templates to find one to update
        response = requests.get(
            f"{BASE_URL}/api/dues-reminders/templates",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        templates = response.json()["templates"]
        template_to_update = templates[0]
        template_id = template_to_update["id"]
        
        # Update the template
        update_data = {
            "subject": template_to_update["subject"],  # Keep same subject
            "body": template_to_update["body"],  # Keep same body
            "is_active": template_to_update["is_active"]  # Keep same active status
        }
        
        response = requests.put(
            f"{BASE_URL}/api/dues-reminders/templates/{template_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to update template: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✅ Template {template_id} updated successfully")
    
    def test_update_template_unauthorized(self, non_authorized_token):
        """Non-authorized users should get 403 on update"""
        update_data = {
            "subject": "Test Subject",
            "body": "Test Body",
            "is_active": True
        }
        response = requests.put(
            f"{BASE_URL}/api/dues-reminders/templates/dues_reminder_day3",
            json=update_data,
            headers={"Authorization": f"Bearer {non_authorized_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✅ Non-authorized user correctly received 403 on PUT template")
    
    def test_update_nonexistent_template(self, admin_token):
        """Updating non-existent template should return 404"""
        update_data = {
            "subject": "Test Subject",
            "body": "Test Body",
            "is_active": True
        }
        response = requests.put(
            f"{BASE_URL}/api/dues-reminders/templates/nonexistent_template_id",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ Non-existent template correctly returned 404")


class TestDuesRemindersStatus:
    """Test dues reminder status endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get token for authorized admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def non_authorized_token(self):
        """Get token for non-authorized user"""
        if NON_AUTHORIZED_CREDENTIALS is None:
            pytest.skip("No non-authorized credentials available")
        response = requests.post(f"{BASE_URL}/api/auth/login", json=NON_AUTHORIZED_CREDENTIALS)
        if response.status_code != 200:
            pytest.skip("Non-authorized user login failed")
        return response.json().get("token")
    
    def test_get_status_returns_expected_fields(self, admin_token):
        """GET /api/dues-reminders/status should return expected fields"""
        response = requests.get(
            f"{BASE_URL}/api/dues-reminders/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to get status: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "current_month" in data, "Missing current_month field"
        assert "day_of_month" in data, "Missing day_of_month field"
        assert "unpaid_count" in data, "Missing unpaid_count field"
        assert "suspended_count" in data, "Missing suspended_count field"
        assert "unpaid_members" in data, "Missing unpaid_members field"
        
        # Verify data types
        assert isinstance(data["unpaid_count"], int)
        assert isinstance(data["suspended_count"], int)
        assert isinstance(data["day_of_month"], int)
        assert isinstance(data["unpaid_members"], list)
        
        print(f"✅ Status returned: {data['current_month']}, Day {data['day_of_month']}")
        print(f"   Unpaid: {data['unpaid_count']}, Suspended: {data['suspended_count']}")
    
    def test_status_unpaid_members_structure(self, admin_token):
        """Verify unpaid_members list has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/dues-reminders/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        unpaid_members = data.get("unpaid_members", [])
        
        if len(unpaid_members) > 0:
            member = unpaid_members[0]
            assert "id" in member, "Missing id in unpaid member"
            assert "handle" in member, "Missing handle in unpaid member"
            assert "name" in member, "Missing name in unpaid member"
            assert "email" in member, "Missing email in unpaid member"
            assert "chapter" in member, "Missing chapter in unpaid member"
            assert "reminders_sent" in member, "Missing reminders_sent in unpaid member"
            print(f"✅ Unpaid members structure verified ({len(unpaid_members)} members)")
        else:
            print("✅ No unpaid members found (all dues paid)")
    
    def test_get_status_unauthorized(self, non_authorized_token):
        """Non-authorized users should get 403 on status endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/dues-reminders/status",
            headers={"Authorization": f"Bearer {non_authorized_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✅ Non-authorized user correctly received 403 on GET status")


class TestDuesRemindersRunCheck:
    """Test dues reminder run-check endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get token for authorized admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def non_authorized_token(self):
        """Get token for non-authorized user"""
        if NON_AUTHORIZED_CREDENTIALS is None:
            pytest.skip("No non-authorized credentials available")
        response = requests.post(f"{BASE_URL}/api/auth/login", json=NON_AUTHORIZED_CREDENTIALS)
        if response.status_code != 200:
            pytest.skip("Non-authorized user login failed")
        return response.json().get("token")
    
    def test_run_check_success(self, admin_token):
        """POST /api/dues-reminders/run-check should process unpaid members"""
        response = requests.post(
            f"{BASE_URL}/api/dues-reminders/run-check",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to run check: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "message" in data, "Missing message in response"
        assert "emails_sent" in data, "Missing emails_sent in response"
        
        print(f"✅ Run check completed: {data.get('message')}")
        print(f"   Emails sent: {data.get('emails_sent')}")
        if data.get("template_used"):
            print(f"   Template used: {data.get('template_used')}")
    
    def test_run_check_unauthorized(self, non_authorized_token):
        """Non-authorized users should get 403 on run-check"""
        response = requests.post(
            f"{BASE_URL}/api/dues-reminders/run-check",
            json={},
            headers={"Authorization": f"Bearer {non_authorized_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✅ Non-authorized user correctly received 403 on POST run-check")


class TestDuesRemindersSendTest:
    """Test dues reminder send-test endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get token for authorized admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def non_authorized_token(self):
        """Get token for non-authorized user"""
        if NON_AUTHORIZED_CREDENTIALS is None:
            pytest.skip("No non-authorized credentials available")
        response = requests.post(f"{BASE_URL}/api/auth/login", json=NON_AUTHORIZED_CREDENTIALS)
        if response.status_code != 200:
            pytest.skip("Non-authorized user login failed")
        return response.json().get("token")
    
    def test_send_test_generates_preview(self, admin_token):
        """POST /api/dues-reminders/send-test should generate email preview"""
        response = requests.post(
            f"{BASE_URL}/api/dues-reminders/send-test",
            params={"template_id": "dues_reminder_day3", "email": "test@example.com"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to send test: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data.get("success") == True, "Expected success=True"
        assert "preview" in data, "Missing preview in response"
        
        preview = data["preview"]
        assert "to" in preview, "Missing 'to' in preview"
        assert "subject" in preview, "Missing 'subject' in preview"
        assert "body" in preview, "Missing 'body' in preview"
        
        # Verify placeholders were replaced (if template has them)
        # Note: Template may have been modified, so just check structure
        assert preview["to"] == "test@example.com", "Email address mismatch"
        
        print(f"✅ Test email preview generated")
        print(f"   To: {preview['to']}")
        print(f"   Subject: {preview['subject'][:50]}...")
    
    def test_send_test_nonexistent_template(self, admin_token):
        """Sending test with non-existent template should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/dues-reminders/send-test",
            params={"template_id": "nonexistent_template", "email": "test@example.com"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ Non-existent template correctly returned 404")
    
    def test_send_test_unauthorized(self, non_authorized_token):
        """Non-authorized users should get 403 on send-test"""
        response = requests.post(
            f"{BASE_URL}/api/dues-reminders/send-test",
            params={"template_id": "dues_reminder_day3", "email": "test@example.com"},
            headers={"Authorization": f"Bearer {non_authorized_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✅ Non-authorized user correctly received 403 on POST send-test")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
