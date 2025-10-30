import requests
import json
import urllib3
from pymongo import MongoClient
import os

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://member-hub-29.preview.emergentagent.com/api"

def login():
    """Login and get token"""
    login_data = {"username": "testadmin", "password": "testpass123"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data, verify=False)
    if response.status_code == 200:
        return response.json()['token']
    return None

def check_database_directly():
    """Check what's actually stored in the database"""
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017")
        db = client["test_database"]
        
        print("Checking members collection directly...")
        members = list(db.members.find({}))
        
        print(f"Found {len(members)} members in database:")
        for member in members:
            if member.get('handle', '').startswith('DebugTest'):
                print(f"  - Handle: {member.get('handle')}")
                print(f"  - Email (raw): {member.get('email')}")
                print(f"  - ID: {member.get('id')}")
                print(f"  - Full member: {json.dumps(member, indent=2, default=str)}")
                print("---")
        
        client.close()
        
    except Exception as e:
        print(f"Error connecting to database: {e}")

def test_encryption_issue():
    """Test the encryption issue with duplicate emails"""
    token = login()
    if not token:
        print("❌ Login failed")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Create first member
    first_member = {
        "chapter": "National",
        "title": "Prez",
        "handle": "DebugTest1",
        "name": "Debug First Member",
        "email": "debug@test.com",
        "phone": "555-0001",
        "address": "123 Debug Street"
    }
    
    print("Creating first member...")
    response = requests.post(f"{BASE_URL}/members", json=first_member, headers=headers, verify=False)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        first_member_data = response.json()
        first_member_id = first_member_data['id']
        print(f"✅ First member created with ID: {first_member_id}")
        print(f"Email in API response: {first_member_data.get('email')}")
        
        # Check database directly
        check_database_directly()
        
        # Try to create second member with same email
        second_member = {
            "chapter": "AD",
            "title": "VP",
            "handle": "DebugTest2",
            "name": "Debug Second Member",
            "email": "debug@test.com",  # Same email
            "phone": "555-0002",
            "address": "456 Debug Street"
        }
        
        print("\nTrying to create second member with same email...")
        response = requests.post(f"{BASE_URL}/members", json=second_member, headers=headers, verify=False)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("❌ PROBLEM: Second member was created despite duplicate email!")
            second_member_data = response.json()
            second_member_id = second_member_data['id']
            
            # Check database again
            print("\nDatabase after creating second member:")
            check_database_directly()
            
            # Clean up second member
            requests.delete(f"{BASE_URL}/members/{second_member_id}", headers=headers, verify=False)
        
        # Clean up first member
        requests.delete(f"{BASE_URL}/members/{first_member_id}", headers=headers, verify=False)
    else:
        print(f"❌ Failed to create first member: {response.text}")

if __name__ == "__main__":
    test_encryption_issue()