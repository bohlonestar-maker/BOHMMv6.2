#!/usr/bin/env python3
"""
Focused test for member creation and retrieval with encryption
Tests the specific scenario requested in the review.
"""

import requests
import json
import sys
import urllib3
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv('/app/backend/.env')

class EncryptionTester:
    def __init__(self):
        self.base_url = "https://memberportal-12.preview.emergentagent.com/api"
        self.token = None
        self.mongo_client = None
        self.db = None
        self.test_results = []
        
        # Connect to MongoDB for direct database inspection
        try:
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            db_name = os.environ.get('DB_NAME', 'test_database')
            self.mongo_client = MongoClient(mongo_url)
            self.db = self.mongo_client[db_name]
            print(f"✅ Connected to MongoDB: {mongo_url}/{db_name}")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            self.mongo_client = None
            self.db = None

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        return success

    def login_testadmin(self):
        """Login with testadmin credentials"""
        print("\n🔐 Testing Authentication with testadmin...")
        
        credentials = {
            "username": "testadmin",
            "password": "testpass123"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=credentials,
                headers={'Content-Type': 'application/json'},
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    self.token = data['token']
                    return self.log_result(
                        "Login with testadmin credentials",
                        True,
                        f"Token obtained: {self.token[:20]}..."
                    )
                else:
                    return self.log_result(
                        "Login with testadmin credentials",
                        False,
                        "No token in response"
                    )
            else:
                return self.log_result(
                    "Login with testadmin credentials",
                    False,
                    f"Status: {response.status_code}, Response: {response.text[:100]}"
                )
                
        except Exception as e:
            return self.log_result(
                "Login with testadmin credentials",
                False,
                f"Exception: {str(e)}"
            )

    def create_member_with_encryption_data(self):
        """Create a member with the specific test data"""
        print("\n👥 Creating Member with Encryption Test Data...")
        
        if not self.token:
            return self.log_result(
                "Create member (no token)",
                False,
                "No authentication token available"
            )
        
        # Test data as specified in the request
        member_data = {
            "chapter": "Test Chapter",
            "title": "Test Title",
            "handle": "TestHandle123",
            "name": "Test Member",
            "email": "encrypted@test.com",
            "phone": "555-1234-5678",
            "address": "123 Encrypted Street"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/members",
                json=member_data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.token}'
                },
                verify=False
            )
            
            if response.status_code == 201:
                created_member = response.json()
                
                # Verify all fields are present and readable
                success = True
                missing_fields = []
                
                for field, expected_value in member_data.items():
                    if field not in created_member:
                        missing_fields.append(field)
                        success = False
                    elif created_member[field] != expected_value:
                        success = False
                        missing_fields.append(f"{field} (value mismatch)")
                
                if success:
                    self.created_member_id = created_member.get('id')
                    return self.log_result(
                        "Create member with test data",
                        True,
                        f"Member created with ID: {self.created_member_id}"
                    )
                else:
                    return self.log_result(
                        "Create member with test data",
                        False,
                        f"Missing or incorrect fields: {missing_fields}"
                    )
            else:
                return self.log_result(
                    "Create member with test data",
                    False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            return self.log_result(
                "Create member with test data",
                False,
                f"Exception: {str(e)}"
            )

    def retrieve_member_and_verify_readable(self):
        """Retrieve the member and verify data is readable (not encrypted strings)"""
        print("\n📖 Retrieving Member and Verifying Readable Data...")
        
        if not hasattr(self, 'created_member_id') or not self.created_member_id:
            return self.log_result(
                "Retrieve member (no member ID)",
                False,
                "No member ID available from creation step"
            )
        
        try:
            # Test GET /api/members (list all)
            response = requests.get(
                f"{self.base_url}/members",
                headers={'Authorization': f'Bearer {self.token}'},
                verify=False
            )
            
            if response.status_code == 200:
                members = response.json()
                
                # Find our test member
                test_member = None
                for member in members:
                    if member.get('id') == self.created_member_id:
                        test_member = member
                        break
                
                if test_member:
                    # Verify sensitive data is readable (not encrypted)
                    email = test_member.get('email', '')
                    phone = test_member.get('phone', '')
                    address = test_member.get('address', '')
                    
                    # Check if data looks like readable text (not base64 encrypted strings)
                    email_readable = email == "encrypted@test.com"
                    phone_readable = phone == "555-1234-5678"
                    address_readable = address == "123 Encrypted Street"
                    
                    if email_readable and phone_readable and address_readable:
                        return self.log_result(
                            "Retrieve member - data is readable",
                            True,
                            f"Email: {email}, Phone: {phone}, Address: {address}"
                        )
                    else:
                        return self.log_result(
                            "Retrieve member - data is readable",
                            False,
                            f"Data appears encrypted: Email={email}, Phone={phone}, Address={address}"
                        )
                else:
                    return self.log_result(
                        "Retrieve member - find test member",
                        False,
                        f"Test member with ID {self.created_member_id} not found in list"
                    )
            else:
                return self.log_result(
                    "Retrieve member - API call",
                    False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            return self.log_result(
                "Retrieve member - exception",
                False,
                f"Exception: {str(e)}"
            )

    def verify_encryption_in_database(self):
        """Check if the data in MongoDB is actually encrypted"""
        print("\n🔒 Verifying Encryption in Database...")
        
        if self.db is None:
            return self.log_result(
                "Database encryption check (no DB connection)",
                False,
                "No database connection available"
            )
        
        if not hasattr(self, 'created_member_id') or not self.created_member_id:
            return self.log_result(
                "Database encryption check (no member ID)",
                False,
                "No member ID available"
            )
        
        try:
            # Query the database directly
            member_doc = self.db.members.find_one({"id": self.created_member_id})
            
            if member_doc:
                # Check if sensitive fields are encrypted in the database
                db_email = member_doc.get('email', '')
                db_phone = member_doc.get('phone', '')
                db_address = member_doc.get('address', '')
                
                # Encrypted data should not match the original readable values
                email_encrypted = db_email != "encrypted@test.com" and len(db_email) > 20
                phone_encrypted = db_phone != "555-1234-5678" and len(db_phone) > 15
                address_encrypted = db_address != "123 Encrypted Street" and len(db_address) > 25
                
                # Also check if they look like base64 encoded strings (typical for Fernet encryption)
                email_looks_encrypted = '=' in db_email or len(db_email) > 50
                phone_looks_encrypted = '=' in db_phone or len(db_phone) > 30
                address_looks_encrypted = '=' in db_address or len(db_address) > 40
                
                if email_encrypted and phone_encrypted and address_encrypted:
                    return self.log_result(
                        "Database encryption verification",
                        True,
                        f"Data is encrypted in DB - Email: {db_email[:30]}..., Phone: {db_phone[:20]}..., Address: {db_address[:30]}..."
                    )
                else:
                    return self.log_result(
                        "Database encryption verification",
                        False,
                        f"Data appears unencrypted in DB - Email: {db_email}, Phone: {db_phone}, Address: {db_address}"
                    )
            else:
                return self.log_result(
                    "Database encryption verification",
                    False,
                    f"Member document not found in database with ID: {self.created_member_id}"
                )
                
        except Exception as e:
            return self.log_result(
                "Database encryption verification",
                False,
                f"Exception: {str(e)}"
            )

    def test_response_validation(self):
        """Test that the response passes validation"""
        print("\n✅ Testing Response Validation...")
        
        if not hasattr(self, 'created_member_id') or not self.created_member_id:
            return self.log_result(
                "Response validation (no member ID)",
                False,
                "No member ID available"
            )
        
        try:
            # Get specific member by ID
            response = requests.get(
                f"{self.base_url}/members/{self.created_member_id}",
                headers={'Authorization': f'Bearer {self.token}'},
                verify=False
            )
            
            if response.status_code == 200:
                member = response.json()
                
                # Validate required fields are present
                required_fields = ['id', 'chapter', 'title', 'handle', 'name', 'email', 'phone', 'address', 'created_at', 'updated_at']
                missing_fields = [field for field in required_fields if field not in member]
                
                if not missing_fields:
                    # Validate data types and formats
                    validation_errors = []
                    
                    # Check email format
                    email = member.get('email', '')
                    if '@' not in email:
                        validation_errors.append("Invalid email format")
                    
                    # Check that timestamps are present
                    if not member.get('created_at'):
                        validation_errors.append("Missing created_at timestamp")
                    
                    if not member.get('updated_at'):
                        validation_errors.append("Missing updated_at timestamp")
                    
                    # Check meeting_attendance structure
                    if 'meeting_attendance' in member:
                        attendance = member['meeting_attendance']
                        if not isinstance(attendance, dict):
                            validation_errors.append("meeting_attendance should be a dict")
                    
                    if not validation_errors:
                        return self.log_result(
                            "Response validation",
                            True,
                            f"All required fields present and valid: {required_fields}"
                        )
                    else:
                        return self.log_result(
                            "Response validation",
                            False,
                            f"Validation errors: {validation_errors}"
                        )
                else:
                    return self.log_result(
                        "Response validation",
                        False,
                        f"Missing required fields: {missing_fields}"
                    )
            else:
                return self.log_result(
                    "Response validation",
                    False,
                    f"Failed to get member: Status {response.status_code}"
                )
                
        except Exception as e:
            return self.log_result(
                "Response validation",
                False,
                f"Exception: {str(e)}"
            )

    def cleanup_test_data(self):
        """Clean up the test member"""
        print("\n🧹 Cleaning up test data...")
        
        if not hasattr(self, 'created_member_id') or not self.created_member_id:
            return self.log_result(
                "Cleanup (no member ID)",
                True,
                "No member to clean up"
            )
        
        try:
            response = requests.delete(
                f"{self.base_url}/members/{self.created_member_id}",
                headers={'Authorization': f'Bearer {self.token}'},
                verify=False
            )
            
            if response.status_code == 200:
                return self.log_result(
                    "Cleanup test member",
                    True,
                    f"Test member {self.created_member_id} deleted successfully"
                )
            else:
                return self.log_result(
                    "Cleanup test member",
                    False,
                    f"Failed to delete: Status {response.status_code}"
                )
                
        except Exception as e:
            return self.log_result(
                "Cleanup test member",
                False,
                f"Exception: {str(e)}"
            )

    def run_encryption_tests(self):
        """Run all encryption-related tests"""
        print("🔐 Starting Member Encryption Tests")
        print("=" * 60)
        
        # Step 1: Login with testadmin
        if not self.login_testadmin():
            print("❌ Cannot continue without authentication")
            return self.generate_report()
        
        # Step 2: Create member with test data
        if not self.create_member_with_encryption_data():
            print("❌ Cannot continue without creating member")
            return self.generate_report()
        
        # Step 3: Retrieve member and verify data is readable
        self.retrieve_member_and_verify_readable()
        
        # Step 4: Verify response passes validation
        self.test_response_validation()
        
        # Step 5: Check encryption in database
        self.verify_encryption_in_database()
        
        # Step 6: Cleanup
        self.cleanup_test_data()
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        print(f"📊 Encryption Test Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All encryption tests passed!")
        else:
            print(f"⚠️  {total_tests - passed_tests} tests failed")
            
            # Show failed tests
            failed_tests = [test for test in self.test_results if not test['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        # Close MongoDB connection
        if self.mongo_client:
            self.mongo_client.close()
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "test_results": self.test_results
        }

def main():
    tester = EncryptionTester()
    results = tester.run_encryption_tests()
    
    # Return appropriate exit code
    return 0 if results["success_rate"] == 100 else 1

if __name__ == "__main__":
    sys.exit(main())