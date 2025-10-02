#!/usr/bin/env python3
"""
Comprehensive Backend Diagnostics and Testing
"""

import requests
import json
import time
import sys
import os

def test_server_health():
    """Test if server is responding"""
    try:
        print("🔍 Testing server connection...")
        response = requests.get("http://127.0.0.1:5001/api/tasks", timeout=10)
        print(f"   ✅ Server responding (Status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("   ❌ Server not responding - connection refused")
        return False
    except requests.exceptions.Timeout:
        print("   ❌ Server timeout")
        return False
    except Exception as e:
        print(f"   ❌ Server error: {e}")
        return False

def test_task_operations():
    """Test task CRUD operations"""
    print("\n📝 Testing Task Operations...")
    
    # Create a test task
    task_data = {
        "title": "Diagnostic Test Task",
        "description": "Testing multiple task operations",
        "status": "todo",
        "priority": "high"
    }
    
    try:
        # CREATE
        response = requests.post("http://127.0.0.1:5001/api/tasks", json=task_data, timeout=10)
        if response.status_code == 201:
            task = response.json()
            task_id = task['id']
            print(f"   ✅ CREATE: Task created (ID: {task_id})")
            
            # READ
            response = requests.get(f"http://127.0.0.1:5001/api/tasks/{task_id}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ READ: Task retrieved successfully")
                
                # UPDATE
                update_data = {"title": "Updated Test Task", "status": "in_progress"}
                response = requests.put(f"http://127.0.0.1:5001/api/tasks/{task_id}", 
                                      json=update_data, timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ UPDATE: Task updated successfully")
                else:
                    print(f"   ❌ UPDATE failed: {response.status_code}")
                
                # DELETE
                response = requests.delete(f"http://127.0.0.1:5001/api/tasks/{task_id}", timeout=10)
                if response.status_code == 204:
                    print(f"   ✅ DELETE: Task deleted successfully")
                else:
                    print(f"   ❌ DELETE failed: {response.status_code}")
            else:
                print(f"   ❌ READ failed: {response.status_code}")
        else:
            print(f"   ❌ CREATE failed: {response.status_code}")
            if response.text:
                print(f"      Error: {response.text}")
    
    except Exception as e:
        print(f"   ❌ Task operations error: {e}")

def test_multiple_tasks():
    """Test creating multiple tasks simultaneously"""
    print("\n🔄 Testing Multiple Task Operations...")
    
    tasks_data = [
        {"title": f"Test Task {i}", "description": f"Testing task {i}", "priority": "medium"}
        for i in range(1, 6)
    ]
    
    created_tasks = []
    
    try:
        # Create multiple tasks
        for i, task_data in enumerate(tasks_data):
            response = requests.post("http://127.0.0.1:5001/api/tasks", json=task_data, timeout=10)
            if response.status_code == 201:
                task = response.json()
                created_tasks.append(task['id'])
                print(f"   ✅ Created task {i+1} (ID: {task['id']})")
            else:
                print(f"   ❌ Failed to create task {i+1}: {response.status_code}")
        
        # Get all tasks
        response = requests.get("http://127.0.0.1:5001/api/tasks", timeout=10)
        if response.status_code == 200:
            all_tasks = response.json()
            print(f"   ✅ Retrieved {len(all_tasks)} total tasks")
        
        # Clean up - delete created tasks
        for task_id in created_tasks:
            requests.delete(f"http://127.0.0.1:5001/api/tasks/{task_id}", timeout=5)
        print(f"   🧹 Cleaned up {len(created_tasks)} test tasks")
        
    except Exception as e:
        print(f"   ❌ Multiple task operations error: {e}")

def test_ai_coordination():
    """Test AI coordination features"""
    print("\n🤖 Testing AI Coordination...")
    
    try:
        ai_data = {"query": "What tasks need immediate attention?"}
        response = requests.post("http://127.0.0.1:5001/ai/analyze", json=ai_data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ AI coordination working")
            if 'response' in result:
                print(f"   🤖 AI Response: {result['response'][:100]}...")
        else:
            print(f"   ❌ AI coordination failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ AI coordination error: {e}")

def main():
    print("🚀 AI COORDINATION AGENT - COMPREHENSIVE DIAGNOSTICS")
    print("=" * 60)
    
    # Test 1: Server Health
    if not test_server_health():
        print("\n❌ Server is not running! Please start the backend first.")
        return
    
    # Test 2: Basic Task Operations
    test_task_operations()
    
    # Test 3: Multiple Task Handling
    test_multiple_tasks()
    
    # Test 4: AI Coordination
    test_ai_coordination()
    
    print("\n" + "=" * 60)
    print("✨ DIAGNOSTIC COMPLETE!")
    print("\nIf any tests failed, check:")
    print("  1. Backend server is running on port 5001")
    print("  2. Database is properly configured")
    print("  3. All dependencies are installed")
    print("  4. No firewall blocking connections")

if __name__ == "__main__":
    main()