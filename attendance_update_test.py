#!/usr/bin/env python3
"""
Specific test for the attendance update fix mentioned in the review request.
Tests that PUT /api/members/{member_id} now accepts and saves meeting_attendance data.
"""

import requests
import json
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AttendanceUpdateTester:
    def __init__(self, base_url="https://dues-tracker-15.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        
    def login(self, username="testadmin", password="testpass123"):
        """Login and get auth token"""
        url = f"{self.base_url}/auth/login"
        data = {"username": username, "password": password}
        
        try:
            response = requests.post(url, json=data, verify=False)
            if response.status_code == 200:
                result = response.json()
                self.token = result['token']
                print(f"✅ Login successful - Token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ Login failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def create_test_member(self):
        """Create a test member for attendance testing"""
        url = f"{self.base_url}/members"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        member_data = {
            "chapter": "National",
            "title": "Prez", 
            "handle": "AttendanceFixTest",
            "name": "Attendance Fix Test User",
            "email": "attendancefix@example.com",
            "phone": "+1-555-0199",
            "address": "199 Fix Test Street, Test City, TC 12345"
        }
        
        try:
            response = requests.post(url, json=member_data, headers=headers, verify=False)
            if response.status_code == 201:
                member = response.json()
                print(f"✅ Test member created - ID: {member['id']}")
                return member['id']
            else:
                print(f"❌ Failed to create test member - Status: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error creating test member: {str(e)}")
            return None
    
    def get_member(self, member_id):
        """Get member data"""
        url = f"{self.base_url}/members/{member_id}"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, verify=False)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get member - Status: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error getting member: {str(e)}")
            return None
    
    def test_member_update_with_attendance(self, member_id):
        """Test updating member with meeting_attendance data using PUT /api/members/{member_id}"""
        print(f"\n🎯 Testing PUT /api/members/{member_id} with meeting_attendance...")
        
        url = f"{self.base_url}/members/{member_id}"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Test data as specified in the review request
        update_data = {
            "name": "Updated Attendance Test User",
            "meeting_attendance": {
                "year": 2025,
                "meetings": [
                    {"status": 1, "note": ""},  # Jan-1st Present
                    {"status": 2, "note": "doctor appointment"},  # Jan-3rd Excused with note
                    {"status": 0, "note": "missed without notice"},  # Feb-1st Unexcused with note
                    {"status": 1, "note": ""},  # Feb-3rd Present
                    {"status": 2, "note": "family emergency"},  # Mar-1st Excused with note
                    {"status": 0, "note": "work conflict"},  # Mar-3rd Unexcused with note
                    {"status": 1, "note": ""},  # Apr-1st Present
                    {"status": 2, "note": "medical appointment"},  # Apr-3rd Excused with note
                ] + [{"status": 0, "note": ""} for _ in range(16)]  # Fill remaining 16 meetings
            }
        }
        
        try:
            response = requests.put(url, json=update_data, headers=headers, verify=False)
            if response.status_code == 200:
                updated_member = response.json()
                print(f"✅ Member update successful")
                
                # Verify the meeting_attendance was saved
                if 'meeting_attendance' in updated_member:
                    attendance = updated_member['meeting_attendance']
                    print(f"✅ meeting_attendance field present in response")
                    
                    if attendance.get('year') == 2025:
                        print(f"✅ Attendance year correctly set to 2025")
                    else:
                        print(f"❌ Attendance year incorrect: {attendance.get('year')}")
                    
                    meetings = attendance.get('meetings', [])
                    if len(meetings) == 24:
                        print(f"✅ Correct number of meetings (24)")
                    else:
                        print(f"❌ Incorrect number of meetings: {len(meetings)}")
                    
                    # Test specific meeting data
                    test_cases = [
                        (0, 1, "", "Jan-1st Present"),
                        (1, 2, "doctor appointment", "Jan-3rd Excused with note"),
                        (2, 0, "missed without notice", "Feb-1st Unexcused with note"),
                        (3, 1, "", "Feb-3rd Present"),
                        (4, 2, "family emergency", "Mar-1st Excused with note"),
                        (5, 0, "work conflict", "Mar-3rd Unexcused with note"),
                        (6, 1, "", "Apr-1st Present"),
                        (7, 2, "medical appointment", "Apr-3rd Excused with note")
                    ]
                    
                    for idx, expected_status, expected_note, description in test_cases:
                        if idx < len(meetings):
                            meeting = meetings[idx]
                            actual_status = meeting.get('status')
                            actual_note = meeting.get('note', '')
                            
                            if actual_status == expected_status and actual_note == expected_note:
                                print(f"✅ {description} - Status: {actual_status}, Note: '{actual_note}'")
                            else:
                                print(f"❌ {description} - Expected status {expected_status} with note '{expected_note}', got status {actual_status} with note '{actual_note}'")
                    
                    return True
                else:
                    print(f"❌ meeting_attendance field missing from response")
                    return False
            else:
                print(f"❌ Member update failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', 'No error details')}")
                except:
                    print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error updating member: {str(e)}")
            return False
    
    def test_attendance_persistence(self, member_id):
        """Test that attendance data persists after update by retrieving the member again"""
        print(f"\n🔍 Testing attendance data persistence...")
        
        member = self.get_member(member_id)
        if not member:
            print(f"❌ Failed to retrieve member for persistence test")
            return False
        
        if 'meeting_attendance' not in member:
            print(f"❌ meeting_attendance field missing after retrieval")
            return False
        
        attendance = member['meeting_attendance']
        
        # Verify key data points persist
        if attendance.get('year') != 2025:
            print(f"❌ Attendance year not persisted correctly: {attendance.get('year')}")
            return False
        
        meetings = attendance.get('meetings', [])
        if len(meetings) != 24:
            print(f"❌ Meeting count not persisted correctly: {len(meetings)}")
            return False
        
        # Check specific meetings that should have notes
        excused_with_notes = [m for m in meetings if m.get('status') == 2 and m.get('note', '').strip()]
        unexcused_with_notes = [m for m in meetings if m.get('status') == 0 and m.get('note', '').strip()]
        
        if len(excused_with_notes) >= 3:
            print(f"✅ Excused absences with notes persisted: {len(excused_with_notes)} found")
        else:
            print(f"❌ Excused absences with notes not persisted correctly: {len(excused_with_notes)} found")
            return False
        
        if len(unexcused_with_notes) >= 2:
            print(f"✅ Unexcused absences with notes persisted: {len(unexcused_with_notes)} found")
        else:
            print(f"❌ Unexcused absences with notes not persisted correctly: {len(unexcused_with_notes)} found")
            return False
        
        # Check specific notes
        expected_notes = ["doctor appointment", "missed without notice", "family emergency", "work conflict", "medical appointment"]
        found_notes = [m.get('note', '') for m in meetings if m.get('note', '').strip()]
        
        for expected_note in expected_notes:
            if expected_note in found_notes:
                print(f"✅ Note '{expected_note}' persisted correctly")
            else:
                print(f"❌ Note '{expected_note}' not found in persisted data")
                return False
        
        print(f"✅ All attendance data persisted correctly")
        return True
    
    def cleanup_member(self, member_id):
        """Delete the test member"""
        url = f"{self.base_url}/members/{member_id}"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.delete(url, headers=headers, verify=False)
            if response.status_code == 200:
                print(f"✅ Test member cleaned up")
                return True
            else:
                print(f"❌ Failed to cleanup test member - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error cleaning up test member: {str(e)}")
            return False
    
    def run_attendance_update_test(self):
        """Run the complete attendance update test"""
        print("🎯 Testing Attendance Update Fix for Brothers of the Highway Member Directory")
        print("=" * 80)
        
        # Login
        if not self.login():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Create test member
        member_id = self.create_test_member()
        if not member_id:
            print("❌ Cannot proceed without test member")
            return False
        
        try:
            # Test member update with attendance data
            update_success = self.test_member_update_with_attendance(member_id)
            
            # Test persistence
            persistence_success = self.test_attendance_persistence(member_id)
            
            # Overall result
            overall_success = update_success and persistence_success
            
            print("\n" + "=" * 80)
            if overall_success:
                print("🎉 ATTENDANCE UPDATE FIX VERIFIED - All tests passed!")
                print("✅ PUT /api/members/{member_id} now accepts meeting_attendance")
                print("✅ Attendance data persists after update")
                print("✅ Notes work for both Excused and Unexcused statuses")
            else:
                print("❌ ATTENDANCE UPDATE FIX FAILED - Some tests failed")
            
            return overall_success
            
        finally:
            # Cleanup
            self.cleanup_member(member_id)

def main():
    tester = AttendanceUpdateTester()
    success = tester.run_attendance_update_test()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())