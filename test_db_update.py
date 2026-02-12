#!/usr/bin/env python3
"""
Test database update directly to see if the issue is with the update operation
"""

import requests
import json
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://member-manager-26.preview.emergentagent.com/api"

def login():
    """Login and get token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "testadmin", "password": "testpass123"},
        verify=False
    )
    if response.status_code == 200:
        return response.json()['token']
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def get_discord_members(token):
    """Get Discord members"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{BASE_URL}/discord/members", headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Get Discord members failed: {response.status_code} - {response.text}")
        return None

def get_database_members(token):
    """Get database members"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{BASE_URL}/members", headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Get database members failed: {response.status_code} - {response.text}")
        return None

def main():
    print("🔍 Test Database Update Issue")
    print("=" * 40)
    
    # Login
    token = login()
    if not token:
        return
    
    print("✅ Login successful")
    
    # Get Discord members
    discord_members = get_discord_members(token)
    if not discord_members:
        print("❌ Failed to get Discord members")
        return
    
    # Get database members
    db_members = get_database_members(token)
    if not db_members:
        print("❌ Failed to get database members")
        return
    
    print(f"📊 Found {len(discord_members)} Discord members and {len(db_members)} database members")
    
    # Look for a specific match we know should work
    qball_discord = None
    qball_db = None
    
    for discord_member in discord_members:
        if discord_member.get('username') == 'qball3577':
            qball_discord = discord_member
            break
    
    for db_member in db_members:
        if 'q-ball' in db_member.get('handle', '').lower():
            qball_db = db_member
            break
    
    if qball_discord and qball_db:
        print(f"\n🎯 Found matching pair:")
        print(f"   Discord: {qball_discord.get('username')} (ID: {qball_discord.get('discord_id')})")
        print(f"   Database: {qball_db.get('handle')} (ID: {qball_db.get('id')})")
        print(f"   Current member_id: {qball_discord.get('member_id', 'None')}")
        
        # Check if they're already linked
        if qball_discord.get('member_id') == qball_db.get('id'):
            print("   ✅ Already linked correctly!")
        else:
            print("   ❌ Not linked - this should be fixed by import")
    else:
        print("❌ Could not find Q-Ball match candidates")
        if not qball_discord:
            print("   No Discord user 'qball3577' found")
        if not qball_db:
            print("   No database member with 'q-ball' in handle found")
            # Show available handles
            handles = [m.get('handle', 'N/A') for m in db_members[:10]]
            print(f"   Available handles: {', '.join(handles)}")

if __name__ == "__main__":
    main()