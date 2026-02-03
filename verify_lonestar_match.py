#!/usr/bin/env python3
"""
Verify the specific Lonestar matching test case
"""

import requests
import json
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://bohnexus.preview.emergentagent.com/api"

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
    print("🎯 Verify Lonestar Matching Test Case")
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
    
    # Look for Lonestar matches
    lonestar_discord_members = []
    lonestar_db_members = []
    
    # Find Discord members with "lonestar" in username or display name
    for discord_member in discord_members:
        username = (discord_member.get('username') or '').lower()
        display_name = (discord_member.get('display_name') or '').lower()
        if 'lonestar' in username or 'lonestar' in display_name:
            lonestar_discord_members.append(discord_member)
    
    # Find database members with "lonestar" in handle or name
    for db_member in db_members:
        handle = (db_member.get('handle') or '').lower()
        name = (db_member.get('name') or '').lower()
        if 'lonestar' in handle or 'lonestar' in name:
            lonestar_db_members.append(db_member)
    
    print(f"\n🔍 Lonestar Search Results:")
    print(f"   Discord members with 'lonestar': {len(lonestar_discord_members)}")
    for member in lonestar_discord_members:
        username = member.get('username', 'N/A')
        display_name = member.get('display_name', 'N/A')
        member_id = member.get('member_id', None)
        status = "LINKED" if member_id else "UNLINKED"
        print(f"      - {username} ({display_name}) - {status}")
        if member_id:
            # Find the linked database member
            linked_db = next((m for m in db_members if m.get('id') == member_id), None)
            if linked_db:
                print(f"        -> Linked to: {linked_db.get('handle')} ({linked_db.get('name')})")
    
    print(f"   Database members with 'lonestar': {len(lonestar_db_members)}")
    for member in lonestar_db_members:
        handle = member.get('handle', 'N/A')
        name = member.get('name', 'N/A')
        member_id = member.get('id', 'N/A')
        print(f"      - {handle} ({name}) [ID: {member_id}]")
    
    # Check if any lonestar Discord members are linked to lonestar database members
    successful_matches = []
    for discord_member in lonestar_discord_members:
        member_id = discord_member.get('member_id')
        if member_id:
            linked_db = next((m for m in lonestar_db_members if m.get('id') == member_id), None)
            if linked_db:
                successful_matches.append((discord_member, linked_db))
    
    print(f"\n✅ Successful Lonestar Matches: {len(successful_matches)}")
    for discord_member, db_member in successful_matches:
        discord_user = discord_member.get('username', 'N/A')
        discord_display = discord_member.get('display_name', 'N/A')
        db_handle = db_member.get('handle', 'N/A')
        db_name = db_member.get('name', 'N/A')
        print(f"   ✅ {discord_user} ({discord_display}) -> {db_handle} ({db_name})")
    
    if successful_matches:
        print("\n🎉 Lonestar matching test case PASSED!")
    else:
        print("\n❌ Lonestar matching test case FAILED - no successful matches found")

if __name__ == "__main__":
    main()