#!/usr/bin/env python3

import requests
import json
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://biker-roster.preview.emergentagent.com/api"

def login():
    """Login and get token"""
    login_data = {
        "username": "testadmin",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data, verify=False)
    if response.status_code == 200:
        return response.json()['token']
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def create_test_prospect(token, handle, name, email):
    """Create a test prospect"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    prospect_data = {
        "handle": handle,
        "name": name,
        "email": email,
        "phone": "555-1234",
        "address": "123 Test Street"
    }
    
    response = requests.post(f"{BASE_URL}/prospects", json=prospect_data, headers=headers, verify=False)
    if response.status_code == 201:
        return response.json()['id']
    else:
        print(f"Failed to create prospect: {response.status_code} - {response.text}")
        return None

def test_bulk_promotion_api(token, prospect_ids):
    """Test different ways to call the bulk promotion API"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("Testing bulk promotion API...")
    
    # Method 1: Query parameters
    print("\n1. Testing with query parameters:")
    params = {
        'prospect_ids': prospect_ids,
        'chapter': 'Test Chapter',
        'title': 'Member'
    }
    response = requests.post(f"{BASE_URL}/prospects/bulk-promote", params=params, headers=headers, verify=False)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Method 2: JSON body
    print("\n2. Testing with JSON body:")
    data = {
        'prospect_ids': prospect_ids,
        'chapter': 'Test Chapter',
        'title': 'Member'
    }
    response = requests.post(f"{BASE_URL}/prospects/bulk-promote", json=data, headers=headers, verify=False)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Method 3: Form data
    print("\n3. Testing with form data:")
    form_data = {
        'chapter': 'Test Chapter',
        'title': 'Member'
    }
    # Add prospect_ids as multiple form fields
    for prospect_id in prospect_ids:
        form_data[f'prospect_ids'] = prospect_id
    
    response = requests.post(f"{BASE_URL}/prospects/bulk-promote", data=form_data, headers={'Authorization': f'Bearer {token}'}, verify=False)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

def main():
    # Login
    token = login()
    if not token:
        return
    
    print(f"Logged in successfully. Token: {token[:20]}...")
    
    # Create test prospects
    prospect_ids = []
    for i in range(1, 4):
        prospect_id = create_test_prospect(token, f"BulkTest{i}", f"Test Prospect {i}", f"bulktest{i}@example.com")
        if prospect_id:
            prospect_ids.append(prospect_id)
            print(f"Created prospect {i}: {prospect_id}")
    
    if len(prospect_ids) < 3:
        print("Failed to create enough test prospects")
        return
    
    # Test bulk promotion API
    test_bulk_promotion_api(token, prospect_ids)

if __name__ == "__main__":
    main()