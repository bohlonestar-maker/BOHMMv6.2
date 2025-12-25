#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class QuarterlyReportsAPITester:
    def __init__(self, base_url="https://flexmeet.preview.emergentagent.com/api"):
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

    def test_login(self, username="admin", password="admin123"):
        """Test login and get token"""
        print(f"\n🔐 Testing Authentication...")
        
        success, response = self.run_test(
            f"Login as {username}",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            print(f"   ✅ Successful login with {username}")
            print(f"   Token obtained: {self.token[:20]}...")
            return True, response
        
        print("   ❌ Login failed")
        return False, {}

    def test_quarterly_reports(self):
        """Test quarterly reports endpoints - NEW FEATURE"""
        print(f"\n📊 Testing Quarterly Reports Functionality...")
        
        # First, create some test data for reports
        # Create a test member with meeting attendance and dues data
        test_member = {
            "chapter": "National",
            "title": "Prez",
            "handle": "ReportTestRider",
            "name": "Report Test Member",
            "email": "reporttest@example.com",
            "phone": "555-0199",
            "address": "199 Report Street, Report City, RC 12345",
            "meeting_attendance": {
                "2025": [
                    {"date": "2025-10-01", "status": 1, "note": ""},
                    {"date": "2025-10-15", "status": 2, "note": "sick"},
                    {"date": "2025-11-01", "status": 1, "note": ""},
                    {"date": "2025-11-15", "status": 0, "note": "no show"},
                    {"date": "2025-12-01", "status": 1, "note": ""},
                    {"date": "2025-12-15", "status": 1, "note": ""}
                ]
            },
            "dues": {
                "2025": [
                    {"status": "paid", "note": ""},
                    {"status": "paid", "note": ""},
                    {"status": "paid", "note": ""},
                    {"status": "paid", "note": ""},
                    {"status": "paid", "note": ""},
                    {"status": "paid", "note": ""},
                    {"status": "paid", "note": ""},
                    {"status": "paid", "note": ""},
                    {"status": "paid", "note": ""},
                    {"status": "paid", "note": ""},  # October
                    {"status": "paid", "note": ""},  # November
                    {"status": "unpaid", "note": ""}  # December
                ]
            }
        }
        
        success, created_member = self.run_test(
            "Create Member for Report Testing",
            "POST",
            "members",
            201,
            data=test_member
        )
        
        member_id = None
        if success and 'id' in created_member:
            member_id = created_member['id']
            print(f"   Created test member ID: {member_id}")
        else:
            print("❌ Failed to create test member - continuing with existing data")
        
        # Create a test prospect with meeting attendance
        test_prospect = {
            "handle": "ReportTestProspect",
            "name": "Report Test Prospect",
            "email": "prospectreport@example.com",
            "phone": "555-0299",
            "address": "299 Prospect Street",
            "meeting_attendance": {
                "2025": [
                    {"date": "2025-10-01", "status": 1, "note": ""},
                    {"date": "2025-10-15", "status": 0, "note": "missed"},
                    {"date": "2025-11-01", "status": 1, "note": ""},
                    {"date": "2025-11-15", "status": 2, "note": "excused"},
                    {"date": "2025-12-01", "status": 1, "note": ""},
                    {"date": "2025-12-15", "status": 1, "note": ""}
                ]
            }
        }
        
        success, created_prospect = self.run_test(
            "Create Prospect for Report Testing",
            "POST",
            "prospects",
            201,
            data=test_prospect
        )
        
        prospect_id = None
        if success and 'id' in created_prospect:
            prospect_id = created_prospect['id']
            print(f"   Created test prospect ID: {prospect_id}")
        
        # Test 1: Member Attendance Quarterly Report
        success, attendance_report = self.run_test(
            "Member Attendance Quarterly Report",
            "GET",
            "reports/attendance/quarterly?year=2025&quarter=4&chapter=National",
            200
        )
        
        if success and isinstance(attendance_report, str):
            # Check if it's CSV format
            lines = attendance_report.strip().split('\n')
            if len(lines) > 0:
                header = lines[0]
                expected_columns = ['Chapter', 'Title', 'Handle', 'Name', 'Total', 'Present', 'Excused', 'Absent', 'Attendance %']
                found_columns = [col for col in expected_columns if col in header]
                
                if len(found_columns) >= 5:  # At least basic columns
                    self.log_test("Member Attendance Report - CSV Format", True, f"Found columns: {found_columns}")
                    
                    # Check for month columns (Oct, Nov, Dec for Q4)
                    month_columns = ['Oct', 'Nov', 'Dec']
                    found_months = [month for month in month_columns if month in header]
                    
                    if len(found_months) >= 3:
                        self.log_test("Member Attendance Report - Month Columns", True, f"Found months: {found_months}")
                    else:
                        self.log_test("Member Attendance Report - Month Columns", False, f"Expected Q4 months, found: {found_months}")
                else:
                    self.log_test("Member Attendance Report - CSV Format", False, f"Missing expected columns. Found: {found_columns}")
            else:
                self.log_test("Member Attendance Report - CSV Format", False, "Empty response")
        
        # Test 2: Member Dues Quarterly Report
        success, dues_report = self.run_test(
            "Member Dues Quarterly Report",
            "GET",
            "reports/dues/quarterly?year=2025&quarter=4&chapter=All",
            200
        )
        
        if success and isinstance(dues_report, str):
            lines = dues_report.strip().split('\n')
            if len(lines) > 0:
                header = lines[0]
                expected_columns = ['Chapter', 'Title', 'Handle', 'Name', 'Quarter Paid', 'Quarter Late', 'Quarter Unpaid']
                found_columns = [col for col in expected_columns if col in header]
                
                if len(found_columns) >= 5:
                    self.log_test("Member Dues Report - CSV Format", True, f"Found columns: {found_columns}")
                    
                    # Check for month columns
                    month_columns = ['Oct', 'Nov', 'Dec']
                    found_months = [month for month in month_columns if month in header]
                    
                    if len(found_months) >= 3:
                        self.log_test("Member Dues Report - Month Columns", True, f"Found months: {found_months}")
                    else:
                        self.log_test("Member Dues Report - Month Columns", False, f"Expected Q4 months, found: {found_months}")
                else:
                    self.log_test("Member Dues Report - CSV Format", False, f"Missing expected columns. Found: {found_columns}")
        
        # Test 3: Prospect Attendance Quarterly Report
        success, prospect_report = self.run_test(
            "Prospect Attendance Quarterly Report",
            "GET",
            "reports/prospects/attendance/quarterly?year=2025&quarter=4",
            200
        )
        
        if success and isinstance(prospect_report, str):
            lines = prospect_report.strip().split('\n')
            if len(lines) > 0:
                header = lines[0]
                expected_columns = ['Handle', 'Name', 'Email', 'Phone', 'Total', 'Present', 'Excused', 'Absent', 'Attendance %']
                found_columns = [col for col in expected_columns if col in header]
                
                if len(found_columns) >= 5:
                    self.log_test("Prospect Attendance Report - CSV Format", True, f"Found columns: {found_columns}")
                    
                    # Check for month columns
                    month_columns = ['Oct', 'Nov', 'Dec']
                    found_months = [month for month in month_columns if month in header]
                    
                    if len(found_months) >= 3:
                        self.log_test("Prospect Attendance Report - Month Columns", True, f"Found months: {found_months}")
                    else:
                        self.log_test("Prospect Attendance Report - Month Columns", False, f"Expected Q4 months, found: {found_months}")
                else:
                    self.log_test("Prospect Attendance Report - CSV Format", False, f"Missing expected columns. Found: {found_columns}")
        
        # Test 4: Test different quarters
        success, q1_report = self.run_test(
            "Member Attendance Q1 Report",
            "GET",
            "reports/attendance/quarterly?year=2025&quarter=1&chapter=All",
            200
        )
        
        if success and isinstance(q1_report, str):
            header = q1_report.split('\n')[0] if q1_report else ""
            q1_months = ['Jan', 'Feb', 'Mar']
            found_q1_months = [month for month in q1_months if month in header]
            
            if len(found_q1_months) >= 3:
                self.log_test("Q1 Report - Correct Months", True, f"Found Q1 months: {found_q1_months}")
            else:
                self.log_test("Q1 Report - Correct Months", False, f"Expected Q1 months, found: {found_q1_months}")
        
        # Test 5: Test different chapters
        success, ad_report = self.run_test(
            "Member Attendance AD Chapter Report",
            "GET",
            "reports/attendance/quarterly?year=2025&quarter=4&chapter=AD",
            200
        )
        
        # Test 6: Test invalid parameters
        success, invalid_quarter = self.run_test(
            "Invalid Quarter Parameter (Should Fail)",
            "GET",
            "reports/attendance/quarterly?year=2025&quarter=5&chapter=National",
            400
        )
        
        success, invalid_year = self.run_test(
            "Invalid Year Parameter (Should Fail)",
            "GET",
            "reports/attendance/quarterly?year=abc&quarter=1&chapter=National",
            400
        )
        
        # Test 7: Test unauthorized access (without admin token)
        original_token = self.token
        self.token = None
        
        success, unauthorized = self.run_test(
            "Quarterly Reports Without Auth (Should Fail)",
            "GET",
            "reports/attendance/quarterly?year=2025&quarter=4&chapter=National",
            403
        )
        
        self.token = original_token
        
        print(f"   📊 Quarterly reports testing completed")
        return member_id, prospect_id

    def test_flexible_meeting_attendance(self):
        """Test new flexible meeting attendance format - NEW FEATURE"""
        print(f"\n📅 Testing Flexible Meeting Attendance Format...")
        
        # Create a test member for flexible attendance testing
        test_member = {
            "chapter": "National",
            "title": "Member",
            "handle": "FlexAttendanceTest",
            "name": "Flexible Attendance Test",
            "email": "flexattendance@example.com",
            "phone": "555-0399",
            "address": "399 Flex Street"
        }
        
        success, created_member = self.run_test(
            "Create Member for Flexible Attendance Testing",
            "POST",
            "members",
            201,
            data=test_member
        )
        
        member_id = None
        if success and 'id' in created_member:
            member_id = created_member['id']
            print(f"   Created test member ID: {member_id}")
        else:
            print("❌ Failed to create test member - cannot continue flexible attendance tests")
            return
        
        # Test 1: Update member with new flexible meeting attendance format
        flexible_attendance = {
            "meeting_attendance": {
                "2025": [
                    {"date": "2025-01-15", "status": 1, "note": ""},
                    {"date": "2025-01-29", "status": 0, "note": "sick"},
                    {"date": "2025-02-12", "status": 2, "note": "work conflict"},
                    {"date": "2025-02-26", "status": 1, "note": ""},
                    {"date": "2025-03-12", "status": 1, "note": ""},
                    {"date": "2025-03-26", "status": 0, "note": ""},
                    {"date": "2025-04-09", "status": 2, "note": "family emergency"},
                    {"date": "2025-04-23", "status": 1, "note": ""}
                ]
            }
        }
        
        success, updated_member = self.run_test(
            "Update Member with Flexible Attendance Format",
            "PUT",
            f"members/{member_id}",
            200,
            data=flexible_attendance
        )
        
        if success:
            # Verify the flexible format was saved correctly
            success, member = self.run_test(
                "Get Member to Verify Flexible Attendance",
                "GET",
                f"members/{member_id}",
                200
            )
            
            if success and 'meeting_attendance' in member:
                attendance = member['meeting_attendance']
                
                # Check if it's the new flexible format (year-based with date objects)
                if '2025' in attendance and isinstance(attendance['2025'], list):
                    meetings = attendance['2025']
                    self.log_test("Flexible Attendance - New Format Saved", True, f"Found {len(meetings)} meetings in 2025")
                    
                    # Verify specific meeting data
                    if len(meetings) >= 8:
                        # Check first meeting
                        first_meeting = meetings[0]
                        if (first_meeting.get('date') == '2025-01-15' and 
                            first_meeting.get('status') == 1 and 
                            first_meeting.get('note') == ''):
                            self.log_test("Flexible Attendance - First Meeting Data", True, "Date, status, and note correct")
                        else:
                            self.log_test("Flexible Attendance - First Meeting Data", False, f"Expected date=2025-01-15, status=1, note='', got {first_meeting}")
                        
                        # Check meeting with note
                        second_meeting = meetings[1]
                        if (second_meeting.get('date') == '2025-01-29' and 
                            second_meeting.get('status') == 0 and 
                            second_meeting.get('note') == 'sick'):
                            self.log_test("Flexible Attendance - Meeting with Note", True, "Absent meeting with note saved correctly")
                        else:
                            self.log_test("Flexible Attendance - Meeting with Note", False, f"Expected date=2025-01-29, status=0, note='sick', got {second_meeting}")
                        
                        # Check excused meeting
                        third_meeting = meetings[2]
                        if (third_meeting.get('date') == '2025-02-12' and 
                            third_meeting.get('status') == 2 and 
                            third_meeting.get('note') == 'work conflict'):
                            self.log_test("Flexible Attendance - Excused Meeting", True, "Excused meeting with note saved correctly")
                        else:
                            self.log_test("Flexible Attendance - Excused Meeting", False, f"Expected date=2025-02-12, status=2, note='work conflict', got {third_meeting}")
                    else:
                        self.log_test("Flexible Attendance - Meeting Count", False, f"Expected at least 8 meetings, got {len(meetings)}")
                else:
                    self.log_test("Flexible Attendance - New Format Saved", False, f"Expected new format with 2025 key, got {attendance}")
            else:
                self.log_test("Flexible Attendance - Data Retrieval", False, "No meeting_attendance found in member")
        
        # Test 2: Test with prospect (should work the same way)
        test_prospect = {
            "handle": "FlexProspectTest",
            "name": "Flexible Prospect Test",
            "email": "flexprospect@example.com",
            "phone": "555-0499",
            "address": "499 Prospect Flex Street"
        }
        
        success, created_prospect = self.run_test(
            "Create Prospect for Flexible Attendance Testing",
            "POST",
            "prospects",
            201,
            data=test_prospect
        )
        
        prospect_id = None
        if success and 'id' in created_prospect:
            prospect_id = created_prospect['id']
            
            # Update prospect with flexible attendance
            prospect_attendance = {
                "meeting_attendance": {
                    "2025": [
                        {"date": "2025-01-15", "status": 1, "note": ""},
                        {"date": "2025-01-29", "status": 2, "note": "family event"},
                        {"date": "2025-02-12", "status": 1, "note": ""}
                    ]
                }
            }
            
            success, updated_prospect = self.run_test(
                "Update Prospect with Flexible Attendance",
                "PUT",
                f"prospects/{prospect_id}",
                200,
                data=prospect_attendance
            )
            
            if success:
                success, prospect = self.run_test(
                    "Verify Prospect Flexible Attendance",
                    "GET",
                    f"prospects/{prospect_id}",
                    200
                )
                
                if success and 'meeting_attendance' in prospect:
                    attendance = prospect['meeting_attendance']
                    if '2025' in attendance and len(attendance['2025']) == 3:
                        self.log_test("Flexible Attendance - Prospect Support", True, f"Prospect has {len(attendance['2025'])} meetings in 2025")
                    else:
                        self.log_test("Flexible Attendance - Prospect Support", False, f"Expected 3 meetings for prospect, got {attendance}")
        
        print(f"   📅 Flexible meeting attendance testing completed")
        return member_id, prospect_id

    def print_summary(self):
        """Print test summary"""
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("✅ All tests passed!")
        else:
            print("⚠️  Some tests failed - check details above")

    def run_tests(self):
        """Run all tests"""
        print("🚀 Starting Quarterly Reports and Flexible Meeting Attendance Tests...")
        print(f"   Base URL: {self.base_url}")
        print(f"   Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test authentication first
        success, response = self.test_login()
        if not success:
            print("❌ Authentication failed - cannot continue tests")
            return
        
        # Run the new tests
        self.test_quarterly_reports()
        self.test_flexible_meeting_attendance()
        
        # Print final summary
        self.print_summary()

if __name__ == "__main__":
    tester = QuarterlyReportsAPITester()
    tester.run_tests()