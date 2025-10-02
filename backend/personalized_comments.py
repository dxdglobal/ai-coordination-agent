#!/usr/bin/env python3
"""
Enhanced personalized commenting system for tasks
Uses actual employee names and varied feedback messages
"""

import mysql.connector
import os
from dotenv import load_dotenv
import random

load_dotenv()

def get_database_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(
            host='92.113.22.65',
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database='u906714182_sqlrrefdvdv'
        )
        return connection
    except mysql.connector.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

def get_employee_first_name(staff_id):
    """Get employee's first name from staff ID"""
    connection = get_database_connection()
    if not connection:
        return "Employee"
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT firstname FROM tblstaff WHERE staffid = %s", (staff_id,))
        result = cursor.fetchone()
        if result:
            return result['firstname'].strip().lower()
        return "Employee"
    except mysql.connector.Error:
        return "Employee"
    finally:
        cursor.close()
        connection.close()

def get_positive_comments():
    """Get variety of positive comments for on-time completion"""
    return [
        "you are doing well! Keep up the excellent work",
        "excellent timing! Great job staying on schedule",
        "fantastic work! Your punctuality is appreciated",
        "well done! You're maintaining great momentum",
        "superb! Your time management skills are impressive",
        "outstanding! You delivered right on time",
        "brilliant work! Your dedication shows",
        "amazing! You're setting a great example",
        "perfect timing! Your consistency is valuable",
        "excellent! You're exceeding expectations"
    ]

def get_late_comments():
    """Get variety of constructive comments for late completion"""
    return [
        "please do it fast you are so late",
        "please improve your timing, this was delayed",
        "please focus on meeting deadlines, this was overdue",
        "please prioritize time management, this task was late",
        "please work on punctuality, the deadline was missed",
        "please speed up delivery, this took longer than expected",
        "please manage your schedule better, this was behind schedule",
        "please be more mindful of deadlines in future tasks"
    ]

def get_coordination_agent_id():
    """Get COORDINATION AGENT DXD AI staff ID"""
    connection = get_database_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT staffid FROM tblstaff 
            WHERE firstname = 'COORDINATION AGENT' 
            AND lastname LIKE '%DXD AI%'
        """)
        result = cursor.fetchone()
        return result['staffid'] if result else None
    except mysql.connector.Error:
        return None
    finally:
        cursor.close()
        connection.close()

def update_personalized_comments():
    """Update all testing comments with personalized versions"""
    agent_id = get_coordination_agent_id()
    if not agent_id:
        print("❌ Could not find COORDINATION AGENT DXD AI")
        return
    
    connection = get_database_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get all tasks with our testing comments
        cursor.execute("""
            SELECT 
                tc.id as comment_id,
                tc.taskid,
                tc.content,
                ta.staffid,
                t.name as task_name,
                t.duedate,
                t.datefinished
            FROM tbltask_comments tc
            JOIN tbltasks t ON tc.taskid = t.id
            JOIN tbltask_assigned ta ON t.id = ta.taskid
            WHERE tc.staffid = %s 
            AND tc.content LIKE '%testing%'
            ORDER BY tc.dateadded DESC
        """, (agent_id,))
        
        comments_to_update = cursor.fetchall()
        
        print(f"🔍 Found {len(comments_to_update)} comments to personalize...")
        
        positive_comments = get_positive_comments()
        late_comments = get_late_comments()
        
        updated_count = 0
        
        for comment_data in comments_to_update:
            # Get employee name
            employee_name = get_employee_first_name(comment_data['staffid'])
            
            # Determine if task was late or on time
            is_late = False
            if comment_data['duedate'] and comment_data['datefinished']:
                due_date = comment_data['duedate']
                finished_date = comment_data['datefinished']
                
                # Convert both to datetime for comparison
                from datetime import datetime, date
                
                if isinstance(finished_date, datetime):
                    finished_datetime = finished_date
                else:
                    finished_datetime = datetime.combine(finished_date, datetime.min.time())
                
                if isinstance(due_date, datetime):
                    due_datetime = due_date
                elif isinstance(due_date, date):
                    due_datetime = datetime.combine(due_date, datetime.max.time())  # End of day for due date
                else:
                    due_datetime = due_date
                
                is_late = finished_datetime > due_datetime
            else:
                # If task was completed but no due date, assume it was late based on current comment
                is_late = "please do it fast testing" in comment_data['content']
            
            # Generate personalized comment
            if is_late:
                base_comment = random.choice(late_comments)
                new_comment = f"@{employee_name} {base_comment}"
            else:
                base_comment = random.choice(positive_comments)
                new_comment = f"@{employee_name} {base_comment}"
            
            # Update the comment
            cursor.execute("""
                UPDATE tbltask_comments 
                SET content = %s 
                WHERE id = %s
            """, (new_comment, comment_data['comment_id']))
            
            updated_count += 1
            
            print(f"✅ Task {comment_data['taskid']}: '{comment_data['task_name'][:40]}...'")
            print(f"   👤 Employee: @{employee_name}")
            print(f"   💬 New comment: '{new_comment}'")
            print(f"   ⏰ Status: {'LATE' if is_late else 'ON TIME'}")
            print("-" * 60)
        
        connection.commit()
        print(f"\n🎉 Successfully updated {updated_count} comments with personalized feedback!")
        
    except mysql.connector.Error as e:
        print(f"❌ Error updating comments: {e}")
    finally:
        cursor.close()
        connection.close()

def verify_personalized_comments():
    """Verify the personalized comments were applied"""
    agent_id = get_coordination_agent_id()
    if not agent_id:
        return
    
    connection = get_database_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                tc.taskid,
                tc.content,
                CONCAT(s.firstname, ' ', s.lastname) as staff_name,
                t.name as task_name
            FROM tbltask_comments tc
            JOIN tblstaff s ON tc.staffid = s.staffid
            JOIN tbltasks t ON tc.taskid = t.id
            WHERE tc.staffid = %s 
            AND tc.content LIKE '@%'
            ORDER BY tc.dateadded DESC
            LIMIT 10
        """, (agent_id,))
        
        personalized_comments = cursor.fetchall()
        
        print(f"\n🔍 VERIFICATION - Found {len(personalized_comments)} personalized comments:")
        print("=" * 80)
        
        for comment in personalized_comments:
            print(f"📝 Task: {comment['task_name'][:50]}...")
            print(f"💬 Comment: '{comment['content']}'")
            print(f"👤 By: {comment['staff_name']}")
            print("-" * 40)
        
    except mysql.connector.Error as e:
        print(f"❌ Error verifying: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    print("🤖 PERSONALIZING COMMENTS WITH EMPLOYEE NAMES...")
    print("=" * 60)
    update_personalized_comments()
    verify_personalized_comments()