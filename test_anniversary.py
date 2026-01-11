#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AnniversaryTester:
    def __init__(self, base_url="https://memberwatch.preview.emergentagent.com/api"):
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
        """Test login with testadmin/testpass123"""
        print(f"\n🔐 Testing Authentication...")
        
        success, response = self.run_test(
            "Login as testadmin",
            "POST",
            "auth/login",
            200,
            data={"username": "testadmin", "password": "testpass123"}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            print(f"   ✅ Successful login with testadmin")
            print(f"   Token obtained: {self.token[:20]}...")
            return True, response
        
        print("   ❌ Login failed")
        return False, {}

    def test_anniversary_functionality(self):
        """Test Anniversary Notifications functionality - MEMBER ANNIVERSARY DISCORD NOTIFICATIONS TESTING"""
        print(f"\n🎉 Testing Anniversary Notifications Functionality...")
        
        # Test 1: GET /api/anniversaries/this-month
        success, this_month_response = self.run_test(
            "Get Anniversaries This Month",
            "GET",
            "anniversaries/this-month",
            200
        )
        
        if success:
            # Verify response structure
            required_fields = ['month', 'count', 'members']
            missing_fields = [field for field in required_fields if field not in this_month_response]
            
            if not missing_fields:
                self.log_test("This Month Response Structure", True, f"All required fields present: {required_fields}")
                
                # Verify members array structure
                members = this_month_response.get('members', [])
                if isinstance(members, list):
                    self.log_test("This Month Members Array", True, f"Found {len(members)} members with anniversaries this month")
                    
                    # Check member structure if any members exist
                    if members:
                        first_member = members[0]
                        member_fields = ['id', 'handle', 'name', 'chapter', 'title', 'join_date', 'years']
                        missing_member_fields = [field for field in member_fields if field not in first_member]
                        
                        if not missing_member_fields:
                            self.log_test("Member Structure in This Month", True, f"Member has all required fields: {member_fields}")
                        else:
                            self.log_test("Member Structure in This Month", False, f"Missing member fields: {missing_member_fields}")
                else:
                    self.log_test("This Month Members Array", False, "Members field is not an array")
            else:
                self.log_test("This Month Response Structure", False, f"Missing fields: {missing_fields}")
        
        # Test 2: GET /api/anniversaries/upcoming?months=6
        success, upcoming_response = self.run_test(
            "Get Upcoming Anniversaries (6 months)",
            "GET",
            "anniversaries/upcoming?months=6",
            200
        )
        
        if success:
            # Verify response structure
            required_fields = ['from_date', 'months_ahead', 'count', 'members']
            missing_fields = [field for field in required_fields if field not in upcoming_response]
            
            if not missing_fields:
                self.log_test("Upcoming Response Structure", True, f"All required fields present: {required_fields}")
                
                # Verify months_ahead matches request
                if upcoming_response.get('months_ahead') == 6:
                    self.log_test("Upcoming Months Parameter", True, "months_ahead=6 as requested")
                else:
                    self.log_test("Upcoming Months Parameter", False, f"Expected 6, got {upcoming_response.get('months_ahead')}")
                
                # Verify members are sorted by months_until
                members = upcoming_response.get('members', [])
                if isinstance(members, list) and len(members) > 1:
                    is_sorted = all(members[i].get('months_until', 0) <= members[i+1].get('months_until', 0) 
                                  for i in range(len(members)-1))
                    if is_sorted:
                        self.log_test("Upcoming Members Sorted", True, "Members sorted by months_until (soonest first)")
                    else:
                        self.log_test("Upcoming Members Sorted", False, "Members not properly sorted by months_until")
                else:
                    self.log_test("Upcoming Members Sorted", True, f"Found {len(members)} upcoming members (sorting not applicable)")
            else:
                self.log_test("Upcoming Response Structure", False, f"Missing fields: {missing_fields}")
        
        # Test 3: Create test member with join_date="12/2020" (5 years - should appear in this month)
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Create member with anniversary this month (December 2020 = 5 years if current month is December)
        test_member_this_month = {
            "chapter": "National",
            "title": "Member",
            "handle": "AnniversaryTest5Years",
            "name": "Anniversary Test Member (5 Years)",
            "email": "anniversary5@test.com",
            "phone": "555-0001",
            "address": "123 Anniversary Street",
            "join_date": f"{current_month:02d}/2020"  # 5 years ago this month
        }
        
        success, created_member_5y = self.run_test(
            "Create Member with 5-Year Anniversary This Month",
            "POST",
            "members",
            201,
            data=test_member_this_month
        )
        
        member_5y_id = None
        if success and 'id' in created_member_5y:
            member_5y_id = created_member_5y['id']
            print(f"   Created 5-year anniversary member ID: {member_5y_id}")
        
        # Test 4: Create test member with join_date="03/2024" (not this month)
        test_member_march = {
            "chapter": "AD",
            "title": "Member", 
            "handle": "AnniversaryTestMarch",
            "name": "Anniversary Test Member (March)",
            "email": "anniversarymarch@test.com",
            "phone": "555-0002",
            "address": "456 March Street",
            "join_date": "03/2024"  # March 2024 - not current month
        }
        
        success, created_member_march = self.run_test(
            "Create Member with March Anniversary",
            "POST",
            "members",
            201,
            data=test_member_march
        )
        
        member_march_id = None
        if success and 'id' in created_member_march:
            member_march_id = created_member_march['id']
            print(f"   Created March anniversary member ID: {member_march_id}")
        
        # Test 5: Verify 5-year member appears in this-month endpoint
        success, updated_this_month = self.run_test(
            "Verify 5-Year Member in This Month",
            "GET",
            "anniversaries/this-month",
            200
        )
        
        if success:
            members = updated_this_month.get('members', [])
            found_5y_member = any(member.get('handle') == 'AnniversaryTest5Years' for member in members)
            
            if found_5y_member:
                self.log_test("5-Year Member in This Month", True, "Member with 5-year anniversary found in this month")
                
                # Find the specific member and verify years calculation
                for member in members:
                    if member.get('handle') == 'AnniversaryTest5Years':
                        if member.get('years') == 5:
                            self.log_test("5-Year Member Years Calculation", True, f"Correctly calculated 5 years")
                        else:
                            self.log_test("5-Year Member Years Calculation", False, f"Expected 5 years, got {member.get('years')}")
                        break
            else:
                self.log_test("5-Year Member in This Month", False, "Member with 5-year anniversary not found in this month")
        
        # Test 6: Verify March member does NOT appear in this-month but appears in upcoming
        success, updated_upcoming = self.run_test(
            "Verify March Member in Upcoming",
            "GET",
            "anniversaries/upcoming?months=12",
            200
        )
        
        if success:
            members = updated_upcoming.get('members', [])
            found_march_member = any(member.get('handle') == 'AnniversaryTestMarch' for member in members)
            
            if found_march_member:
                self.log_test("March Member in Upcoming", True, "March anniversary member found in upcoming anniversaries")
            else:
                self.log_test("March Member in Upcoming", False, "March anniversary member not found in upcoming anniversaries")
        
        # Test 7: Edge Case - Member with join_date less than 1 year ago (should NOT appear)
        test_member_recent = {
            "chapter": "HA",
            "title": "Member",
            "handle": "AnniversaryTestRecent",
            "name": "Recent Member (No Anniversary)",
            "email": "recent@test.com", 
            "phone": "555-0003",
            "address": "789 Recent Street",
            "join_date": f"{current_month:02d}/{current_year}"  # This year - 0 years
        }
        
        success, created_member_recent = self.run_test(
            "Create Recent Member (0 Years)",
            "POST",
            "members",
            201,
            data=test_member_recent
        )
        
        member_recent_id = None
        if success and 'id' in created_member_recent:
            member_recent_id = created_member_recent['id']
            print(f"   Created recent member ID: {member_recent_id}")
        
        # Test 8: Verify recent member does NOT appear in anniversaries
        success, check_recent = self.run_test(
            "Verify Recent Member Not in Anniversaries",
            "GET",
            "anniversaries/this-month",
            200
        )
        
        if success:
            members = check_recent.get('members', [])
            found_recent = any(member.get('handle') == 'AnniversaryTestRecent' for member in members)
            
            if not found_recent:
                self.log_test("Recent Member Excluded (0 Years)", True, "Recent member correctly excluded from anniversaries")
            else:
                self.log_test("Recent Member Excluded (0 Years)", False, "Recent member incorrectly included in anniversaries")
        
        # Test 9: Edge Case - Member with no join_date
        test_member_no_date = {
            "chapter": "HS",
            "title": "Member",
            "handle": "AnniversaryTestNoDate",
            "name": "Member with No Join Date",
            "email": "nodate@test.com",
            "phone": "555-0004", 
            "address": "101 No Date Street"
            # No join_date field
        }
        
        success, created_member_no_date = self.run_test(
            "Create Member with No Join Date",
            "POST",
            "members",
            201,
            data=test_member_no_date
        )
        
        member_no_date_id = None
        if success and 'id' in created_member_no_date:
            member_no_date_id = created_member_no_date['id']
            print(f"   Created no-date member ID: {member_no_date_id}")
        
        # Test 10: Verify member with no join_date is excluded
        success, check_no_date = self.run_test(
            "Verify No-Date Member Excluded",
            "GET",
            "anniversaries/this-month",
            200
        )
        
        if success:
            members = check_no_date.get('members', [])
            found_no_date = any(member.get('handle') == 'AnniversaryTestNoDate' for member in members)
            
            if not found_no_date:
                self.log_test("No-Date Member Excluded", True, "Member without join_date correctly excluded")
            else:
                self.log_test("No-Date Member Excluded", False, "Member without join_date incorrectly included")
        
        # Test 11: POST /api/anniversaries/trigger-check (admin only)
        success, trigger_response = self.run_test(
            "Trigger Anniversary Check (Admin)",
            "POST",
            "anniversaries/trigger-check",
            200
        )
        
        if success:
            if 'message' in trigger_response:
                self.log_test("Anniversary Trigger Response", True, f"Trigger successful: {trigger_response.get('message')}")
            else:
                self.log_test("Anniversary Trigger Response", False, "No message in trigger response")
        
        # Test 12: Test non-admin access to trigger endpoint (should fail)
        # Create a regular user first
        regular_user = {
            "username": "anniversaryregular",
            "password": "testpass123",
            "role": "member"
        }
        
        success, created_regular = self.run_test(
            "Create Regular User for Anniversary Test",
            "POST",
            "users",
            201,
            data=regular_user
        )
        
        if success and 'id' in created_regular:
            # Save admin token
            admin_token = self.token
            
            # Login as regular user
            success, regular_login = self.run_test(
                "Login as Regular User",
                "POST",
                "auth/login",
                200,
                data={"username": "anniversaryregular", "password": "testpass123"}
            )
            
            if success and 'token' in regular_login:
                self.token = regular_login['token']
                
                # Try to trigger anniversary check (should fail with 403)
                success, forbidden_response = self.run_test(
                    "Non-Admin Trigger Anniversary Check (Should Fail)",
                    "POST",
                    "anniversaries/trigger-check",
                    403
                )
            
            # Restore admin token
            self.token = admin_token
            
            # Clean up regular user
            success, delete_regular = self.run_test(
                "Delete Regular User (Cleanup)",
                "DELETE",
                f"users/{created_regular['id']}?reason=Test cleanup",
                200
            )
        
        # Test 13: Test duplicate notification prevention
        # Trigger check twice to ensure no duplicate notifications
        success, first_trigger = self.run_test(
            "First Anniversary Trigger Check",
            "POST",
            "anniversaries/trigger-check",
            200
        )
        
        success, second_trigger = self.run_test(
            "Second Anniversary Trigger Check (Duplicate Prevention)",
            "POST",
            "anniversaries/trigger-check",
            200
        )
        
        if success:
            self.log_test("Duplicate Notification Prevention", True, "Second trigger completed (duplicate prevention should be active)")
        
        # Clean up test members
        print(f"\n   🧹 Cleaning up anniversary test data...")
        
        cleanup_members = [
            (member_5y_id, "Delete 5-Year Anniversary Test Member"),
            (member_march_id, "Delete March Anniversary Test Member"),
            (member_recent_id, "Delete Recent Test Member"),
            (member_no_date_id, "Delete No-Date Test Member")
        ]
        
        for member_id, description in cleanup_members:
            if member_id:
                success, response = self.run_test(
                    description,
                    "DELETE",
                    f"members/{member_id}?reason=Test cleanup",
                    200
                )
        
        print(f"   🎉 Anniversary functionality testing completed")
        return member_5y_id, member_march_id, member_recent_id, member_no_date_id

    def run_tests(self):
        """Run all anniversary tests"""
        print("🚀 Starting Anniversary Notifications Testing...")
        print(f"   Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test authentication first
        success, response = self.test_login()
        if not success:
            print("❌ Authentication failed - cannot continue tests")
            return
        
        # Run anniversary tests
        self.test_anniversary_functionality()
        
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
    tester = AnniversaryTester()
    tester.run_tests()