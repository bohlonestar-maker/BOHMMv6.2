#!/usr/bin/env python3
"""
Discord Import Matching Algorithm Test Script
Tests the enhanced fuzzy matching algorithm for linking Discord members to database members.
"""

import sys
import os
sys.path.append('/app')

from backend_test import BOHDirectoryAPITester

def main():
    """Run only the Discord import matching algorithm test"""
    print("🔗 Discord Import Matching Algorithm Test")
    print("=" * 50)
    
    # Initialize tester
    tester = BOHDirectoryAPITester()
    
    # Run the specific test
    try:
        matched_count, match_details = tester.test_discord_import_matching_algorithm()
        
        # Print final summary
        print(f"\n📊 Discord Import Test Summary:")
        print(f"   Total tests run: {tester.tests_run}")
        print(f"   Tests passed: {tester.tests_passed}")
        print(f"   Tests failed: {tester.tests_run - tester.tests_passed}")
        print(f"   Success rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
        
        if matched_count is not None:
            print(f"   Matched Discord members: {matched_count}")
            if match_details:
                print(f"   Match details available: {len(match_details)} entries")
        
        if tester.tests_passed == tester.tests_run:
            print("🎉 All Discord import tests passed!")
            return True
        else:
            print("⚠️  Some Discord import tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Error running Discord import test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)