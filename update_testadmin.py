#!/usr/bin/env python3
"""
Update testadmin user to have chapter='National' for testing
"""

import requests
import json
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def update_testadmin():
    base_url = "https://boh-tracker.preview.emergentagent.com/api"
    
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
        
        # Get testadmin user ID
        headers = {'Authorization': f'Bearer {token}'}
        users_response = requests.get(
            f"{base_url}/users",
            headers=headers,
            verify=False
        )
        
        if users_response.status_code == 200:
            users = users_response.json()
            testadmin_user = None
            for user in users:
                if user.get('username') == 'testadmin':
                    testadmin_user = user
                    break
            
            if testadmin_user:
                user_id = testadmin_user['id']
                print(f"✅ Found testadmin user ID: {user_id}")
                
                # Update testadmin to have chapter='National'
                update_data = {
                    "chapter": "National",
                    "title": "Prez"
                }
                
                update_response = requests.put(
                    f"{base_url}/users/{user_id}",
                    json=update_data,
                    headers=headers,
                    verify=False
                )
                
                if update_response.status_code == 200:
                    updated_user = update_response.json()
                    print(f"✅ Updated testadmin user:")
                    print(f"   Chapter: {updated_user.get('chapter')}")
                    print(f"   Title: {updated_user.get('title')}")
                else:
                    print(f"❌ Failed to update testadmin: {update_response.status_code}")
                    print(f"   Response: {update_response.text}")
            else:
                print(f"❌ testadmin user not found")
        else:
            print(f"❌ Failed to get users: {users_response.status_code}")
    else:
        print(f"❌ Login failed: {response.status_code}")

if __name__ == "__main__":
    update_testadmin()