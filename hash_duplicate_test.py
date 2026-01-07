import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HashDuplicatePreventionTester:
    def __init__(self, base_url="https://memberportal-12.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_members = []  # Track created members for cleanup

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

    def test_login(self):
        """Test login and get token"""
        print(f"\n🔐 Testing Authentication...")
        
        # Try multiple credential combinations
        credentials_to_try = [
            ("testadmin", "testpass123"),
            ("admin", "admin123"),
            ("Lonestar", "password"),
        ]
        
        for user, pwd in credentials_to_try:
            success, response = self.run_test(
                f"Login attempt: {user}",
                "POST",
                "auth/login",
                200,
                data={"username": user, "password": pwd}
            )
            
            if success and 'token' in response:
                self.token = response['token']
                print(f"   ✅ Successful login with {user}")
                return True, response
        
        print("   ❌ All login attempts failed")
        return False, {}

    def cleanup_members(self):
        """Clean up all created test members"""
        print(f"\n🧹 Cleaning up {len(self.created_members)} test members...")
        for member_id in self.created_members:
            success, response = self.run_test(
                f"Cleanup Member {member_id[:8]}...",
                "DELETE",
                f"members/{member_id}",
                200
            )

    def test_hash_based_duplicate_prevention(self):
        """Test hash-based duplicate prevention with case-insensitive email detection"""
        print(f"\n🔒 Testing Hash-Based Duplicate Prevention...")
        
        # Test 1: Create first test member
        first_member = {
            "chapter": "National",
            "title": "Prez",
            "handle": "HashTest1",
            "name": "Hash Test Member 1",
            "email": "hashtest@example.com",
            "phone": "555-0001",
            "address": "123 Hash Test Street"
        }
        
        success, created_member = self.run_test(
            "Create First Test Member (HashTest1)",
            "POST",
            "members",
            201,
            data=first_member
        )
        
        first_member_id = None
        if success and 'id' in created_member:
            first_member_id = created_member['id']
            self.created_members.append(first_member_id)
            print(f"   Created first member ID: {first_member_id}")
        else:
            print("❌ Failed to create first member - cannot continue duplicate tests")
            return False
        
        # Test 2: Try to create duplicate with same email (should FAIL with 400)
        duplicate_email_member = {
            "chapter": "AD",
            "title": "VP",
            "handle": "HashTest2",
            "name": "Hash Test Member 2",
            "email": "hashtest@example.com",  # Exact same email
            "phone": "555-0002",
            "address": "456 Different Street"
        }
        
        success, response = self.run_test(
            "Try Duplicate Email (Should FAIL)",
            "POST",
            "members",
            400,  # Should fail with 400 error
            data=duplicate_email_member
        )
        
        # Test 3: Try with same email but different case (should FAIL with 400)
        case_different_email_member = {
            "chapter": "HA",
            "title": "S@A",
            "handle": "HashTest3",
            "name": "Hash Test Member 3",
            "email": "HashTest@Example.COM",  # Same email, different case
            "phone": "555-0003",
            "address": "789 Case Test Street"
        }
        
        success, response = self.run_test(
            "Try Same Email Different Case (Should FAIL)",
            "POST",
            "members",
            400,  # Should fail with 400 error - case insensitive
            data=case_different_email_member
        )
        
        # Test 4: Create valid unique member (should SUCCEED)
        unique_member = {
            "chapter": "HS",
            "title": "ENF",
            "handle": "HashTest4",
            "name": "Hash Test Member 4",
            "email": "unique@example.com",  # Different email
            "phone": "555-0004",
            "address": "101 Unique Street"
        }
        
        success, created_unique_member = self.run_test(
            "Create Valid Unique Member (Should SUCCEED)",
            "POST",
            "members",
            201,
            data=unique_member
        )
        
        unique_member_id = None
        if success and 'id' in created_unique_member:
            unique_member_id = created_unique_member['id']
            self.created_members.append(unique_member_id)
            print(f"   Created unique member ID: {unique_member_id}")
        
        # Test 5: Try to update to duplicate email (should FAIL with 400)
        if unique_member_id:
            update_to_duplicate = {
                "email": "hashtest@example.com"  # Try to change to first member's email
            }
            
            success, response = self.run_test(
                "Update to Duplicate Email (Should FAIL)",
                "PUT",
                f"members/{unique_member_id}",
                400,  # Should fail with 400 error
                data=update_to_duplicate
            )
        
        # Test 6: Try to update to duplicate email with different case (should FAIL with 400)
        if unique_member_id:
            update_to_case_duplicate = {
                "email": "HASHTEST@EXAMPLE.COM"  # Same email as first member, different case
            }
            
            success, response = self.run_test(
                "Update to Case Different Duplicate Email (Should FAIL)",
                "PUT",
                f"members/{unique_member_id}",
                400,  # Should fail with 400 error
                data=update_to_case_duplicate
            )
        
        # Test 7: Valid update to different email (should SUCCEED)
        if unique_member_id:
            valid_update = {
                "email": "newemail@example.com",
                "name": "Updated Hash Test Member 4"
            }
            
            success, response = self.run_test(
                "Valid Update to Different Email (Should SUCCEED)",
                "PUT",
                f"members/{unique_member_id}",
                200,
                data=valid_update
            )
        
        # Test 8: Verify the updated member can be retrieved with new email
        if unique_member_id:
            success, updated_member = self.run_test(
                "Retrieve Updated Member",
                "GET",
                f"members/{unique_member_id}",
                200
            )
            
            if success and 'email' in updated_member:
                if updated_member['email'] == 'newemail@example.com':
                    self.log_test("Verify Email Update", True, f"Email correctly updated to: {updated_member['email']}")
                else:
                    self.log_test("Verify Email Update", False, f"Expected 'newemail@example.com', got: {updated_member['email']}")
        
        # Test 9: Now try to create a member with the old unique email (should SUCCEED)
        reuse_old_email_member = {
            "chapter": "National",
            "title": "T",
            "handle": "HashTest5",
            "name": "Hash Test Member 5",
            "email": "unique@example.com",  # This email should now be available
            "phone": "555-0005",
            "address": "202 Reuse Street"
        }
        
        success, reused_email_member = self.run_test(
            "Reuse Previously Used Email (Should SUCCEED)",
            "POST",
            "members",
            201,
            data=reuse_old_email_member
        )
        
        if success and 'id' in reused_email_member:
            self.created_members.append(reused_email_member['id'])
        
        return True

    def run_hash_duplicate_tests(self):
        """Run hash-based duplicate prevention tests"""
        print("🚀 Starting Hash-Based Duplicate Prevention Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test authentication
        login_success, login_data = self.test_login()
        if not login_success:
            print("❌ Login failed - cannot continue with tests")
            return self.generate_report()
        
        # Run hash-based duplicate prevention tests
        self.test_hash_based_duplicate_prevention()
        
        # Clean up test data
        self.cleanup_members()
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print(f"📊 Hash Duplicate Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All hash duplicate prevention tests passed!")
            success_rate = 100
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            success_rate = (self.tests_passed / self.tests_run) * 100
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate,
            "failed_tests": failed_tests,
            "all_results": self.test_results
        }

def main():
    tester = HashDuplicatePreventionTester()
    results = tester.run_hash_duplicate_tests()
    
    # Return appropriate exit code
    return 0 if results["success_rate"] == 100 else 1

if __name__ == "__main__":
    sys.exit(main())