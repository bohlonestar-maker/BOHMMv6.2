#!/usr/bin/env python3
"""
Officer Tracking Feature Test
Tests the new permission logic for Officer Tracking API endpoints
"""

import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OfficerTrackingTester:
    def __init__(self, base_url="https://member-hub-54.preview.emergentagent.com/api"):
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

    def test_officer_tracking_feature(self):
        """Test Officer Tracking feature API endpoints with new permission logic"""
        print(f"\n👮 Testing Officer Tracking Feature...")
        
        # Test credentials from review request
        admin_credentials = {"username": "admin", "password": "2X13y75Z"}
        lonestar_credentials = {"username": "Lonestar", "password": "boh2158tc"}
        
        # Test 1: Login as admin user
        print(f"\n   🔐 Testing Admin Access...")
        success, admin_login = self.run_test(
            "Login as Admin (admin/2X13y75Z)",
            "POST",
            "auth/login",
            200,
            data=admin_credentials
        )
        
        if success and 'token' in admin_login:
            self.token = admin_login['token']
            
            # Test GET /api/officer-tracking/members
            success, members_response = self.run_test(
                "Admin - GET /api/officer-tracking/members",
                "GET",
                "officer-tracking/members",
                200
            )
            
            if success:
                # Verify response structure (members grouped by chapter)
                expected_chapters = ['National', 'AD', 'HA', 'HS']
                if isinstance(members_response, dict):
                    found_chapters = list(members_response.keys())
                    if all(chapter in found_chapters for chapter in expected_chapters):
                        self.log_test("Admin - Members Response Structure", True, f"All chapters found: {found_chapters}")
                    else:
                        self.log_test("Admin - Members Response Structure", False, f"Expected {expected_chapters}, got {found_chapters}")
                else:
                    self.log_test("Admin - Members Response Structure", False, "Response is not a dictionary")
            
            # Test GET /api/officer-tracking/attendance
            success, attendance_list = self.run_test(
                "Admin - GET /api/officer-tracking/attendance",
                "GET",
                "officer-tracking/attendance",
                200
            )
            
            # Test GET /api/officer-tracking/dues
            success, dues_list = self.run_test(
                "Admin - GET /api/officer-tracking/dues",
                "GET",
                "officer-tracking/dues",
                200
            )
            
            # Test GET /api/officer-tracking/summary
            success, summary_response = self.run_test(
                "Admin - GET /api/officer-tracking/summary",
                "GET",
                "officer-tracking/summary",
                200
            )
            
            # Test POST /api/officer-tracking/attendance (admin should have edit access)
            test_attendance = {
                "member_id": "test-member-id",
                "meeting_date": "2025-01-06",
                "meeting_type": "national_officer",
                "status": "present",
                "notes": "Test attendance record"
            }
            
            success, attendance_response = self.run_test(
                "Admin - POST /api/officer-tracking/attendance",
                "POST",
                "officer-tracking/attendance",
                200,
                data=test_attendance
            )
            
            # Test POST /api/officer-tracking/dues (admin should have edit access)
            test_dues = {
                "member_id": "test-member-id",
                "quarter": "Q1_2025",
                "status": "paid",
                "amount_paid": 25.00,
                "payment_date": "2025-01-06",
                "notes": "Test dues payment"
            }
            
            success, dues_response = self.run_test(
                "Admin - POST /api/officer-tracking/dues",
                "POST",
                "officer-tracking/dues",
                200,
                data=test_dues
            )
        
        # Test 2: Login as Lonestar (SEC title - should have edit access)
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
            
            # Test GET /api/officer-tracking/members (should succeed - all officers can view)
            success, members_response = self.run_test(
                "SEC Officer - GET /api/officer-tracking/members",
                "GET",
                "officer-tracking/members",
                200
            )
            
            # Test GET /api/officer-tracking/attendance (should succeed - all officers can view)
            success, attendance_list = self.run_test(
                "SEC Officer - GET /api/officer-tracking/attendance",
                "GET",
                "officer-tracking/attendance",
                200
            )
            
            # Test GET /api/officer-tracking/dues (should succeed - all officers can view)
            success, dues_list = self.run_test(
                "SEC Officer - GET /api/officer-tracking/dues",
                "GET",
                "officer-tracking/dues",
                200
            )
            
            # Test GET /api/officer-tracking/summary (should succeed - all officers can view)
            success, summary_response = self.run_test(
                "SEC Officer - GET /api/officer-tracking/summary",
                "GET",
                "officer-tracking/summary",
                200
            )
            
            # Test POST /api/officer-tracking/attendance (should succeed - SEC has edit access)
            test_attendance_sec = {
                "member_id": "test-member-id-2",
                "meeting_date": "2025-01-06",
                "meeting_type": "chapter_officer",
                "status": "absent",
                "notes": "SEC test attendance record"
            }
            
            success, attendance_response = self.run_test(
                "SEC Officer - POST /api/officer-tracking/attendance",
                "POST",
                "officer-tracking/attendance",
                200,
                data=test_attendance_sec
            )
            
            # Test POST /api/officer-tracking/dues (should succeed - SEC has edit access)
            test_dues_sec = {
                "member_id": "test-member-id-2",
                "quarter": "Q1_2025",
                "status": "unpaid",
                "notes": "SEC test dues record"
            }
            
            success, dues_response = self.run_test(
                "SEC Officer - POST /api/officer-tracking/dues",
                "POST",
                "officer-tracking/dues",
                200,
                data=test_dues_sec
            )
        
        print(f"   👮 Officer Tracking feature testing completed")

    def run_tests(self):
        """Run all Officer Tracking tests"""
        print("🚀 Starting Officer Tracking API Tests...")
        print(f"   Base URL: {self.base_url}")
        print(f"   Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run Officer Tracking tests
        self.test_officer_tracking_feature()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Total tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Tests failed: {self.tests_run - self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed - check output above")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = OfficerTrackingTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)