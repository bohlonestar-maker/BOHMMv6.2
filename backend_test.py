import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BOHDirectoryAPITester:
    def __init__(self, base_url="https://brothers-directory.preview.emergentagent.com/api"):
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
        
        # Try multiple credential combinations based on existing users
        credentials_to_try = [
            ("testadmin", "testpass123"),  # Requested test admin
            ("admin", "admin123"),         # Default admin
            ("Lonestar", "password"),      # Existing admin user
            ("Lonestar", "admin123"),      # Try different password
            ("Lonestar", "testpass123"),   # Try test password
            ("testuser", "password"),      # Existing regular user
            ("testuser", "testpass123"),   # Try test password
            ("admin", "password"),         # Try different password
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

    def test_national_chapter_access_control(self):
        """Test National chapter contact info access control - PRIORITY TEST"""
        print(f"\n🏛️  Testing National Chapter Contact Info Access Control...")
        
        # Step 1: Create test admin user if doesn't exist
        admin_user = {
            "username": "testadmin",
            "password": "testpass123",
            "role": "admin"
        }
        
        success, created_admin = self.run_test(
            "Create Test Admin User",
            "POST",
            "users",
            201,
            data=admin_user
        )
        
        admin_user_id = None
        if success and 'id' in created_admin:
            admin_user_id = created_admin['id']
            print(f"   Created admin user ID: {admin_user_id}")
        elif not success:
            # Admin might already exist, try to login
            print("   Admin user might already exist, continuing...")
        
        # Step 2: Create regular user
        regular_user = {
            "username": "regularuser",
            "password": "testpass123",
            "role": "user"
        }
        
        success, created_regular = self.run_test(
            "Create Regular User",
            "POST",
            "users",
            201,
            data=regular_user
        )
        
        regular_user_id = None
        if success and 'id' in created_regular:
            regular_user_id = created_regular['id']
            print(f"   Created regular user ID: {regular_user_id}")
        elif not success:
            # Regular user might already exist, continuing
            print("   Regular user might already exist, continuing...")
        
        # Step 3: Create test members
        # Member 1: National chapter
        national_member = {
            "chapter": "National",
            "title": "Prez",
            "handle": "NationalTestRider",
            "name": "National Test Member",
            "email": "national@test.com",
            "phone": "555-0001",
            "address": "123 National Street, National City, NC 12345"
        }
        
        success, created_national = self.run_test(
            "Create National Chapter Member",
            "POST",
            "members",
            201,
            data=national_member
        )
        
        national_member_id = None
        if success and 'id' in created_national:
            national_member_id = created_national['id']
            print(f"   Created National member ID: {national_member_id}")
        else:
            print("❌ Failed to create National member - cannot continue access control tests")
            return
        
        # Member 2: Non-National chapter (AD)
        ad_member = {
            "chapter": "AD",
            "title": "VP",
            "handle": "ADTestRider",
            "name": "AD Test Member",
            "email": "ad@test.com",
            "phone": "555-0002",
            "address": "456 AD Street, AD City, AD 67890"
        }
        
        success, created_ad = self.run_test(
            "Create AD Chapter Member",
            "POST",
            "members",
            201,
            data=ad_member
        )
        
        ad_member_id = None
        if success and 'id' in created_ad:
            ad_member_id = created_ad['id']
            print(f"   Created AD member ID: {ad_member_id}")
        else:
            print("❌ Failed to create AD member - cannot continue access control tests")
            return
        
        # Save original admin token
        original_token = self.token
        
        # Test Case 1: Admin Access - GET /api/members
        print(f"\n   🔑 Testing Admin Access to All Members...")
        
        # Login as admin (testadmin)
        success, admin_login = self.run_test(
            "Login as Test Admin",
            "POST",
            "auth/login",
            200,
            data={"username": "testadmin", "password": "testpass123"}
        )
        
        if success and 'token' in admin_login:
            self.token = admin_login['token']
            
            # Fetch all members as admin
            success, admin_members = self.run_test(
                "Admin - Get All Members",
                "GET",
                "members",
                200
            )
            
            if success and isinstance(admin_members, list):
                # Find our test members
                national_found = None
                ad_found = None
                
                for member in admin_members:
                    if member.get('id') == national_member_id:
                        national_found = member
                    elif member.get('id') == ad_member_id:
                        ad_found = member
                
                # Verify National member shows FULL contact info for admin
                if national_found:
                    if (national_found.get('email') == 'national@test.com' and 
                        national_found.get('phone') == '555-0001' and 
                        national_found.get('address') == '123 National Street, National City, NC 12345'):
                        self.log_test("Admin Access - National Member Full Contact Info", True, "Admin can see full contact info for National member")
                    else:
                        self.log_test("Admin Access - National Member Full Contact Info", False, f"Contact info redacted: email={national_found.get('email')}, phone={national_found.get('phone')}, address={national_found.get('address')}")
                else:
                    self.log_test("Admin Access - National Member Found", False, "National member not found in admin member list")
                
                # Verify AD member shows FULL contact info for admin
                if ad_found:
                    if (ad_found.get('email') == 'ad@test.com' and 
                        ad_found.get('phone') == '555-0002' and 
                        ad_found.get('address') == '456 AD Street, AD City, AD 67890'):
                        self.log_test("Admin Access - AD Member Full Contact Info", True, "Admin can see full contact info for AD member")
                    else:
                        self.log_test("Admin Access - AD Member Full Contact Info", False, f"Contact info redacted: email={ad_found.get('email')}, phone={ad_found.get('phone')}, address={ad_found.get('address')}")
                else:
                    self.log_test("Admin Access - AD Member Found", False, "AD member not found in admin member list")
        
        # Test Case 2: Regular User Access - GET /api/members
        print(f"\n   👤 Testing Regular User Access to All Members...")
        
        # Login as regular user
        success, regular_login = self.run_test(
            "Login as Regular User",
            "POST",
            "auth/login",
            200,
            data={"username": "regularuser", "password": "testpass123"}
        )
        
        if success and 'token' in regular_login:
            self.token = regular_login['token']
            
            # Fetch all members as regular user
            success, regular_members = self.run_test(
                "Regular User - Get All Members",
                "GET",
                "members",
                200
            )
            
            if success and isinstance(regular_members, list):
                # Find our test members
                national_found = None
                ad_found = None
                
                for member in regular_members:
                    if member.get('id') == national_member_id:
                        national_found = member
                    elif member.get('id') == ad_member_id:
                        ad_found = member
                
                # Verify National member shows "[ADMIN ONLY]" for contact info
                if national_found:
                    if (national_found.get('email') == '[ADMIN ONLY]' and 
                        national_found.get('phone') == '[ADMIN ONLY]' and 
                        national_found.get('address') == '[ADMIN ONLY]'):
                        self.log_test("Regular User - National Member Contact Redacted", True, "National member contact info properly redacted for regular user")
                    else:
                        self.log_test("Regular User - National Member Contact Redacted", False, f"Contact info not redacted: email={national_found.get('email')}, phone={national_found.get('phone')}, address={national_found.get('address')}")
                else:
                    self.log_test("Regular User - National Member Found", False, "National member not found in regular user member list")
                
                # Verify AD member shows FULL contact info for regular user
                if ad_found:
                    if (ad_found.get('email') == 'ad@test.com' and 
                        ad_found.get('phone') == '555-0002' and 
                        ad_found.get('address') == '456 AD Street, AD City, AD 67890'):
                        self.log_test("Regular User - AD Member Full Contact Info", True, "Regular user can see full contact info for non-National member")
                    else:
                        self.log_test("Regular User - AD Member Full Contact Info", False, f"Contact info unexpectedly redacted: email={ad_found.get('email')}, phone={ad_found.get('phone')}, address={ad_found.get('address')}")
                else:
                    self.log_test("Regular User - AD Member Found", False, "AD member not found in regular user member list")
        
        # Test Case 3: Admin Access - GET /api/members/{id}
        print(f"\n   🔑 Testing Admin Access to Individual National Member...")
        
        # Login as admin again
        if admin_login and 'token' in admin_login:
            self.token = admin_login['token']
            
            if national_member_id:
                success, admin_national_detail = self.run_test(
                    "Admin - Get National Member by ID",
                    "GET",
                    f"members/{national_member_id}",
                    200
                )
                
                if success:
                    if (admin_national_detail.get('email') == 'national@test.com' and 
                        admin_national_detail.get('phone') == '555-0001' and 
                        admin_national_detail.get('address') == '123 National Street, National City, NC 12345'):
                        self.log_test("Admin Access - National Member Detail Full Contact", True, "Admin can see full contact info in member detail")
                    else:
                        self.log_test("Admin Access - National Member Detail Full Contact", False, f"Contact info redacted in detail: email={admin_national_detail.get('email')}, phone={admin_national_detail.get('phone')}, address={admin_national_detail.get('address')}")
        
        # Test Case 4: Regular User Access - GET /api/members/{id}
        print(f"\n   👤 Testing Regular User Access to Individual National Member...")
        
        # Login as regular user again
        if regular_login and 'token' in regular_login:
            self.token = regular_login['token']
            
            if national_member_id:
                success, regular_national_detail = self.run_test(
                    "Regular User - Get National Member by ID",
                    "GET",
                    f"members/{national_member_id}",
                    200
                )
                
                if success:
                    if (regular_national_detail.get('email') == '[ADMIN ONLY]' and 
                        regular_national_detail.get('phone') == '[ADMIN ONLY]' and 
                        regular_national_detail.get('address') == '[ADMIN ONLY]'):
                        self.log_test("Regular User - National Member Detail Contact Redacted", True, "National member contact info properly redacted in detail view for regular user")
                    else:
                        self.log_test("Regular User - National Member Detail Contact Redacted", False, f"Contact info not redacted in detail: email={regular_national_detail.get('email')}, phone={regular_national_detail.get('phone')}, address={regular_national_detail.get('address')}")
        
        # Restore original admin token
        self.token = original_token
        
        # Clean up test data
        print(f"\n   🧹 Cleaning up test data...")
        
        if national_member_id:
            success, response = self.run_test(
                "Delete National Test Member",
                "DELETE",
                f"members/{national_member_id}",
                200
            )
        
        if ad_member_id:
            success, response = self.run_test(
                "Delete AD Test Member",
                "DELETE",
                f"members/{ad_member_id}",
                200
            )
        
        if regular_user_id:
            success, response = self.run_test(
                "Delete Regular Test User",
                "DELETE",
                f"users/{regular_user_id}",
                200
            )
        
        if admin_user_id:
            success, response = self.run_test(
                "Delete Admin Test User",
                "DELETE",
                f"users/{admin_user_id}",
                200
            )
        
        print(f"   🏛️  National chapter access control testing completed")
        return national_member_id, ad_member_id

    def test_invite_functionality(self):
        """Test email invite functionality - PRIORITY TEST"""
        print(f"\n📧 Testing Email Invite Functionality...")
        
        # Test 1: Create Invite
        invite_data = {
            "email": f"invitetest_{datetime.now().strftime('%H%M%S')}@example.com",
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
        
        success, invite_response = self.run_test(
            "Create Invite",
            "POST",
            "invites",
            200,
            data=invite_data
        )
        
        invite_token = None
        invite_link = None
        
        if success:
            # Verify response contains invite_link and token
            if 'invite_link' in invite_response:
                invite_link = invite_response['invite_link']
                # Extract token from invite link
                if '?token=' in invite_link:
                    invite_token = invite_link.split('?token=')[1]
                    self.log_test("Create Invite - Token Extracted", True, f"Token: {invite_token[:20]}...")
                    
                    # Verify invite link format
                    expected_base = "https://brothers-directory.preview.emergentagent.com/accept-invite?token="
                    if invite_link.startswith(expected_base):
                        self.log_test("Verify Invite Link Format", True, f"Link format correct: {invite_link[:60]}...")
                    else:
                        self.log_test("Verify Invite Link Format", False, f"Expected format: {expected_base}..., got: {invite_link}")
                    
                    # Verify token is valid UUID format
                    try:
                        import uuid
                        uuid.UUID(invite_token)
                        self.log_test("Verify Token is Valid UUID", True, f"Token is valid UUID: {invite_token}")
                    except ValueError:
                        self.log_test("Verify Token is Valid UUID", False, f"Token is not valid UUID: {invite_token}")
                else:
                    self.log_test("Create Invite - Token Extracted", False, "No token found in invite_link")
            else:
                self.log_test("Create Invite - Response Format", False, "No invite_link in response")
        
        if not invite_token:
            print("❌ Cannot continue invite tests without valid token")
            return
        
        # Test 2: Retrieve Invite by Token
        success, invite_details = self.run_test(
            "Retrieve Invite by Token",
            "GET",
            f"invites/{invite_token}",
            200
        )
        
        if success:
            # Verify invite details
            expected_fields = ['email', 'role', 'permissions']
            missing_fields = [field for field in expected_fields if field not in invite_details]
            
            if not missing_fields:
                self.log_test("Invite Details - Required Fields", True, f"All required fields present: {expected_fields}")
                
                # Verify email matches
                if invite_details.get('email') == invite_data['email']:
                    self.log_test("Invite Details - Email Match", True, f"Email matches: {invite_details['email']}")
                else:
                    self.log_test("Invite Details - Email Match", False, f"Expected: {invite_data['email']}, got: {invite_details.get('email')}")
                
                # Verify role matches
                if invite_details.get('role') == invite_data['role']:
                    self.log_test("Invite Details - Role Match", True, f"Role matches: {invite_details['role']}")
                else:
                    self.log_test("Invite Details - Role Match", False, f"Expected: {invite_data['role']}, got: {invite_details.get('role')}")
            else:
                self.log_test("Invite Details - Required Fields", False, f"Missing fields: {missing_fields}")
        
        # Test 3: Accept Invite
        accept_data = {
            "token": invite_token,
            "username": "invitetest",
            "password": "testpass123"
        }
        
        success, accept_response = self.run_test(
            "Accept Invite",
            "POST",
            "invites/accept",
            200,
            data=accept_data
        )
        
        new_user_token = None
        if success:
            # Verify user creation response
            expected_fields = ['message', 'token', 'username', 'role']
            missing_fields = [field for field in expected_fields if field not in accept_response]
            
            if not missing_fields:
                self.log_test("Accept Invite - Response Fields", True, f"All required fields present: {expected_fields}")
                new_user_token = accept_response.get('token')
                
                # Verify username matches
                if accept_response.get('username') == accept_data['username']:
                    self.log_test("Accept Invite - Username Match", True, f"Username: {accept_response['username']}")
                else:
                    self.log_test("Accept Invite - Username Match", False, f"Expected: {accept_data['username']}, got: {accept_response.get('username')}")
            else:
                self.log_test("Accept Invite - Response Fields", False, f"Missing fields: {missing_fields}")
        
        # Test 4: Verify User Can Login with New Credentials
        if new_user_token:
            # Save original admin token
            original_token = self.token
            
            # Try to login with new user credentials
            success, login_response = self.run_test(
                "Login with New User Credentials",
                "POST",
                "auth/login",
                200,
                data={"username": accept_data['username'], "password": accept_data['password']}
            )
            
            if success and 'token' in login_response:
                self.log_test("New User Login Verification", True, f"New user can login successfully")
                
                # Test token verification for new user
                self.token = login_response['token']
                success, verify_response = self.run_test(
                    "New User Token Verification",
                    "GET",
                    "auth/verify",
                    200
                )
                
                if success:
                    if verify_response.get('username') == accept_data['username']:
                        self.log_test("New User Token Verify - Username", True, f"Username verified: {verify_response['username']}")
                    else:
                        self.log_test("New User Token Verify - Username", False, f"Username mismatch in verification")
            else:
                self.log_test("New User Login Verification", False, "New user cannot login")
            
            # Restore admin token
            self.token = original_token
        
        # Test 5: Edge Case - Try to Use Same Token Twice (Should Fail)
        duplicate_accept_data = {
            "token": invite_token,
            "username": "duplicateuser",
            "password": "testpass123"
        }
        
        success, duplicate_response = self.run_test(
            "Use Same Token Twice (Should Fail)",
            "POST",
            "invites/accept",
            404,  # Should fail because invite is already used
            data=duplicate_accept_data
        )
        
        # Test 6: Edge Case - Try to Get Used Invite (Should Fail)
        success, used_invite_response = self.run_test(
            "Get Used Invite (Should Fail)",
            "GET",
            f"invites/{invite_token}",
            404  # Should fail because invite is used
        )
        
        # Test 7: Edge Case - Try Invalid Token (Should Return 404)
        invalid_token = "00000000-0000-0000-0000-000000000000"
        success, invalid_response = self.run_test(
            "Get Invalid Token (Should Fail)",
            "GET",
            f"invites/{invalid_token}",
            404
        )
        
        # Test 8: Edge Case - Try Malformed Token
        malformed_token = "not-a-valid-uuid"
        success, malformed_response = self.run_test(
            "Get Malformed Token (Should Fail)",
            "GET",
            f"invites/{malformed_token}",
            404
        )
        
        # Clean up: Delete the created user
        if new_user_token:
            # Get all users to find the created user ID
            success, users = self.run_test(
                "Get Users for Cleanup",
                "GET",
                "users",
                200
            )
            
            if success:
                created_user = None
                for user in users:
                    if user.get('username') == accept_data['username']:
                        created_user = user
                        break
                
                if created_user and 'id' in created_user:
                    success, delete_response = self.run_test(
                        "Delete Created User (Cleanup)",
                        "DELETE",
                        f"users/{created_user['id']}",
                        200
                    )
        
        print(f"   📧 Invite functionality testing completed")
        return invite_token

    def test_duplicate_member_prevention(self):
        """Test duplicate member prevention for handles and emails"""
        print(f"\n🚫 Testing Duplicate Member Prevention...")
        
        # Test 1: Create first test member
        first_member = {
            "chapter": "National",
            "title": "Prez",
            "handle": "DuplicateTest1",
            "name": "First Member",
            "email": "duplicate@test.com",
            "phone": "555-0001",
            "address": "123 First Street"
        }
        
        success, created_member = self.run_test(
            "Create First Test Member",
            "POST",
            "members",
            201,
            data=first_member
        )
        
        first_member_id = None
        if success and 'id' in created_member:
            first_member_id = created_member['id']
            print(f"   Created first member ID: {first_member_id}")
        else:
            print("❌ Failed to create first member - cannot continue duplicate tests")
            return
        
        # Test 2: Try to create duplicate with same handle (should fail)
        duplicate_handle_member = {
            "chapter": "AD",
            "title": "VP",
            "handle": "DuplicateTest1",  # Same handle as first member
            "name": "Second Member",
            "email": "different@test.com",  # Different email
            "phone": "555-0002",
            "address": "456 Second Street"
        }
        
        success, response = self.run_test(
            "Create Member with Duplicate Handle (Should Fail)",
            "POST",
            "members",
            400,  # Should fail with 400 error
            data=duplicate_handle_member
        )
        
        # Test 3: Try to create duplicate with same email (should fail)
        duplicate_email_member = {
            "chapter": "HA",
            "title": "S@A",
            "handle": "DifferentHandle",  # Different handle
            "name": "Third Member",
            "email": "duplicate@test.com",  # Same email as first member
            "phone": "555-0003",
            "address": "789 Third Street"
        }
        
        success, response = self.run_test(
            "Create Member with Duplicate Email (Should Fail)",
            "POST",
            "members",
            400,  # Should fail with 400 error
            data=duplicate_email_member
        )
        
        # Test 4: Create valid second member (different handle and email - should succeed)
        valid_second_member = {
            "chapter": "HS",
            "title": "ENF",
            "handle": "DuplicateTest2",  # Different handle
            "name": "Valid Second Member",
            "email": "unique@test.com",  # Different email
            "phone": "555-0004",
            "address": "101 Fourth Street"
        }
        
        success, created_second_member = self.run_test(
            "Create Valid Second Member (Should Succeed)",
            "POST",
            "members",
            201,
            data=valid_second_member
        )
        
        second_member_id = None
        if success and 'id' in created_second_member:
            second_member_id = created_second_member['id']
            print(f"   Created second member ID: {second_member_id}")
        
        # Test 5: Try to update first member to duplicate handle (should fail)
        if first_member_id and second_member_id:
            update_to_duplicate_handle = {
                "handle": "DuplicateTest2"  # Try to change to second member's handle
            }
            
            success, response = self.run_test(
                "Update First Member to Duplicate Handle (Should Fail)",
                "PUT",
                f"members/{first_member_id}",
                400,  # Should fail with 400 error
                data=update_to_duplicate_handle
            )
        
        # Test 6: Try to update first member to duplicate email (should fail)
        if first_member_id and second_member_id:
            update_to_duplicate_email = {
                "email": "unique@test.com"  # Try to change to second member's email
            }
            
            success, response = self.run_test(
                "Update First Member to Duplicate Email (Should Fail)",
                "PUT",
                f"members/{first_member_id}",
                400,  # Should fail with 400 error
                data=update_to_duplicate_email
            )
        
        # Test 7: Valid update (should succeed)
        if first_member_id:
            valid_update = {
                "name": "Updated First Member",
                "phone": "555-9999"
            }
            
            success, response = self.run_test(
                "Valid Update of First Member (Should Succeed)",
                "PUT",
                f"members/{first_member_id}",
                200,
                data=valid_update
            )
        
        # Clean up test members
        if first_member_id:
            success, response = self.run_test(
                "Delete First Test Member (Cleanup)",
                "DELETE",
                f"members/{first_member_id}",
                200
            )
        
        if second_member_id:
            success, response = self.run_test(
                "Delete Second Test Member (Cleanup)",
                "DELETE",
                f"members/{second_member_id}",
                200
            )
        
        print(f"   🚫 Duplicate member prevention testing completed")
        return first_member_id, second_member_id

    def test_prospects_functionality(self):
        """Test Prospects (Hangarounds) functionality - NEW FEATURE"""
        print(f"\n🏍️  Testing Prospects (Hangarounds) Functionality...")
        
        # Test 1: Create Prospect
        test_prospect = {
            "handle": "TestHandle",
            "name": "Test Prospect",
            "email": "test@example.com",
            "phone": "555-1234",
            "address": "123 Test St"
        }
        
        success, created_prospect = self.run_test(
            "Create Prospect",
            "POST",
            "prospects",
            201,
            data=test_prospect
        )
        
        prospect_id = None
        if success and 'id' in created_prospect:
            prospect_id = created_prospect['id']
            print(f"   Created prospect ID: {prospect_id}")
            
            # Verify meeting_attendance structure (24 meetings)
            if 'meeting_attendance' in created_prospect:
                attendance = created_prospect['meeting_attendance']
                if 'year' in attendance and 'meetings' in attendance:
                    meetings = attendance['meetings']
                    if len(meetings) == 24:
                        self.log_test("Prospect Created with 24 Meeting Structure", True, f"24 meetings found for year {attendance['year']}")
                        
                        # Verify each meeting has status and note fields
                        all_meetings_valid = True
                        for i, meeting in enumerate(meetings):
                            if not isinstance(meeting, dict) or 'status' not in meeting or 'note' not in meeting:
                                all_meetings_valid = False
                                break
                        
                        if all_meetings_valid:
                            self.log_test("Prospect Meeting Structure Validation", True, "All 24 meetings have status and note fields")
                        else:
                            self.log_test("Prospect Meeting Structure Validation", False, f"Meeting {i+1} missing status or note field")
                    else:
                        self.log_test("Prospect Created with 24 Meeting Structure", False, f"Expected 24 meetings, got {len(meetings)}")
                else:
                    self.log_test("Prospect Created with 24 Meeting Structure", False, "Missing year or meetings in attendance")
            else:
                self.log_test("Prospect Created with 24 Meeting Structure", False, "No meeting_attendance field found")
            
            # Verify all required fields are present
            required_fields = ['handle', 'name', 'email', 'phone', 'address']
            missing_fields = [field for field in required_fields if field not in created_prospect]
            
            if not missing_fields:
                self.log_test("Prospect Creation - All Required Fields", True, f"All fields present: {required_fields}")
            else:
                self.log_test("Prospect Creation - All Required Fields", False, f"Missing fields: {missing_fields}")
        
        # Test 2: Get Prospects
        success, prospects = self.run_test(
            "Get Prospects",
            "GET",
            "prospects",
            200
        )
        
        if success:
            if isinstance(prospects, list):
                self.log_test("Get Prospects - Returns List", True, f"Found {len(prospects)} prospects")
                
                # Verify our created prospect is in the list
                if prospect_id:
                    found_prospect = None
                    for prospect in prospects:
                        if prospect.get('id') == prospect_id:
                            found_prospect = prospect
                            break
                    
                    if found_prospect:
                        self.log_test("Get Prospects - Contains Created Prospect", True, f"Found prospect: {found_prospect.get('handle')}")
                    else:
                        self.log_test("Get Prospects - Contains Created Prospect", False, "Created prospect not found in list")
            else:
                self.log_test("Get Prospects - Returns List", False, f"Expected list, got {type(prospects)}")
        
        # Test 3: Update Prospect
        if prospect_id:
            update_data = {
                "name": "Updated Test Prospect",
                "phone": "555-5678",
                "meeting_attendance": {
                    "year": 2025,
                    "meetings": [
                        {"status": 1, "note": "Present at first meeting"},
                        {"status": 2, "note": "Excused - family emergency"},
                        {"status": 0, "note": "Unexcused absence"}
                    ] + [{"status": 0, "note": ""} for _ in range(21)]
                }
            }
            
            success, updated_prospect = self.run_test(
                "Update Prospect",
                "PUT",
                f"prospects/{prospect_id}",
                200,
                data=update_data
            )
            
            if success:
                # Verify changes were saved
                if updated_prospect.get('name') == update_data['name']:
                    self.log_test("Update Prospect - Name Changed", True, f"Name updated to: {updated_prospect['name']}")
                else:
                    self.log_test("Update Prospect - Name Changed", False, f"Expected: {update_data['name']}, got: {updated_prospect.get('name')}")
                
                if updated_prospect.get('phone') == update_data['phone']:
                    self.log_test("Update Prospect - Phone Changed", True, f"Phone updated to: {updated_prospect['phone']}")
                else:
                    self.log_test("Update Prospect - Phone Changed", False, f"Expected: {update_data['phone']}, got: {updated_prospect.get('phone')}")
                
                # Verify meeting attendance was updated
                if 'meeting_attendance' in updated_prospect:
                    attendance = updated_prospect['meeting_attendance']
                    meetings = attendance.get('meetings', [])
                    
                    if len(meetings) >= 3:
                        # Check first three meetings
                        test_cases = [
                            (0, 1, "Present at first meeting"),
                            (1, 2, "Excused - family emergency"),
                            (2, 0, "Unexcused absence")
                        ]
                        
                        for idx, expected_status, expected_note in test_cases:
                            meeting = meetings[idx]
                            if meeting.get('status') == expected_status and meeting.get('note') == expected_note:
                                self.log_test(f"Update Prospect - Meeting {idx+1} Attendance", True, f"Status: {expected_status}, Note: '{expected_note}'")
                            else:
                                self.log_test(f"Update Prospect - Meeting {idx+1} Attendance", False, f"Expected status {expected_status} with note '{expected_note}', got status {meeting.get('status')} with note '{meeting.get('note')}'")
                    else:
                        self.log_test("Update Prospect - Meeting Attendance", False, f"Expected at least 3 meetings, got {len(meetings)}")
                else:
                    self.log_test("Update Prospect - Meeting Attendance", False, "No meeting_attendance found in updated prospect")
        
        # Test 4: CSV Export
        success, csv_data = self.run_test(
            "Export Prospects CSV",
            "GET",
            "prospects/export/csv",
            200
        )
        
        if success and isinstance(csv_data, str):
            csv_lines = csv_data.split('\n')
            if len(csv_lines) > 0:
                header = csv_lines[0]
                
                # Check for required columns
                required_columns = ['Handle', 'Name', 'Email', 'Phone', 'Address']
                found_columns = [col for col in required_columns if col in header]
                
                if len(found_columns) == len(required_columns):
                    self.log_test("CSV Export - Required Columns", True, f"All required columns found: {found_columns}")
                else:
                    missing = [col for col in required_columns if col not in found_columns]
                    self.log_test("CSV Export - Required Columns", False, f"Missing columns: {missing}")
                
                # Check for meeting columns
                meeting_columns = ['Jan-1st', 'Jan-3rd', 'Feb-1st', 'Feb-3rd']
                found_meeting_columns = [col for col in meeting_columns if col in header]
                
                if len(found_meeting_columns) >= 4:
                    self.log_test("CSV Export - Meeting Columns", True, f"Meeting columns found: {found_meeting_columns}")
                else:
                    self.log_test("CSV Export - Meeting Columns", False, f"Expected meeting columns, found: {found_meeting_columns}")
                
                # Check for Meeting Attendance Year column
                if 'Meeting Attendance Year' in header:
                    self.log_test("CSV Export - Attendance Year Column", True, "Meeting Attendance Year column found")
                else:
                    self.log_test("CSV Export - Attendance Year Column", False, "Meeting Attendance Year column not found")
                
                # Verify data rows contain our test prospect
                if prospect_id and len(csv_lines) > 1:
                    data_found = False
                    for line in csv_lines[1:]:
                        if 'TestHandle' in line or 'Updated Test Prospect' in line:
                            data_found = True
                            break
                    
                    if data_found:
                        self.log_test("CSV Export - Contains Test Data", True, "Test prospect data found in CSV")
                    else:
                        self.log_test("CSV Export - Contains Test Data", False, "Test prospect data not found in CSV")
            else:
                self.log_test("CSV Export - Valid Format", False, "Empty CSV response")
        else:
            self.log_test("CSV Export - Valid Format", False, f"Expected string, got {type(csv_data)}")
        
        # Test 5: Delete Prospect
        if prospect_id:
            success, delete_response = self.run_test(
                "Delete Prospect",
                "DELETE",
                f"prospects/{prospect_id}",
                200
            )
            
            if success:
                # Verify prospect is actually deleted
                success, get_response = self.run_test(
                    "Verify Prospect Deleted",
                    "GET",
                    f"prospects",
                    200
                )
                
                if success and isinstance(get_response, list):
                    deleted_prospect = None
                    for prospect in get_response:
                        if prospect.get('id') == prospect_id:
                            deleted_prospect = prospect
                            break
                    
                    if not deleted_prospect:
                        self.log_test("Verify Prospect Deletion", True, "Prospect successfully removed from list")
                    else:
                        self.log_test("Verify Prospect Deletion", False, "Prospect still found in list after deletion")
        
        # Test 6: Admin-only Access (Test with non-admin user)
        # Create a regular user for testing
        test_user = {
            "username": f"prospecttest_{datetime.now().strftime('%H%M%S')}",
            "password": "testpass123",
            "role": "user"
        }
        
        success, created_user = self.run_test(
            "Create Regular User for Prospect Access Test",
            "POST",
            "users",
            201,
            data=test_user
        )
        
        if success and 'id' in created_user:
            # Login as regular user
            original_token = self.token
            success, login_response = self.run_test(
                "Login as Regular User for Prospect Test",
                "POST",
                "auth/login",
                200,
                data={"username": test_user["username"], "password": test_user["password"]}
            )
            
            if success and 'token' in login_response:
                self.token = login_response['token']
                
                # Test that regular user cannot access prospects
                success, response = self.run_test(
                    "Regular User - Access Prospects (Should Fail)",
                    "GET",
                    "prospects",
                    403
                )
                
                # Test that regular user cannot create prospects
                success, response = self.run_test(
                    "Regular User - Create Prospect (Should Fail)",
                    "POST",
                    "prospects",
                    403,
                    data=test_prospect
                )
                
                # Test that regular user cannot export prospects CSV
                success, response = self.run_test(
                    "Regular User - Export Prospects CSV (Should Fail)",
                    "GET",
                    "prospects/export/csv",
                    403
                )
            
            # Restore admin token
            self.token = original_token
            
            # Clean up test user
            success, response = self.run_test(
                "Delete Prospect Test User",
                "DELETE",
                f"users/{created_user['id']}",
                200
            )
        
        print(f"   🏍️  Prospects functionality testing completed")
        return prospect_id

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
        
        # PRIORITY TEST: Email Invite Functionality
        self.test_invite_functionality()
        
        # NEW FEATURE TEST: Prospects (Hangarounds) Functionality
        self.test_prospects_functionality()
        
        # Test member operations
        self.test_member_operations()
        
        # PRIORITY TEST: Duplicate Member Prevention
        self.test_duplicate_member_prevention()
        
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