#!/usr/bin/env python3
"""
Create Test Tasks and Check Database
"""

import requests
import json
from datetime import datetime, timedelta

def create_test_tasks():
    """Create test tasks with different statuses"""
    tasks = [
        {
            'title': 'Overdue Task', 
            'description': 'This task is overdue', 
            'status': 'todo', 
            'end_time': (datetime.now() - timedelta(days=2)).isoformat()
        },
        {
            'title': 'Due Soon Task', 
            'description': 'This task is due soon', 
            'status': 'todo', 
            'end_time': (datetime.now() + timedelta(days=1)).isoformat()
        }, 
        {
            'title': 'Completed Task', 
            'description': 'This task is completed', 
            'status': 'completed', 
            'end_time': datetime.now().isoformat()
        }
    ]

    print('🔨 Creating test tasks...')
    created_tasks = []
    
    for i, task in enumerate(tasks):
        try:
            response = requests.post('http://127.0.0.1:5001/api/tasks', json=task, timeout=10)
            if response.status_code == 201:
                created_task = response.json()
                created_tasks.append(created_task)
                print(f'  ✅ Created task {i+1}: {task["title"]} (ID: {created_task["id"]})')
            else:
                print(f'  ❌ Failed task {i+1}: {response.status_code}')
                print(f'      Response: {response.text}')
        except Exception as e:
            print(f'  ❌ Error creating task {i+1}: {e}')
    
    return created_tasks

def check_all_tasks():
    """Check all tasks in the database"""
    print('\n📊 Getting all tasks from database...')
    try:
        response = requests.get('http://127.0.0.1:5001/api/tasks', timeout=10)
        if response.status_code == 200:
            tasks = response.json()
            print(f'  📝 Total tasks in database: {len(tasks)}')
            
            for task in tasks:
                status = task.get('status', 'Unknown')
                title = task.get('title', 'Unknown')
                task_id = task.get('id', 'Unknown')
                end_time = task.get('end_time', 'No due date')
                
                print(f'    - [{task_id}] {title} [{status}] Due: {end_time}')
            
            return tasks
        else:
            print(f'  ❌ Failed to get tasks: {response.status_code}')
            return []
    except Exception as e:
        print(f'  ❌ Error getting tasks: {e}')
        return []

def main():
    print("🤖 TASK CREATOR & DATABASE CHECKER")
    print("=" * 50)
    
    # Create test tasks
    created_tasks = create_test_tasks()
    
    # Check all tasks
    all_tasks = check_all_tasks()
    
    print("\n" + "=" * 50)
    print("✨ Task creation complete!")
    print(f"📊 Tasks that should be monitored: {len(all_tasks)}")
    
    if all_tasks:
        overdue = [t for t in all_tasks if t.get('status') == 'todo' and t.get('end_time')]
        completed = [t for t in all_tasks if t.get('status') == 'completed']
        
        print(f"   📅 Tasks that need 'late' comments: {len([t for t in overdue if datetime.fromisoformat(t['end_time'].replace('Z', '+00:00')) < datetime.now()])}")
        print(f"   🌟 Tasks that need 'good job' comments: {len(completed)}")

if __name__ == "__main__":
    main()