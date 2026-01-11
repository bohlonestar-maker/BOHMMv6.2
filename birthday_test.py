#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BirthdayNotificationTester:
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
        """Test login as testadmin/testpass123"""
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

    def test_birthday_notifications(self):
        """Test birthday notification feature - NEW FEATURE"""
        print(f"\n🎂 Testing Birthday Notification Feature...")
        
        # Test 1: Login as testadmin/testpass123 as specified in review request
        success, admin_login = self.test_login()
        
        if not success or 'token' not in admin_login:
            print("❌ Cannot continue - testadmin login failed")
            return
        
        # Test 2: GET /api/birthdays/today - should return empty or members with today's birthday
        success, todays_birthdays = self.run_test(
            "Get Today's Birthdays",
            "GET",
            "birthdays/today",
            200
        )
        
        if success:
            # Verify response structure
            required_fields = ['date', 'count', 'members']
            missing_fields = [field for field in required_fields if field not in todays_birthdays]
            
            if not missing_fields:
                self.log_test("Today's Birthdays - Response Structure", True, f"All required fields present: {required_fields}")
                
                # Verify data types
                if (isinstance(todays_birthdays.get('date'), str) and 
                    isinstance(todays_birthdays.get('count'), int) and 
                    isinstance(todays_birthdays.get('members'), list)):
                    self.log_test("Today's Birthdays - Data Types", True, "Correct data types for all fields")
                    
                    # Log current results
                    count = todays_birthdays.get('count', 0)
                    date = todays_birthdays.get('date', '')
                    self.log_test("Today's Birthdays - Current Results", True, f"Date: {date}, Count: {count} members")
                    
                    # If there are members, verify member structure
                    if count > 0:
                        member = todays_birthdays['members'][0]
                        member_fields = ['id', 'handle', 'name', 'chapter', 'title', 'birthday_date']
                        member_missing = [field for field in member_fields if field not in member]
                        
                        if not member_missing:
                            self.log_test("Today's Birthdays - Member Structure", True, f"Member has all required fields: {member_fields}")
                        else:
                            self.log_test("Today's Birthdays - Member Structure", False, f"Missing member fields: {member_missing}")
                else:
                    self.log_test("Today's Birthdays - Data Types", False, f"Incorrect data types in response")
            else:
                self.log_test("Today's Birthdays - Response Structure", False, f"Missing fields: {missing_fields}")
        
        # Test 3: GET /api/birthdays/upcoming - should return upcoming birthdays sorted by days_until
        success, upcoming_birthdays = self.run_test(
            "Get Upcoming Birthdays (Default 30 days)",
            "GET",
            "birthdays/upcoming",
            200
        )
        
        if success:
            # Verify response structure
            required_fields = ['from_date', 'to_date', 'count', 'members']
            missing_fields = [field for field in required_fields if field not in upcoming_birthdays]
            
            if not missing_fields:
                self.log_test("Upcoming Birthdays - Response Structure", True, f"All required fields present: {required_fields}")
                
                # Verify data types and content
                if (isinstance(upcoming_birthdays.get('from_date'), str) and 
                    isinstance(upcoming_birthdays.get('to_date'), str) and 
                    isinstance(upcoming_birthdays.get('count'), int) and 
                    isinstance(upcoming_birthdays.get('members'), list)):
                    self.log_test("Upcoming Birthdays - Data Types", True, "Correct data types for all fields")
                    
                    # Log current results
                    count = upcoming_birthdays.get('count', 0)
                    from_date = upcoming_birthdays.get('from_date', '')
                    to_date = upcoming_birthdays.get('to_date', '')
                    self.log_test("Upcoming Birthdays - Current Results", True, f"From: {from_date}, To: {to_date}, Count: {count} members")
                    
                    # If there are members, verify they are sorted by days_until
                    if count > 1:
                        members = upcoming_birthdays['members']
                        is_sorted = True
                        for i in range(len(members) - 1):
                            if members[i].get('days_until', 0) > members[i + 1].get('days_until', 0):
                                is_sorted = False
                                break
                        
                        if is_sorted:
                            self.log_test("Upcoming Birthdays - Sorted by Days Until", True, "Members correctly sorted by days_until")
                        else:
                            self.log_test("Upcoming Birthdays - Sorted by Days Until", False, "Members not properly sorted")
                    
                    # Verify member structure if members exist
                    if count > 0:
                        member = upcoming_birthdays['members'][0]
                        member_fields = ['id', 'handle', 'name', 'chapter', 'title', 'birthday_date', 'days_until']
                        member_missing = [field for field in member_fields if field not in member]
                        
                        if not member_missing:
                            self.log_test("Upcoming Birthdays - Member Structure", True, f"Member has all required fields: {member_fields}")
                        else:
                            self.log_test("Upcoming Birthdays - Member Structure", False, f"Missing member fields: {member_missing}")
                else:
                    self.log_test("Upcoming Birthdays - Data Types", False, f"Incorrect data types in response")
            else:
                self.log_test("Upcoming Birthdays - Response Structure", False, f"Missing fields: {missing_fields}")
        
        # Test 4: GET /api/birthdays/upcoming?days=90 - should show more results with longer timeframe
        success, extended_birthdays = self.run_test(
            "Get Upcoming Birthdays (90 days)",
            "GET",
            "birthdays/upcoming?days=90",
            200
        )
        
        if success:
            # Verify response structure
            if 'count' in extended_birthdays and 'members' in extended_birthdays:
                extended_count = extended_birthdays.get('count', 0)
                default_count = upcoming_birthdays.get('count', 0) if upcoming_birthdays else 0
                
                # Extended period should have same or more results
                if extended_count >= default_count:
                    self.log_test("Extended Period Birthdays", True, f"90-day period shows {extended_count} vs 30-day period {default_count}")
                else:
                    self.log_test("Extended Period Birthdays", False, f"90-day period shows fewer results ({extended_count}) than 30-day period ({default_count})")
                
                # Verify date range is correct (90 days)
                from_date = extended_birthdays.get('from_date', '')
                to_date = extended_birthdays.get('to_date', '')
                if from_date and to_date:
                    try:
                        from_dt = datetime.fromisoformat(from_date)
                        to_dt = datetime.fromisoformat(to_date)
                        days_diff = (to_dt - from_dt).days
                        
                        if days_diff == 90:
                            self.log_test("Extended Period Date Range", True, f"Date range is exactly 90 days: {from_date} to {to_date}")
                        else:
                            self.log_test("Extended Period Date Range", False, f"Date range is {days_diff} days, expected 90")
                    except:
                        self.log_test("Extended Period Date Range", False, "Could not parse date range")
            else:
                self.log_test("Extended Period Birthdays", False, "Missing required fields in response")
        
        # Test 5: POST /api/birthdays/trigger-check - should trigger the birthday notification check (admin only)
        success, trigger_response = self.run_test(
            "Trigger Birthday Notification Check",
            "POST",
            "birthdays/trigger-check",
            200
        )
        
        if success:
            # Verify response contains success message
            if 'message' in trigger_response:
                message = trigger_response.get('message', '')
                if 'birthday check' in message.lower() or 'triggered' in message.lower():
                    self.log_test("Trigger Birthday Check - Response Message", True, f"Success message: {message}")
                else:
                    self.log_test("Trigger Birthday Check - Response Message", False, f"Unexpected message: {message}")
            else:
                self.log_test("Trigger Birthday Check - Response Message", False, "No message in response")
        
        # Test 6: Test authentication requirement for trigger endpoint
        original_token = self.token
        self.token = None
        
        success, unauthorized_response = self.run_test(
            "Trigger Birthday Check Without Auth (Should Fail)",
            "POST",
            "birthdays/trigger-check",
            403  # Should fail without authentication
        )
        
        # Restore token
        self.token = original_token
        
        # Test 7: Test non-admin access to trigger endpoint
        # Create a regular user to test non-admin access
        regular_user = {
            "username": "birthdaytest",
            "email": "birthdaytest@example.com",
            "password": "testpass123",
            "role": "member"
        }
        
        success, created_user = self.run_test(
            "Create Regular User for Birthday Auth Test",
            "POST",
            "users",
            201,
            data=regular_user
        )
        
        if success and 'id' in created_user:
            user_id = created_user['id']
            
            # Login as regular user
            success, user_login = self.run_test(
                "Login as Regular User",
                "POST",
                "auth/login",
                200,
                data={"username": "birthdaytest", "password": "testpass123"}
            )
            
            if success and 'token' in user_login:
                self.token = user_login['token']
                
                # Try to trigger birthday check (should fail - admin only)
                success, forbidden_response = self.run_test(
                    "Regular User Trigger Birthday Check (Should Fail)",
                    "POST",
                    "birthdays/trigger-check",
                    403  # Should fail - admin only
                )
                
                # Regular user should still be able to view birthdays
                success, user_birthdays = self.run_test(
                    "Regular User - View Today's Birthdays",
                    "GET",
                    "birthdays/today",
                    200
                )
                
                success, user_upcoming = self.run_test(
                    "Regular User - View Upcoming Birthdays",
                    "GET",
                    "birthdays/upcoming",
                    200
                )
            
            # Restore admin token
            self.token = original_token
            
            # Clean up test user
            success, delete_response = self.run_test(
                "Delete Birthday Test User",
                "DELETE",
                f"users/{user_id}",
                200
            )
        
        # Test 8: Create test member with birthday to verify functionality
        # Create member with birthday tomorrow for testing
        tomorrow = datetime.now() + timedelta(days=1)
        timestamp = datetime.now().strftime("%H%M%S")
        birthday_member = {
            "chapter": "National",
            "title": "Member",
            "handle": f"BirthdayTestRider{timestamp}",
            "name": "Birthday Test Member",
            "email": f"birthday{timestamp}@test.com",
            "phone": "555-BDAY",
            "address": "123 Birthday Street",
            "dob": tomorrow.strftime("%Y-%m-%d")  # Birthday tomorrow
        }
        
        success, created_birthday_member = self.run_test(
            "Create Member with Birthday Tomorrow",
            "POST",
            "members",
            201,
            data=birthday_member
        )
        
        birthday_member_id = None
        if success and 'id' in created_birthday_member:
            birthday_member_id = created_birthday_member['id']
            
            # Test upcoming birthdays should now include this member
            success, updated_upcoming = self.run_test(
                "Get Upcoming Birthdays After Adding Test Member",
                "GET",
                "birthdays/upcoming?days=7",
                200
            )
            
            if success and 'members' in updated_upcoming:
                # Look for our test member in the results
                test_member_found = False
                for member in updated_upcoming['members']:
                    if member.get('handle') == f'BirthdayTestRider{timestamp}':
                        test_member_found = True
                        if member.get('days_until') == 1:
                            self.log_test("Test Member Birthday Calculation", True, "Test member shows 1 day until birthday")
                        else:
                            self.log_test("Test Member Birthday Calculation", False, f"Expected 1 day until birthday, got {member.get('days_until')}")
                        break
                
                if test_member_found:
                    self.log_test("Test Member in Upcoming Birthdays", True, "Test member found in upcoming birthdays")
                else:
                    self.log_test("Test Member in Upcoming Birthdays", False, "Test member not found in upcoming birthdays")
        
        # Clean up test member
        if birthday_member_id:
            success, delete_response = self.run_test(
                "Delete Birthday Test Member",
                "DELETE",
                f"members/{birthday_member_id}?reason=Test cleanup",
                200
            )
        
        print(f"   🎂 Birthday notification feature testing completed")
        return True

    def run_tests(self):
        """Run birthday notification tests"""
        print("🚀 Starting Birthday Notification API Tests...")
        print(f"   Base URL: {self.base_url}")
        
        self.test_birthday_notifications()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed - check details above")
            
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = BirthdayNotificationTester()
    tester.run_tests()