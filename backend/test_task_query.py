#!/usr/bin/env python3
"""
Test the actual task query to see what we're getting
"""

import mysql.connector
from datetime import datetime

db_config = {
    'host': '92.113.22.65',
    'user': 'u906714182_sqlrrefdvdv',
    'password': '3@6*t:lU',
    'database': 'u906714182_sqlrrefdvdv'
}

def test_task_query():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        print("🔍 TESTING TASK QUERY...")
        
        # Current query from monitor
        query = """
        SELECT DISTINCT
            t.id as taskid,
            t.name as title,
            t.duedate,
            t.datefinished as completiondate,
            COALESCE(ta.staffid, 0) as staffid,
            'User' as firstname,
            'Staff' as lastname,
            CASE 
                WHEN t.datefinished IS NOT NULL AND t.duedate IS NOT NULL THEN DATEDIFF(CURDATE(), t.duedate)
                WHEN t.duedate IS NOT NULL THEN DATEDIFF(CURDATE(), t.duedate) 
                ELSE 0
            END as days_late,
            CASE 
                WHEN t.datefinished IS NOT NULL THEN 'completed'
                WHEN t.duedate IS NOT NULL AND CURDATE() > t.duedate THEN 'overdue'
                WHEN t.duedate IS NOT NULL AND DATEDIFF(t.duedate, CURDATE()) <= 2 THEN 'due_soon'
                ELSE 'normal'
            END as urgency_status
        FROM tbltasks t
        LEFT JOIN tbltask_assigned ta ON t.id = ta.taskid
        WHERE t.status != 5  -- Not completed status
        ORDER BY 
            CASE 
                WHEN t.datefinished IS NOT NULL AND DATEDIFF(COALESCE(t.datefinished, CURDATE()), t.duedate) <= 0 THEN 1  -- Completed on time
                WHEN CURDATE() > t.duedate THEN 2  -- Overdue (high priority)
                WHEN DATEDIFF(t.duedate, CURDATE()) <= 2 THEN 3  -- Due soon
                ELSE 4  -- Normal
            END,
            t.duedate ASC
        """
        
        cursor.execute(query)
        tasks = cursor.fetchall()
        
        print(f"📊 Query returned {len(tasks)} tasks")
        
        if len(tasks) == 0:
            print("❌ No tasks returned! Let's debug...")
            
            # Check what statuses exist
            cursor.execute("SELECT status, COUNT(*) as count FROM tbltasks GROUP BY status")
            statuses = cursor.fetchall()
            print("📋 Task statuses in database:")
            for status in statuses:
                print(f"   Status {status['status']}: {status['count']} tasks")
            
            # Try simple query without status filter
            print("\n🔍 Trying without status filter...")
            cursor.execute("SELECT COUNT(*) as total FROM tbltasks")
            total = cursor.fetchone()
            print(f"📝 Total tasks without filter: {total['total']}")
            
            # Try with different status
            cursor.execute("SELECT COUNT(*) as count FROM tbltasks WHERE status != 5")
            not_completed = cursor.fetchone()
            print(f"📝 Tasks with status != 5: {not_completed['count']}")
            
        else:
            print(f"✅ Found {len(tasks)} tasks!")
            print("\n📋 Sample tasks:")
            for i, task in enumerate(tasks[:5]):  # Show first 5
                print(f"   {i+1}. Task {task['taskid']}: {task['title'][:50]}...")
                print(f"      Due: {task['duedate']}, Status: {task['urgency_status']}")
                print(f"      Staff: {task['staffid']} ({task['firstname']} {task['lastname']})")
                
            # Count by urgency
            urgency_counts = {}
            for task in tasks:
                urgency = task['urgency_status']
                urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
            
            print(f"\n📊 Tasks by urgency:")
            for urgency, count in urgency_counts.items():
                print(f"   {urgency}: {count} tasks")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_task_query()