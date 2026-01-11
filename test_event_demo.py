#!/usr/bin/env python3
"""
Event Calendar Demo Test Script
Creates a test event for demonstration as requested in the review.
"""

import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class EventCalendarTester:
    def __init__(self, base_url="https://memberwatch.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        
    def login(self, username="testadmin", password="testpass123"):
        """Login and get authentication token"""
        print(f"🔐 Logging in as {username}...")
        
        url = f"{self.base_url}/auth/login"
        data = {"username": username, "password": password}
        
        try:
            response = requests.post(url, json=data, verify=False)
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('token')
                print(f"✅ Login successful! Token obtained.")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def create_demo_event(self):
        """Create the demonstration event as requested"""
        print(f"\n📅 Creating BOH National Rally 2025 demo event...")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        # Event data as specified in the review request
        demo_event = {
            "title": "BOH National Rally 2025",
            "description": "Annual brothers gathering with rides, food, and live music. All chapters welcome!",
            "date": "2025-12-15",
            "time": "10:00",
            "location": "Sturgis Rally Grounds, SD",
            "chapter": None,
            "title_filter": None
        }
        
        url = f"{self.base_url}/events"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        
        try:
            response = requests.post(url, json=demo_event, headers=headers, verify=False)
            
            if response.status_code == 200:
                result = response.json()
                event_id = result.get('id')
                print(f"✅ Event created successfully!")
                print(f"   Event ID: {event_id}")
                print(f"   Title: {demo_event['title']}")
                print(f"   Date: {demo_event['date']} at {demo_event['time']}")
                print(f"   Location: {demo_event['location']}")
                print(f"   Description: {demo_event['description']}")
                return event_id
            else:
                print(f"❌ Event creation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', 'No error details')}")
                except:
                    print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Event creation error: {str(e)}")
            return False
    
    def verify_event_exists(self, event_id):
        """Verify the event was created by getting all events"""
        print(f"\n🔍 Verifying event exists...")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        url = f"{self.base_url}/events"
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        try:
            response = requests.get(url, headers=headers, verify=False)
            
            if response.status_code == 200:
                events = response.json()
                
                # Find our demo event
                demo_event_found = None
                for event in events:
                    if event.get('id') == event_id:
                        demo_event_found = event
                        break
                
                if demo_event_found:
                    print(f"✅ Event found in events list!")
                    print(f"   Title: {demo_event_found.get('title')}")
                    print(f"   Date: {demo_event_found.get('date')}")
                    print(f"   Location: {demo_event_found.get('location')}")
                    print(f"   Created by: {demo_event_found.get('created_by')}")
                    return True
                else:
                    print(f"❌ Event with ID {event_id} not found in events list")
                    print(f"   Found {len(events)} total events")
                    return False
            else:
                print(f"❌ Failed to get events: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting events: {str(e)}")
            return False
    
    def run_demo_test(self):
        """Run the complete demo test"""
        print("🚀 BOH Event Calendar Demo Test")
        print("=" * 50)
        print(f"Testing against: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Login
        if not self.login():
            return False
        
        # Step 2: Create demo event
        event_id = self.create_demo_event()
        if not event_id:
            return False
        
        # Step 3: Verify event exists
        if not self.verify_event_exists(event_id):
            return False
        
        print(f"\n🎉 Demo test completed successfully!")
        print(f"📝 Event 'BOH National Rally 2025' is now available for UI testing")
        return True

def main():
    """Main function"""
    tester = EventCalendarTester()
    success = tester.run_demo_test()
    
    if success:
        print(f"\n✅ All tests passed - demo event created successfully!")
        return 0
    else:
        print(f"\n❌ Test failed - check output above for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())