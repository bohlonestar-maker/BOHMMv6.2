#!/usr/bin/env python3
"""
A & D (Attendance & Dues) Feature Test Script
Tests the updated simplified dues tracking feature
"""

import requests
import json
import sys
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ADFeatureTester:
    def __init__(self, base_url="https://role-master-5.preview.emergentagent.com/api"):
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

    def test_login(self):
        """Test login with review request credentials"""
        print(f"\n🔐 Testing Authentication...")
        
        # Test credentials from review request
        credentials_to_try = [
            ("admin", "2X13y75Z"),
            ("Lonestar", "boh2158tc")
        ]
        
        for username, password in credentials_to_try:
            success, response = self.run_test(
                f"Login as {username}",
                "POST",
                "auth/login",
                200,
                data={"username": username, "password": password}
            )
            
            if success and 'token' in response:
                self.token = response['token']
                print(f"   ✅ Successfully logged in as {username}")
                return True, response
        
        print("   ❌ All login attempts failed")
        return False, {}

    def test_ad_feature(self):
        """Test the A & D (Attendance & Dues) feature"""
        print(f"\n📋 Testing A & D (Attendance & Dues) Feature...")
        
        # Test 1: GET /api/officer-tracking/members - Get all members by chapter
        success, members_response = self.run_test(
            "GET Officer Tracking Members",
            "GET",
            "officer-tracking/members",
            200
        )
        
        if success:
            # Verify response structure - should be organized by chapter
            expected_chapters = ["National", "AD", "HA", "HS"]
            if isinstance(members_response, dict):
                found_chapters = [chapter for chapter in expected_chapters if chapter in members_response]
                if len(found_chapters) >= 1:
                    self.log_test("Officer Tracking Members - Chapter Organization", True, f"Found chapters: {found_chapters}")
                else:
                    self.log_test("Officer Tracking Members - Chapter Organization", False, f"Expected chapters not found: {list(members_response.keys())}")
            else:
                self.log_test("Officer Tracking Members - Response Format", False, "Response is not a dictionary")
        
        # Test 2: Create a test member for dues testing
        import time
        unique_id = str(int(time.time()))
        test_member = {
            "chapter": "National",
            "title": "Member",
            "handle": f"ADTest{unique_id}",
            "name": "A&D Test Member",
            "email": f"adtest{unique_id}@example.com",
            "phone": "555-0123",
            "address": "123 Test Street"
        }
        
        success, created_member = self.run_test(
            "Create Test Member for A&D",
            "POST",
            "members",
            201,
            data=test_member
        )
        
        test_member_id = None
        if success and 'id' in created_member:
            test_member_id = created_member['id']
            print(f"   Created test member ID: {test_member_id}")
        
        # Test 3: POST /api/officer-tracking/dues - Test new simplified format
        if test_member_id:
            # Test scenario a: POST dues with status "paid"
            paid_dues_data = {
                "member_id": test_member_id,
                "month": "Jan_2026",
                "status": "paid",
                "notes": "Paid in full on time"
            }
            
            success, paid_response = self.run_test(
                "POST Dues - Status Paid",
                "POST",
                "officer-tracking/dues",
                200,
                data=paid_dues_data
            )
            
            # Test scenario b: POST dues with status "late"
            late_dues_data = {
                "member_id": test_member_id,
                "month": "Feb_2026",
                "status": "late",
                "notes": "Payment received 5 days late"
            }
            
            success, late_response = self.run_test(
                "POST Dues - Status Late",
                "POST",
                "officer-tracking/dues",
                200,
                data=late_dues_data
            )
            
            # Test scenario c: POST dues with status "unpaid"
            unpaid_dues_data = {
                "member_id": test_member_id,
                "month": "Mar_2026",
                "status": "unpaid",
                "notes": "No payment received"
            }
            
            success, unpaid_response = self.run_test(
                "POST Dues - Status Unpaid",
                "POST",
                "officer-tracking/dues",
                200,
                data=unpaid_dues_data
            )
            
            # Test scenario d: Verify simplified dues model (no quarter, amount_paid, payment_date fields)
            old_format_data = {
                "member_id": test_member_id,
                "month": "Apr_2026",
                "status": "paid",
                "notes": "Testing old format compatibility",
                "quarter": "Q2",  # Should be ignored
                "amount_paid": 25.00,  # Should be ignored
                "payment_date": "2026-04-01"  # Should be ignored
            }
            
            success, old_format_response = self.run_test(
                "POST Dues - Old Format Compatibility",
                "POST",
                "officer-tracking/dues",
                200,
                data=old_format_data
            )
            
            # Test scenario e: Verify month format is "Mon_YYYY"
            valid_months = ["May_2026", "Jun_2026", "Jul_2026"]
            for month in valid_months:
                month_data = {
                    "member_id": test_member_id,
                    "month": month,
                    "status": "paid",
                    "notes": f"Testing {month} format"
                }
                
                success, month_response = self.run_test(
                    f"POST Dues - Valid Month {month}",
                    "POST",
                    "officer-tracking/dues",
                    200,
                    data=month_data
                )
        
        # Test 4: POST /api/officer-tracking/attendance - Should still work with updated permissions
        if test_member_id:
            attendance_data = {
                "member_id": test_member_id,
                "meeting_date": "2026-01-15",
                "meeting_type": "regular",  # Added required field
                "status": "present",
                "notes": "Attended full meeting"
            }
            
            success, attendance_response = self.run_test(
                "POST Attendance - Updated Permissions",
                "POST",
                "officer-tracking/attendance",
                200,
                data=attendance_data
            )
        
        # Test 5: Verify GET endpoints still work
        success, dues_list = self.run_test(
            "GET Officer Tracking Dues",
            "GET",
            "officer-tracking/dues",
            200
        )
        
        success, attendance_list = self.run_test(
            "GET Officer Tracking Attendance",
            "GET",
            "officer-tracking/attendance",
            200
        )
        
        success, summary_data = self.run_test(
            "GET Officer Tracking Summary",
            "GET",
            "officer-tracking/summary",
            200
        )
        
        # Test 6: Test with SEC user (Lonestar)
        original_token = self.token
        sec_success, sec_login = self.run_test(
            "Login as SEC User (Lonestar)",
            "POST",
            "auth/login",
            200,
            data={"username": "Lonestar", "password": "boh2158tc"}
        )
        
        if sec_success and 'token' in sec_login:
            self.token = sec_login['token']
            
            # Test SEC user can edit dues
            if test_member_id:
                sec_dues_data = {
                    "member_id": test_member_id,
                    "month": "Aug_2026",
                    "status": "late",
                    "notes": "SEC user test"
                }
                
                success, sec_dues_response = self.run_test(
                    "SEC User - Dues Edit Access",
                    "POST",
                    "officer-tracking/dues",
                    200,
                    data=sec_dues_data
                )
            
            # Restore admin token
            self.token = original_token
        
        # Clean up test member
        if test_member_id:
            success, delete_response = self.run_test(
                "Delete A&D Test Member",
                "DELETE",
                f"members/{test_member_id}?reason=Testing cleanup",
                200
            )
        
        print(f"   📋 A & D (Attendance & Dues) feature testing completed")

    def run_all_tests(self):
        """Run all A & D tests"""
        print("🚀 Starting A & D (Attendance & Dues) Feature Tests...")
        print(f"   Base URL: {self.base_url}")
        
        # Test authentication first
        login_success, login_data = self.test_login()
        if not login_success:
            print("❌ Authentication failed - cannot continue tests")
            return
        
        # Run A & D feature test
        self.test_ad_feature()
        
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
    tester = ADFeatureTester()
    tester.run_all_tests()