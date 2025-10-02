#!/usr/bin/env python3
"""
Test Fixed SQL Queries
"""

import mysql.connector
from datetime import datetime

def test_fixed_queries():
    try:
        conn = mysql.connector.connect(
            host='92.113.22.65',
            user='u906714182_sqlrrefdvdv',
            password='3@6*t:lU',
            database='u906714182_sqlrrefdvdv'
        )
        cursor = conn.cursor(dictionary=True)
        
        print('🔍 Testing fixed SQL query...')
        
        # Test the fixed query
        query = """
        SELECT DISTINCT
            t.id as taskid,
            t.name as title,
            t.duedate,
            t.datefinished as completiondate,
            COALESCE(ta.staffid, 0) as staffid,
            COALESCE(s.firstname, 'Unknown') as firstname,
            COALESCE(s.lastname, 'User') as lastname,
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
        LEFT JOIN tblstaff s ON ta.staffid = s.id
        WHERE t.status != 5
        LIMIT 5
        """
        
        cursor.execute(query)
        tasks = cursor.fetchall()
        
        print(f'✅ Query successful! Found {len(tasks)} tasks:')
        for task in tasks:
            print(f"  - Task {task['taskid']}: {task['title'][:50]}... [{task['urgency_status']}]")
            
        # Test adding a comment
        if tasks:
            test_task = tasks[0]
            test_comment = f'🤖 Fixed monitor test - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            
            cursor.execute("""
                INSERT INTO tbltask_comments (taskid, staffid, dateadded, content)
                VALUES (%s, %s, %s, %s)
            """, (test_task['taskid'], 248, datetime.now(), test_comment))
            
            conn.commit()
            print(f"✅ Successfully added test comment to task {test_task['taskid']}")
        
        conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    test_fixed_queries()