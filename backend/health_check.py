#!/usr/bin/env python3
"""
Backend Health Check - Test All Task Management Functions
"""

import sys
import os
import requests
import time
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_server_connection():
    """Test if the Flask server is running"""
    try:
        response = requests.get("http://127.0.0.1:5001/api/tasks", timeout=5)
        return True, response.status_code
    except requests.exceptions.ConnectionError:
        return False, "Connection refused"
    except Exception as e:
        return False, str(e)

def test_task_creation():
    """Test task creation functionality"""
    try:
        task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "status": "todo",
            "priority": "medium"
        }
        response = requests.post("http://127.0.0.1:5001/api/tasks", json=task_data, timeout=5)
        return True, response.status_code, response.json() if response.status_code == 201 else None
    except Exception as e:
        return False, str(e), None

def test_project_management():
    """Test project management functionality"""
    try:
        project_data = {
            "name": "Test Project",
            "description": "This is a test project"
        }
        response = requests.post("http://127.0.0.1:5001/api/projects", json=project_data, timeout=5)
        return True, response.status_code, response.json() if response.status_code == 201 else None
    except Exception as e:
        return False, str(e), None

def test_ai_coordination():
    """Test AI coordination functionality"""
    try:
        ai_data = {
            "query": "What tasks need attention?"
        }
        response = requests.post("http://127.0.0.1:5001/ai/analyze", json=ai_data, timeout=10)
        return True, response.status_code, response.json() if response.status_code == 200 else None
    except Exception as e:
        return False, str(e), None

def main():
    print("🔍 AI COORDINATION AGENT - HEALTH CHECK")
    print("=" * 50)
    
    # Test 1: Server Connection
    print("\n1. Testing Server Connection...")
    is_connected, status = test_server_connection()
    if is_connected:
        print(f"   ✅ Server is running (Status: {status})")
    else:
        print(f"   ❌ Server connection failed: {status}")
        return
    
    # Test 2: Task Management
    print("\n2. Testing Task Management...")
    success, status, data = test_task_creation()
    if success and status == 201:
        print(f"   ✅ Task creation works (Status: {status})")
        print(f"   📝 Created task ID: {data.get('id') if data else 'Unknown'}")
    else:
        print(f"   ❌ Task creation failed: {status}")
    
    # Test 3: Project Management  
    print("\n3. Testing Project Management...")
    success, status, data = test_project_management()
    if success and status == 201:
        print(f"   ✅ Project creation works (Status: {status})")
        print(f"   📁 Created project ID: {data.get('id') if data else 'Unknown'}")
    else:
        print(f"   ❌ Project creation failed: {status}")
    
    # Test 4: AI Coordination
    print("\n4. Testing AI Coordination...")
    success, status, data = test_ai_coordination()
    if success and status == 200:
        print(f"   ✅ AI coordination works (Status: {status})")
        print(f"   🤖 AI Response: {data.get('response', 'No response')[:100]}...")
    else:
        print(f"   ❌ AI coordination failed: {status}")
    
    print("\n" + "=" * 50)
    print("✨ Health check complete!")

if __name__ == "__main__":
    main()