#!/usr/bin/env python3
"""
Debug JWT token contents to verify chapter field is included
"""

import requests
import json
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_jwt_contents():
    base_url = "https://themed-login-build.preview.emergentagent.com/api"
    
    # Login as testadmin
    print("🔐 Testing testadmin JWT contents...")
    response = requests.post(
        f"{base_url}/auth/login",
        json={"username": "testadmin", "password": "testpass123"},
        verify=False
    )
    
    if response.status_code == 200:
        login_data = response.json()
        token = login_data['token']
        print(f"✅ Login successful")
        
        # Verify token
        headers = {'Authorization': f'Bearer {token}'}
        verify_response = requests.get(
            f"{base_url}/auth/verify",
            headers=headers,
            verify=False
        )
        
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            print(f"✅ JWT verification successful")
            print(f"   Username: {verify_data.get('username')}")
            print(f"   Role: {verify_data.get('role')}")
            print(f"   Permissions: {verify_data.get('permissions', {})}")
            print(f"   Full response: {verify_data}")
        else:
            print(f"❌ JWT verification failed: {verify_response.status_code}")
    else:
        print(f"❌ Login failed: {response.status_code}")
    
    # Test National admin user
    print("\n🔐 Testing nationaladmin JWT contents...")
    response = requests.post(
        f"{base_url}/auth/login",
        json={"username": "nationaladmin", "password": "testpass123"},
        verify=False
    )
    
    if response.status_code == 200:
        login_data = response.json()
        token = login_data['token']
        print(f"✅ National admin login successful")
        
        # Verify token
        headers = {'Authorization': f'Bearer {token}'}
        verify_response = requests.get(
            f"{base_url}/auth/verify",
            headers=headers,
            verify=False
        )
        
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            print(f"✅ National admin JWT verification successful")
            print(f"   Username: {verify_data.get('username')}")
            print(f"   Role: {verify_data.get('role')}")
            print(f"   Permissions: {verify_data.get('permissions', {})}")
            print(f"   Full response: {verify_data}")
        else:
            print(f"❌ National admin JWT verification failed: {verify_response.status_code}")
    else:
        print(f"❌ National admin login failed: {response.status_code}")

if __name__ == "__main__":
    test_jwt_contents()