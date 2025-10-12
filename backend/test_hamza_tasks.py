#!/usr/bin/env python3
"""Test to check Hamza's actual completed tasks"""

import sys
sys.path.append('/Users/dds/Desktop/Git-Projects/ai-coordination-agent/backend')

from task_management.crm_connector import get_crm_connector
from task_management.config import Config

def check_hamza_tasks():
    """Check Hamza's tasks by status"""
    crm = get_crm_connector()
    
    # Hamza's employee ID is 188
    hamza_id = 188
    
    print("🔍 Checking Hamza's Tasks by Status")
    print("=" * 50)
    
    print("\n📋 Task Status Mapping:")
    for status_id, status_name in Config.TASK_STATUS_MAP.items():
        print(f"  {status_id}: {status_name}")
    
    print(f"\n🔍 All tasks for Hamza (ID: {hamza_id}):")
    all_tasks = crm.get_tasks_for_employee(hamza_id)
    print(f"Total tasks: {len(all_tasks)}")
    
    # Group by status
    status_counts = {}
    for task in all_tasks:
        status = task['status']
        status_name = Config.TASK_STATUS_MAP.get(status, f'Unknown({status})')
        if status_name not in status_counts:
            status_counts[status_name] = []
        status_counts[status_name].append(task)
    
    for status_name, tasks in status_counts.items():
        print(f"  {status_name}: {len(tasks)} tasks")
        if len(tasks) <= 3:  # Show first few task names
            for task in tasks:
                print(f"    - {task['name'][:50]}...")
    
    print(f"\n🔍 Testing completed filter (status 5 and 9):")
    completed_tasks = crm.get_tasks_for_employee(hamza_id, status_filter=[5, 9])
    print(f"Completed tasks found: {len(completed_tasks)}")
    
    for task in completed_tasks[:5]:  # Show first 5
        status_name = Config.TASK_STATUS_MAP.get(task['status'], f'Unknown({task["status"]})')
        print(f"  - {task['name'][:50]}... (Status: {status_name})")

if __name__ == "__main__":
    check_hamza_tasks()