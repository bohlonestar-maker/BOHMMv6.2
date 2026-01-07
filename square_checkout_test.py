#!/usr/bin/env python3
"""
Square Hosted Checkout Test Script
Tests the Square Hosted Checkout implementation for BOHTC Store
"""

import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SquareCheckoutTester:
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

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, params=params, verify=False)
            elif method == 'POST':
                if params:
                    response = requests.post(url, json=data, headers=test_headers, params=params, verify=False)
                else:
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

    def test_square_checkout_functionality(self):
        """Test Square Hosted Checkout functionality - PRIORITY TEST"""
        print(f"\n💳 Testing Square Hosted Checkout Functionality...")
        
        # Test 1: Get products list (verify products exist)
        success, products = self.run_test(
            "Get Store Products",
            "GET",
            "store/products",
            200
        )
        
        if not success or not products:
            print("❌ No products available - cannot test checkout")
            return
        
        # Find a product to add to cart
        test_product = None
        for product in products:
            if product.get('is_active', True):
                test_product = product
                break
        
        if not test_product:
            print("❌ No active products found - cannot test checkout")
            return
        
        print(f"   Using test product: {test_product.get('name', 'Unknown')} (ID: {test_product.get('id')})")
        
        # Test 2: Add product to cart
        cart_params = {
            "product_id": test_product['id'],
            "quantity": 1
        }
        
        # Add variation if product has variations
        if test_product.get('has_variations') and test_product.get('variations'):
            variation = test_product['variations'][0]
            cart_params["variation_id"] = variation.get('id')
        
        success, add_response = self.run_test(
            "Add Product to Cart",
            "POST",
            "store/cart/add",
            200,
            params=cart_params
        )
        
        if not success:
            print("❌ Failed to add product to cart - cannot test checkout")
            return
        
        # Test 3: Verify cart has items
        success, cart = self.run_test(
            "Get Cart Contents",
            "GET",
            "store/cart",
            200
        )
        
        if not success or not cart.get('items'):
            print("❌ Cart is empty after adding item - cannot test checkout")
            return
        
        cart_items = cart.get('items', [])
        print(f"   Cart contains {len(cart_items)} item(s)")
        
        # Test 4: Call POST /api/store/checkout endpoint
        checkout_data = {
            "shipping_address": "123 Test Street, Test City, TC 12345",
            "notes": "Test order for Square checkout"
        }
        
        success, checkout_response = self.run_test(
            "Create Square Checkout Link",
            "POST",
            "store/checkout",
            200,
            data=checkout_data
        )
        
        if success:
            # Test 5: Verify response contains required fields
            required_fields = ['success', 'checkout_url', 'order_id', 'square_order_id', 'total']
            missing_fields = [field for field in required_fields if field not in checkout_response]
            
            if not missing_fields:
                self.log_test("Checkout Response - Required Fields", True, f"All required fields present: {required_fields}")
                
                # Verify success is true
                if checkout_response.get('success') == True:
                    self.log_test("Checkout Response - Success Flag", True, "success=True")
                else:
                    self.log_test("Checkout Response - Success Flag", False, f"success={checkout_response.get('success')}")
                
                # Verify checkout_url format
                checkout_url = checkout_response.get('checkout_url', '')
                if checkout_url.startswith('https://square.link/') or checkout_url.startswith('https://checkout.square.site/'):
                    self.log_test("Checkout URL Format", True, f"Valid Square URL: {checkout_url[:50]}...")
                else:
                    self.log_test("Checkout URL Format", False, f"Invalid URL format: {checkout_url}")
                
                # Verify order_id is present and valid
                order_id = checkout_response.get('order_id')
                if order_id and isinstance(order_id, str) and len(order_id) > 0:
                    self.log_test("Order ID Present", True, f"Order ID: {order_id}")
                else:
                    self.log_test("Order ID Present", False, f"Invalid order_id: {order_id}")
                
                # Verify square_order_id is present
                square_order_id = checkout_response.get('square_order_id')
                if square_order_id and isinstance(square_order_id, str) and len(square_order_id) > 0:
                    self.log_test("Square Order ID Present", True, f"Square Order ID: {square_order_id}")
                else:
                    self.log_test("Square Order ID Present", False, f"Invalid square_order_id: {square_order_id}")
                
                # Verify total is numeric
                total = checkout_response.get('total')
                if isinstance(total, (int, float)) and total > 0:
                    self.log_test("Total Amount Valid", True, f"Total: ${total}")
                else:
                    self.log_test("Total Amount Valid", False, f"Invalid total: {total}")
                
            else:
                self.log_test("Checkout Response - Required Fields", False, f"Missing fields: {missing_fields}")
        
        # Test 6: Verify cart is cleared after checkout call
        success, cart_after = self.run_test(
            "Verify Cart Cleared After Checkout",
            "GET",
            "store/cart",
            200
        )
        
        if success:
            items_after = cart_after.get('items', [])
            if len(items_after) == 0:
                self.log_test("Cart Cleared After Checkout", True, "Cart is empty after checkout")
            else:
                self.log_test("Cart Cleared After Checkout", False, f"Cart still has {len(items_after)} items")
        
        # Test 7: Verify order was created in database with "pending" status
        if success and checkout_response and checkout_response.get('order_id'):
            order_id = checkout_response['order_id']
            success, order_details = self.run_test(
                "Get Created Order Details",
                "GET",
                f"store/orders/{order_id}",
                200
            )
            
            if success:
                # Verify order status is "pending"
                if order_details.get('status') == 'pending':
                    self.log_test("Order Status Pending", True, "Order created with pending status")
                else:
                    self.log_test("Order Status Pending", False, f"Order status: {order_details.get('status')}")
                
                # Verify order contains items
                order_items = order_details.get('items', [])
                if len(order_items) > 0:
                    self.log_test("Order Contains Items", True, f"Order has {len(order_items)} items")
                else:
                    self.log_test("Order Contains Items", False, "Order has no items")
                
                # Verify shipping address was saved
                if order_details.get('shipping_address') == checkout_data['shipping_address']:
                    self.log_test("Shipping Address Saved", True, "Shipping address matches")
                else:
                    self.log_test("Shipping Address Saved", False, f"Address mismatch: {order_details.get('shipping_address')}")
        
        print(f"   💳 Square checkout functionality testing completed")

    def test_square_checkout_edge_cases(self):
        """Test Square Checkout edge cases"""
        print(f"\n🚫 Testing Square Checkout Edge Cases...")
        
        # Test 1: Checkout with empty cart (should return 400 error)
        # First ensure cart is empty
        success, cart = self.run_test(
            "Get Cart for Empty Test",
            "GET",
            "store/cart",
            200
        )
        
        # If cart has items, we need to clear it first by doing a checkout or manually clearing
        if success and cart.get('items'):
            print("   Cart has items, clearing for empty cart test...")
            # We'll test with empty cart by using a different approach
        
        # Try checkout with empty cart
        success, response = self.run_test(
            "Checkout with Empty Cart (Should Fail)",
            "POST",
            "store/checkout",
            400,  # Should return 400 error
            data={"shipping_address": "Test Address"}
        )
        
        # Test 2: Checkout without authentication (should return 401 error)
        original_token = self.token
        self.token = None  # Remove authentication
        
        success, response = self.run_test(
            "Checkout without Authentication (Should Fail)",
            "POST",
            "store/checkout",
            401,  # Should return 401 error
            data={"shipping_address": "Test Address"}
        )
        
        # Restore authentication
        self.token = original_token
        
        print(f"   🚫 Square checkout edge cases testing completed")

    def run_all_tests(self):
        """Run all Square checkout tests"""
        print("🚀 Starting Square Hosted Checkout Tests...")
        print(f"   Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test authentication first
        success, response = self.test_login()
        if not success:
            print("❌ Authentication failed - cannot continue with other tests")
            return
        
        # Test Square Hosted Checkout functionality
        self.test_square_checkout_functionality()
        self.test_square_checkout_edge_cases()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
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
        
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate,
            "failed_tests": failed_tests,
            "all_results": self.test_results
        }

if __name__ == "__main__":
    tester = SquareCheckoutTester()
    tester.run_all_tests()