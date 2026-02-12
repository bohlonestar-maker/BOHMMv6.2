#!/usr/bin/env python3
"""
Check if testadmin user has chapter field in database
"""

import requests
import json
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_user_chapter():
    base_url = "https://member-manager-26.preview.emergentagent.com/api"
    
    # Login as testadmin
    response = requests.post(
        f"{base_url}/auth/login",
        json={"username": "testadmin", "password": "testpass123"},
        verify=False
    )
    
    if response.status_code == 200:
        login_data = response.json()
        token = login_data['token']
        print(f"✅ Login successful")
        
        # Get all users to check testadmin's chapter field
        headers = {'Authorization': f'Bearer {token}'}
        users_response = requests.get(
            f"{base_url}/users",
            headers=headers,
            verify=False
        )
        
        if users_response.status_code == 200:
            users = users_response.json()
            print(f"✅ Got {len(users)} users")
            
            # Find testadmin
            testadmin_user = None
            for user in users:
                if user.get('username') == 'testadmin':
                    testadmin_user = user
                    break
            
            if testadmin_user:
                print(f"✅ Found testadmin user:")
                print(f"   ID: {testadmin_user.get('id')}")
                print(f"   Username: {testadmin_user.get('username')}")
                print(f"   Role: {testadmin_user.get('role')}")
                print(f"   Chapter: {testadmin_user.get('chapter')}")
                print(f"   Title: {testadmin_user.get('title')}")
                print(f"   Full user data: {testadmin_user}")
            else:
                print(f"❌ testadmin user not found")
        else:
            print(f"❌ Failed to get users: {users_response.status_code}")
    else:
        print(f"❌ Login failed: {response.status_code}")

if __name__ == "__main__":
    check_user_chapter()