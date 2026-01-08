#!/usr/bin/env python3
"""
Discord Analytics Data Pipeline Investigation
============================================

This script investigates the Discord analytics data pipeline to find where data is being lost.
Based on the review request, we need to:

1. Check raw database data (discord_voice_activity and discord_text_activity collections)
2. Test the analytics aggregation (GET /api/discord/analytics)
3. Compare data at each step
4. Verify if usernames are being resolved correctly from discord_members

The logs show the bot IS detecting activity from users like:
- ⭐NSEC Lonestar⭐ (ID: 1288662056748191766) 
- HAB Goat Roper (ID: 127638717115400192)

But the dashboard may not be showing all this activity.
"""

import requests
import sys
import json
from datetime import datetime
import urllib3
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DiscordAnalyticsInvestigator:
    def __init__(self, base_url="https://dues-tracker-15.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Load environment variables for direct database access
        load_dotenv('/app/backend/.env')
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'test_database')
        
        # Initialize MongoDB client for direct database queries
        try:
            self.mongo_client = MongoClient(self.mongo_url)
            self.db = self.mongo_client[self.db_name]
            print(f"✅ Connected to MongoDB: {self.mongo_url}/{self.db_name}")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            self.mongo_client = None
            self.db = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def login(self):
        """Login and get authentication token"""
        print(f"\n🔐 Authenticating...")
        
        # Try testadmin/testpass123 as specified in review request
        credentials = [
            ("testadmin", "testpass123"),
            ("admin", "admin123"),
            ("Lonestar", "password"),
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
                        print(f"✅ Successfully logged in as {username}")
                        return True
                        
            except Exception as e:
                print(f"❌ Login attempt failed for {username}: {e}")
                continue
        
        print("❌ All login attempts failed")
        return False

    def query_database_direct(self, collection_name, query=None, limit=None):
        """Query MongoDB database directly"""
        if self.db is None:
            return None, "No database connection"
        
        try:
            collection = self.db[collection_name]
            
            if query is None:
                query = {}
            
            cursor = collection.find(query)
            if limit:
                cursor = cursor.limit(limit)
            
            results = list(cursor)
            return results, None
            
        except Exception as e:
            return None, str(e)

    def investigate_raw_database_data(self):
        """Step 1: Check raw database data"""
        print(f"\n📊 STEP 1: Investigating Raw Database Data...")
        
        # Check discord_voice_activity collection
        print(f"\n   🎤 Checking discord_voice_activity collection...")
        voice_records, error = self.query_database_direct('discord_voice_activity')
        
        if error:
            self.log_test("Query discord_voice_activity collection", False, f"Database error: {error}")
        else:
            total_voice_records = len(voice_records)
            self.log_test("Query discord_voice_activity collection", True, f"Found {total_voice_records} voice activity records")
            
            if total_voice_records > 0:
                # Show sample records
                print(f"   📋 Sample voice activity records:")
                for i, record in enumerate(voice_records[:3]):
                    print(f"      Record {i+1}: User {record.get('discord_user_id', 'Unknown')} - Channel: {record.get('channel_name', 'Unknown')} - Duration: {record.get('duration_seconds', 0)}s")
                
                # Check for specific users mentioned in logs
                lonestar_voice = [r for r in voice_records if r.get('discord_user_id') == '1288662056748191766']
                goat_roper_voice = [r for r in voice_records if r.get('discord_user_id') == '127638717115400192']
                
                self.log_test("Lonestar voice activity in database", len(lonestar_voice) > 0, f"Found {len(lonestar_voice)} voice records for Lonestar (1288662056748191766)")
                self.log_test("HAB Goat Roper voice activity in database", len(goat_roper_voice) > 0, f"Found {len(goat_roper_voice)} voice records for HAB Goat Roper (127638717115400192)")
            
        # Check discord_text_activity collection
        print(f"\n   💬 Checking discord_text_activity collection...")
        text_records, error = self.query_database_direct('discord_text_activity')
        
        if error:
            self.log_test("Query discord_text_activity collection", False, f"Database error: {error}")
        else:
            total_text_records = len(text_records)
            self.log_test("Query discord_text_activity collection", True, f"Found {total_text_records} text activity records")
            
            if total_text_records > 0:
                # Show sample records
                print(f"   📋 Sample text activity records:")
                for i, record in enumerate(text_records[:3]):
                    print(f"      Record {i+1}: User {record.get('discord_user_id', 'Unknown')} - Channel: {record.get('channel_name', 'Unknown')} - Messages: {record.get('message_count', 0)}")
                
                # Check for specific users mentioned in logs
                lonestar_text = [r for r in text_records if r.get('discord_user_id') == '1288662056748191766']
                goat_roper_text = [r for r in text_records if r.get('discord_user_id') == '127638717115400192']
                
                self.log_test("Lonestar text activity in database", len(lonestar_text) > 0, f"Found {len(lonestar_text)} text records for Lonestar (1288662056748191766)")
                self.log_test("HAB Goat Roper text activity in database", len(goat_roper_text) > 0, f"Found {len(goat_roper_text)} text records for HAB Goat Roper (127638717115400192)")
        
        # Check discord_members collection for username resolution
        print(f"\n   👥 Checking discord_members collection...")
        members_records, error = self.query_database_direct('discord_members')
        
        if error:
            self.log_test("Query discord_members collection", False, f"Database error: {error}")
        else:
            total_members = len(members_records)
            self.log_test("Query discord_members collection", True, f"Found {total_members} Discord member records")
            
            if total_members > 0:
                # Check for specific users
                lonestar_member = None
                goat_roper_member = None
                
                for member in members_records:
                    if member.get('discord_id') == '1288662056748191766':
                        lonestar_member = member
                    elif member.get('discord_id') == '127638717115400192':
                        goat_roper_member = member
                
                if lonestar_member:
                    self.log_test("Lonestar in discord_members", True, f"Found: {lonestar_member.get('username', 'Unknown')} / {lonestar_member.get('display_name', 'Unknown')}")
                else:
                    self.log_test("Lonestar in discord_members", False, "Lonestar (1288662056748191766) not found in discord_members")
                
                if goat_roper_member:
                    self.log_test("HAB Goat Roper in discord_members", True, f"Found: {goat_roper_member.get('username', 'Unknown')} / {goat_roper_member.get('display_name', 'Unknown')}")
                else:
                    self.log_test("HAB Goat Roper in discord_members", False, "HAB Goat Roper (127638717115400192) not found in discord_members")
        
        return {
            'voice_records': total_voice_records if voice_records else 0,
            'text_records': total_text_records if text_records else 0,
            'members': total_members if members_records else 0,
            'lonestar_voice': len(lonestar_voice) if 'lonestar_voice' in locals() else 0,
            'lonestar_text': len(lonestar_text) if 'lonestar_text' in locals() else 0,
            'goat_roper_voice': len(goat_roper_voice) if 'goat_roper_voice' in locals() else 0,
            'goat_roper_text': len(goat_roper_text) if 'goat_roper_text' in locals() else 0
        }

    def test_analytics_api(self):
        """Step 2: Test the analytics aggregation API"""
        print(f"\n🔍 STEP 2: Testing Analytics API Aggregation...")
        
        if not self.token:
            self.log_test("Analytics API Test", False, "No authentication token available")
            return None
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Test GET /api/discord/analytics
            response = requests.get(
                f"{self.base_url}/discord/analytics",
                headers=headers,
                verify=False
            )
            
            if response.status_code == 200:
                analytics_data = response.json()
                self.log_test("GET /api/discord/analytics", True, f"Status: {response.status_code}")
                
                # Analyze the response structure
                required_fields = ['total_members', 'voice_stats', 'text_stats']
                missing_fields = [field for field in required_fields if field not in analytics_data]
                
                if not missing_fields:
                    self.log_test("Analytics API - Required Fields", True, f"All required fields present: {required_fields}")
                    
                    # Check total_members
                    total_members = analytics_data.get('total_members', 0)
                    print(f"   👥 Total members from API: {total_members}")
                    
                    # Check voice_stats
                    voice_stats = analytics_data.get('voice_stats', {})
                    print(f"   🎤 Voice stats structure: {list(voice_stats.keys())}")
                    
                    # Check text_stats  
                    text_stats = analytics_data.get('text_stats', {})
                    print(f"   💬 Text stats structure: {list(text_stats.keys())}")
                    
                    # Look for top users data
                    if 'top_voice_users' in analytics_data:
                        top_voice = analytics_data['top_voice_users']
                        print(f"   🏆 Top voice users: {len(top_voice)} users")
                        for i, user in enumerate(top_voice[:3]):
                            print(f"      {i+1}. {user.get('username', 'Unknown')} - {user.get('total_duration', 0)}s")
                    
                    if 'top_text_users' in analytics_data:
                        top_text = analytics_data['top_text_users']
                        print(f"   🏆 Top text users: {len(top_text)} users")
                        for i, user in enumerate(top_text[:3]):
                            print(f"      {i+1}. {user.get('username', 'Unknown')} - {user.get('total_messages', 0)} messages")
                    
                    # Check for specific users in aggregated data
                    lonestar_in_voice = False
                    lonestar_in_text = False
                    goat_roper_in_voice = False
                    goat_roper_in_text = False
                    
                    if 'top_voice_users' in analytics_data:
                        for user in analytics_data['top_voice_users']:
                            username = user.get('username', '').lower()
                            if 'lonestar' in username:
                                lonestar_in_voice = True
                            if 'goat' in username or 'roper' in username:
                                goat_roper_in_voice = True
                    
                    if 'top_text_users' in analytics_data:
                        for user in analytics_data['top_text_users']:
                            username = user.get('username', '').lower()
                            if 'lonestar' in username:
                                lonestar_in_text = True
                            if 'goat' in username or 'roper' in username:
                                goat_roper_in_text = True
                    
                    self.log_test("Lonestar in voice analytics", lonestar_in_voice, "Found in top voice users" if lonestar_in_voice else "Not found in top voice users")
                    self.log_test("Lonestar in text analytics", lonestar_in_text, "Found in top text users" if lonestar_in_text else "Not found in top text users")
                    self.log_test("HAB Goat Roper in voice analytics", goat_roper_in_voice, "Found in top voice users" if goat_roper_in_voice else "Not found in top voice users")
                    self.log_test("HAB Goat Roper in text analytics", goat_roper_in_text, "Found in top text users" if goat_roper_in_text else "Not found in top text users")
                    
                    return analytics_data
                    
                else:
                    self.log_test("Analytics API - Required Fields", False, f"Missing fields: {missing_fields}")
                    return analytics_data
                    
            else:
                self.log_test("GET /api/discord/analytics", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log_test("Analytics API Test", False, f"Exception: {str(e)}")
            return None

    def test_discord_members_api(self):
        """Test the Discord members API endpoint"""
        print(f"\n👥 Testing Discord Members API...")
        
        if not self.token:
            self.log_test("Discord Members API Test", False, "No authentication token available")
            return None
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/discord/members",
                headers=headers,
                verify=False
            )
            
            if response.status_code == 200:
                members_data = response.json()
                self.log_test("GET /api/discord/members", True, f"Status: {response.status_code}, Members: {len(members_data)}")
                
                # Look for specific users
                lonestar_found = None
                goat_roper_found = None
                
                for member in members_data:
                    discord_id = member.get('discord_id', '')
                    username = member.get('username', '').lower()
                    display_name = member.get('display_name', '').lower()
                    
                    if discord_id == '1288662056748191766' or 'lonestar' in username or 'lonestar' in display_name:
                        lonestar_found = member
                    
                    if discord_id == '127638717115400192' or ('goat' in username and 'roper' in username) or ('goat' in display_name and 'roper' in display_name):
                        goat_roper_found = member
                
                if lonestar_found:
                    self.log_test("Lonestar in Discord members API", True, f"Found: {lonestar_found.get('username')} / {lonestar_found.get('display_name')} (ID: {lonestar_found.get('discord_id')})")
                else:
                    self.log_test("Lonestar in Discord members API", False, "Lonestar not found in members API")
                
                if goat_roper_found:
                    self.log_test("HAB Goat Roper in Discord members API", True, f"Found: {goat_roper_found.get('username')} / {goat_roper_found.get('display_name')} (ID: {goat_roper_found.get('discord_id')})")
                else:
                    self.log_test("HAB Goat Roper in Discord members API", False, "HAB Goat Roper not found in members API")
                
                return members_data
                
            else:
                self.log_test("GET /api/discord/members", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log_test("Discord Members API Test", False, f"Exception: {str(e)}")
            return None

    def compare_data_pipeline(self, db_stats, api_analytics, api_members):
        """Step 3: Compare data at each step of the pipeline"""
        print(f"\n🔍 STEP 3: Comparing Data Pipeline...")
        
        if not db_stats:
            self.log_test("Data Pipeline Comparison", False, "No database statistics available")
            return
        
        # Compare total records
        db_voice_total = db_stats.get('voice_records', 0)
        db_text_total = db_stats.get('text_records', 0)
        db_members_total = db_stats.get('members', 0)
        
        print(f"   📊 Database totals:")
        print(f"      Voice records: {db_voice_total}")
        print(f"      Text records: {db_text_total}")
        print(f"      Members: {db_members_total}")
        
        if api_analytics:
            api_members_total = api_analytics.get('total_members', 0)
            print(f"   📊 API Analytics totals:")
            print(f"      Total members: {api_members_total}")
            
            # Compare member counts
            if db_members_total == api_members_total:
                self.log_test("Member count consistency", True, f"Database and API both report {db_members_total} members")
            else:
                self.log_test("Member count consistency", False, f"Database: {db_members_total}, API: {api_members_total}")
        
        if api_members:
            api_members_count = len(api_members)
            print(f"   📊 API Members endpoint:")
            print(f"      Members returned: {api_members_count}")
            
            if db_members_total == api_members_count:
                self.log_test("Members API consistency", True, f"Database and Members API both report {db_members_total} members")
            else:
                self.log_test("Members API consistency", False, f"Database: {db_members_total}, Members API: {api_members_count}")
        
        # Check for data loss indicators
        print(f"\n   🔍 Checking for data loss indicators...")
        
        # Check if we have activity data but no aggregated results
        if db_voice_total > 0 or db_text_total > 0:
            if api_analytics:
                voice_stats = api_analytics.get('voice_stats', {})
                text_stats = api_analytics.get('text_stats', {})
                
                if not voice_stats and db_voice_total > 0:
                    self.log_test("Voice data aggregation", False, f"Database has {db_voice_total} voice records but API returns empty voice_stats")
                elif voice_stats and db_voice_total > 0:
                    self.log_test("Voice data aggregation", True, f"Voice data successfully aggregated")
                
                if not text_stats and db_text_total > 0:
                    self.log_test("Text data aggregation", False, f"Database has {db_text_total} text records but API returns empty text_stats")
                elif text_stats and db_text_total > 0:
                    self.log_test("Text data aggregation", True, f"Text data successfully aggregated")
        
        # Check specific user data pipeline
        print(f"\n   👤 Checking specific user data pipeline...")
        
        lonestar_db_voice = db_stats.get('lonestar_voice', 0)
        lonestar_db_text = db_stats.get('lonestar_text', 0)
        goat_roper_db_voice = db_stats.get('goat_roper_voice', 0)
        goat_roper_db_text = db_stats.get('goat_roper_text', 0)
        
        print(f"      Lonestar - DB voice: {lonestar_db_voice}, DB text: {lonestar_db_text}")
        print(f"      HAB Goat Roper - DB voice: {goat_roper_db_voice}, DB text: {goat_roper_db_text}")
        
        # Summary of potential data loss points
        print(f"\n   📋 Data Loss Analysis Summary:")
        
        issues_found = []
        
        if (lonestar_db_voice > 0 or lonestar_db_text > 0) and api_analytics:
            # Check if Lonestar appears in analytics
            lonestar_in_analytics = False
            if 'top_voice_users' in api_analytics:
                for user in api_analytics['top_voice_users']:
                    if 'lonestar' in user.get('username', '').lower():
                        lonestar_in_analytics = True
                        break
            if 'top_text_users' in api_analytics:
                for user in api_analytics['top_text_users']:
                    if 'lonestar' in user.get('username', '').lower():
                        lonestar_in_analytics = True
                        break
            
            if not lonestar_in_analytics:
                issues_found.append("Lonestar has database activity but doesn't appear in analytics aggregation")
        
        if (goat_roper_db_voice > 0 or goat_roper_db_text > 0) and api_analytics:
            # Check if HAB Goat Roper appears in analytics
            goat_roper_in_analytics = False
            if 'top_voice_users' in api_analytics:
                for user in api_analytics['top_voice_users']:
                    username = user.get('username', '').lower()
                    if 'goat' in username and 'roper' in username:
                        goat_roper_in_analytics = True
                        break
            if 'top_text_users' in api_analytics:
                for user in api_analytics['top_text_users']:
                    username = user.get('username', '').lower()
                    if 'goat' in username and 'roper' in username:
                        goat_roper_in_analytics = True
                        break
            
            if not goat_roper_in_analytics:
                issues_found.append("HAB Goat Roper has database activity but doesn't appear in analytics aggregation")
        
        if issues_found:
            for issue in issues_found:
                print(f"      ⚠️  {issue}")
            self.log_test("Data Pipeline Issues", False, f"Found {len(issues_found)} potential data loss points")
        else:
            self.log_test("Data Pipeline Issues", True, "No obvious data loss detected")

    def investigate_aggregation_pipeline(self):
        """Investigate the aggregation pipeline logic"""
        print(f"\n🔧 STEP 4: Investigating Aggregation Pipeline Logic...")
        
        if self.db is None:
            self.log_test("Aggregation Pipeline Investigation", False, "No database connection available")
            return
        
        try:
            # Test aggregation queries similar to what the API might be doing
            print(f"   🔍 Testing voice activity aggregation...")
            
            voice_pipeline = [
                {
                    "$group": {
                        "_id": "$discord_user_id",
                        "total_duration": {"$sum": "$duration_seconds"},
                        "session_count": {"$sum": 1}
                    }
                },
                {"$sort": {"total_duration": -1}},
                {"$limit": 10}
            ]
            
            voice_results = list(self.db.discord_voice_activity.aggregate(voice_pipeline))
            
            if voice_results:
                self.log_test("Voice aggregation pipeline", True, f"Aggregated {len(voice_results)} users")
                print(f"      Top voice users from aggregation:")
                for i, user in enumerate(voice_results[:3]):
                    user_id = user.get('_id', 'Unknown')
                    duration = user.get('total_duration', 0)
                    sessions = user.get('session_count', 0)
                    print(f"         {i+1}. User ID: {user_id} - {duration}s total, {sessions} sessions")
                    
                    # Check if this is one of our target users
                    if user_id in ['1288662056748191766', '127638717115400192']:
                        print(f"            ✅ Found target user {user_id} in aggregation!")
            else:
                self.log_test("Voice aggregation pipeline", False, "No results from voice aggregation")
            
            print(f"   🔍 Testing text activity aggregation...")
            
            text_pipeline = [
                {
                    "$group": {
                        "_id": "$discord_user_id",
                        "total_messages": {"$sum": "$message_count"}
                    }
                },
                {"$sort": {"total_messages": -1}},
                {"$limit": 10}
            ]
            
            text_results = list(self.db.discord_text_activity.aggregate(text_pipeline))
            
            if text_results:
                self.log_test("Text aggregation pipeline", True, f"Aggregated {len(text_results)} users")
                print(f"      Top text users from aggregation:")
                for i, user in enumerate(text_results[:3]):
                    user_id = user.get('_id', 'Unknown')
                    messages = user.get('total_messages', 0)
                    print(f"         {i+1}. User ID: {user_id} - {messages} messages")
                    
                    # Check if this is one of our target users
                    if user_id in ['1288662056748191766', '127638717115400192']:
                        print(f"            ✅ Found target user {user_id} in aggregation!")
            else:
                self.log_test("Text aggregation pipeline", False, "No results from text aggregation")
            
            # Test username resolution
            print(f"   🔍 Testing username resolution...")
            
            if voice_results:
                # Try to resolve usernames for top voice users
                for user in voice_results[:3]:
                    user_id = user.get('_id')
                    member_record = self.db.discord_members.find_one({"discord_id": user_id})
                    
                    if member_record:
                        username = member_record.get('username', 'Unknown')
                        display_name = member_record.get('display_name', 'Unknown')
                        print(f"         User {user_id} -> {username} / {display_name}")
                        self.log_test(f"Username resolution for {user_id}", True, f"Resolved to {username} / {display_name}")
                    else:
                        print(f"         User {user_id} -> NOT FOUND in discord_members")
                        self.log_test(f"Username resolution for {user_id}", False, "User not found in discord_members collection")
            
        except Exception as e:
            self.log_test("Aggregation Pipeline Investigation", False, f"Exception: {str(e)}")

    def run_full_investigation(self):
        """Run the complete Discord analytics data pipeline investigation"""
        print(f"🔍 Discord Analytics Data Pipeline Investigation")
        print(f"=" * 60)
        print(f"Investigating where data is being lost in the Discord analytics pipeline...")
        print(f"Target users: ⭐NSEC Lonestar⭐ (1288662056748191766), HAB Goat Roper (127638717115400192)")
        print(f"=" * 60)
        
        # Step 0: Authentication
        if not self.login():
            print(f"\n❌ Investigation failed: Could not authenticate")
            return
        
        # Step 1: Check raw database data
        db_stats = self.investigate_raw_database_data()
        
        # Step 2: Test analytics API
        api_analytics = self.test_analytics_api()
        
        # Step 2.5: Test Discord members API
        api_members = self.test_discord_members_api()
        
        # Step 3: Compare data pipeline
        self.compare_data_pipeline(db_stats, api_analytics, api_members)
        
        # Step 4: Investigate aggregation pipeline
        self.investigate_aggregation_pipeline()
        
        # Final summary
        print(f"\n📊 INVESTIGATION SUMMARY")
        print(f"=" * 40)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        print(f"\n🔍 KEY FINDINGS:")
        
        if db_stats:
            print(f"   Database Records:")
            print(f"   - Voice activity: {db_stats.get('voice_records', 0)} records")
            print(f"   - Text activity: {db_stats.get('text_records', 0)} records")
            print(f"   - Discord members: {db_stats.get('members', 0)} records")
            
            print(f"\n   Target User Activity in Database:")
            print(f"   - Lonestar voice: {db_stats.get('lonestar_voice', 0)} records")
            print(f"   - Lonestar text: {db_stats.get('lonestar_text', 0)} records")
            print(f"   - HAB Goat Roper voice: {db_stats.get('goat_roper_voice', 0)} records")
            print(f"   - HAB Goat Roper text: {db_stats.get('goat_roper_text', 0)} records")
        
        if api_analytics:
            print(f"\n   API Analytics Response:")
            print(f"   - Total members: {api_analytics.get('total_members', 0)}")
            print(f"   - Voice stats available: {'Yes' if api_analytics.get('voice_stats') else 'No'}")
            print(f"   - Text stats available: {'Yes' if api_analytics.get('text_stats') else 'No'}")
        
        # Identify critical issues
        critical_issues = []
        for result in self.test_results:
            if not result['success'] and any(keyword in result['test'].lower() for keyword in ['lonestar', 'goat roper', 'aggregation', 'pipeline']):
                critical_issues.append(result['test'])
        
        if critical_issues:
            print(f"\n⚠️  CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ No critical data loss issues detected")
        
        print(f"\n" + "=" * 60)

if __name__ == "__main__":
    investigator = DiscordAnalyticsInvestigator()
    investigator.run_full_investigation()