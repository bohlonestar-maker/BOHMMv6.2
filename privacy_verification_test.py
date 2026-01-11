#!/usr/bin/env python3
"""
Privacy Feature Verification Test
Tests the specific scenarios from the review request with corrected field names.
"""

import requests
import json
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PrivacyVerificationTester:
    def __init__(self, base_url="https://fraternity-manager.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.regular_token = None
        self.test_member_id = None
        self.test_user_id = None

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")

    def make_request(self, method, endpoint, data=None, token=None):
        """Make HTTP request"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, verify=False)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, verify=False)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, verify=False)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, verify=False)

            return response.status_code, response.json() if response.text else {}
        except Exception as e:
            print(f"Request error: {e}")
            return 500, {}

    def test_admin_login(self):
        """Test admin login"""
        print("🔐 Testing Admin Authentication...")
        
        status, response = self.make_request(
            'POST', 
            'auth/login', 
            {"username": "testadmin", "password": "testpass123"}
        )
        
        if status == 200 and 'token' in response:
            self.admin_token = response['token']
            self.log_result("Admin Login", True, f"Token obtained")
            return True
        else:
            self.log_result("Admin Login", False, f"Status: {status}")
            return False

    def test_scenario_1_create_member_with_privacy(self):
        """Scenario 1: Create Member with Privacy Enabled"""
        print("\n📝 Scenario 1: Create Member with Privacy Enabled...")
        
        member_data = {
            "chapter": "HA",
            "title": "Member",
            "handle": "PrivacyFixTest",
            "name": "Privacy Fix Test",
            "email": "privacyfix@test.com",
            "phone": "555-1234-5678",
            "address": "789 Fix Street",
            "phone_private": True,
            "address_private": True
        }
        
        status, response = self.make_request(
            'POST', 
            'members', 
            member_data, 
            self.admin_token
        )
        
        if status == 201 and 'id' in response:
            self.test_member_id = response['id']
            
            # Verify privacy flags
            phone_private = response.get('phone_private', False)
            address_private = response.get('address_private', False)
            
            if phone_private and address_private:
                self.log_result("Member Created with Privacy Flags", True, 
                              f"phone_private={phone_private}, address_private={address_private}")
                return True
            else:
                self.log_result("Member Created with Privacy Flags", False, 
                              f"phone_private={phone_private}, address_private={address_private}")
                return False
        else:
            self.log_result("Create Member with Privacy", False, f"Status: {status}")
            return False

    def test_scenario_2_admin_sees_actual_values(self):
        """Scenario 2: Admin Can See Actual Values"""
        print("\n🔑 Scenario 2: Admin Can See Actual Values...")
        
        status, response = self.make_request(
            'GET', 
            'members', 
            token=self.admin_token
        )
        
        if status == 200 and isinstance(response, list):
            # Find our test member
            test_member = None
            for member in response:
                if member.get('handle') == 'PrivacyFixTest':
                    test_member = member
                    break
            
            if test_member:
                phone = test_member.get('phone')
                address = test_member.get('address')
                
                if phone == '555-1234-5678' and address == '789 Fix Street':
                    self.log_result("Admin Sees Actual Values", True, 
                                  f"Phone: {phone}, Address: {address}")
                    return True
                else:
                    self.log_result("Admin Sees Actual Values", False, 
                                  f"Phone: {phone}, Address: {address}")
                    return False
            else:
                self.log_result("Find Test Member", False, "PrivacyFixTest not found")
                return False
        else:
            self.log_result("Get Members as Admin", False, f"Status: {status}")
            return False

    def test_scenario_3_create_regular_user_and_test_privacy(self):
        """Scenario 3: Create Regular User and Test Privacy"""
        print("\n👤 Scenario 3: Create Regular User and Test Privacy...")
        
        # Create regular user
        user_data = {
            "username": "privacytest_regular",
            "password": "testpass123",
            "role": "user"
        }
        
        status, response = self.make_request(
            'POST', 
            'users', 
            user_data, 
            self.admin_token
        )
        
        if status == 201 and 'id' in response:
            self.test_user_id = response['id']
            self.log_result("Create Regular User", True, f"User ID: {self.test_user_id}")
        else:
            self.log_result("Create Regular User", False, f"Status: {status}")
            return False
        
        # Login as regular user
        status, response = self.make_request(
            'POST', 
            'auth/login', 
            {"username": "privacytest_regular", "password": "testpass123"}
        )
        
        if status == 200 and 'token' in response:
            self.regular_token = response['token']
            self.log_result("Regular User Login", True, "Token obtained")
        else:
            self.log_result("Regular User Login", False, f"Status: {status}")
            return False
        
        # Get members as regular user
        status, response = self.make_request(
            'GET', 
            'members', 
            token=self.regular_token
        )
        
        if status == 200 and isinstance(response, list):
            # Find our test member
            test_member = None
            for member in response:
                if member.get('handle') == 'PrivacyFixTest':
                    test_member = member
                    break
            
            if test_member:
                phone = test_member.get('phone')
                address = test_member.get('address')
                
                if phone == 'Private' and address == 'Private':
                    self.log_result("Non-Admin Sees 'Private' Text", True, 
                                  f"Phone: {phone}, Address: {address}")
                    return True
                else:
                    self.log_result("Non-Admin Sees 'Private' Text", False, 
                                  f"Phone: {phone}, Address: {address}")
                    return False
            else:
                self.log_result("Find Test Member as Regular User", False, "PrivacyFixTest not found")
                return False
        else:
            self.log_result("Get Members as Regular User", False, f"Status: {status}")
            return False

    def test_scenario_4_cleanup(self):
        """Scenario 4: Cleanup"""
        print("\n🧹 Scenario 4: Cleanup...")
        
        success = True
        
        # Delete test member
        if self.test_member_id:
            status, response = self.make_request(
                'DELETE', 
                f'members/{self.test_member_id}', 
                token=self.admin_token
            )
            
            if status == 200:
                self.log_result("Delete Test Member", True, "Member deleted successfully")
            else:
                self.log_result("Delete Test Member", False, f"Status: {status}")
                success = False
        
        # Delete test user
        if self.test_user_id:
            status, response = self.make_request(
                'DELETE', 
                f'users/{self.test_user_id}', 
                token=self.admin_token
            )
            
            if status == 200:
                self.log_result("Delete Test User", True, "User deleted successfully")
            else:
                self.log_result("Delete Test User", False, f"Status: {status}")
                success = False
        
        return success

    def run_verification_tests(self):
        """Run all verification tests"""
        print("🔒 Privacy Feature Verification Test")
        print("Testing corrected field names: phone_private and address_private")
        print("=" * 60)
        
        # Test admin authentication
        if not self.test_admin_login():
            print("❌ Cannot continue without admin authentication")
            return False
        
        # Run all scenarios
        scenario_results = []
        
        scenario_results.append(self.test_scenario_1_create_member_with_privacy())
        scenario_results.append(self.test_scenario_2_admin_sees_actual_values())
        scenario_results.append(self.test_scenario_3_create_regular_user_and_test_privacy())
        scenario_results.append(self.test_scenario_4_cleanup())
        
        # Print summary
        print("\n📊 Test Summary:")
        print(f"   Total Scenarios: {len(scenario_results)}")
        print(f"   Passed: {sum(scenario_results)}")
        print(f"   Failed: {len(scenario_results) - sum(scenario_results)}")
        
        all_passed = all(scenario_results)
        if all_passed:
            print("🎉 All privacy verification tests PASSED!")
            print("✅ Privacy feature is working correctly with corrected field names")
        else:
            print("⚠️  Some privacy verification tests FAILED")
        
        return all_passed

if __name__ == "__main__":
    tester = PrivacyVerificationTester()
    tester.run_verification_tests()