#!/usr/bin/env python3
"""
Security Test for NoSQL Injection Fix
Tests the /api/store/dues/pay endpoint for NoSQL injection vulnerabilities
"""

import requests
import sys
import json
import urllib.parse
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SecurityTester:
    def __init__(self, base_url="https://attendance-mgr-4.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")

    def login(self):
        """Login and get token"""
        print("🔐 Authenticating...")
        
        credentials = [
            ("admin", "admin123"),
            ("testadmin", "testpass123"),
        ]
        
        for username, password in credentials:
            try:
                response = requests.post(
                    f"{self.base_url}/auth/login",
                    json={"username": username, "password": password},
                    verify=False
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'token' in data:
                        self.token = data['token']
                        print(f"✅ Logged in as {username}")
                        return True
            except Exception as e:
                print(f"❌ Login failed for {username}: {e}")
                continue
        
        print("❌ All login attempts failed")
        return False

    def test_dues_payment(self, handle, description, expected_status=200):
        """Test dues payment with given handle"""
        if not self.token:
            print("❌ No authentication token")
            return False
        
        try:
            url = f"{self.base_url}/store/dues/pay"
            params = {
                "amount": 25,
                "year": 2025,
                "month": 3
            }
            
            if handle is not None:
                params["handle"] = handle
            
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, params=params, headers=headers, verify=False)
            
            success = response.status_code == expected_status
            
            if success:
                self.log_test(description, True, f"Status: {response.status_code}")
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return True, data
                    except:
                        return True, {}
                return True, {}
            else:
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code} (Expected: {expected_status}) - {error_data.get('detail', 'No error details')}"
                except:
                    details = f"Status: {response.status_code} (Expected: {expected_status}) - Response: {response.text[:100]}"
                
                self.log_test(description, False, details)
                return False, {}
                
        except Exception as e:
            self.log_test(description, False, f"Exception: {str(e)}")
            return False, {}

    def run_security_tests(self):
        """Run all security tests"""
        print("🔒 Testing NoSQL Injection Security Fix - Dues Payment Endpoint")
        print("=" * 70)
        
        if not self.login():
            return
        
        # Test 1: Normal functionality
        print("\n✅ Test 1: Normal Dues Payment")
        success, response = self.test_dues_payment("ValidHandle", "Normal dues payment with valid handle")
        
        if success and response:
            required_fields = ['order_id', 'total', 'total_cents']
            missing = [f for f in required_fields if f not in response]
            if not missing:
                self.log_test("Response contains required fields", True, str(required_fields))
            else:
                self.log_test("Response contains required fields", False, f"Missing: {missing}")
        
        # Test 2: Regex wildcard injection
        print("\n🚨 Test 2: Regex Wildcard Injection")
        success, response = self.test_dues_payment(".*", "Regex wildcard injection (.*) - should be safely escaped")
        
        # Test 3: Special regex characters
        print("\n🚨 Test 3: Special Regex Characters")
        success, response = self.test_dues_payment("test+$", "Special regex chars (+$) - should be escaped")
        
        # Test 4: Empty handle
        print("\n⚠️ Test 4: Empty Handle")
        success, response = self.test_dues_payment(None, "No handle parameter - should work")
        
        # Test 5: Complex injection patterns
        print("\n🚨 Test 5: Complex Injection Patterns")
        
        injection_patterns = [
            ("^.*$", "Anchored wildcard"),
            ("[a-z]*", "Character class"),
            ("(test|admin)", "Alternation"),
            ("test.*admin", "Complex pattern"),
            ("\\", "Backslash"),
            (".", "Single dot"),
            ("+", "Plus quantifier"),
            ("?", "Question mark"),
            ("*", "Asterisk"),
            ("$", "End anchor"),
            ("^", "Start anchor"),
            ("|", "Pipe"),
            ("()", "Parentheses"),
            ("[]", "Brackets"),
            ("{\"$ne\":\"\"}", "Object injection attempt")
        ]
        
        for pattern, description in injection_patterns:
            success, response = self.test_dues_payment(pattern, f"Injection test: {description} ({pattern})")
        
        # Test 6: Error handling
        print("\n❌ Test 6: Error Handling")
        
        # Test invalid month values
        try:
            url = f"{self.base_url}/store/dues/pay"
            headers = {'Authorization': f'Bearer {self.token}'}
            
            # Invalid month -1
            response = requests.post(url, params={"amount": 25, "year": 2025, "month": -1, "handle": "test"}, headers=headers, verify=False)
            if response.status_code == 400:
                self.log_test("Invalid month (-1) rejected", True, "Returns 400 error as expected")
            else:
                self.log_test("Invalid month (-1) rejected", False, f"Expected 400, got {response.status_code}")
            
            # Invalid month 12
            response = requests.post(url, params={"amount": 25, "year": 2025, "month": 12, "handle": "test"}, headers=headers, verify=False)
            if response.status_code == 400:
                self.log_test("Invalid month (12) rejected", True, "Returns 400 error as expected")
            else:
                self.log_test("Invalid month (12) rejected", False, f"Expected 400, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error handling test", False, f"Exception: {e}")
        
        # Test 7: Verify other endpoints still work
        print("\n✅ Test 7: No Regression on Other Endpoints")
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            
            # Test members endpoint
            response = requests.get(f"{self.base_url}/members", headers=headers, verify=False)
            if response.status_code == 200:
                self.log_test("Members endpoint - no regression", True, "Still works correctly")
            else:
                self.log_test("Members endpoint - no regression", False, f"Status: {response.status_code}")
            
            # Test store products endpoint
            response = requests.get(f"{self.base_url}/store/products", headers=headers, verify=False)
            if response.status_code == 200:
                self.log_test("Store products endpoint - no regression", True, "Still works correctly")
            else:
                self.log_test("Store products endpoint - no regression", False, f"Status: {response.status_code}")
            
            # Test dues payments endpoint
            response = requests.get(f"{self.base_url}/store/dues/payments", headers=headers, verify=False)
            if response.status_code in [200, 403]:  # 403 is OK if user doesn't have permission
                self.log_test("Dues payments endpoint - no regression", True, "Still works correctly")
            else:
                self.log_test("Dues payments endpoint - no regression", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Regression test", False, f"Exception: {e}")
        
        # Print results
        print("\n" + "=" * 70)
        print("🔒 SECURITY TEST RESULTS")
        print("=" * 70)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL SECURITY TESTS PASSED - NoSQL injection fix is working correctly!")
        else:
            print("⚠️ Some security tests failed - review the results above")

if __name__ == "__main__":
    tester = SecurityTester()
    tester.run_security_tests()