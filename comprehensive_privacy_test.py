#!/usr/bin/env python3
"""
Comprehensive Privacy Feature Test - All scenarios from review request
"""

import requests
import json
import urllib3
import sys
from datetime import datetime

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ComprehensivePrivacyTester:
    def __init__(self, base_url="https://bohtrack-app.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        
    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - FAILED: {details}")
    
    def run_test(self, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, verify=False)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, verify=False)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, verify=False)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, verify=False)
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                try:
                    error_data = response.json()
                    return False, f"Status: {response.status_code}, Error: {error_data.get('detail', 'No details')}"
                except:
                    return False, f"Status: {response.status_code}, Response: {response.text[:100]}"
        
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def test_all_privacy_scenarios(self):
        """Test all privacy scenarios from the review request"""
        print("🔐 COMPREHENSIVE PRIVACY FEATURE TEST - ALL SCENARIOS")
        print("=" * 80)
        
        # Setup: Login with testadmin/testpass123 (now National Chapter admin)
        print("\n📋 SETUP: Login with testadmin/testpass123")
        
        success, login_response = self.run_test(
            "POST", "auth/login", 200,
            {"username": "testadmin", "password": "testpass123"}
        )
        
        if not success:
            print(f"❌ Setup failed: {login_response}")
            return False
        
        self.token = login_response['token']
        self.log_test("Setup - Login with testadmin/testpass123", True)
        
        # Verify JWT contains chapter field
        success, verify_response = self.run_test("GET", "auth/verify", 200)
        if success:
            chapter = verify_response.get('chapter')
            if chapter == 'National':
                self.log_test("Setup - JWT contains chapter='National'", True)
            else:
                self.log_test("Setup - JWT contains chapter='National'", False, f"Got chapter='{chapter}'")
        
        # Create test member with phone_private=true, address_private=true
        print("\n📋 SETUP: Create test member with privacy flags")
        
        timestamp = datetime.now().strftime('%H%M%S')
        test_member_data = {
            "chapter": "National",
            "title": "Member",
            "handle": f"PrivacyTest{timestamp}",
            "name": "Privacy Test Member",
            "email": f"privacy{timestamp}@test.com",
            "phone": "555-1111-2222",
            "address": "123 Private Street",
            "phone_private": True,
            "address_private": True
        }
        
        success, test_member = self.run_test(
            "POST", "members", 201, test_member_data
        )
        
        if not success:
            print(f"❌ Setup failed: {test_member}")
            return False
        
        test_member_id = test_member['id']
        self.log_test("Setup - Create member with privacy flags", True, f"ID: {test_member_id}")
        
        # TEST 1: Non-National Admin Cannot See Private Data
        print("\n📋 TEST 1: Non-National Admin Cannot See Private Data")
        
        # Create Non-National admin
        non_national_admin_data = {
            "username": f"adminad{timestamp}",
            "email": f"adminad{timestamp}@test.com",
            "password": "testpass123",
            "role": "admin",
            "chapter": "AD",
            "title": "VP"
        }
        
        success, non_national_admin = self.run_test(
            "POST", "users", 201, non_national_admin_data
        )
        
        non_national_admin_id = None
        if success:
            non_national_admin_id = non_national_admin['id']
            self.log_test("Test 1 - Create Non-National admin", True)
            
            # Login as Non-National admin
            success, ad_login = self.run_test(
                "POST", "auth/login", 200,
                {"username": non_national_admin_data["username"], "password": "testpass123"}
            )
            
            if success:
                self.token = ad_login['token']
                self.log_test("Test 1 - Login as Non-National admin", True)
                
                # Check JWT
                success, verify_ad = self.run_test("GET", "auth/verify", 200)
                if success and verify_ad.get('chapter') == 'AD':
                    self.log_test("Test 1 - Non-National admin JWT chapter='AD'", True)
                
                # Get members - should see 'Private'
                success, members = self.run_test("GET", "members", 200)
                if success:
                    test_member_found = None
                    for member in members:
                        if member.get('id') == test_member_id:
                            test_member_found = member
                            break
                    
                    if test_member_found:
                        phone = test_member_found.get('phone')
                        address = test_member_found.get('address')
                        
                        if phone == 'Private' and address == 'Private':
                            self.log_test("Test 1 - Non-National admin sees 'Private'", True, "✅ EXPECTED")
                        else:
                            self.log_test("Test 1 - Non-National admin sees 'Private'", False, 
                                        f"phone='{phone}', address='{address}'")
                    else:
                        self.log_test("Test 1 - Find test member", False)
        else:
            self.log_test("Test 1 - Create Non-National admin", False, non_national_admin)
        
        # TEST 2: National Chapter Admin CAN See Private Data (CRITICAL)
        print("\n📋 TEST 2: National Chapter Admin CAN See Private Data (CRITICAL)")
        
        # Login back as testadmin (National admin)
        success, national_login = self.run_test(
            "POST", "auth/login", 200,
            {"username": "testadmin", "password": "testpass123"}
        )
        
        if success:
            self.token = national_login['token']
            self.log_test("Test 2 - Login as National admin (testadmin)", True)
            
            # Verify JWT
            success, verify_national = self.run_test("GET", "auth/verify", 200)
            if success and verify_national.get('chapter') == 'National':
                self.log_test("Test 2 - National admin JWT chapter='National'", True)
            
            # Get members - should see actual data
            success, members = self.run_test("GET", "members", 200)
            if success:
                test_member_found = None
                for member in members:
                    if member.get('id') == test_member_id:
                        test_member_found = member
                        break
                
                if test_member_found:
                    phone = test_member_found.get('phone')
                    address = test_member_found.get('address')
                    
                    if phone == "555-1111-2222" and address == "123 Private Street":
                        self.log_test("Test 2 - National admin sees actual data", True, "✅ CRITICAL FIX WORKING!")
                    else:
                        self.log_test("Test 2 - National admin sees actual data", False, 
                                    f"phone='{phone}', address='{address}'")
                else:
                    self.log_test("Test 2 - Find test member", False)
        
        # TEST 3: Regular Member Without Privacy Flags
        print("\n📋 TEST 3: Regular Member Without Privacy Flags")
        
        # Create member without privacy flags
        public_member_data = {
            "chapter": "National",
            "title": "Member",
            "handle": f"PublicTest{timestamp}",
            "name": "Public Test Member",
            "email": f"public{timestamp}@test.com",
            "phone": "555-3333-4444",
            "address": "456 Public Street",
            "phone_private": False,
            "address_private": False
        }
        
        success, public_member = self.run_test(
            "POST", "members", 201, public_member_data
        )
        
        public_member_id = None
        if success:
            public_member_id = public_member['id']
            self.log_test("Test 3 - Create public member", True)
            
            # Create regular user
            regular_user_data = {
                "username": f"regularuser{timestamp}",
                "email": f"regularuser{timestamp}@test.com",
                "password": "testpass123",
                "role": "member"
            }
            
            success, regular_user = self.run_test(
                "POST", "users", 201, regular_user_data
            )
            
            regular_user_id = None
            if success:
                regular_user_id = regular_user['id']
                self.log_test("Test 3 - Create regular user", True)
                
                # Login as regular user
                success, regular_login = self.run_test(
                    "POST", "auth/login", 200,
                    {"username": regular_user_data["username"], "password": "testpass123"}
                )
                
                if success:
                    self.token = regular_login['token']
                    self.log_test("Test 3 - Login as regular user", True)
                    
                    # Get members - should see actual data for non-private member
                    success, members = self.run_test("GET", "members", 200)
                    if success:
                        public_member_found = None
                        for member in members:
                            if member.get('id') == public_member_id:
                                public_member_found = member
                                break
                        
                        if public_member_found:
                            phone = public_member_found.get('phone')
                            address = public_member_found.get('address')
                            
                            if phone == "555-3333-4444" and address == "456 Public Street":
                                self.log_test("Test 3 - Regular user sees non-private data", True, "✅ EXPECTED")
                            else:
                                self.log_test("Test 3 - Regular user sees non-private data", False, 
                                            f"phone='{phone}', address='{address}'")
        
        # TEST 4: Single Member Endpoint
        print("\n📋 TEST 4: Single Member Endpoint")
        
        # Test with National admin
        success, national_login = self.run_test(
            "POST", "auth/login", 200,
            {"username": "testadmin", "password": "testpass123"}
        )
        
        if success:
            self.token = national_login['token']
            
            # Get single member - should see actual data
            success, member_detail = self.run_test("GET", f"members/{test_member_id}", 200)
            if success:
                phone = member_detail.get('phone')
                address = member_detail.get('address')
                
                if phone == "555-1111-2222" and address == "123 Private Street":
                    self.log_test("Test 4 - National admin single member endpoint", True, "✅ EXPECTED")
                else:
                    self.log_test("Test 4 - National admin single member endpoint", False, 
                                f"phone='{phone}', address='{address}'")
        
        # TEST 5: Mixed Privacy Settings
        print("\n📋 TEST 5: Mixed Privacy Settings")
        
        # Create member with mixed privacy
        mixed_member_data = {
            "chapter": "National",
            "title": "Member",
            "handle": f"MixedTest{timestamp}",
            "name": "Mixed Privacy Member",
            "email": f"mixed{timestamp}@test.com",
            "phone": "555-5555-6666",
            "address": "789 Mixed Street",
            "phone_private": True,   # Phone is private
            "address_private": False # Address is public
        }
        
        success, mixed_member = self.run_test(
            "POST", "members", 201, mixed_member_data
        )
        
        mixed_member_id = None
        if success:
            mixed_member_id = mixed_member['id']
            self.log_test("Test 5 - Create mixed privacy member", True)
            
            # Test with National admin - should see actual data for both
            success, member_detail = self.run_test("GET", f"members/{mixed_member_id}", 200)
            if success:
                phone = member_detail.get('phone')
                address = member_detail.get('address')
                
                if phone == "555-5555-6666" and address == "789 Mixed Street":
                    self.log_test("Test 5 - National admin sees all mixed data", True, "✅ EXPECTED")
                else:
                    self.log_test("Test 5 - National admin sees all mixed data", False, 
                                f"phone='{phone}', address='{address}'")
            
            # Test with regular user - should see 'Private' for phone, actual address
            if regular_user_data:
                success, regular_login = self.run_test(
                    "POST", "auth/login", 200,
                    {"username": regular_user_data["username"], "password": "testpass123"}
                )
                
                if success:
                    self.token = regular_login['token']
                    
                    success, member_detail = self.run_test("GET", f"members/{mixed_member_id}", 200)
                    if success:
                        phone = member_detail.get('phone')
                        address = member_detail.get('address')
                        
                        if phone == 'Private' and address == "789 Mixed Street":
                            self.log_test("Test 5 - Regular user sees mixed privacy correctly", True, "✅ EXPECTED")
                        else:
                            self.log_test("Test 5 - Regular user sees mixed privacy correctly", False, 
                                        f"phone='{phone}', address='{address}'")
        
        # CLEANUP
        print("\n📋 CLEANUP: Delete test data")
        
        # Switch back to admin
        success, admin_login = self.run_test(
            "POST", "auth/login", 200,
            {"username": "testadmin", "password": "testpass123"}
        )
        
        if success:
            self.token = admin_login['token']
            
            # Delete test members
            for member_id, name in [(test_member_id, "privacy test member"), 
                                  (public_member_id, "public test member"),
                                  (mixed_member_id, "mixed privacy member")]:
                if member_id:
                    success, _ = self.run_test("DELETE", f"members/{member_id}?reason=Test cleanup", 200)
                    self.log_test(f"Cleanup - Delete {name}", success)
            
            # Delete test users
            for user_id, name in [(non_national_admin_id, "non-national admin"),
                                (regular_user_id, "regular user")]:
                if user_id:
                    success, _ = self.run_test("DELETE", f"users/{user_id}", 200)
                    self.log_test(f"Cleanup - Delete {name}", success)
        
        # Print results
        print("\n" + "=" * 80)
        print("🏁 COMPREHENSIVE PRIVACY TEST RESULTS")
        print("=" * 80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL COMPREHENSIVE PRIVACY TESTS PASSED!")
            print("✅ JWT FIX WORKING CORRECTLY!")
            print("✅ National Chapter admins can see private contact info")
            print("✅ Non-National admins see 'Private' text")
            print("✅ Regular users see 'Private' text")
            print("✅ Mixed privacy settings work correctly")
            print("✅ Both list and single member endpoints work")
            return True
        else:
            print("⚠️  Some comprehensive privacy tests failed")
            return False

if __name__ == "__main__":
    tester = ComprehensivePrivacyTester()
    success = tester.test_all_privacy_scenarios()
    sys.exit(0 if success else 1)