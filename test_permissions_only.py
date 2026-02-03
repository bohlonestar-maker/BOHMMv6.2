#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PermissionTester:
    def __init__(self, base_url="https://bohnexus.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, verify=False)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, verify=False)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, verify=False)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, verify=False)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected: {expected_status})"
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'No error details')}"
                except:
                    details += f" - Response: {response.text[:100]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_login(self, username="admin", password="admin123"):
        """Test login and get token"""
        print(f"\n🔐 Testing Authentication...")
        
        success, response = self.run_test(
            f"Login as {username}",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            print(f"   ✅ Successful login with {username}")
            print(f"   Token obtained: {self.token[:20]}...")
            return True, response
        
        print("   ❌ Login failed")
        return False, {}

    def test_role_based_permissions(self):
        """Test role-based permission system for member management application"""
        print(f"\n🔐 Testing Role-Based Permission System...")
        
        # Test with admin credentials (National chapter)
        success, login_response = self.test_login("admin", "admin123")
        if not success:
            print("❌ Cannot continue without admin authentication")
            return
        
        # Test 1: Auth Verify - Check chapter information
        success, verify_response = self.run_test(
            "Auth Verify - Returns Chapter Info",
            "GET",
            "auth/verify",
            200
        )
        
        if success:
            expected_fields = ['username', 'role', 'chapter', 'permissions']
            missing_fields = [field for field in expected_fields if field not in verify_response]
            
            if not missing_fields:
                self.log_test("Auth Verify - Required Fields Present", True, f"All fields present: {expected_fields}")
                
                # Check if user is National Admin
                if verify_response.get('role') == 'admin' and verify_response.get('chapter') == 'National':
                    self.log_test("Auth Verify - National Admin Detected", True, f"User: {verify_response.get('username')} (admin - National)")
                else:
                    self.log_test("Auth Verify - National Admin Detected", False, f"Role: {verify_response.get('role')}, Chapter: {verify_response.get('chapter')}")
            else:
                self.log_test("Auth Verify - Required Fields Present", False, f"Missing fields: {missing_fields}")
        
        # Test 2: Member Permission Tests
        print(f"\n   👥 Testing Member Permissions...")
        
        # Create test member for permission testing
        import time
        timestamp = str(int(time.time()))
        test_member = {
            "chapter": "AD",
            "title": "Member",
            "handle": f"PermissionTestRider{timestamp}",
            "name": "Permission Test Member",
            "email": f"permtest{timestamp}@example.com",
            "phone": "555-0199",
            "address": "199 Permission St"
        }
        
        success, created_member = self.run_test(
            "Create Test Member for Permissions",
            "POST",
            "members",
            201,
            data=test_member
        )
        
        member_id = None
        if success and 'id' in created_member:
            member_id = created_member['id']
        
        # Test GET /api/members - Should return members with can_edit flag
        success, members_list = self.run_test(
            "Get Members - Check can_edit Flag",
            "GET",
            "members",
            200
        )
        
        if success and isinstance(members_list, list) and len(members_list) > 0:
            # Check if can_edit flag is present
            member_with_flag = None
            for member in members_list:
                if 'can_edit' in member:
                    member_with_flag = member
                    break
            
            if member_with_flag:
                self.log_test("Members List - can_edit Flag Present", True, f"can_edit flag found: {member_with_flag.get('can_edit')}")
                
                # National Admin should be able to edit any member
                if member_with_flag.get('can_edit') == True:
                    self.log_test("National Admin - Can Edit Any Member", True, "National Admin has edit permissions")
                else:
                    self.log_test("National Admin - Can Edit Any Member", False, f"can_edit is {member_with_flag.get('can_edit')}")
            else:
                self.log_test("Members List - can_edit Flag Present", False, "No can_edit flag found in member objects")
        
        # Test PUT /api/members/{id} - National Admin should be able to edit
        if member_id:
            update_data = {"name": "Updated Permission Test Member"}
            success, updated_member = self.run_test(
                "National Admin - Edit Member",
                "PUT",
                f"members/{member_id}",
                200,
                data=update_data
            )
        
        # Test 3: Prospects Permission Tests (National/HA Admin only)
        print(f"\n   🏍️  Testing Prospects Permissions...")
        
        # Test GET /api/prospects - Should work for National Admin
        success, prospects_list = self.run_test(
            "National Admin - Get Prospects",
            "GET",
            "prospects",
            200
        )
        
        # Test POST /api/prospects - Should work for National Admin
        import time
        timestamp = str(int(time.time()))
        test_prospect = {
            "handle": f"TestProspect{timestamp}",
            "name": "Test Prospect Name",
            "email": f"testprospect{timestamp}@test.com",
            "phone": "555-0123",
            "address": "123 Test St"
        }
        
        success, created_prospect = self.run_test(
            "National Admin - Create Prospect",
            "POST",
            "prospects",
            201,
            data=test_prospect
        )
        
        prospect_id = None
        if success and 'id' in created_prospect:
            prospect_id = created_prospect['id']
        
        # Test PUT /api/prospects/{id} - Should work for National Admin
        if prospect_id:
            update_prospect_data = {"name": "Updated Test Prospect"}
            success, updated_prospect = self.run_test(
                "National Admin - Edit Prospect",
                "PUT",
                f"prospects/{prospect_id}",
                200,
                data=update_prospect_data
            )
        
        # Test DELETE /api/prospects/{id} - Should work for National Admin
        if prospect_id:
            success, deleted_prospect = self.run_test(
                "National Admin - Archive Prospect",
                "DELETE",
                f"prospects/{prospect_id}?reason=test",
                200
            )
        
        # Test 4: Wall of Honor Permission Tests (National Admin only)
        print(f"\n   🏛️  Testing Wall of Honor Permissions...")
        
        # Test GET /api/fallen - Should work for any authenticated user
        success, fallen_list = self.run_test(
            "Get Fallen Members List",
            "GET",
            "fallen",
            200
        )
        
        # Test POST /api/fallen - Should work for National Admin
        import time
        timestamp = str(int(time.time()))
        test_fallen = {
            "name": "Test Memorial",
            "handle": f"TestHandle{timestamp}",
            "chapter": "National",
            "tribute": "In memory"
        }
        
        success, created_fallen = self.run_test(
            "National Admin - Create Fallen Member",
            "POST",
            "fallen",
            201,
            data=test_fallen
        )
        
        fallen_id = None
        if success and 'id' in created_fallen:
            fallen_id = created_fallen['id']
        
        # Test PUT /api/fallen/{id} - Should work for National Admin
        if fallen_id:
            update_fallen_data = {"tribute": "Updated memorial"}
            success, updated_fallen = self.run_test(
                "National Admin - Edit Fallen Member",
                "PUT",
                f"fallen/{fallen_id}",
                200,
                data=update_fallen_data
            )
        
        # Test DELETE /api/fallen/{id} - Should work for National Admin
        if fallen_id:
            success, deleted_fallen = self.run_test(
                "National Admin - Delete Fallen Member",
                "DELETE",
                f"fallen/{fallen_id}",
                200
            )
        
        # Clean up test data
        if member_id:
            success, response = self.run_test(
                "Cleanup - Delete Test Member",
                "DELETE",
                f"members/{member_id}?reason=test_cleanup",
                200
            )
        
        print(f"   🔐 Role-based permission testing completed")
        return True

    def run_tests(self):
        """Run permission tests"""
        print("🚀 Starting Role-Based Permission Tests...")
        print(f"Base URL: {self.base_url}")
        
        self.test_role_based_permissions()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed. Check the details above.")

if __name__ == "__main__":
    tester = PermissionTester()
    tester.run_tests()