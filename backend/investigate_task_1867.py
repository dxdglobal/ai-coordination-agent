#!/usr/bin/env python3
"""
Investigate specific task #1867 to see why it's not getting comments
"""

import mysql.connector
from datetime import datetime, timedelta

db_config = {
    'host': '92.113.22.65',
    'user': 'u906714182_sqlrrefdvdv',
    'password': '3@6*t:lU',
    'database': 'u906714182_sqlrrefdvdv'
}

def investigate_task_1867():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        task_id = 1867
        ai_staff_id = 248
        
        print(f"🔍 INVESTIGATING TASK #{task_id}")
        print("=" * 50)
        
        # 1. Get task details
        print("📋 TASK DETAILS...")
        cursor.execute("""
            SELECT 
                t.id,
                t.name,
                t.description,
                t.duedate,
                t.dateadded,
                t.datefinished,
                t.status,
                t.priority,
                CASE 
                    WHEN t.datefinished IS NOT NULL THEN 'completed'
                    WHEN t.duedate IS NOT NULL AND CURDATE() > t.duedate THEN 'overdue'
                    WHEN t.duedate IS NOT NULL AND DATEDIFF(t.duedate, CURDATE()) <= 2 THEN 'due_soon'
                    ELSE 'normal'
                END as urgency_status,
                CASE 
                    WHEN t.datefinished IS NOT NULL AND t.duedate IS NOT NULL THEN DATEDIFF(CURDATE(), t.duedate)
                    WHEN t.duedate IS NOT NULL THEN DATEDIFF(CURDATE(), t.duedate) 
                    ELSE 0
                END as days_late
            FROM tbltasks t
            WHERE t.id = %s
        """, (task_id,))
        
        task = cursor.fetchone()
        
        if not task:
            print(f"❌ Task {task_id} not found!")
            return
        
        print(f"✅ Task found:")
        print(f"   ID: {task['id']}")
        print(f"   Name: {task['name']}")
        print(f"   Status: {task['status']}")
        print(f"   Due Date: {task['duedate']}")
        print(f"   Finished Date: {task['datefinished']}")
        print(f"   Urgency: {task['urgency_status']}")
        print(f"   Days Late: {task['days_late']}")
        
        # 2. Check task assignments
        print(f"\n👥 TASK ASSIGNMENTS...")
        cursor.execute("""
            SELECT ta.staffid, s.firstname, s.lastname
            FROM tbltask_assigned ta
            LEFT JOIN tblstaff s ON ta.staffid = s.staffid
            WHERE ta.taskid = %s
        """, (task_id,))
        
        assignments = cursor.fetchall()
        if assignments:
            print(f"✅ Task assigned to {len(assignments)} people:")
            for assignment in assignments:
                print(f"   Staff {assignment['staffid']}: {assignment['firstname']} {assignment['lastname']}")
        else:
            print("❌ Task has no assignments!")
        
        # 3. Check existing comments
        print(f"\n💬 EXISTING COMMENTS...")
        cursor.execute("""
            SELECT 
                tc.id,
                tc.content,
                tc.dateadded,
                tc.staffid,
                s.firstname,
                s.lastname
            FROM tbltask_comments tc
            LEFT JOIN tblstaff s ON tc.staffid = s.staffid
            WHERE tc.taskid = %s
            ORDER BY tc.dateadded DESC
        """, (task_id,))
        
        comments = cursor.fetchall()
        if comments:
            print(f"✅ Found {len(comments)} comments:")
            for comment in comments:
                print(f"   {comment['dateadded']} - {comment['firstname']} {comment['lastname']} (ID: {comment['staffid']}):")
                print(f"      {comment['content'][:80]}...")
        else:
            print("❌ No comments found on this task!")
        
        # 4. Check AI agent recent comments
        print(f"\n🤖 AI AGENT COMMENT CHECK...")
        cursor.execute("""
            SELECT COUNT(*) as recent_count
            FROM tbltask_comments 
            WHERE taskid = %s 
                AND staffid = %s 
                AND dateadded >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """, (task_id, ai_staff_id))
        
        recent_ai = cursor.fetchone()
        print(f"AI comments in last 24 hours: {recent_ai['recent_count']}")
        
        if recent_ai['recent_count'] > 0:
            print("⏭️ REASON: AI already commented within 24 hours (cooldown active)")
        
        # 5. Check if task appears in monitor query
        print(f"\n🔍 MONITOR QUERY CHECK...")
        cursor.execute("""
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
            AND t.id = %s
        """, (task_id,))
        
        monitor_result = cursor.fetchone()
        if monitor_result:
            print("✅ Task appears in monitor query")
            print(f"   Urgency: {monitor_result['urgency_status']}")
            print(f"   Staff ID: {monitor_result['staffid']}")
        else:
            print("❌ Task does NOT appear in monitor query!")
            print("   Possible reasons:")
            print("   - Status = 5 (completed)")
            print("   - Other filter conditions not met")
        
        # 6. Simulate should_comment logic
        print(f"\n🧠 COMMENT LOGIC SIMULATION...")
        if monitor_result:
            urgency = monitor_result['urgency_status']
            days_late = monitor_result.get('days_late', 0) or 0
            
            print(f"Urgency: {urgency}, Days Late: {days_late}")
            
            # Simulate the logic from should_comment_on_task
            if recent_ai['recent_count'] > 0:
                print("❌ SKIP: Already commented within 24 hours")
            elif urgency == 'completed' and days_late <= 0:
                print("✅ SHOULD COMMENT: Completed task (celebration)")
            elif urgency == 'due_soon':
                print("✅ MIGHT COMMENT: Due soon (30% chance)")
            elif urgency == 'overdue':
                if days_late == 1:
                    print("✅ SHOULD COMMENT: Just became overdue")
                elif days_late <= 3:
                    print("✅ MIGHT COMMENT: Overdue 1-3 days (70% chance)")
                elif days_late <= 7:
                    print("✅ MIGHT COMMENT: Overdue 4-7 days (90% chance)")
                else:
                    print("✅ SHOULD COMMENT: Seriously overdue (>7 days)")
            else:
                print("❌ SKIP: Normal task (5% chance)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    investigate_task_1867()