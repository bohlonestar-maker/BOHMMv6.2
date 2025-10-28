import requests
import sys
import json
from datetime import datetime

class BOHDirectoryAPITester:
    def __init__(self, base_url="https://road-roster.preview.emergentagent.com/api"):
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
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

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
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            print(f"   Token obtained: {self.token[:20]}...")
            return True, response
        return False, {}

    def test_auth_verify(self):
        """Test token verification"""
        success, response = self.run_test(
            "Token Verification",
            "GET",
            "auth/verify",
            200
        )
        return success, response

    def test_member_operations(self):
        """Test all member CRUD operations"""
        print(f"\n👥 Testing Member Operations...")
        
        # Test get members (empty initially)
        success, members = self.run_test(
            "Get Members (Initial)",
            "GET",
            "members",
            200
        )
        
        # Test create member
        test_member = {
            "chapter": "National",
            "title": "Prez",
            "handle": "TestRider",
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1-555-0123",
            "address": "123 Test Street, Test City, TC 12345"
        }
        
        success, created_member = self.run_test(
            "Create Member",
            "POST",
            "members",
            201,
            data=test_member
        )
        
        member_id = None
        if success and 'id' in created_member:
            member_id = created_member['id']
            print(f"   Created member ID: {member_id}")
        
        # Test get specific member
        if member_id:
            success, member = self.run_test(
                "Get Specific Member",
                "GET",
                f"members/{member_id}",
                200
            )
        
        # Test update member
        if member_id:
            update_data = {
                "name": "Updated Test User",
                "title": "VP"
            }
            success, updated_member = self.run_test(
                "Update Member",
                "PUT",
                f"members/{member_id}",
                200,
                data=update_data
            )
        
        # Test get all members (should have our test member)
        success, all_members = self.run_test(
            "Get All Members",
            "GET",
            "members",
            200
        )
        
        # Test CSV export
        success, csv_data = self.run_test(
            "Export Members CSV",
            "GET",
            "members/export/csv",
            200
        )
        
        # Test delete member
        if member_id:
            success, delete_response = self.run_test(
                "Delete Member",
                "DELETE",
                f"members/{member_id}",
                200
            )
        
        return member_id

    def test_user_management(self):
        """Test user management operations"""
        print(f"\n👤 Testing User Management...")
        
        # Test get users
        success, users = self.run_test(
            "Get Users",
            "GET",
            "users",
            200
        )
        
        # Test create user
        test_user = {
            "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
            "password": "testpass123",
            "role": "user"
        }
        
        success, created_user = self.run_test(
            "Create User",
            "POST",
            "users",
            201,
            data=test_user
        )
        
        user_id = None
        if success and 'id' in created_user:
            user_id = created_user['id']
            print(f"   Created user ID: {user_id}")
        
        # Test create admin user
        admin_user = {
            "username": f"testadmin_{datetime.now().strftime('%H%M%S')}",
            "password": "adminpass123",
            "role": "admin"
        }
        
        success, created_admin = self.run_test(
            "Create Admin User",
            "POST",
            "users",
            201,
            data=admin_user
        )
        
        admin_id = None
        if success and 'id' in created_admin:
            admin_id = created_admin['id']
        
        # Test update user
        if user_id:
            update_data = {
                "role": "admin"
            }
            success, updated_user = self.run_test(
                "Update User Role",
                "PUT",
                f"users/{user_id}",
                200,
                data=update_data
            )
        
        # Test delete user (not admin)
        if user_id:
            success, delete_response = self.run_test(
                "Delete User",
                "DELETE",
                f"users/{user_id}",
                200
            )
        
        # Test delete admin user
        if admin_id:
            success, delete_response = self.run_test(
                "Delete Admin User",
                "DELETE",
                f"users/{admin_id}",
                200
            )
        
        return user_id, admin_id

    def test_unauthorized_access(self):
        """Test unauthorized access scenarios"""
        print(f"\n🚫 Testing Unauthorized Access...")
        
        # Save current token
        original_token = self.token
        self.token = None
        
        # Test accessing members without token
        success, response = self.run_test(
            "Access Members Without Token",
            "GET",
            "members",
            401
        )
        
        # Test creating member without token
        success, response = self.run_test(
            "Create Member Without Token",
            "POST",
            "members",
            401,
            data={"chapter": "National", "title": "Prez", "handle": "Test", "name": "Test", "email": "test@test.com", "phone": "123", "address": "Test"}
        )
        
        # Restore token
        self.token = original_token

    def test_user_role_restrictions(self):
        """Test user role restrictions"""
        print(f"\n🔒 Testing Role-Based Access Control...")
        
        # Create a regular user and get their token
        test_user = {
            "username": f"roletest_{datetime.now().strftime('%H%M%S')}",
            "password": "testpass123",
            "role": "user"
        }
        
        success, created_user = self.run_test(
            "Create Test User for Role Testing",
            "POST",
            "users",
            201,
            data=test_user
        )
        
        if not success:
            return
        
        # Login as regular user
        original_token = self.token
        success, login_response = self.run_test(
            "Login as Regular User",
            "POST",
            "auth/login",
            200,
            data={"username": test_user["username"], "password": test_user["password"]}
        )
        
        if success and 'token' in login_response:
            self.token = login_response['token']
            
            # Test that regular user can view members
            success, response = self.run_test(
                "Regular User - View Members",
                "GET",
                "members",
                200
            )
            
            # Test that regular user can export CSV
            success, response = self.run_test(
                "Regular User - Export CSV",
                "GET",
                "members/export/csv",
                200
            )
            
            # Test that regular user cannot create members
            success, response = self.run_test(
                "Regular User - Create Member (Should Fail)",
                "POST",
                "members",
                403,
                data={"chapter": "National", "title": "Prez", "handle": "Test", "name": "Test", "email": "test@test.com", "phone": "123", "address": "Test"}
            )
            
            # Test that regular user cannot access user management
            success, response = self.run_test(
                "Regular User - Access User Management (Should Fail)",
                "GET",
                "users",
                403
            )
        
        # Restore admin token
        self.token = original_token
        
        # Clean up test user
        if created_user and 'id' in created_user:
            success, response = self.run_test(
                "Delete Test User",
                "DELETE",
                f"users/{created_user['id']}",
                200
            )

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Brothers of the Highway Directory API Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test authentication
        login_success, login_data = self.test_login()
        if not login_success:
            print("❌ Login failed - cannot continue with other tests")
            return self.generate_report()
        
        # Test token verification
        self.test_auth_verify()
        
        # Test member operations
        self.test_member_operations()
        
        # Test user management
        self.test_user_management()
        
        # Test unauthorized access
        self.test_unauthorized_access()
        
        # Test role-based access control
        self.test_user_role_restrictions()
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
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
    tester = BOHDirectoryAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["success_rate"] == 100 else 1

if __name__ == "__main__":
    sys.exit(main())