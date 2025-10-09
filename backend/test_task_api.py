#!/usr/bin/env python3
"""
Test script for the Task Controller
"""

import os
import sys
import json

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Set up environment variables if not already set
if not os.getenv('DB_HOST'):
    os.environ['DB_HOST'] = '92.113.22.65'
if not os.getenv('DB_NAME'):
    os.environ['DB_NAME'] = 'u906714182_sqlrrefdvdv'
if not os.getenv('DB_USER'):
    os.environ['DB_USER'] = 'u906714182_sqlrrefdvdv'
if not os.getenv('DB_PASSWORD'):
    os.environ['DB_PASSWORD'] = '3@6*t:lU'
if not os.getenv('DB_PORT'):
    os.environ['DB_PORT'] = '3306'

try:
    # Import Flask app to create application context
    from app import create_app
    from controllers.task_controller import TaskController
    
    print("🔧 Testing Task Controller...")
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Initialize controller
        task_controller = TaskController()
        
        # Test 1: Get all tasks
        print("\n📋 Test 1: Getting all tasks...")
        response, status_code = task_controller.get_all_tasks()
        
        # Parse response if it's a Flask response
        if hasattr(response, 'get_json'):
            data = response.get_json()
        else:
            data = response.json if hasattr(response, 'json') else response
        
        print(f"Status Code: {status_code}")
        if isinstance(data, dict):
            if data.get('success'):
                print(f"✅ Success! Found {data.get('total_count', 0)} tasks")
                if data.get('tasks'):
                    print(f"First task: {data['tasks'][0].get('title', 'No title')}")
            else:
                print(f"❌ Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"Response: {str(data)[:200]}...")
        
        # Test 2: Search tasks with filters
        print("\n🔍 Test 2: Searching tasks with status filter...")
        filters = {'status': 'todo', 'limit': 5}
        response, status_code = task_controller.search_tasks(filters)
        
        if hasattr(response, 'get_json'):
            data = response.get_json()
        else:
            data = response.json if hasattr(response, 'json') else response
        
        print(f"Status Code: {status_code}")
        if isinstance(data, dict):
            if data.get('success'):
                print(f"✅ Success! Found {data.get('total', 0)} todo tasks")
            else:
                print(f"❌ Error: {data.get('error', 'Unknown error')}")
        
        # Test 3: Get task statistics
        print("\n📊 Test 3: Getting task statistics...")
        response, status_code = task_controller.get_task_stats()
        
        if hasattr(response, 'get_json'):
            data = response.get_json()
        else:
            data = response.json if hasattr(response, 'json') else response
        
        print(f"Status Code: {status_code}")
        if isinstance(data, dict):
            if data.get('success'):
                stats = data.get('stats', {})
                print(f"✅ Success! Stats:")
                print(f"   Total tasks: {stats.get('total_tasks', 0)}")
                print(f"   Active tasks: {stats.get('active_tasks', 0)}")
                print(f"   Completed tasks: {stats.get('completed_tasks', 0)}")
                print(f"   Tasks by status: {stats.get('tasks_by_status', {})}")
            else:
                print(f"❌ Error: {data.get('error', 'Unknown error')}")
    
    print("\n🎉 Task Controller tests completed!")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure all dependencies are installed")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()