#!/usr/bin/env python3
"""
BOH Directory API Testing - Review Request Features
Tests for archived member/prospect delete functionality and CSV export decryption
"""

import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ReviewRequestTester:
    def __init__(self, base_url="https://dues-tracker-15.preview.emergentagent.com/api"):
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
        """Test login and get token"""
        print(f"\n🔐 Testing Authentication...")
        
        # Try testadmin/testpass123 as requested
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
        
        print("   ❌ testadmin login failed")
        return False, {}

    def test_archived_delete_functionality(self):
        """Test archived member and prospect delete functionality - NEW FEATURE"""
        print(f"\n🗑️  Testing Archived Delete Functionality...")
        
        # Step 1: Create a test member to archive and delete
        test_member = {
            "chapter": "National",
            "title": "Member",
            "handle": "ArchiveDeleteTest",
            "name": "Archive Delete Test Member",
            "email": "archivedelete@test.com",
            "phone": "555-9999-8888",
            "address": "999 Archive Street, Delete City, DC 99999"
        }
        
        success, created_member = self.run_test(
            "Create Member for Archive Delete Test",
            "POST",
            "members",
            201,
            data=test_member
        )
        
        member_id = None
        if success and 'id' in created_member:
            member_id = created_member['id']
            print(f"   Created member ID for archive delete test: {member_id}")
        else:
            print("❌ Failed to create member for archive delete test")
            return
        
        # Step 2: Archive the member (delete with reason)
        success, archive_response = self.run_test(
            "Archive Member",
            "DELETE",
            f"members/{member_id}?reason=Test%20Archive%20for%20Delete%20Testing",
            200
        )
        
        if not success:
            print("❌ Failed to archive member - cannot continue delete test")
            return
        
        # Step 3: Verify member is in archived collection
        success, archived_members = self.run_test(
            "Get Archived Members",
            "GET",
            "archived/members",
            200
        )
        
        archived_member_found = False
        if success and isinstance(archived_members, list):
            for archived in archived_members:
                if archived.get('id') == member_id:
                    archived_member_found = True
                    self.log_test("Member Found in Archived Collection", True, f"Member {member_id} found in archived_members")
                    break
        
        if not archived_member_found:
            self.log_test("Member Found in Archived Collection", False, f"Member {member_id} not found in archived_members")
            return
        
        # Step 4: Test DELETE archived member endpoint
        success, delete_response = self.run_test(
            "Delete Archived Member",
            "DELETE",
            f"archived/members/{member_id}",
            200
        )
        
        if success:
            # Verify response message
            if isinstance(delete_response, dict) and 'message' in delete_response:
                if 'permanently deleted' in delete_response['message'].lower():
                    self.log_test("Delete Archived Member - Response Message", True, f"Message: {delete_response['message']}")
                else:
                    self.log_test("Delete Archived Member - Response Message", False, f"Unexpected message: {delete_response['message']}")
        
        # Step 5: Verify member is permanently removed from archived collection
        success, archived_members_after = self.run_test(
            "Verify Member Removed from Archived Collection",
            "GET",
            "archived/members",
            200
        )
        
        member_still_exists = False
        if success and isinstance(archived_members_after, list):
            for archived in archived_members_after:
                if archived.get('id') == member_id:
                    member_still_exists = True
                    break
        
        if not member_still_exists:
            self.log_test("Member Permanently Removed from Archived", True, f"Member {member_id} no longer in archived_members")
        else:
            self.log_test("Member Permanently Removed from Archived", False, f"Member {member_id} still exists in archived_members")
        
        # Step 6: Test with prospects
        test_prospect = {
            "handle": "ArchiveDeleteProspect",
            "name": "Archive Delete Test Prospect",
            "email": "prospectarchivedelete@test.com",
            "phone": "555-7777-6666",
            "address": "777 Prospect Archive Street"
        }
        
        success, created_prospect = self.run_test(
            "Create Prospect for Archive Delete Test",
            "POST",
            "prospects",
            201,
            data=test_prospect
        )
        
        prospect_id = None
        if success and 'id' in created_prospect:
            prospect_id = created_prospect['id']
            print(f"   Created prospect ID for archive delete test: {prospect_id}")
        
        if prospect_id:
            # Archive the prospect
            success, archive_prospect_response = self.run_test(
                "Archive Prospect",
                "DELETE",
                f"prospects/{prospect_id}?reason=Test%20Archive%20for%20Delete%20Testing",
                200
            )
            
            if success:
                # Test DELETE archived prospect endpoint
                success, delete_prospect_response = self.run_test(
                    "Delete Archived Prospect",
                    "DELETE",
                    f"archived/prospects/{prospect_id}",
                    200
                )
                
                if success:
                    # Verify response message
                    if isinstance(delete_prospect_response, dict) and 'message' in delete_prospect_response:
                        if 'permanently deleted' in delete_prospect_response['message'].lower():
                            self.log_test("Delete Archived Prospect - Response Message", True, f"Message: {delete_prospect_response['message']}")
                        else:
                            self.log_test("Delete Archived Prospect - Response Message", False, f"Unexpected message: {delete_prospect_response['message']}")
                
                # Verify prospect is permanently removed
                success, archived_prospects_after = self.run_test(
                    "Verify Prospect Removed from Archived Collection",
                    "GET",
                    "archived/prospects",
                    200
                )
                
                prospect_still_exists = False
                if success and isinstance(archived_prospects_after, list):
                    for archived in archived_prospects_after:
                        if archived.get('id') == prospect_id:
                            prospect_still_exists = True
                            break
                
                if not prospect_still_exists:
                    self.log_test("Prospect Permanently Removed from Archived", True, f"Prospect {prospect_id} no longer in archived_prospects")
                else:
                    self.log_test("Prospect Permanently Removed from Archived", False, f"Prospect {prospect_id} still exists in archived_prospects")
        
        # Step 7: Test error handling - try to delete non-existent archived member
        fake_id = "00000000-0000-0000-0000-000000000000"
        success, error_response = self.run_test(
            "Delete Non-Existent Archived Member (Should Fail)",
            "DELETE",
            f"archived/members/{fake_id}",
            404
        )
        
        # Step 8: Test error handling - try to delete non-existent archived prospect
        success, error_response = self.run_test(
            "Delete Non-Existent Archived Prospect (Should Fail)",
            "DELETE",
            f"archived/prospects/{fake_id}",
            404
        )
        
        print(f"   🗑️  Archived delete functionality testing completed")
        return member_id, prospect_id

    def test_csv_export_decryption(self):
        """Test CSV export decryption verification - CRITICAL TEST"""
        print(f"\n🔓 Testing CSV Export Decryption...")
        
        # Step 1: Create test member with known phone and address data
        test_member = {
            "chapter": "National",
            "title": "Member",
            "handle": "CSVDecryptTest",
            "name": "CSV Decrypt Test Member",
            "email": "csvdecrypt@test.com",
            "phone": "555-1234-5678",  # Known phone number
            "address": "123 Decrypt Street, Test City, TC 12345"  # Known address
        }
        
        success, created_member = self.run_test(
            "Create Member for CSV Decryption Test",
            "POST",
            "members",
            201,
            data=test_member
        )
        
        member_id = None
        if success and 'id' in created_member:
            member_id = created_member['id']
            print(f"   Created member ID for CSV decryption test: {member_id}")
        else:
            print("❌ Failed to create member for CSV decryption test")
            return
        
        # Step 2: Export CSV and verify decryption
        success, csv_data = self.run_test(
            "Export Members CSV for Decryption Test",
            "GET",
            "members/export/csv",
            200
        )
        
        if success and isinstance(csv_data, str):
            # Check if CSV contains the BOM (UTF-8 marker)
            if csv_data.startswith('\ufeff'):
                self.log_test("CSV Export - UTF-8 BOM Present", True, "CSV starts with UTF-8 BOM")
                csv_content = csv_data[1:]  # Remove BOM for parsing
            else:
                self.log_test("CSV Export - UTF-8 BOM Present", False, "No UTF-8 BOM found")
                csv_content = csv_data
            
            # Parse CSV content
            csv_lines = csv_content.split('\n')
            if len(csv_lines) >= 2:  # Header + at least one data row
                header = csv_lines[0]
                
                # Find our test member in the CSV
                test_member_found = False
                decrypted_phone_found = False
                decrypted_address_found = False
                encrypted_data_found = False
                
                for line in csv_lines[1:]:
                    if line.strip() and 'CSVDecryptTest' in line:
                        test_member_found = True
                        
                        # Check if phone number appears as decrypted (formatted)
                        if '(555) 123-4567' in line or '555-1234-5678' in line:
                            decrypted_phone_found = True
                            self.log_test("CSV Export - Phone Number Decrypted", True, "Phone number appears in readable format")
                        
                        # Check if address appears as decrypted
                        if '123 Decrypt Street' in line:
                            decrypted_address_found = True
                            self.log_test("CSV Export - Address Decrypted", True, "Address appears in readable format")
                        
                        # Check for encrypted data patterns (should NOT be present)
                        if 'gAAAAAB' in line:
                            encrypted_data_found = True
                            self.log_test("CSV Export - No Encrypted Data", False, "Found encrypted data pattern 'gAAAAAB' in CSV")
                        
                        print(f"   Found test member in CSV: {line[:100]}...")
                        break
                
                if test_member_found:
                    self.log_test("CSV Export - Test Member Found", True, "Test member found in CSV export")
                    
                    if not decrypted_phone_found:
                        self.log_test("CSV Export - Phone Number Decrypted", False, "Phone number not found in readable format")
                    
                    if not decrypted_address_found:
                        self.log_test("CSV Export - Address Decrypted", False, "Address not found in readable format")
                    
                    if not encrypted_data_found:
                        self.log_test("CSV Export - No Encrypted Data", True, "No encrypted data patterns found in CSV")
                else:
                    self.log_test("CSV Export - Test Member Found", False, "Test member not found in CSV export")
                
                # Additional verification: Check CSV structure
                expected_columns = ['Chapter', 'Title', 'Member Handle', 'Name', 'Email Address', 'Phone Number', 'Mailing Address']
                found_columns = []
                for col in expected_columns:
                    if col in header:
                        found_columns.append(col)
                
                if len(found_columns) >= 5:  # At least basic columns
                    self.log_test("CSV Export - Required Columns Present", True, f"Found columns: {found_columns}")
                else:
                    self.log_test("CSV Export - Required Columns Present", False, f"Missing columns. Found: {found_columns}")
                
                # Check for meeting attendance columns (should be decrypted too)
                meeting_columns_found = 0
                meeting_patterns = ['Meeting - January', 'Meeting - February', 'Meeting - March']
                for pattern in meeting_patterns:
                    if pattern in header:
                        meeting_columns_found += 1
                
                if meeting_columns_found > 0:
                    self.log_test("CSV Export - Meeting Attendance Columns", True, f"Found {meeting_columns_found} meeting columns")
                else:
                    self.log_test("CSV Export - Meeting Attendance Columns", False, "No meeting attendance columns found")
            else:
                self.log_test("CSV Export - Valid CSV Structure", False, f"CSV has only {len(csv_lines)} lines")
        else:
            self.log_test("CSV Export - Response Format", False, "CSV export did not return string data")
        
        # Step 3: Clean up test member
        if member_id:
            success, delete_response = self.run_test(
                "Delete CSV Test Member (Cleanup)",
                "DELETE",
                f"members/{member_id}?reason=CSV%20Decryption%20Test%20Cleanup",
                200
            )
        
        print(f"   🔓 CSV export decryption testing completed")
        return member_id

    def run_review_tests(self):
        """Run the review request tests"""
        print("🚀 Starting BOH Directory API Testing - Review Request Features...")
        print(f"   Base URL: {self.base_url}")
        
        # Test authentication first
        success, response = self.test_login()
        if not success:
            print("❌ Authentication failed - cannot continue tests")
            return False
        
        # Run the new tests for the review request
        self.test_archived_delete_functionality()
        self.test_csv_export_decryption()
        
        # Print final results
        print(f"\n📊 Test Results Summary:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            return True
        else:
            print("⚠️  Some tests failed - check details above")
            return False

if __name__ == "__main__":
    tester = ReviewRequestTester()
    success = tester.run_review_tests()
    sys.exit(0 if success else 1)