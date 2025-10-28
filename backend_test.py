import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        """Test login and get token - try multiple credentials if first fails"""
        print(f"\n🔐 Testing Authentication...")
        
        # Try multiple credential combinations
        credentials_to_try = [
            ("testadmin", "testpass123"),  # Our test admin
            ("admin", "admin123"),
            ("Admin", "admin123"),
            ("admin", "password"),
            ("Admin", "password"),
            ("testuser", "password"),
            ("Lonestar", "password"),
            ("Lonestar ", "password")  # Note the space
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
                print(f"   Token obtained: {self.token[:20]}...")
                return True, response
        
        print("   ❌ All login attempts failed")
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
            
            # Verify meeting_attendance structure
            if 'meeting_attendance' in created_member:
                attendance = created_member['meeting_attendance']
                if 'year' in attendance and 'meetings' in attendance:
                    meetings = attendance['meetings']
                    if len(meetings) == 24:
                        self.log_test("Member Created with Correct Meeting Attendance Structure", True, f"24 meetings found for year {attendance['year']}")
                    else:
                        self.log_test("Member Created with Correct Meeting Attendance Structure", False, f"Expected 24 meetings, got {len(meetings)}")
                else:
                    self.log_test("Member Created with Correct Meeting Attendance Structure", False, "Missing year or meetings in attendance")
            else:
                self.log_test("Member Created with Correct Meeting Attendance Structure", False, "No meeting_attendance field found")
        
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

    def test_meeting_attendance(self):
        """Test meeting attendance functionality with notes for Excused/Unexcused absences"""
        print(f"\n📅 Testing Meeting Attendance with Notes...")
        
        # Create a test member first
        test_member = {
            "chapter": "National",
            "title": "Prez",
            "handle": "AttendanceTestRider",
            "name": "Attendance Test User",
            "email": "attendance@example.com",
            "phone": "+1-555-0124",
            "address": "124 Test Street, Test City, TC 12345"
        }
        
        success, created_member = self.run_test(
            "Create Member for Attendance Testing",
            "POST",
            "members",
            201,
            data=test_member
        )
        
        member_id = None
        if success and 'id' in created_member:
            member_id = created_member['id']
            print(f"   Created member ID for attendance testing: {member_id}")
        else:
            print("❌ Failed to create member for attendance testing")
            return None
        
        # Test updating meeting attendance with different statuses and notes
        attendance_data = {
            "year": 2025,
            "meetings": [
                {"status": 0, "note": "Unexcused absence - no call"},  # Absent with note
                {"status": 1, "note": ""},  # Present
                {"status": 2, "note": "Family emergency"},  # Excused with note
                {"status": 0, "note": "Work conflict"},  # Another absent with note
                {"status": 1, "note": ""},  # Present
                {"status": 2, "note": "Medical appointment"},  # Another excused with note
            ] + [{"status": 0, "note": ""} for _ in range(18)]  # Fill remaining 18 meetings
        }
        
        success, updated_member = self.run_test(
            "Update Member Attendance with Notes",
            "PUT",
            f"members/{member_id}/attendance",
            200,
            data=attendance_data
        )
        
        if success:
            # Verify the attendance data was saved correctly
            success, member = self.run_test(
                "Get Member to Verify Attendance",
                "GET",
                f"members/{member_id}",
                200
            )
            
            if success and 'meeting_attendance' in member:
                attendance = member['meeting_attendance']
                meetings = attendance.get('meetings', [])
                
                # Check if we have 24 meetings
                if len(meetings) == 24:
                    self.log_test("Meeting Attendance - Correct Number of Meetings", True, "24 meetings found")
                else:
                    self.log_test("Meeting Attendance - Correct Number of Meetings", False, f"Expected 24, got {len(meetings)}")
                
                # Check specific meeting statuses and notes
                test_cases = [
                    (0, 0, "Unexcused absence - no call", "Absent with note"),
                    (1, 1, "", "Present without note"),
                    (2, 2, "Family emergency", "Excused with note"),
                    (3, 0, "Work conflict", "Absent with note"),
                    (4, 1, "", "Present without note"),
                    (5, 2, "Medical appointment", "Excused with note")
                ]
                
                for meeting_idx, expected_status, expected_note, description in test_cases:
                    if meeting_idx < len(meetings):
                        meeting = meetings[meeting_idx]
                        actual_status = meeting.get('status', -1)
                        actual_note = meeting.get('note', '')
                        
                        if actual_status == expected_status and actual_note == expected_note:
                            self.log_test(f"Meeting {meeting_idx + 1} - {description}", True, f"Status: {actual_status}, Note: '{actual_note}'")
                        else:
                            self.log_test(f"Meeting {meeting_idx + 1} - {description}", False, f"Expected status {expected_status} with note '{expected_note}', got status {actual_status} with note '{actual_note}'")
                    else:
                        self.log_test(f"Meeting {meeting_idx + 1} - {description}", False, "Meeting not found")
                
                # Test that notes work for both Excused (status=2) and Unexcused (status=0) absences
                excused_with_notes = [m for m in meetings if m.get('status') == 2 and m.get('note', '').strip()]
                unexcused_with_notes = [m for m in meetings if m.get('status') == 0 and m.get('note', '').strip()]
                
                if len(excused_with_notes) >= 2:
                    self.log_test("Notes for Excused Absences", True, f"Found {len(excused_with_notes)} excused absences with notes")
                else:
                    self.log_test("Notes for Excused Absences", False, f"Expected at least 2 excused absences with notes, found {len(excused_with_notes)}")
                
                if len(unexcused_with_notes) >= 2:
                    self.log_test("Notes for Unexcused Absences", True, f"Found {len(unexcused_with_notes)} unexcused absences with notes")
                else:
                    self.log_test("Notes for Unexcused Absences", False, f"Expected at least 2 unexcused absences with notes, found {len(unexcused_with_notes)}")
            else:
                self.log_test("Verify Attendance Data Saved", False, "No meeting_attendance found in member data")
        
        # Test CSV export includes meeting attendance data
        success, csv_data = self.run_test(
            "CSV Export with Meeting Attendance",
            "GET",
            "members/export/csv",
            200
        )
        
        if success and isinstance(csv_data, str):
            # Check if CSV contains meeting attendance columns
            csv_lines = csv_data.split('\n')
            if len(csv_lines) > 0:
                header = csv_lines[0]
                # Check for meeting attendance columns (Jan-1st, Jan-3rd, etc.)
                meeting_columns = ['Jan-1st', 'Jan-3rd', 'Feb-1st', 'Feb-3rd', 'Mar-1st', 'Mar-3rd']
                found_columns = [col for col in meeting_columns if col in header]
                
                if len(found_columns) >= 6:
                    self.log_test("CSV Export - Meeting Attendance Columns", True, f"Found meeting columns: {found_columns}")
                else:
                    self.log_test("CSV Export - Meeting Attendance Columns", False, f"Expected meeting columns, found: {found_columns}")
                
                # Check if attendance year is included
                if 'Attendance Year' in header:
                    self.log_test("CSV Export - Attendance Year Column", True, "Attendance Year column found")
                else:
                    self.log_test("CSV Export - Attendance Year Column", False, "Attendance Year column not found")
            else:
                self.log_test("CSV Export - Meeting Attendance Data", False, "Empty CSV response")
        
        # Clean up test member
        if member_id:
            success, delete_response = self.run_test(
                "Delete Attendance Test Member",
                "DELETE",
                f"members/{member_id}",
                200
            )
        
        return member_id

    def test_permissions_meeting_attendance(self):
        """Test that meeting_attendance permission is respected"""
        print(f"\n🔐 Testing Meeting Attendance Permissions...")
        
        # Create a user with meeting_attendance permission
        test_user_with_permission = {
            "username": f"attendanceuser_{datetime.now().strftime('%H%M%S')}",
            "password": "testpass123",
            "role": "user",
            "permissions": {
                "basic_info": True,
                "email": False,
                "phone": False,
                "address": False,
                "dues_tracking": False,
                "meeting_attendance": True,
                "admin_actions": False
            }
        }
        
        success, created_user = self.run_test(
            "Create User with Meeting Attendance Permission",
            "POST",
            "users",
            201,
            data=test_user_with_permission
        )
        
        if not success:
            return
        
        # Create a user without meeting_attendance permission
        test_user_without_permission = {
            "username": f"noattendanceuser_{datetime.now().strftime('%H%M%S')}",
            "password": "testpass123",
            "role": "user",
            "permissions": {
                "basic_info": True,
                "email": False,
                "phone": False,
                "address": False,
                "dues_tracking": False,
                "meeting_attendance": False,
                "admin_actions": False
            }
        }
        
        success, created_user_no_perm = self.run_test(
            "Create User without Meeting Attendance Permission",
            "POST",
            "users",
            201,
            data=test_user_without_permission
        )
        
        # Test CSV export with meeting_attendance permission
        original_token = self.token
        
        # Login as user with permission
        success, login_response = self.run_test(
            "Login User with Meeting Attendance Permission",
            "POST",
            "auth/login",
            200,
            data={"username": test_user_with_permission["username"], "password": test_user_with_permission["password"]}
        )
        
        if success and 'token' in login_response:
            self.token = login_response['token']
            
            # Test CSV export (should include meeting attendance data)
            success, csv_data = self.run_test(
                "CSV Export with Meeting Attendance Permission",
                "GET",
                "members/export/csv",
                200
            )
            
            if success and isinstance(csv_data, str):
                header = csv_data.split('\n')[0] if csv_data else ""
                if 'Jan-1st' in header or 'Attendance Year' in header:
                    self.log_test("Meeting Attendance Permission - CSV Includes Attendance", True, "Meeting attendance data found in CSV")
                else:
                    self.log_test("Meeting Attendance Permission - CSV Includes Attendance", False, "Meeting attendance data not found in CSV")
        
        # Login as user without permission
        if created_user_no_perm:
            success, login_response = self.run_test(
                "Login User without Meeting Attendance Permission",
                "POST",
                "auth/login",
                200,
                data={"username": test_user_without_permission["username"], "password": test_user_without_permission["password"]}
            )
            
            if success and 'token' in login_response:
                self.token = login_response['token']
                
                # Test CSV export (should not include meeting attendance data)
                success, csv_data = self.run_test(
                    "CSV Export without Meeting Attendance Permission",
                    "GET",
                    "members/export/csv",
                    200
                )
                
                if success and isinstance(csv_data, str):
                    header = csv_data.split('\n')[0] if csv_data else ""
                    if 'Jan-1st' not in header and 'Attendance Year' not in header:
                        self.log_test("Meeting Attendance Permission - CSV Excludes Attendance", True, "Meeting attendance data correctly excluded from CSV")
                    else:
                        self.log_test("Meeting Attendance Permission - CSV Excludes Attendance", False, "Meeting attendance data incorrectly included in CSV")
        
        # Restore admin token
        self.token = original_token
        
        # Clean up test users
        if created_user and 'id' in created_user:
            success, response = self.run_test(
                "Delete User with Meeting Attendance Permission",
                "DELETE",
                f"users/{created_user['id']}",
                200
            )
        
        if created_user_no_perm and 'id' in created_user_no_perm:
            success, response = self.run_test(
                "Delete User without Meeting Attendance Permission",
                "DELETE",
                f"users/{created_user_no_perm['id']}",
                200
            )

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
        
        # Test accessing members without token (403 is also acceptable)
        success, response = self.run_test(
            "Access Members Without Token",
            "GET",
            "members",
            403
        )
        
        # Test creating member without token (403 is also acceptable)
        success, response = self.run_test(
            "Create Member Without Token",
            "POST",
            "members",
            403,
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
        
        # Test meeting attendance functionality (Priority Test)
        self.test_meeting_attendance()
        
        # Test meeting attendance permissions (Priority Test)
        self.test_permissions_meeting_attendance()
        
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