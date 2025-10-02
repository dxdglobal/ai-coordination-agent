#!/usr/bin/env python3
"""
Test Comment Addition System
===========================
Test if the AI agent is actually adding comments to tasks
"""

import mysql.connector
from datetime import datetime, timedelta

db_config = {
    'host': '92.113.22.65',
    'user': 'u906714182_sqlrrefdvdv',
    'password': '3@6*t:lU',
    'database': 'u906714182_sqlrrefdvdv'
}

def test_comment_system():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        print("🔍 TESTING COMMENT SYSTEM...")
        print("=" * 50)
        
        # Check if AI agent exists and can comment
        ai_staff_id = 248
        
        # 1. Check recent comments by AI agent
        print(f"📝 Checking recent comments by AI Agent (Staff ID {ai_staff_id})...")
        
        cursor.execute("""
            SELECT COUNT(*) as recent_comments
            FROM tbltask_comments 
            WHERE staffid = %s 
            AND dateadded >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """, (ai_staff_id,))
        
        recent = cursor.fetchone()
        print(f"💬 Comments by AI in last 24 hours: {recent['recent_comments']}")
        
        # 2. Check all comments by AI agent
        cursor.execute("""
            SELECT COUNT(*) as total_comments
            FROM tbltask_comments 
            WHERE staffid = %s
        """, (ai_staff_id,))
        
        total = cursor.fetchone()
        print(f"💭 Total comments by AI agent: {total['total_comments']}")
        
        # 3. Get latest comments by AI
        cursor.execute("""
            SELECT tc.taskid, tc.content, tc.dateadded, t.name as task_name
            FROM tbltask_comments tc
            LEFT JOIN tbltasks t ON tc.taskid = t.id
            WHERE tc.staffid = %s
            ORDER BY tc.dateadded DESC
            LIMIT 5
        """, (ai_staff_id,))
        
        latest_comments = cursor.fetchall()
        if latest_comments:
            print(f"\n📋 Latest {len(latest_comments)} comments by AI:")
            for comment in latest_comments:
                print(f"   • Task {comment['taskid']}: {comment['task_name'][:40]}...")
                print(f"     Comment: {comment['content'][:60]}...")
                print(f"     Date: {comment['dateadded']}")
                print()
        else:
            print("❌ No comments found by AI agent")
        
        # 4. Test adding a comment manually
        print("🧪 TESTING MANUAL COMMENT ADDITION...")
        
        # Get a sample overdue task
        cursor.execute("""
            SELECT t.id as taskid, t.name, ta.staffid
            FROM tbltasks t
            LEFT JOIN tbltask_assigned ta ON t.id = ta.taskid
            WHERE t.status != 5 
            AND t.duedate IS NOT NULL 
            AND CURDATE() > t.duedate
            AND ta.staffid IS NOT NULL
            LIMIT 1
        """)
        
        test_task = cursor.fetchone()
        
        if test_task:
            print(f"🎯 Found test task: {test_task['taskid']} - {test_task['name'][:40]}...")
            
            # Check if we commented recently on this task
            cursor.execute("""
                SELECT COUNT(*) as recent_count
                FROM tbltask_comments 
                WHERE taskid = %s 
                AND staffid = %s 
                AND dateadded >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """, (test_task['taskid'], ai_staff_id))
            
            recent_check = cursor.fetchone()
            
            if recent_check['recent_count'] == 0:
                print("✅ No recent comment on this task - we can add one")
                
                # Try to add a test comment
                test_comment = "🤖 TEST: AI Agent monitoring system verification"
                
                try:
                    cursor.execute("""
                        INSERT INTO tbltask_comments (content, taskid, staffid, dateadded)
                        VALUES (%s, %s, %s, NOW())
                    """, (test_comment, test_task['taskid'], ai_staff_id))
                    
                    conn.commit()
                    print(f"✅ Successfully added test comment to task {test_task['taskid']}")
                    
                    # Verify it was added
                    cursor.execute("""
                        SELECT content, dateadded 
                        FROM tbltask_comments 
                        WHERE taskid = %s AND staffid = %s 
                        ORDER BY dateadded DESC 
                        LIMIT 1
                    """, (test_task['taskid'], ai_staff_id))
                    
                    new_comment = cursor.fetchone()
                    if new_comment:
                        print(f"✅ Verified: Comment added at {new_comment['dateadded']}")
                        print(f"   Content: {new_comment['content']}")
                    
                except Exception as e:
                    print(f"❌ Failed to add comment: {e}")
                    
            else:
                print(f"⏭️ Already commented on this task recently ({recent_check['recent_count']} times)")
        else:
            print("❌ No suitable test task found")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Comment system test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_comment_system()