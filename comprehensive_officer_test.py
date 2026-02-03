#!/usr/bin/env python3
"""
Comprehensive Officer Tracking Feature Test
Tests the complete permission logic for Officer Tracking API endpoints
"""

import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ComprehensiveOfficerTrackingTester:
    def __init__(self, base_url="https://bohnexus.preview.emergentagent.com/api"):
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

    def test_comprehensive_officer_tracking(self):
        """Test comprehensive Officer Tracking feature with all permission scenarios"""
        print(f"\n👮 Testing Comprehensive Officer Tracking Feature...")
        
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
            
            # Test all GET endpoints (admin should have view access)
            success, members_response = self.run_test(
                "Admin - GET /api/officer-tracking/members",
                "GET",
                "officer-tracking/members",
                200
            )
            
            # Verify data structure
            if success and isinstance(members_response, dict):
                expected_chapters = ['National', 'AD', 'HA', 'HS']
                found_chapters = list(members_response.keys())
                if all(chapter in found_chapters for chapter in expected_chapters):
                    self.log_test("Admin - Members Data Structure Valid", True, f"All chapters present: {found_chapters}")
                    
                    # Check if we have member data
                    total_members = sum(len(members_response[chapter]) for chapter in found_chapters)
                    self.log_test("Admin - Members Data Present", total_members > 0, f"Total members found: {total_members}")
                else:
                    self.log_test("Admin - Members Data Structure Valid", False, f"Missing chapters. Expected: {expected_chapters}, Found: {found_chapters}")
            
            success, attendance_list = self.run_test(
                "Admin - GET /api/officer-tracking/attendance",
                "GET",
                "officer-tracking/attendance",
                200
            )
            
            success, dues_list = self.run_test(
                "Admin - GET /api/officer-tracking/dues",
                "GET",
                "officer-tracking/dues",
                200
            )
            
            success, summary_response = self.run_test(
                "Admin - GET /api/officer-tracking/summary",
                "GET",
                "officer-tracking/summary",
                200
            )
            
            # Test POST endpoints (admin should have edit access)
            test_attendance = {
                "member_id": "admin-test-member",
                "meeting_date": "2025-01-07",
                "meeting_type": "national_officer",
                "status": "present",
                "notes": "Admin test attendance"
            }
            
            success, attendance_response = self.run_test(
                "Admin - POST /api/officer-tracking/attendance (Edit Access)",
                "POST",
                "officer-tracking/attendance",
                200,
                data=test_attendance
            )
            
            test_dues = {
                "member_id": "admin-test-member",
                "quarter": "Q1_2025",
                "status": "paid",
                "amount_paid": 50.00,
                "payment_date": "2025-01-07",
                "notes": "Admin test dues"
            }
            
            success, dues_response = self.run_test(
                "Admin - POST /api/officer-tracking/dues (Edit Access)",
                "POST",
                "officer-tracking/dues",
                200,
                data=test_dues
            )
        
        # Test 2: SEC Officer Access (Lonestar - should have full access)
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
            
            # Test all GET endpoints (SEC should have view access)
            success, members_response = self.run_test(
                "SEC - GET /api/officer-tracking/members",
                "GET",
                "officer-tracking/members",
                200
            )
            
            success, attendance_list = self.run_test(
                "SEC - GET /api/officer-tracking/attendance",
                "GET",
                "officer-tracking/attendance",
                200
            )
            
            success, dues_list = self.run_test(
                "SEC - GET /api/officer-tracking/dues",
                "GET",
                "officer-tracking/dues",
                200
            )
            
            success, summary_response = self.run_test(
                "SEC - GET /api/officer-tracking/summary",
                "GET",
                "officer-tracking/summary",
                200
            )
            
            # Test POST endpoints (SEC should have edit access)
            test_attendance_sec = {
                "member_id": "sec-test-member",
                "meeting_date": "2025-01-07",
                "meeting_type": "chapter_officer",
                "status": "excused",
                "notes": "SEC test attendance"
            }
            
            success, attendance_response = self.run_test(
                "SEC - POST /api/officer-tracking/attendance (Edit Access)",
                "POST",
                "officer-tracking/attendance",
                200,
                data=test_attendance_sec
            )
            
            test_dues_sec = {
                "member_id": "sec-test-member",
                "quarter": "Q1_2025",
                "status": "partial",
                "amount_paid": 25.00,
                "payment_date": "2025-01-07",
                "notes": "SEC test dues"
            }
            
            success, dues_response = self.run_test(
                "SEC - POST /api/officer-tracking/dues (Edit Access)",
                "POST",
                "officer-tracking/dues",
                200,
                data=test_dues_sec
            )
        
        # Test 3: Create and test regular officer (VP - should have view access but not edit)
        print(f"\n   🔐 Testing Regular Officer Access (VP)...")
        
        if admin_token:
            self.token = admin_token  # Switch back to admin to create test user
            
            # Create test VP officer
            test_vp_user = {
                "username": "testvp",
                "email": "testvp@test.com",
                "password": "testpass123",
                "role": "admin",
                "chapter": "AD",
                "title": "VP"
            }
            
            success, created_vp = self.run_test(
                "Create Test VP Officer",
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
                    "Login as Test VP",
                    "POST",
                    "auth/login",
                    200,
                    data={"username": "testvp", "password": "testpass123"}
                )
                
                if success and 'token' in vp_login:
                    self.token = vp_login['token']
                    
                    # Test GET endpoints (VP should have view access)
                    success, members_response = self.run_test(
                        "VP - GET /api/officer-tracking/members (View Access)",
                        "GET",
                        "officer-tracking/members",
                        200
                    )
                    
                    success, attendance_list = self.run_test(
                        "VP - GET /api/officer-tracking/attendance (View Access)",
                        "GET",
                        "officer-tracking/attendance",
                        200
                    )
                    
                    success, dues_list = self.run_test(
                        "VP - GET /api/officer-tracking/dues (View Access)",
                        "GET",
                        "officer-tracking/dues",
                        200
                    )
                    
                    success, summary_response = self.run_test(
                        "VP - GET /api/officer-tracking/summary (View Access)",
                        "GET",
                        "officer-tracking/summary",
                        200
                    )
                    
                    # Test POST endpoints (VP should NOT have edit access - should fail with 403)
                    test_attendance_vp = {
                        "member_id": "vp-test-member",
                        "meeting_date": "2025-01-07",
                        "meeting_type": "chapter_officer",
                        "status": "present",
                        "notes": "VP test - should fail"
                    }
                    
                    success, attendance_response = self.run_test(
                        "VP - POST /api/officer-tracking/attendance (Should Fail - No Edit Access)",
                        "POST",
                        "officer-tracking/attendance",
                        403,
                        data=test_attendance_vp
                    )
                    
                    test_dues_vp = {
                        "member_id": "vp-test-member",
                        "quarter": "Q1_2025",
                        "status": "paid",
                        "amount_paid": 25.00,
                        "notes": "VP test - should fail"
                    }
                    
                    success, dues_response = self.run_test(
                        "VP - POST /api/officer-tracking/dues (Should Fail - No Edit Access)",
                        "POST",
                        "officer-tracking/dues",
                        403,
                        data=test_dues_vp
                    )
            
            # Clean up test VP user
            if vp_user_id:
                self.token = admin_token  # Switch back to admin for cleanup
                success, delete_response = self.run_test(
                    "Delete Test VP Officer (Cleanup)",
                    "DELETE",
                    f"users/{vp_user_id}",
                    200
                )
        
        # Test 4: Create and test non-officer user (should have no access)
        print(f"\n   🔐 Testing Non-Officer Access...")
        
        if admin_token:
            self.token = admin_token  # Switch back to admin to create test user
            
            # Create test regular member
            test_member_user = {
                "username": "testmember",
                "email": "testmember@test.com",
                "password": "testpass123",
                "role": "member",
                "chapter": "National",
                "title": "Member"
            }
            
            success, created_member = self.run_test(
                "Create Test Member (Non-Officer)",
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
                    "Login as Test Member",
                    "POST",
                    "auth/login",
                    200,
                    data={"username": "testmember", "password": "testpass123"}
                )
                
                if success and 'token' in member_login:
                    self.token = member_login['token']
                    
                    # Test GET endpoints (Member should NOT have access - should fail with 403)
                    success, members_response = self.run_test(
                        "Member - GET /api/officer-tracking/members (Should Fail - No Access)",
                        "GET",
                        "officer-tracking/members",
                        403
                    )
                    
                    success, attendance_list = self.run_test(
                        "Member - GET /api/officer-tracking/attendance (Should Fail - No Access)",
                        "GET",
                        "officer-tracking/attendance",
                        403
                    )
                    
                    success, dues_list = self.run_test(
                        "Member - GET /api/officer-tracking/dues (Should Fail - No Access)",
                        "GET",
                        "officer-tracking/dues",
                        403
                    )
                    
                    success, summary_response = self.run_test(
                        "Member - GET /api/officer-tracking/summary (Should Fail - No Access)",
                        "GET",
                        "officer-tracking/summary",
                        403
                    )
            
            # Clean up test member user
            if member_user_id:
                self.token = admin_token  # Switch back to admin for cleanup
                success, delete_response = self.run_test(
                    "Delete Test Member (Cleanup)",
                    "DELETE",
                    f"users/{member_user_id}",
                    200
                )
        
        print(f"   👮 Comprehensive Officer Tracking feature testing completed")

    def run_tests(self):
        """Run all comprehensive Officer Tracking tests"""
        print("🚀 Starting Comprehensive Officer Tracking API Tests...")
        print(f"   Base URL: {self.base_url}")
        print(f"   Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run comprehensive Officer Tracking tests
        self.test_comprehensive_officer_tracking()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Total tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Tests failed: {self.tests_run - self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        # Print detailed results
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"   {status}: {result['test']}")
            if not result['success'] and result['details']:
                print(f"      Details: {result['details']}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} tests failed - check output above")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = ComprehensiveOfficerTrackingTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)