#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_test import BOHDirectoryAPITester

def main():
    tester = BOHDirectoryAPITester()
    
    # Login first
    login_success, login_data = tester.test_login()
    if not login_success:
        print("❌ Login failed - cannot continue with bulk promotion test")
        return 1
    
    # Run only the bulk promotion test
    tester.test_bulk_promotion_functionality()
    
    # Generate report
    results = tester.generate_report()
    return 0 if results["success_rate"] == 100 else 1

if __name__ == "__main__":
    sys.exit(main())