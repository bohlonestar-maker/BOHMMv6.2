#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_test import BOHDirectoryAPITester

def run_priority_tests():
    """Run only the priority tests"""
    tester = BOHDirectoryAPITester()
    
    print("🚀 Starting Priority Backend Tests")
    print(f"Testing against: {tester.base_url}")
    print("=" * 60)
    
    # Test authentication first
    login_success, login_data = tester.test_login()
    if not login_success:
        print("❌ Login failed - cannot continue with priority tests")
        return
    
    print("\n🔥 RUNNING PRIORITY TESTS...")
    
    # Priority Test 1: Resend Invite Functionality
    print("\n" + "="*50)
    print("PRIORITY TEST 1: RESEND INVITE FUNCTIONALITY")
    print("="*50)
    tester.test_resend_invite_functionality()
    
    # Priority Test 2: Member Loading Regression
    print("\n" + "="*50)
    print("PRIORITY TEST 2: MEMBER LOADING REGRESSION")
    print("="*50)
    tester.test_member_loading_regression()
    
    # Print summary
    print("\n" + "=" * 60)
    print("🏁 PRIORITY TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL PRIORITY TESTS PASSED!")
    else:
        print("⚠️  Some priority tests failed - check details above")
        
        # Show failed tests
        failed_tests = [test for test in tester.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
    
    print("=" * 60)
    return tester.tests_passed == tester.tests_run

if __name__ == "__main__":
    success = run_priority_tests()
    sys.exit(0 if success else 1)