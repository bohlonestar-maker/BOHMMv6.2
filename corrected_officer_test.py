#!/usr/bin/env python3
"""
Corrected Officer Tracking Feature Test
Tests the permission logic correctly by creating users with appropriate roles
"""

import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CorrectedOfficerTrackingTester:
    def __init__(self, base_url="https://member-manager-26.preview.emergentagent.com/api"):
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

    def test_corrected_officer_tracking(self):
        """Test Officer Tracking with corrected permission logic"""
        print(f"\n👮 Testing Corrected Officer Tracking Feature...")
        
        # Test credentials
        admin_credentials = {"username": "admin", "password": "2X13y75Z"}
        lonestar_credentials = {"username": "Lonestar", "password": "boh2158tc"}
        
        # Test 1: Admin Access (should have full access)
        print(f"\n   🔐 Testing Admin Access...")
        success, admin_login = self.run_test(
            "Login as Admin",
            "POST",
            "auth/login",
            200,
            data=admin_credentials
        )
        
        admin_token = None
        if success and 'token' in admin_login:
            admin_token = admin_login['token']
            self.token = admin_token
            
            # Test admin can view and edit
            success, members_response = self.run_test(
                "Admin - GET /api/officer-tracking/members",
                "GET",
                "officer-tracking/members",
                200
            )
            
            test_attendance = {
                "member_id": "admin-test-member",
                "meeting_date": "2025-01-07",
                "meeting_type": "national_officer",
                "status": "present",
                "notes": "Admin test attendance"
            }
            
            success, attendance_response = self.run_test(
                "Admin - POST /api/officer-tracking/attendance (Should Succeed)",
                "POST",
                "officer-tracking/attendance",
                200,
                data=test_attendance
            )
        
        # Test 2: SEC Officer Access (should have full access)
        print(f"\n   🔐 Testing SEC Officer Access...")
        success, lonestar_login = self.run_test(
            "Login as Lonestar (SEC)",
            "POST",
            "auth/login",
            200,
            data=lonestar_credentials
        )
        
        if success and 'token' in lonestar_login:
            self.token = lonestar_login['token']
            
            # Test SEC can view and edit
            success, members_response = self.run_test(
                "SEC - GET /api/officer-tracking/members",
                "GET",
                "officer-tracking/members",
                200
            )
            
            test_attendance_sec = {
                "member_id": "sec-test-member",
                "meeting_date": "2025-01-07",
                "meeting_type": "chapter_officer",
                "status": "present",
                "notes": "SEC test attendance"
            }
            
            success, attendance_response = self.run_test(
                "SEC - POST /api/officer-tracking/attendance (Should Succeed)",
                "POST",
                "officer-tracking/attendance",
                200,
                data=test_attendance_sec
            )
        
        # Test 3: Create NVP user (should have edit access)
        print(f"\n   🔐 Testing NVP Officer Access...")
        
        if admin_token:
            self.token = admin_token  # Switch back to admin to create test user
            
            # Create test NVP officer with admin role (NVP should have admin privileges)
            test_nvp_user = {
                "username": "testnvp",
                "email": "testnvp@test.com",
                "password": "testpass123",
                "role": "admin",
                "chapter": "National",
                "title": "NVP"
            }
            
            success, created_nvp = self.run_test(
                "Create Test NVP Officer",
                "POST",
                "users",
                201,
                data=test_nvp_user
            )
            
            nvp_user_id = None
            if success and 'id' in created_nvp:
                nvp_user_id = created_nvp['id']
                
                # Login as NVP
                success, nvp_login = self.run_test(
                    "Login as Test NVP",
                    "POST",
                    "auth/login",
                    200,
                    data={"username": "testnvp", "password": "testpass123"}
                )
                
                if success and 'token' in nvp_login:
                    self.token = nvp_login['token']
                    
                    # Test NVP can view and edit
                    success, members_response = self.run_test(
                        "NVP - GET /api/officer-tracking/members (Should Succeed)",
                        "GET",
                        "officer-tracking/members",
                        200
                    )
                    
                    test_attendance_nvp = {
                        "member_id": "nvp-test-member",
                        "meeting_date": "2025-01-07",
                        "meeting_type": "national_officer",
                        "status": "present",
                        "notes": "NVP test attendance"
                    }
                    
                    success, attendance_response = self.run_test(
                        "NVP - POST /api/officer-tracking/attendance (Should Succeed)",
                        "POST",
                        "officer-tracking/attendance",
                        200,
                        data=test_attendance_nvp
                    )
            
            # Clean up NVP user
            if nvp_user_id:
                self.token = admin_token  # Switch back to admin for cleanup
                success, delete_response = self.run_test(
                    "Delete Test NVP Officer (Cleanup)",
                    "DELETE",
                    f"users/{nvp_user_id}",
                    200
                )
        
        # Test 4: Create regular officer with member role (should have view access but not edit)
        print(f"\n   🔐 Testing Regular Officer Access (VP with member role)...")
        
        if admin_token:
            self.token = admin_token  # Switch back to admin to create test user
            
            # Create test VP officer with MEMBER role (not admin role)
            test_vp_user = {
                "username": "testvpmember",
                "email": "testvpmember@test.com",
                "password": "testpass123",
                "role": "member",  # This is the key - member role, not admin
                "chapter": "AD",
                "title": "VP"
            }
            
            success, created_vp = self.run_test(
                "Create Test VP Officer (Member Role)",
                "POST",
                "users",
                201,
                data=test_vp_user
            )
            
            vp_user_id = None
            if success and 'id' in created_vp:
                vp_user_id = created_vp['id']
                
                # Login as VP
                success, vp_login = self.run_test(
                    "Login as Test VP (Member Role)",
                    "POST",
                    "auth/login",
                    200,
                    data={"username": "testvpmember", "password": "testpass123"}
                )
                
                if success and 'token' in vp_login:
                    self.token = vp_login['token']
                    
                    # Test VP can view (VP is an officer title)
                    success, members_response = self.run_test(
                        "VP (Member Role) - GET /api/officer-tracking/members (Should Succeed)",
                        "GET",
                        "officer-tracking/members",
                        200
                    )
                    
                    # Test VP cannot edit (not SEC or NVP, and not admin role)
                    test_attendance_vp = {
                        "member_id": "vp-member-test",
                        "meeting_date": "2025-01-07",
                        "meeting_type": "chapter_officer",
                        "status": "present",
                        "notes": "VP test - should fail"
                    }
                    
                    success, attendance_response = self.run_test(
                        "VP (Member Role) - POST /api/officer-tracking/attendance (Should Fail)",
                        "POST",
                        "officer-tracking/attendance",
                        403,
                        data=test_attendance_vp
                    )
                    
                    test_dues_vp = {
                        "member_id": "vp-member-test",
                        "quarter": "Q1_2025",
                        "status": "paid",
                        "amount_paid": 25.00,
                        "notes": "VP test - should fail"
                    }
                    
                    success, dues_response = self.run_test(
                        "VP (Member Role) - POST /api/officer-tracking/dues (Should Fail)",
                        "POST",
                        "officer-tracking/dues",
                        403,
                        data=test_dues_vp
                    )
            
            # Clean up VP user
            if vp_user_id:
                self.token = admin_token  # Switch back to admin for cleanup
                success, delete_response = self.run_test(
                    "Delete Test VP Officer (Cleanup)",
                    "DELETE",
                    f"users/{vp_user_id}",
                    200
                )
        
        # Test 5: Create non-officer user (should have no access)
        print(f"\n   🔐 Testing Non-Officer Access...")
        
        if admin_token:
            self.token = admin_token  # Switch back to admin to create test user
            
            # Create test regular member
            test_member_user = {
                "username": "testregularmember",
                "email": "testregularmember@test.com",
                "password": "testpass123",
                "role": "member",
                "chapter": "National",
                "title": "Member"  # Not an officer title
            }
            
            success, created_member = self.run_test(
                "Create Test Regular Member (Non-Officer)",
                "POST",
                "users",
                201,
                data=test_member_user
            )
            
            member_user_id = None
            if success and 'id' in created_member:
                member_user_id = created_member['id']
                
                # Login as member
                success, member_login = self.run_test(
                    "Login as Test Regular Member",
                    "POST",
                    "auth/login",
                    200,
                    data={"username": "testregularmember", "password": "testpass123"}
                )
                
                if success and 'token' in member_login:
                    self.token = member_login['token']
                    
                    # Test regular member cannot view (not an officer)
                    success, members_response = self.run_test(
                        "Regular Member - GET /api/officer-tracking/members (Should Fail)",
                        "GET",
                        "officer-tracking/members",
                        403
                    )
                    
                    success, attendance_list = self.run_test(
                        "Regular Member - GET /api/officer-tracking/attendance (Should Fail)",
                        "GET",
                        "officer-tracking/attendance",
                        403
                    )
            
            # Clean up member user
            if member_user_id:
                self.token = admin_token  # Switch back to admin for cleanup
                success, delete_response = self.run_test(
                    "Delete Test Regular Member (Cleanup)",
                    "DELETE",
                    f"users/{member_user_id}",
                    200
                )
        
        print(f"   👮 Corrected Officer Tracking feature testing completed")

    def run_tests(self):
        """Run all corrected Officer Tracking tests"""
        print("🚀 Starting Corrected Officer Tracking API Tests...")
        print(f"   Base URL: {self.base_url}")
        print(f"   Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run corrected Officer Tracking tests
        self.test_corrected_officer_tracking()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Total tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Tests failed: {self.tests_run - self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        # Print detailed results for failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for result in failed_tests:
                print(f"   - {result['test']}: {result['details']}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} tests failed - check output above")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = CorrectedOfficerTrackingTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)