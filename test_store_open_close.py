#!/usr/bin/env python3
"""
Test script for Store Open/Close feature
"""
import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class StoreOpenCloseAPITester:
    def __init__(self, base_url="https://memberportal-12.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

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
        
        print(f"   ❌ Login failed for {username}")
        return False, {}

    def test_store_open_close_feature(self):
        """Test Store Open/Close feature - NEW FEATURE"""
        print(f"\n🏪 Testing Store Open/Close Feature...")
        
        # Test 1: Public Store Settings (No Auth Required)
        print(f"\n   📋 Step 1: Testing Public Store Settings (No Auth Required)...")
        
        # Temporarily remove token for public endpoint test
        original_token = self.token
        self.token = None
        
        success, public_settings = self.run_test(
            "Get Public Store Settings",
            "GET",
            "store/settings/public",
            200
        )
        
        # Restore token
        self.token = original_token
        
        if success:
            # Verify required fields are present
            required_fields = ['supporter_store_open', 'member_store_open', 'supporter_store_message', 'member_store_message']
            missing_fields = [field for field in required_fields if field not in public_settings]
            
            if not missing_fields:
                self.log_test("Public Settings - Required Fields", True, f"All required fields present: {required_fields}")
                print(f"   Current settings: supporter_store_open={public_settings.get('supporter_store_open')}, member_store_open={public_settings.get('member_store_open')}")
            else:
                self.log_test("Public Settings - Required Fields", False, f"Missing fields: {missing_fields}")
        
        # Test 2: Authenticated Store Settings with admin (National Prez)
        print(f"\n   🔑 Step 2: Testing Authenticated Store Settings (admin)...")
        
        success, auth_settings = self.run_test(
            "Get Authenticated Store Settings (admin)",
            "GET",
            "store/settings",
            200
        )
        
        if success:
            # Verify can_bypass flag is present and true for admin
            if 'can_bypass' in auth_settings:
                if auth_settings['can_bypass'] == True:
                    self.log_test("Admin Can Bypass - Flag Present", True, "can_bypass=true for National Prez")
                else:
                    self.log_test("Admin Can Bypass - Flag Present", False, f"can_bypass={auth_settings['can_bypass']} (expected true)")
            else:
                self.log_test("Admin Can Bypass - Flag Present", False, "can_bypass field missing")
            
            print(f"   Admin settings: can_bypass={auth_settings.get('can_bypass')}")
        
        # Test 3: Create adadmin user (AD VP) for testing non-bypass user
        print(f"\n   👤 Step 3: Creating adadmin user (AD VP)...")
        
        adadmin_user = {
            "username": "adadmin",
            "email": "adadmin@test.com",
            "password": "test",
            "role": "admin",
            "chapter": "AD",
            "title": "VP"
        }
        
        success, created_adadmin = self.run_test(
            "Create adadmin User (AD VP)",
            "POST",
            "users",
            201,
            data=adadmin_user
        )
        
        adadmin_id = None
        if success and 'id' in created_adadmin:
            adadmin_id = created_adadmin['id']
            print(f"   Created adadmin ID: {adadmin_id}")
        
        # Test 4: Login as adadmin and test can_bypass=false
        print(f"\n   🔒 Step 4: Testing adadmin permissions...")
        
        original_admin_token = self.token
        success, adadmin_login = self.run_test(
            "Login as adadmin (AD VP)",
            "POST",
            "auth/login",
            200,
            data={"username": "adadmin", "password": "test"}
        )
        
        if success and 'token' in adadmin_login:
            self.token = adadmin_login['token']
            
            # Test authenticated settings with adadmin
            success, adadmin_settings = self.run_test(
                "Get Authenticated Store Settings (adadmin)",
                "GET",
                "store/settings",
                200
            )
            
            if success:
                # Verify can_bypass flag is false for adadmin
                if 'can_bypass' in adadmin_settings:
                    if adadmin_settings['can_bypass'] == False:
                        self.log_test("adadmin Cannot Bypass - Flag Present", True, "can_bypass=false for AD VP")
                    else:
                        self.log_test("adadmin Cannot Bypass - Flag Present", False, f"can_bypass={adadmin_settings['can_bypass']} (expected false)")
                else:
                    self.log_test("adadmin Cannot Bypass - Flag Present", False, "can_bypass field missing")
                
                print(f"   adadmin settings: can_bypass={adadmin_settings.get('can_bypass')}")
            
            # Test 5: Try to update settings as adadmin (should fail with 403)
            success, update_response = self.run_test(
                "Update Settings as adadmin (Should Fail)",
                "PUT",
                "store/settings?member_store_open=false",
                403
            )
        
        # Restore admin token
        self.token = original_admin_token
        
        # Test 6: Update store settings as admin (should succeed)
        print(f"\n   ⚙️  Step 5: Testing store settings updates as admin...")
        
        # First, close member store
        success, close_response = self.run_test(
            "Close Member Store (admin)",
            "PUT",
            "store/settings?member_store_open=false",
            200
        )
        
        if success:
            if 'message' in close_response and 'settings' in close_response:
                self.log_test("Close Member Store - Response Format", True, "Response contains message and settings")
                
                # Verify the setting was updated
                settings = close_response['settings']
                if settings.get('member_store_open') == False:
                    self.log_test("Close Member Store - Setting Updated", True, "member_store_open=false")
                    print(f"   Member store closed successfully")
                else:
                    self.log_test("Close Member Store - Setting Updated", False, f"member_store_open={settings.get('member_store_open')}")
            else:
                self.log_test("Close Member Store - Response Format", False, "Missing message or settings in response")
        
        # Test 7: Verify public endpoint reflects the change
        print(f"\n   🌐 Step 6: Verifying public endpoint reflects changes...")
        
        # Remove token for public endpoint
        self.token = None
        
        success, updated_public_settings = self.run_test(
            "Verify Public Settings After Update",
            "GET",
            "store/settings/public",
            200
        )
        
        # Restore token
        self.token = original_admin_token
        
        if success:
            if updated_public_settings.get('member_store_open') == False:
                self.log_test("Public Settings Reflect Update", True, "member_store_open=false in public endpoint")
                print(f"   Public endpoint correctly shows member store closed")
            else:
                self.log_test("Public Settings Reflect Update", False, f"member_store_open={updated_public_settings.get('member_store_open')} (expected false)")
        
        # Test 8: Close supporter store as well
        success, close_supporter_response = self.run_test(
            "Close Supporter Store (admin)",
            "PUT",
            "store/settings?supporter_store_open=false",
            200
        )
        
        if success:
            print(f"   Supporter store closed successfully")
        
        # Test 9: Reset stores back to open (cleanup)
        print(f"\n   🔄 Step 7: Resetting stores to open state...")
        
        success, reset_response = self.run_test(
            "Reset Stores to Open (cleanup)",
            "PUT",
            "store/settings?supporter_store_open=true&member_store_open=true",
            200
        )
        
        if success:
            print(f"   Both stores reset to open")
        
        # Test 10: Verify final state
        # Remove token for public endpoint
        self.token = None
        
        success, final_public_settings = self.run_test(
            "Verify Final Public Settings",
            "GET",
            "store/settings/public",
            200
        )
        
        # Restore token
        self.token = original_admin_token
        
        if success:
            if (final_public_settings.get('supporter_store_open') == True and 
                final_public_settings.get('member_store_open') == True):
                self.log_test("Final State - Both Stores Open", True, "Both stores reset to open")
                print(f"   Final state verified: both stores open")
            else:
                self.log_test("Final State - Both Stores Open", False, f"supporter_store_open={final_public_settings.get('supporter_store_open')}, member_store_open={final_public_settings.get('member_store_open')}")
        
        # Clean up adadmin user
        if adadmin_id:
            success, delete_response = self.run_test(
                "Delete adadmin User (cleanup)",
                "DELETE",
                f"users/{adadmin_id}",
                200
            )
            if success:
                print(f"   Cleaned up adadmin user")
        
        print(f"\n   🏪 Store Open/Close feature testing completed")
        return True

    def run_tests(self):
        """Run all Store Open/Close tests"""
        print("🚀 Starting Store Open/Close Feature Tests...")
        print(f"   Base URL: {self.base_url}")
        print(f"   Testing started at: {datetime.now()}")
        
        # Test authentication first
        success, response = self.test_login()
        if not success:
            print("❌ Authentication failed - cannot continue tests")
            return
        
        # Run Store Open/Close feature tests
        self.test_store_open_close_feature()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed - check details above")
            
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = StoreOpenCloseAPITester()
    tester.run_tests()