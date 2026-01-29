import requests
import sys
import json
from datetime import datetime
import urllib3
import uuid

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PrivacyFeatureTester:
    def __init__(self, base_url="https://attendance-mgr-4.preview.emergentagent.com/api"):
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

    def test_privacy_feature(self):
        """Test privacy feature - National Chapter admin only access"""
        print(f"\n🔒 Testing Privacy Feature - National Chapter Admin Access...")
        
        # Generate unique identifiers for this test run
        test_id = str(uuid.uuid4())[:8]
        
        # Step 1: Login with testadmin/testpass123
        success, admin_login = self.run_test(
            "Login as testadmin",
            "POST",
            "auth/login",
            200,
            data={"username": "testadmin", "password": "testpass123"}
        )
        
        if not success:
            print("❌ Failed to login as testadmin - cannot continue privacy tests")
            return
        
        self.token = admin_login['token']
        
        # Step 2: Create test member with privacy flags
        test_member = {
            "chapter": "AD",
            "title": "Member",
            "handle": f"PrivacyTest_{test_id}",
            "name": "Privacy Test Member",
            "email": f"privacy_{test_id}@test.com",
            "phone": "555-1111-2222",
            "address": "123 Private Street",
            "phone_private": True,
            "address_private": True
        }
        
        success, created_member = self.run_test(
            "Create Member with Privacy Flags",
            "POST",
            "members",
            201,
            data=test_member
        )
        
        member_id = None
        if success and 'id' in created_member:
            member_id = created_member['id']
            print(f"   Created privacy test member ID: {member_id}")
        else:
            print("❌ Failed to create test member - cannot continue privacy tests")
            return
        
        # Step 3: Check if testadmin is National Chapter admin
        success, auth_verify = self.run_test(
            "Verify testadmin details",
            "GET",
            "auth/verify",
            200
        )
        
        is_national_admin = False
        if success:
            user_role = auth_verify.get('role')
            # Need to check user's chapter - get user details
            success, users = self.run_test(
                "Get users to check testadmin chapter",
                "GET",
                "users",
                200
            )
            
            if success:
                testadmin_user = None
                for user in users:
                    if user.get('username') == 'testadmin':
                        testadmin_user = user
                        break
                
                if testadmin_user:
                    user_chapter = testadmin_user.get('chapter')
                    is_national_admin = user_role == 'admin' and user_chapter == 'National'
                    print(f"   testadmin role: {user_role}, chapter: {user_chapter}, is_national_admin: {is_national_admin}")
        
        # Step 4: Test access based on National admin status
        if is_national_admin:
            # Test 1: National admin should see actual values
            success, members = self.run_test(
                "National Admin - Get Members (should see actual values)",
                "GET",
                "members",
                200
            )
            
            if success:
                privacy_member = None
                for member in members:
                    if member.get('id') == member_id:
                        privacy_member = member
                        break
                
                if privacy_member:
                    actual_phone = privacy_member.get('phone')
                    actual_address = privacy_member.get('address')
                    
                    if actual_phone == "555-1111-2222" and actual_address == "123 Private Street":
                        self.log_test("National Admin - Can See Private Contact Info", True, f"Phone: {actual_phone}, Address: {actual_address}")
                    else:
                        self.log_test("National Admin - Can See Private Contact Info", False, f"Expected actual values, got Phone: {actual_phone}, Address: {actual_address}")
                else:
                    self.log_test("National Admin - Find Privacy Test Member", False, "Privacy test member not found")
        else:
            # Test 2: Non-National admin should see 'Private'
            success, members = self.run_test(
                "Non-National Admin - Get Members (should see 'Private')",
                "GET",
                "members",
                200
            )
            
            if success:
                privacy_member = None
                for member in members:
                    if member.get('id') == member_id:
                        privacy_member = member
                        break
                
                if privacy_member:
                    actual_phone = privacy_member.get('phone')
                    actual_address = privacy_member.get('address')
                    
                    if actual_phone == "Private" and actual_address == "Private":
                        self.log_test("Non-National Admin - Sees Private Text", True, f"Phone: {actual_phone}, Address: {actual_address}")
                    else:
                        self.log_test("Non-National Admin - Sees Private Text", False, f"Expected 'Private', got Phone: {actual_phone}, Address: {actual_address}")
                else:
                    self.log_test("Non-National Admin - Find Privacy Test Member", False, "Privacy test member not found")
        
        # Step 5: Create National Chapter admin for testing
        national_admin = {
            "username": f"nationaladmin_{test_id}",
            "email": f"nationaladmin_{test_id}@test.com", 
            "password": "testpass123",
            "role": "admin",
            "chapter": "National",
            "title": "Prez"
        }
        
        success, created_national_admin = self.run_test(
            "Create National Chapter Admin",
            "POST",
            "users",
            201,
            data=national_admin
        )
        
        national_admin_id = None
        if success and 'id' in created_national_admin:
            national_admin_id = created_national_admin['id']
        
        # Step 6: Test National admin access
        if national_admin_id:
            # Login as National admin
            success, national_login = self.run_test(
                "Login as National Admin",
                "POST",
                "auth/login",
                200,
                data={"username": f"nationaladmin_{test_id}", "password": "testpass123"}
            )
            
            if success and 'token' in national_login:
                original_token = self.token
                self.token = national_login['token']
                
                # Test National admin can see private data
                success, members = self.run_test(
                    "National Admin - Get Members (should see actual values)",
                    "GET",
                    "members",
                    200
                )
                
                if success:
                    privacy_member = None
                    for member in members:
                        if member.get('id') == member_id:
                            privacy_member = member
                            break
                    
                    if privacy_member:
                        actual_phone = privacy_member.get('phone')
                        actual_address = privacy_member.get('address')
                        
                        if actual_phone == "555-1111-2222" and actual_address == "123 Private Street":
                            self.log_test("National Admin - Can See Private Contact Info", True, f"Phone: {actual_phone}, Address: {actual_address}")
                        else:
                            self.log_test("National Admin - Can See Private Contact Info", False, f"Expected actual values, got Phone: {actual_phone}, Address: {actual_address}")
                
                # Test single member endpoint
                if member_id:
                    success, single_member = self.run_test(
                        "National Admin - Get Single Member (should see actual values)",
                        "GET",
                        f"members/{member_id}",
                        200
                    )
                    
                    if success:
                        actual_phone = single_member.get('phone')
                        actual_address = single_member.get('address')
                        
                        if actual_phone == "555-1111-2222" and actual_address == "123 Private Street":
                            self.log_test("National Admin - Single Member Private Contact Info", True, f"Phone: {actual_phone}, Address: {actual_address}")
                        else:
                            self.log_test("National Admin - Single Member Private Contact Info", False, f"Expected actual values, got Phone: {actual_phone}, Address: {actual_address}")
                
                # Restore original token
                self.token = original_token
        
        # Step 7: Create regular member for testing
        regular_member = {
            "username": f"regularmember_{test_id}",
            "email": f"regularmember_{test_id}@test.com",
            "password": "testpass123", 
            "role": "member",
            "chapter": "AD",
            "title": "Member"
        }
        
        success, created_regular = self.run_test(
            "Create Regular Member User",
            "POST",
            "users",
            201,
            data=regular_member
        )
        
        regular_member_id = None
        if success and 'id' in created_regular:
            regular_member_id = created_regular['id']
        
        # Step 8: Test regular member access
        if regular_member_id:
            # Login as regular member
            success, regular_login = self.run_test(
                "Login as Regular Member",
                "POST", 
                "auth/login",
                200,
                data={"username": f"regularmember_{test_id}", "password": "testpass123"}
            )
            
            if success and 'token' in regular_login:
                original_token = self.token
                self.token = regular_login['token']
                
                # Test regular member sees 'Private'
                success, members = self.run_test(
                    "Regular Member - Get Members (should see 'Private')",
                    "GET",
                    "members", 
                    200
                )
                
                if success:
                    privacy_member = None
                    for member in members:
                        if member.get('id') == member_id:
                            privacy_member = member
                            break
                    
                    if privacy_member:
                        actual_phone = privacy_member.get('phone')
                        actual_address = privacy_member.get('address')
                        
                        if actual_phone == "Private" and actual_address == "Private":
                            self.log_test("Regular Member - Sees Private Text", True, f"Phone: {actual_phone}, Address: {actual_address}")
                        else:
                            self.log_test("Regular Member - Sees Private Text", False, f"Expected 'Private', got Phone: {actual_phone}, Address: {actual_address}")
                
                # Restore original token
                self.token = original_token
        
        # Step 9: Test member without privacy flags
        non_private_member = {
            "chapter": "HA",
            "title": "Member", 
            "handle": f"NonPrivateTest_{test_id}",
            "name": "Non Private Member",
            "email": f"nonprivate_{test_id}@test.com",
            "phone": "555-3333-4444",
            "address": "456 Public Street",
            "phone_private": False,
            "address_private": False
        }
        
        success, created_non_private = self.run_test(
            "Create Member Without Privacy Flags",
            "POST",
            "members",
            201,
            data=non_private_member
        )
        
        non_private_id = None
        if success and 'id' in created_non_private:
            non_private_id = created_non_private['id']
            
            # Test that all users can see non-private data
            if regular_member_id:
                # Login as regular member again
                success, regular_login = self.run_test(
                    "Login as Regular Member (for non-private test)",
                    "POST",
                    "auth/login", 
                    200,
                    data={"username": f"regularmember_{test_id}", "password": "testpass123"}
                )
                
                if success and 'token' in regular_login:
                    original_token = self.token
                    self.token = regular_login['token']
                    
                    success, members = self.run_test(
                        "Regular Member - Get Non-Private Member",
                        "GET",
                        "members",
                        200
                    )
                    
                    if success:
                        non_private_found = None
                        for member in members:
                            if member.get('id') == non_private_id:
                                non_private_found = member
                                break
                        
                        if non_private_found:
                            actual_phone = non_private_found.get('phone')
                            actual_address = non_private_found.get('address')
                            
                            if actual_phone == "555-3333-4444" and actual_address == "456 Public Street":
                                self.log_test("Regular Member - Can See Non-Private Contact Info", True, f"Phone: {actual_phone}, Address: {actual_address}")
                            else:
                                self.log_test("Regular Member - Can See Non-Private Contact Info", False, f"Expected actual values, got Phone: {actual_phone}, Address: {actual_address}")
                    
                    # Restore original token
                    self.token = original_token
        
        # Cleanup
        if member_id:
            self.run_test("Delete Privacy Test Member", "DELETE", f"members/{member_id}?reason=test_cleanup", 200)
        if non_private_id:
            self.run_test("Delete Non-Private Test Member", "DELETE", f"members/{non_private_id}?reason=test_cleanup", 200)
        if national_admin_id:
            self.run_test("Delete National Admin User", "DELETE", f"users/{national_admin_id}", 200)
        if regular_member_id:
            self.run_test("Delete Regular Member User", "DELETE", f"users/{regular_member_id}", 200)
        
        print(f"   🔒 Privacy feature testing completed")

    def run_tests(self):
        """Run privacy feature tests"""
        print("🚀 Starting Privacy Feature Tests...")
        print(f"   Base URL: {self.base_url}")
        
        self.test_privacy_feature()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All privacy tests passed!")
        else:
            print("⚠️  Some privacy tests failed - check details above")
            
            # Print failed tests
            failed_tests = [test for test in self.test_results if not test['success']]
            if failed_tests:
                print(f"\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   • {test['test']}: {test['details']}")

if __name__ == "__main__":
    tester = PrivacyFeatureTester()
    tester.run_tests()