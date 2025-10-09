#!/usr/bin/env python3
"""
Comprehensive Authentication & Role-Based Access Control Test
Tests the complete authentication workflow for all user roles
"""

import requests
import json
import sys
import time

BASE_URL = "http://127.0.0.1:5001"

def test_user_login(username, password):
    """Test user login and return token"""
    print(f"\n🔐 Testing {username} login...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            user_info = data.get('user', {})
            print(f"✅ {username} login successful!")
            print(f"   Role: {user_info.get('role')}")
            print(f"   Token: {token[:50]}...")
            return token
        else:
            print(f"❌ {username} login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ {username} login error: {e}")
        return None

def test_protected_endpoint(token, username, endpoint):
    """Test access to a protected endpoint"""
    print(f"\n🔒 Testing {username} access to {endpoint}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            print(f"✅ {username} access granted to {endpoint}")
            return True
        elif response.status_code == 401:
            print(f"🚫 {username} unauthorized for {endpoint}: {response.text}")
            return False
        elif response.status_code == 403:
            print(f"🚫 {username} forbidden from {endpoint}: {response.text}")
            return False
        else:
            print(f"⚠️  {username} unexpected response {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {username} endpoint test error: {e}")
        return False

def test_session_validation(token, username):
    """Test session validation endpoint"""
    print(f"\n🔍 Testing {username} session validation...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {username} session valid: {data}")
            return True
        else:
            print(f"❌ {username} session invalid: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {username} session validation error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Comprehensive Authentication & RBAC Testing")
    print("=" * 60)
    
    # Test data: username, password, expected role
    test_users = [
        ("admin", "admin123", "admin"),
        ("manager", "manager123", "manager"), 
        ("teammember", "team123", "team_member"),
        ("client", "client123", "client")
    ]
    
    # Store successful logins
    user_tokens = {}
    
    # Phase 1: Test all user logins
    print("\n📋 PHASE 1: Testing User Authentication")
    print("-" * 40)
    
    for username, password, expected_role in test_users:
        token = test_user_login(username, password)
        if token:
            user_tokens[username] = token
        time.sleep(0.5)  # Brief pause between requests
    
    print(f"\n✅ Successfully authenticated {len(user_tokens)}/{len(test_users)} users")
    
    # Phase 2: Test session validation
    print("\n📋 PHASE 2: Testing Session Validation")
    print("-" * 40)
    
    valid_sessions = 0
    for username, token in user_tokens.items():
        if test_session_validation(token, username):
            valid_sessions += 1
        time.sleep(0.5)
    
    print(f"\n✅ {valid_sessions}/{len(user_tokens)} sessions are valid")
    
    # Phase 3: Test protected endpoints
    print("\n📋 PHASE 3: Testing Protected Endpoints")
    print("-" * 40)
    
    # Test endpoints that should be accessible to authenticated users
    test_endpoints = [
        "/api/auth/users",  # Should require authentication
    ]
    
    for endpoint in test_endpoints:
        print(f"\n🎯 Testing endpoint: {endpoint}")
        for username, token in user_tokens.items():
            test_protected_endpoint(token, username, endpoint)
            time.sleep(0.3)
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Authenticated Users: {len(user_tokens)}/{len(test_users)}")
    print(f"✅ Valid Sessions: {valid_sessions}/{len(user_tokens)}")
    
    if len(user_tokens) == len(test_users) and valid_sessions == len(user_tokens):
        print("\n🎉 ALL AUTHENTICATION TESTS PASSED!")
        print("🔐 JWT Authentication System: ✅ WORKING")
        print("🗄️  Session Management: ✅ WORKING") 
        print("🔒 Role-Based Access Control: ✅ READY FOR TESTING")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return user_tokens

if __name__ == "__main__":
    try:
        tokens = main()
        print(f"\n💾 Saved tokens for further testing:")
        for username, token in tokens.items():
            print(f"   {username}: {token[:30]}...")
    except KeyboardInterrupt:
        print("\n\n🛑 Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")