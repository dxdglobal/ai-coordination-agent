#!/usr/bin/env python3
"""
Human-like casual yet professional commenting system
Natural, friendly team lead style comments
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

def get_human_positive_comments():
    """Natural, encouraging comments for on-time work"""
    return [
        "Nice work! You nailed the deadline perfectly 👍",
        "Great job getting this done on time! Your consistency is really appreciated",
        "Well done! Right on schedule as always. Keep up the good work",
        "Excellent timing! Thanks for staying on track with this one",
        "Perfect! Delivered exactly when needed. Really solid work here",
        "Awesome job! Your punctuality makes planning so much easier",
        "Love seeing this completed on time! You're really on top of things",
        "Fantastic work! Right on target with the deadline. Much appreciated",
        "Great execution! Delivered as promised. This kind of reliability is gold",
        "Spot on timing! Thanks for making this look easy 😊"
    ]

def get_human_late_comments():
    """Natural, constructive comments for late work - casual but professional"""
    return [
        "Hey, this one ran a bit behind schedule. Let's try to tighten up the timing on the next one",
        "This came in late - no worries, but let's aim to hit those deadlines moving forward",
        "Looks like we missed the target date here. Can we work on getting back on track?",
        "This one took longer than expected. Let's chat about what we can do to speed things up",
        "Running behind on this one - happens to everyone! Let's focus on better time management",
        "Deadline was missed on this task. Let's see how we can improve the workflow next time",
        "This came in after the due date. No big deal, but let's try to be more mindful of timing",
        "A bit late on delivery here. Let's work together to get future tasks done on schedule"
    ]

def get_very_late_comments():
    """For significantly late tasks - more direct but still professional"""
    return [
        "This is quite overdue now. We really need to pick up the pace on future tasks",
        "Way past the deadline here. Let's have a quick chat about what's holding things up",
        "This is running very late. We need to get better at meeting our commitments",
        "Significantly behind schedule on this one. Time to step it up and catch up",
        "This is very overdue. Let's figure out how to prevent this from happening again",
        "Major delay on this task. We need to be more proactive about hitting deadlines"
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

def get_employee_first_name(staff_id):
    """Get employee's first name from staff ID"""
    connection = get_database_connection()
    if not connection:
        return "team"
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT firstname FROM tblstaff WHERE staffid = %s", (staff_id,))
        result = cursor.fetchone()
        if result:
            return result['firstname'].strip()
        return "team"
    except mysql.connector.Error:
        return "team"
    finally:
        cursor.close()
        connection.close()

def calculate_days_late(due_date, finished_date):
    """Calculate how many days late a task was"""
    if not due_date or not finished_date:
        return 0
    
    from datetime import datetime, date
    
    if isinstance(finished_date, datetime):
        finished_datetime = finished_date
    else:
        finished_datetime = datetime.combine(finished_date, datetime.min.time())
    
    if isinstance(due_date, datetime):
        due_datetime = due_date
    elif isinstance(due_date, date):
        due_datetime = datetime.combine(due_date, datetime.max.time())
    else:
        due_datetime = due_date
    
    if finished_datetime > due_datetime:
        delta = finished_datetime - due_datetime
        return delta.days
    return 0

def update_human_like_comments():
    """Update all comments with human-like, casual professional tone"""
    agent_id = get_coordination_agent_id()
    if not agent_id:
        print("❌ Could not find COORDINATION AGENT DXD AI")
        return
    
    connection = get_database_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get all our existing comments
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
            AND tc.content LIKE '@%'
            ORDER BY tc.dateadded DESC
        """, (agent_id,))
        
        comments_to_update = cursor.fetchall()
        
        print(f"🔍 Found {len(comments_to_update)} comments to make more human-like...")
        
        positive_comments = get_human_positive_comments()
        late_comments = get_human_late_comments()
        very_late_comments = get_very_late_comments()
        
        updated_count = 0
        
        for comment_data in comments_to_update:
            # Get employee name
            employee_name = get_employee_first_name(comment_data['staffid'])
            
            # Calculate if task was late and by how much
            days_late = calculate_days_late(comment_data['duedate'], comment_data['datefinished'])
            
            # Generate human-like comment based on lateness
            if days_late == 0:
                # On time or early
                base_comment = random.choice(positive_comments)
                new_comment = f"Hey {employee_name}! {base_comment}"
            elif days_late <= 3:
                # Slightly late (1-3 days)
                base_comment = random.choice(late_comments)
                new_comment = f"Hi {employee_name}, {base_comment}"
            else:
                # Very late (more than 3 days)
                base_comment = random.choice(very_late_comments)
                new_comment = f"{employee_name}, {base_comment}"
            
            # Update the comment
            cursor.execute("""
                UPDATE tbltask_comments 
                SET content = %s 
                WHERE id = %s
            """, (new_comment, comment_data['comment_id']))
            
            updated_count += 1
            
            print(f"✅ Task {comment_data['taskid']}: '{comment_data['task_name'][:40]}...'")
            print(f"   👤 Employee: {employee_name}")
            print(f"   ⏰ Days late: {days_late}")
            print(f"   💬 New comment: '{new_comment}'")
            print("-" * 60)
        
        connection.commit()
        print(f"\n🎉 Successfully updated {updated_count} comments with human-like tone!")
        
    except mysql.connector.Error as e:
        print(f"❌ Error updating comments: {e}")
    finally:
        cursor.close()
        connection.close()

def verify_human_comments():
    """Verify the human-like comments"""
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
                t.name as task_name,
                tc.dateadded
            FROM tbltask_comments tc
            JOIN tbltasks t ON tc.taskid = t.id
            WHERE tc.staffid = %s 
            AND (tc.content LIKE 'Hey %' OR tc.content LIKE 'Hi %' OR tc.content LIKE '% %')
            ORDER BY tc.dateadded DESC
            LIMIT 10
        """, (agent_id,))
        
        human_comments = cursor.fetchall()
        
        print(f"\n🔍 VERIFICATION - Human-like comments:")
        print("=" * 80)
        
        for comment in human_comments:
            print(f"📝 Task: {comment['task_name'][:50]}...")
            print(f"💬 Comment: '{comment['content']}'")
            print(f"📅 Added: {comment['dateadded']}")
            print("-" * 40)
        
    except mysql.connector.Error as e:
        print(f"❌ Error verifying: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    print("🤖 CREATING HUMAN-LIKE, CASUAL PROFESSIONAL COMMENTS...")
    print("=" * 60)
    update_human_like_comments()
    verify_human_comments()