#!/usr/bin/env python3

import requests
import json
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_can_edit_flag():
    base_url = "https://memberprivacy.preview.emergentagent.com/api"
    
    # Login as admin
    login_response = requests.post(
        f"{base_url}/auth/login",
        json={"username": "admin", "password": "admin123"},
        verify=False
    )
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = login_response.json()['token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Check auth/verify
    verify_response = requests.get(f"{base_url}/auth/verify", headers=headers, verify=False)
    print("🔍 Auth verify response:")
    print(json.dumps(verify_response.json(), indent=2))
    
    # Get members list
    members_response = requests.get(f"{base_url}/members", headers=headers, verify=False)
    
    if members_response.status_code == 200:
        members = members_response.json()
        print(f"\n🔍 Found {len(members)} members")
        
        if len(members) > 0:
            first_member = members[0]
            print("\n🔍 First member structure:")
            print(json.dumps(first_member, indent=2))
            
            # Check if can_edit flag is present
            if 'can_edit' in first_member:
                print(f"\n✅ can_edit flag found: {first_member['can_edit']}")
            else:
                print("\n❌ can_edit flag NOT found")
                print("Available keys:", list(first_member.keys()))
        else:
            print("❌ No members found")
    else:
        print(f"❌ Failed to get members: {members_response.status_code}")
        print(members_response.text)

if __name__ == "__main__":
    test_can_edit_flag()