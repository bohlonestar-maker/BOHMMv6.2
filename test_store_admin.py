#!/usr/bin/env python3
"""
Store Admin Management and Auto-Sync Feature Testing
Test the new Store Admin Management and Auto-Sync features for BOHTC Store
"""

import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class StoreAdminTester:
    def __init__(self, base_url="https://memberportal-12.preview.emergentagent.com/api"):
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
            f"Login with {username}",
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

    def test_store_admin_management(self):
        """Test Store Admin Management and Auto-Sync features"""
        print(f"\n🏪 Testing Store Admin Management and Auto-Sync Features...")
        
        # Test 1: Store Admin Status Endpoint
        print(f"\n   📊 Test 1: Store Admin Status Endpoint...")
        success, status_response = self.run_test(
            "GET /api/store/admins/status - Store Admin Status",
            "GET",
            "store/admins/status",
            200
        )
        
        if success:
            # Verify response includes required fields
            required_fields = ['can_manage_store', 'is_primary_admin', 'is_delegated_admin', 'can_manage_admins']
            missing_fields = [field for field in required_fields if field not in status_response]
            
            if not missing_fields:
                self.log_test("Store Admin Status - Required Fields", True, f"All required fields present: {required_fields}")
                
                # For admin user (Prez title), should return is_primary_admin=true, can_manage_admins=true
                if status_response.get('is_primary_admin') == True and status_response.get('can_manage_admins') == True:
                    self.log_test("Store Admin Status - Primary Admin Rights", True, "Admin user has primary admin rights")
                else:
                    self.log_test("Store Admin Status - Primary Admin Rights", False, f"Expected primary admin rights, got: {status_response}")
            else:
                self.log_test("Store Admin Status - Required Fields", False, f"Missing fields: {missing_fields}")
        
        # Test 2: Store Admin List Endpoints
        print(f"\n   📋 Test 2: Store Admin List Endpoints...")
        success, admins_list = self.run_test(
            "GET /api/store/admins - List Delegated Store Admins",
            "GET",
            "store/admins",
            200
        )
        
        if success:
            if isinstance(admins_list, list):
                self.log_test("Store Admin List - Response Format", True, f"Returned list with {len(admins_list)} admins")
            else:
                self.log_test("Store Admin List - Response Format", False, "Expected list response")
        
        success, eligible_list = self.run_test(
            "GET /api/store/admins/eligible - List Eligible National Users",
            "GET",
            "store/admins/eligible",
            200
        )
        
        if success:
            if isinstance(eligible_list, list):
                self.log_test("Store Admin Eligible List - Response Format", True, f"Returned list with {len(eligible_list)} eligible users")
            else:
                self.log_test("Store Admin Eligible List - Response Format", False, "Expected list response")
        
        # Test 3: Store Admin CRUD Tests
        print(f"\n   🔧 Test 3: Store Admin CRUD Operations...")
        # Test adding a delegated admin (should fail if user doesn't exist)
        success, add_response = self.run_test(
            "POST /api/store/admins - Add Non-existent User (Should Fail)",
            "POST",
            "store/admins",
            400,  # Should fail
            data={"username": "nonexistentuser"}
        )
        
        # Test 4: Permission Verification - Store Product Endpoints
        print(f"\n   🔐 Test 4: Store Product Endpoints with New Permission System...")
        
        # Test store product endpoints still work
        success, products = self.run_test(
            "GET /api/store/products - Store Products with New Permission System",
            "GET",
            "store/products",
            200
        )
        
        if success and isinstance(products, list):
            self.log_test("Store Products - New Permission System", True, f"Retrieved {len(products)} products")
            
            # If we have products, test other CRUD operations
            if len(products) > 0:
                product_id = products[0].get('id')
                
                # Test GET single product
                if product_id:
                    success, product = self.run_test(
                        "GET /api/store/products/{id} - Single Product",
                        "GET",
                        f"store/products/{product_id}",
                        200
                    )
                
                # Test POST new product (should work for primary admin)
                test_product = {
                    "name": "Test Admin Product",
                    "description": "Test product for admin management",
                    "price": 25.00,
                    "category": "merchandise",
                    "inventory_count": 10
                }
                
                success, created_product = self.run_test(
                    "POST /api/store/products - Create Product with New Permission System",
                    "POST",
                    "store/products",
                    201,
                    data=test_product
                )
                
                created_product_id = None
                if success and 'id' in created_product:
                    created_product_id = created_product['id']
                    
                    # Test PUT update product
                    update_data = {
                        "name": "Updated Test Admin Product",
                        "price": 30.00
                    }
                    
                    success, updated_product = self.run_test(
                        "PUT /api/store/products/{id} - Update Product with New Permission System",
                        "PUT",
                        f"store/products/{created_product_id}",
                        200,
                        data=update_data
                    )
                    
                    # Test DELETE product
                    success, delete_response = self.run_test(
                        "DELETE /api/store/products/{id} - Delete Product with New Permission System",
                        "DELETE",
                        f"store/products/{created_product_id}",
                        200
                    )
        
        # Test 5: Auto-Sync on Login Test
        print(f"\n   🔄 Test 5: Auto-Sync on Login...")
        
        # Login should trigger background catalog sync - check backend logs
        # We'll test this by doing a fresh login and checking if sync was triggered
        original_token = self.token
        self.token = None
        
        success, login_response = self.run_test(
            "POST /api/auth/login - Auto-Sync Trigger Test",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        
        if success:
            self.log_test("Auto-Sync on Login - Login Successful", True, "Login completed (auto-sync should be triggered in background)")
            # Note: We can't directly test the background sync without checking logs
            # The sync happens asynchronously and doesn't affect the login response
        
        self.token = original_token
        
        # Test 6: Square Webhook Signature Test
        print(f"\n   🔗 Test 6: Square Webhook Signature Configuration...")
        success, webhook_info = self.run_test(
            "GET /api/webhooks/square/info - Webhook Signature Configuration",
            "GET",
            "webhooks/square/info",
            200
        )
        
        if success:
            if 'signature_key_configured' in webhook_info:
                if webhook_info['signature_key_configured'] == True:
                    self.log_test("Square Webhook Signature - Configuration", True, "Signature key is configured")
                else:
                    self.log_test("Square Webhook Signature - Configuration", False, "Signature key is not configured")
            else:
                self.log_test("Square Webhook Signature - Response Format", False, "Missing signature_key_configured field")
        
        # Test 7: Store Sync Endpoint
        print(f"\n   🔄 Test 7: Manual Store Sync Endpoint...")
        success, sync_response = self.run_test(
            "POST /api/store/sync-square-catalog - Manual Sync with New Permission System",
            "POST",
            "store/sync-square-catalog",
            200
        )
        
        if success:
            if 'message' in sync_response:
                self.log_test("Store Sync Endpoint - New Permission System", True, f"Sync response: {sync_response.get('message', 'No message')}")
            else:
                self.log_test("Store Sync Endpoint - Response Format", False, "Missing message field in sync response")
        
        print(f"\n   🏪 Store Admin Management and Auto-Sync testing completed")

    def check_backend_logs(self):
        """Check backend logs for auto-sync messages"""
        print(f"\n📋 Checking Backend Logs for Auto-Sync Messages...")
        
        try:
            import subprocess
            # Check supervisor backend error logs for auto-sync messages (they're logged there)
            result = subprocess.run(
                ['tail', '-n', '100', '/var/log/supervisor/backend.err.log'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                log_content = result.stdout
                
                # Look for auto-sync related messages
                auto_sync_triggered = "Auto-sync triggered" in log_content
                auto_sync_completed = "Auto-sync completed" in log_content
                
                if auto_sync_triggered:
                    self.log_test("Backend Logs - Auto-sync Triggered", True, "Found 'Auto-sync triggered' message in logs")
                else:
                    self.log_test("Backend Logs - Auto-sync Triggered", False, "No 'Auto-sync triggered' message found in recent logs")
                
                if auto_sync_completed:
                    self.log_test("Backend Logs - Auto-sync Completed", True, "Found 'Auto-sync completed' message in logs")
                else:
                    self.log_test("Backend Logs - Auto-sync Completed", False, "No 'Auto-sync completed' message found in recent logs")
                
                # Show recent log entries related to sync
                sync_lines = [line for line in log_content.split('\n') if 'Auto-sync' in line]
                if sync_lines:
                    print(f"   Recent auto-sync log entries:")
                    for line in sync_lines[-3:]:  # Show last 3 auto-sync entries
                        print(f"     {line}")
                
            else:
                self.log_test("Backend Logs - Access", False, "Could not access backend logs")
                
        except Exception as e:
            self.log_test("Backend Logs - Check", False, f"Error checking logs: {str(e)}")

    def run_all_tests(self):
        """Run all Store Admin Management tests"""
        print("🚀 Starting Store Admin Management and Auto-Sync Feature Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 80)
        
        # Test authentication first
        login_success, login_data = self.test_login()
        if not login_success:
            print("❌ Login failed - cannot continue with other tests")
            return self.generate_report()
        
        # Run Store Admin Management tests
        self.test_store_admin_management()
        
        # Check backend logs for auto-sync messages
        self.check_backend_logs()
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 80)
        print(f"📊 Store Admin Management Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            success_rate = 100
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            success_rate = (self.tests_passed / self.tests_run) * 100
        
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        # Show successful tests summary
        successful_tests = [test for test in self.test_results if test['success']]
        if successful_tests:
            print(f"\n✅ Successful Tests ({len(successful_tests)}):")
            for test in successful_tests:
                print(f"   - {test['test']}")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "failed_test_details": failed_tests
        }

if __name__ == "__main__":
    # Run the Store Admin Management tests
    tester = StoreAdminTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["failed_tests"] == 0:
        sys.exit(0)
    else:
        sys.exit(1)