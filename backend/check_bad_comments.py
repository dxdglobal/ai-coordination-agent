#!/usr/bin/env python3
"""
Check existing AI comments that use "User" and need to be fixed
"""

import mysql.connector

db_config = {
    'host': '92.113.22.65',
    'user': 'u906714182_sqlrrefdvdv',
    'password': '3@6*t:lU',
    'database': 'u906714182_sqlrrefdvdv'
}

def check_ai_comments_with_user():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        print("🔍 CHECKING AI COMMENTS THAT USE 'User' INSTEAD OF REAL NAMES")
        print("=" * 70)
        
        # Find AI comments that contain "User"
        cursor.execute("""
            SELECT 
                tc.taskid,
                tc.content,
                tc.dateadded,
                t.name as task_name,
                ta.staffid,
                s.firstname,
                s.lastname
            FROM tbltask_comments tc
            LEFT JOIN tbltasks t ON tc.taskid = t.id
            LEFT JOIN tbltask_assigned ta ON t.id = ta.taskid
            LEFT JOIN tblstaff s ON ta.staffid = s.staffid
            WHERE tc.staffid = 248  -- AI agent
            AND tc.content LIKE '%User%'
            ORDER BY tc.dateadded DESC
            LIMIT 10
        """)
        
        bad_comments = cursor.fetchall()
        
        if bad_comments:
            print(f"❌ Found {len(bad_comments)} AI comments using 'User' instead of real names:")
            print()
            
            for comment in bad_comments:
                print(f"📝 Task {comment['taskid']}: {comment['task_name'][:40]}...")
                print(f"   👤 Should be: {comment['firstname']} {comment['lastname']} (Staff {comment['staffid']})")
                print(f"   💬 Current comment: {comment['content'][:80]}...")
                print(f"   📅 Date: {comment['dateadded']}")
                print()
        else:
            print("✅ No AI comments found using 'User' - all good!")
        
        # Show recent AI comments for reference
        print("\n📋 RECENT AI COMMENTS (for reference):")
        cursor.execute("""
            SELECT 
                tc.taskid,
                tc.content,
                tc.dateadded,
                t.name as task_name
            FROM tbltask_comments tc
            LEFT JOIN tbltasks t ON tc.taskid = t.id
            WHERE tc.staffid = 248  -- AI agent
            ORDER BY tc.dateadded DESC
            LIMIT 5
        """)
        
        recent_comments = cursor.fetchall()
        for comment in recent_comments:
            print(f"   Task {comment['taskid']}: {comment['content'][:60]}... ({comment['dateadded']})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_ai_comments_with_user()