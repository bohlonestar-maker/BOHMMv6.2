#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UserChapterTitleTester:
    def __init__(self, base_url="https://memberportal-12.preview.emergentagent.com/api"):
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

    def test_login(self):
        """Test login with testadmin credentials"""
        print(f"\n🔐 Testing Authentication...")
        
        success, response = self.run_test(
            "Login as testadmin",
            "POST",
            "auth/login",
            200,
            data={"username": "testadmin", "password": "testpass123"}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            print(f"   ✅ Successful login with testadmin")
            print(f"   Token obtained: {self.token[:20]}...")
            return True, response
        
        print("   ❌ Login failed")
        return False, {}

    def test_user_chapter_title_assignment(self):
        """Test user chapter and title assignment functionality"""
        print(f"\n👥 Testing User Chapter and Title Assignment...")
        
        # Test 1: Get Current Users and verify chapter/title fields
        success, users = self.run_test(
            "Get Current Users",
            "GET",
            "users",
            200
        )
        
        if success and isinstance(users, list):
            # Verify response includes chapter and title fields (may be null)
            sample_user = users[0] if users else None
            if sample_user:
                has_chapter_field = 'chapter' in sample_user
                has_title_field = 'title' in sample_user
                
                if has_chapter_field and has_title_field:
                    self.log_test("Users Response - Chapter and Title Fields Present", True, "Both chapter and title fields found in user response")
                else:
                    missing_fields = []
                    if not has_chapter_field:
                        missing_fields.append('chapter')
                    if not has_title_field:
                        missing_fields.append('title')
                    self.log_test("Users Response - Chapter and Title Fields Present", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Users Response - Chapter and Title Fields Present", False, "No users found to verify fields")
        
        # Find testchat and testmember users
        testchat_user = None
        testmember_user = None
        
        if success and isinstance(users, list):
            for user in users:
                if user.get('username') == 'testchat':
                    testchat_user = user
                elif user.get('username') == 'testmember':
                    testmember_user = user
        
        # Create test users if they don't exist
        if not testchat_user:
            testchat_data = {
                "username": "testchat",
                "password": "testpass123",
                "role": "member"
            }
            
            success, created_testchat = self.run_test(
                "Create testchat User",
                "POST",
                "users",
                201,
                data=testchat_data
            )
            
            if success:
                testchat_user = created_testchat
                print(f"   Created testchat user ID: {testchat_user.get('id')}")
        
        if not testmember_user:
            testmember_data = {
                "username": "testmember",
                "password": "testpass123",
                "role": "member"
            }
            
            success, created_testmember = self.run_test(
                "Create testmember User",
                "POST",
                "users",
                201,
                data=testmember_data
            )
            
            if success:
                testmember_user = created_testmember
                print(f"   Created testmember user ID: {testmember_user.get('id')}")
        
        # Test 2: Update testchat user with chapter "HA" and title "Member"
        if testchat_user and 'id' in testchat_user:
            testchat_id = testchat_user['id']
            
            update_testchat_data = {
                "chapter": "HA",
                "title": "Member"
            }
            
            success, updated_testchat = self.run_test(
                "Update testchat User with Chapter and Title",
                "PUT",
                f"users/{testchat_id}",
                200,
                data=update_testchat_data
            )
            
            if success:
                print(f"   Update response: {json.dumps(updated_testchat, indent=2)}")
                # Verify the update response contains the new values
                if (updated_testchat.get('chapter') == 'HA' and 
                    updated_testchat.get('title') == 'Member'):
                    self.log_test("Update testchat - Chapter and Title Set", True, f"Chapter: {updated_testchat.get('chapter')}, Title: {updated_testchat.get('title')}")
                else:
                    self.log_test("Update testchat - Chapter and Title Set", False, f"Expected HA/Member, got {updated_testchat.get('chapter')}/{updated_testchat.get('title')}")
        else:
            self.log_test("Update testchat User", False, "testchat user not found or missing ID")
        
        # Test 3: Verify testchat update persisted by getting users again
        success, users_after_update = self.run_test(
            "Get Users After testchat Update",
            "GET",
            "users",
            200
        )
        
        if success and isinstance(users_after_update, list):
            updated_testchat_user = None
            for user in users_after_update:
                if user.get('username') == 'testchat':
                    updated_testchat_user = user
                    break
            
            if updated_testchat_user:
                if (updated_testchat_user.get('chapter') == 'HA' and 
                    updated_testchat_user.get('title') == 'Member'):
                    self.log_test("Verify testchat Update Persisted", True, f"testchat has chapter: {updated_testchat_user.get('chapter')}, title: {updated_testchat_user.get('title')}")
                else:
                    self.log_test("Verify testchat Update Persisted", False, f"Expected HA/Member, got {updated_testchat_user.get('chapter')}/{updated_testchat_user.get('title')}")
            else:
                self.log_test("Verify testchat Update Persisted", False, "testchat user not found in updated user list")
        
        # Test 4: Update testmember user with chapter "National" and title "VP"
        if testmember_user and 'id' in testmember_user:
            testmember_id = testmember_user['id']
            
            update_testmember_data = {
                "chapter": "National",
                "title": "VP"
            }
            
            success, updated_testmember = self.run_test(
                "Update testmember User with Chapter and Title",
                "PUT",
                f"users/{testmember_id}",
                200,
                data=update_testmember_data
            )
            
            if success:
                print(f"   Update response: {json.dumps(updated_testmember, indent=2)}")
                # Verify the update response contains the new values
                if (updated_testmember.get('chapter') == 'National' and 
                    updated_testmember.get('title') == 'VP'):
                    self.log_test("Update testmember - Chapter and Title Set", True, f"Chapter: {updated_testmember.get('chapter')}, Title: {updated_testmember.get('title')}")
                else:
                    self.log_test("Update testmember - Chapter and Title Set", False, f"Expected National/VP, got {updated_testmember.get('chapter')}/{updated_testmember.get('title')}")
        else:
            self.log_test("Update testmember User", False, "testmember user not found or missing ID")
        
        # Test 5: Verify multiple users have correct chapter/title assignments
        success, final_users = self.run_test(
            "Get Users - Final Verification",
            "GET",
            "users",
            200
        )
        
        if success and isinstance(final_users, list):
            final_testchat = None
            final_testmember = None
            
            for user in final_users:
                if user.get('username') == 'testchat':
                    final_testchat = user
                elif user.get('username') == 'testmember':
                    final_testmember = user
            
            # Verify testchat has HA/Member
            if final_testchat:
                if (final_testchat.get('chapter') == 'HA' and 
                    final_testchat.get('title') == 'Member'):
                    self.log_test("Final Verification - testchat HA/Member", True, f"testchat correctly has chapter: {final_testchat.get('chapter')}, title: {final_testchat.get('title')}")
                else:
                    self.log_test("Final Verification - testchat HA/Member", False, f"Expected HA/Member, got {final_testchat.get('chapter')}/{final_testchat.get('title')}")
            else:
                self.log_test("Final Verification - testchat Found", False, "testchat user not found in final verification")
            
            # Verify testmember has National/VP
            if final_testmember:
                if (final_testmember.get('chapter') == 'National' and 
                    final_testmember.get('title') == 'VP'):
                    self.log_test("Final Verification - testmember National/VP", True, f"testmember correctly has chapter: {final_testmember.get('chapter')}, title: {final_testmember.get('title')}")
                else:
                    self.log_test("Final Verification - testmember National/VP", False, f"Expected National/VP, got {final_testmember.get('chapter')}/{final_testmember.get('title')}")
            else:
                self.log_test("Final Verification - testmember Found", False, "testmember user not found in final verification")
        
        print(f"   👥 User chapter and title assignment testing completed")
        return testchat_user, testmember_user

    def run_tests(self):
        """Run all tests"""
        print("🚀 Starting User Chapter and Title Assignment Tests...")
        print(f"   Base URL: {self.base_url}")
        
        # Authentication
        success, response = self.test_login()
        if not success:
            print("❌ Authentication failed - cannot continue tests")
            return
        
        # Run the specific test
        self.test_user_chapter_title_assignment()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed - check details above")
            
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = UserChapterTitleTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)