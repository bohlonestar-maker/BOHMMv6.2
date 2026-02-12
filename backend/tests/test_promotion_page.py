"""
Test suite for Promotion Page - Discord role and nickname management
Tests the Discord promotion endpoints for managing member roles and nicknames
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USER = "admin"
ADMIN_PASSWORD = "2X13y75Z"

# Test member - Q-Ball is linked to Discord
TEST_MEMBER_ID = "4b34e4e6-b059-4c1a-92d1-9ceb4d71c76b"
TEST_MEMBER_HANDLE = "Q-Ball"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": ADMIN_USER, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated API client"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestDiscordRolesEndpoint:
    """Tests for GET /api/discord/roles endpoint"""
    
    def test_get_discord_roles_success(self, api_client):
        """Test that Discord roles endpoint returns list of roles"""
        response = api_client.get(f"{BASE_URL}/api/discord/roles")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "roles" in data, "Response should contain 'roles' key"
        assert isinstance(data["roles"], list), "Roles should be a list"
        assert len(data["roles"]) > 0, "Should have at least one role"
        
        # Verify role structure
        first_role = data["roles"][0]
        assert "id" in first_role, "Role should have 'id'"
        assert "name" in first_role, "Role should have 'name'"
        assert "position" in first_role, "Role should have 'position'"
        # color can be null
        assert "color" in first_role or first_role.get("color") is None
    
    def test_get_discord_roles_without_auth(self):
        """Test that Discord roles endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/discord/roles")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_discord_roles_have_expected_fields(self, api_client):
        """Test that roles have all expected fields"""
        response = api_client.get(f"{BASE_URL}/api/discord/roles")
        assert response.status_code == 200
        
        data = response.json()
        for role in data["roles"]:
            assert "id" in role, "Role missing 'id'"
            assert "name" in role, "Role missing 'name'"
            assert "position" in role, "Role missing 'position'"
            assert "permissions" in role, "Role missing 'permissions'"
            # Verify id is a string (Discord IDs are large numbers)
            assert isinstance(role["id"], str), "Role ID should be string"


class TestMemberDiscordRolesEndpoint:
    """Tests for GET /api/discord/member/{id}/roles endpoint"""
    
    def test_get_member_discord_roles_success(self, api_client):
        """Test getting Discord roles for a linked member (Q-Ball)"""
        response = api_client.get(f"{BASE_URL}/api/discord/member/{TEST_MEMBER_ID}/roles")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "roles" in data, "Response should contain 'roles'"
        assert isinstance(data["roles"], list), "Roles should be a list"
        
        # Q-Ball should have roles since they're linked to Discord
        assert len(data["roles"]) > 0, "Q-Ball should have Discord roles"
        
        # Verify role structure
        for role in data["roles"]:
            assert "id" in role, "Role should have 'id'"
            assert "name" in role, "Role should have 'name'"
    
    def test_get_member_discord_roles_returns_nickname(self, api_client):
        """Test that member Discord info includes nickname"""
        response = api_client.get(f"{BASE_URL}/api/discord/member/{TEST_MEMBER_ID}/roles")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have nickname field
        assert "nickname" in data, "Response should include 'nickname'"
        # Q-Ball's nickname should contain their handle
        if data["nickname"]:
            assert "Q-Ball" in data["nickname"], f"Nickname should contain Q-Ball, got: {data['nickname']}"
    
    def test_get_member_discord_roles_returns_discord_id(self, api_client):
        """Test that member Discord info includes discord_id"""
        response = api_client.get(f"{BASE_URL}/api/discord/member/{TEST_MEMBER_ID}/roles")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have discord_id field
        assert "discord_id" in data, "Response should include 'discord_id'"
        assert data["discord_id"], "Discord ID should not be empty for linked member"
    
    def test_get_member_discord_roles_nonexistent_member(self, api_client):
        """Test getting Discord roles for non-existent member returns 404"""
        response = api_client.get(f"{BASE_URL}/api/discord/member/nonexistent-id-12345/roles")
        
        assert response.status_code == 404, f"Expected 404 for non-existent member, got {response.status_code}"
    
    def test_get_member_discord_roles_without_auth(self):
        """Test that member Discord roles endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/discord/member/{TEST_MEMBER_ID}/roles")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"


class TestMembersEndpoint:
    """Tests for GET /api/members endpoint (used by Promotion Page)"""
    
    def test_get_members_success(self, api_client):
        """Test that members endpoint returns list of members"""
        response = api_client.get(f"{BASE_URL}/api/members")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Members should be a list"
        assert len(data) > 0, "Should have at least one member"
        
        # Verify member structure
        first_member = data[0]
        assert "id" in first_member, "Member should have 'id'"
        assert "handle" in first_member, "Member should have 'handle'"
    
    def test_members_include_qball(self, api_client):
        """Test that Q-Ball is in the members list"""
        response = api_client.get(f"{BASE_URL}/api/members")
        
        assert response.status_code == 200
        data = response.json()
        
        qball = next((m for m in data if m.get("handle") == TEST_MEMBER_HANDLE), None)
        assert qball is not None, f"Q-Ball should be in members list"
        assert qball["id"] == TEST_MEMBER_ID, "Q-Ball ID should match"


class TestUpdateRolesEndpoint:
    """Tests for POST /api/discord/member/{id}/roles endpoint"""
    
    def test_update_roles_endpoint_exists(self, api_client):
        """Test that update roles endpoint exists and accepts POST"""
        # Get current roles first
        get_response = api_client.get(f"{BASE_URL}/api/discord/member/{TEST_MEMBER_ID}/roles")
        assert get_response.status_code == 200
        
        current_roles = get_response.json().get("roles", [])
        current_role_ids = [r["id"] for r in current_roles]
        
        # Try to update with same roles (no actual change)
        response = api_client.post(
            f"{BASE_URL}/api/discord/member/{TEST_MEMBER_ID}/roles",
            json={"role_ids": current_role_ids}
        )
        
        # Should succeed (even if no changes made)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data, "Response should have 'success' field"
        assert data["success"] == True, "Update should succeed"
    
    def test_update_roles_nonexistent_member(self, api_client):
        """Test updating roles for non-existent member returns 404"""
        response = api_client.post(
            f"{BASE_URL}/api/discord/member/nonexistent-id-12345/roles",
            json={"role_ids": []}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_update_roles_without_auth(self):
        """Test that update roles endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/discord/member/{TEST_MEMBER_ID}/roles",
            json={"role_ids": []}
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"


class TestUpdateNicknameEndpoint:
    """Tests for POST /api/discord/member/{id}/nickname endpoint"""
    
    def test_update_nickname_endpoint_exists(self, api_client):
        """Test that update nickname endpoint exists"""
        # Get current nickname first
        get_response = api_client.get(f"{BASE_URL}/api/discord/member/{TEST_MEMBER_ID}/roles")
        assert get_response.status_code == 200
        
        current_nickname = get_response.json().get("nickname", "")
        
        # Try to update with same nickname (no actual change)
        response = api_client.post(
            f"{BASE_URL}/api/discord/member/{TEST_MEMBER_ID}/nickname",
            json={"nickname": current_nickname}
        )
        
        # Should succeed
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data, "Response should have 'success' field"
    
    def test_update_nickname_nonexistent_member(self, api_client):
        """Test updating nickname for non-existent member returns 404"""
        response = api_client.post(
            f"{BASE_URL}/api/discord/member/nonexistent-id-12345/nickname",
            json={"nickname": "Test"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_update_nickname_without_auth(self):
        """Test that update nickname endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/discord/member/{TEST_MEMBER_ID}/nickname",
            json={"nickname": "Test"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
