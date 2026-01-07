#!/usr/bin/env python3
"""
Debug Discord Import - Check what's happening with the database updates
"""

import requests
import json
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://boh-tracker.preview.emergentagent.com/api"

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

def run_import(token):
    """Run Discord import"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(f"{BASE_URL}/discord/import-members", headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Import failed: {response.status_code} - {response.text}")
        return None

def main():
    print("🔍 Debug Discord Import Process")
    print("=" * 40)
    
    # Login
    token = login()
    if not token:
        return
    
    print("✅ Login successful")
    
    # Get Discord members BEFORE import
    print("\n📊 Discord Members BEFORE Import:")
    members_before = get_discord_members(token)
    if members_before:
        linked_before = sum(1 for m in members_before if m.get('member_id'))
        unlinked_before = len(members_before) - linked_before
        print(f"   Total: {len(members_before)}, Linked: {linked_before}, Unlinked: {unlinked_before}")
        
        # Show first few members with their link status
        print("   Sample members:")
        for i, member in enumerate(members_before[:5]):
            username = member.get('username', 'N/A')
            display_name = member.get('display_name', 'N/A')
            member_id = member.get('member_id', None)
            status = "LINKED" if member_id else "UNLINKED"
            print(f"      {i+1}. {username} ({display_name}) - {status}")
    
    # Run import
    print("\n🔄 Running Import...")
    import_result = run_import(token)
    if import_result:
        matched_count = import_result.get('matched_count', 0)
        total_discord = import_result.get('total_discord_members', 0)
        match_details = import_result.get('match_details', [])
        
        print(f"   Import result: Matched {matched_count} out of {total_discord}")
        
        if match_details:
            print("   Match details:")
            for i, match in enumerate(match_details[:3]):
                discord_user = match.get('discord_user', 'N/A')
                matched_handle = match.get('matched_handle', 'N/A')
                score = match.get('score', 0)
                method = match.get('method', 'N/A')
                print(f"      {i+1}. {discord_user} -> {matched_handle} ({score}%, {method})")
    
    # Get Discord members AFTER import
    print("\n📊 Discord Members AFTER Import:")
    members_after = get_discord_members(token)
    if members_after:
        linked_after = sum(1 for m in members_after if m.get('member_id'))
        unlinked_after = len(members_after) - linked_after
        print(f"   Total: {len(members_after)}, Linked: {linked_after}, Unlinked: {unlinked_after}")
        
        # Show first few members with their link status
        print("   Sample members:")
        for i, member in enumerate(members_after[:5]):
            username = member.get('username', 'N/A')
            display_name = member.get('display_name', 'N/A')
            member_id = member.get('member_id', None)
            status = "LINKED" if member_id else "UNLINKED"
            print(f"      {i+1}. {username} ({display_name}) - {status}")
        
        # Compare before and after
        improvement = linked_after - linked_before
        print(f"\n📈 Improvement: {improvement} new links created")
        
        if improvement == 0:
            print("⚠️  No new links were created despite matches being found!")
            print("   This suggests the database update is not working properly.")

if __name__ == "__main__":
    main()