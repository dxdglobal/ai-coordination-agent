#!/usr/bin/env python3
"""
Script to analyze Hamza Haseeb's projects and tasks,
and add 'welDone Hamza' comments to tasks completed on time
"""

import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

# Database connection
DB_CONFIG = {
    'host': '92.113.22.65',
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': 'u906714182_sqlrrefdvdv'
}

def get_database_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

def find_hamza_staff_id():
    """Find Hamza Haseeb's staff ID"""
    connection = get_database_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Look for Hamza in various name variations
        name_patterns = ['%hamza%', '%haseeb%', '%Hamza%', '%Haseeb%']
        
        for pattern in name_patterns:
            cursor.execute("""
                SELECT staffid, firstname, lastname, email 
                FROM tblstaff 
                WHERE CONCAT(firstname, ' ', lastname) LIKE %s
                OR firstname LIKE %s
                OR lastname LIKE %s
            """, (pattern, pattern, pattern))
            
            results = cursor.fetchall()
            if results:
                print(f"🔍 Found staff members matching '{pattern}':")
                for staff in results:
                    full_name = f"{staff['firstname']} {staff['lastname']}"
                    print(f"  - ID: {staff['staffid']}, Name: {full_name}, Email: {staff['email']}")
                
                # Look for exact match first
                for staff in results:
                    full_name = f"{staff['firstname']} {staff['lastname']}".lower()
                    if 'hamza' in full_name and 'haseeb' in full_name:
                        return staff['staffid']
                
                # Return first match if no exact match
                return results[0]['staffid']
        
        return None
        
    except mysql.connector.Error as e:
        print(f"❌ Error finding Hamza: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def get_hamza_projects(staff_id):
    """Get all projects where Hamza is involved"""
    connection = get_database_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get projects where Hamza is a member or owner
        cursor.execute("""
            SELECT DISTINCT 
                p.id as project_id,
                p.name as project_name,
                p.description as project_description,
                p.status as project_status,
                p.start_date,
                p.deadline as due_date,
                'member' as role
            FROM tblprojects p
            JOIN tblproject_members pm ON p.id = pm.project_id
            WHERE pm.staff_id = %s
            
            UNION
            
            SELECT DISTINCT 
                p.id as project_id,
                p.name as project_name,
                p.description as project_description,
                p.status as project_status,
                p.start_date,
                p.deadline as due_date,
                'owner' as role
            FROM tblprojects p
            JOIN tblproject_owners po ON p.id = po.project_id
            WHERE po.staff_id = %s
            
            ORDER BY project_id
        """, (staff_id, staff_id))
        
        projects = cursor.fetchall()
        print(f"📊 Found {len(projects)} projects for Hamza (Staff ID: {staff_id})")
        
        return projects
        
    except mysql.connector.Error as e:
        print(f"❌ Error getting projects: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def get_project_tasks(project_id, staff_id):
    """Get all tasks for a specific project assigned to Hamza"""
    connection = get_database_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get tasks assigned to Hamza in this project
        cursor.execute("""
            SELECT 
                t.id as task_id,
                t.name as task_name,
                t.description as task_description,
                t.status as task_status,
                t.priority,
                t.duedate as due_date,
                t.datefinished as completed_date,
                t.dateadded as created_date
            FROM tbltasks t
            JOIN tbltask_assigned ta ON t.id = ta.taskid
            WHERE ta.staffid = %s AND t.rel_id = %s AND t.rel_type = 'project'
            ORDER BY t.duedate
        """, (staff_id, project_id))
        
        tasks = cursor.fetchall()
        return tasks
        
    except mysql.connector.Error as e:
        print(f"❌ Error getting tasks for project {project_id}: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def is_task_completed_on_time(task):
    """Check if task was completed on time"""
    if not task['completed_date'] or not task['due_date']:
        return False
    
    completed_date = task['completed_date']
    due_date = task['due_date']
    
    # Convert to datetime if they're strings
    if isinstance(completed_date, str):
        completed_date = datetime.strptime(completed_date, '%Y-%m-%d %H:%M:%S')
    if isinstance(due_date, str):
        due_date = datetime.strptime(due_date, '%Y-%m-%d')
    
    # Convert date to datetime for comparison
    if hasattr(due_date, 'date'):  # It's already datetime
        due_date_for_comparison = due_date
    else:  # It's a date object, convert to datetime
        due_date_for_comparison = datetime.combine(due_date, datetime.min.time())
    
    if hasattr(completed_date, 'date'):  # It's already datetime
        completed_date_for_comparison = completed_date
    else:  # It's a date object, convert to datetime
        completed_date_for_comparison = datetime.combine(completed_date, datetime.min.time())
    
    return completed_date_for_comparison <= due_date_for_comparison

def get_task_comments(task_id):
    """Get existing comments for a task"""
    connection = get_database_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Use the tbltask_comments table we found
        cursor.execute("""
            SELECT * FROM tbltask_comments 
            WHERE taskid = %s
        """, (task_id,))
        comments = cursor.fetchall()
        return comments
        
    except mysql.connector.Error as e:
        print(f"❌ Error getting comments for task {task_id}: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def add_comment_to_task(task_id, comment_text):
    """Add a comment to a task"""
    connection = get_database_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Insert into tbltask_comments table
        cursor.execute("""
            INSERT INTO tbltask_comments (content, taskid, staffid, dateadded)
            VALUES (%s, %s, %s, NOW())
        """, (comment_text, task_id, 1))  # Using staffid=1 as system user
        
        connection.commit()
        print(f"✅ Added comment to task {task_id}")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error adding comment to task {task_id}: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def analyze_hamza_tasks():
    """Main function to analyze all of Hamza's tasks"""
    print("🚀 Starting Hamza Haseeb task analysis...")
    
    # Step 1: Find Hamza's staff ID
    staff_id = find_hamza_staff_id()
    if not staff_id:
        print("❌ Could not find Hamza Haseeb in staff table")
        return
    
    print(f"✅ Found Hamza Haseeb with Staff ID: {staff_id}")
    
    # Step 2: Get all his projects
    projects = get_hamza_projects(staff_id)
    if not projects:
        print("❌ No projects found for Hamza")
        return
    
    print(f"📊 Analyzing {len(projects)} projects...")
    
    total_tasks = 0
    completed_on_time = 0
    comments_added = 0
    
    # Step 3: For each project, analyze tasks
    for project in projects:
        print(f"\n🎯 Project: {project['project_name']} (ID: {project['project_id']})")
        print(f"   Role: {project['role']}")
        print(f"   Status: {project['project_status']}")
        
        tasks = get_project_tasks(project['project_id'], staff_id)
        print(f"   📋 Found {len(tasks)} tasks for Hamza in this project")
        
        total_tasks += len(tasks)
        
        for task in tasks:
            print(f"\n   📝 Task: {task['task_name']} (ID: {task['task_id']})")
            print(f"      Status: {task['task_status']}")
            print(f"      Due Date: {task['due_date']}")
            print(f"      Completed: {task['completed_date']}")
            
            if is_task_completed_on_time(task):
                completed_on_time += 1
                print("      ✅ Task completed ON TIME!")
                
                # Check if we already have a 'Keep it up testing' comment
                existing_comments = get_task_comments(task['task_id'])
                has_good_comment = any('Keep it up testing' in str(comment) for comment in existing_comments)
                
                if not has_good_comment:
                    if add_comment_to_task(task['task_id'], "Keep it up testing"):
                        comments_added += 1
                        print("      💬 Added 'Keep it up testing' comment")
                    else:
                        print("      ⚠️ Could not add comment")
                else:
                    print("      ℹ️ 'Keep it up testing' comment already exists")
            else:
                if task['completed_date']:
                    print("      ⚠️ Task completed LATE")
                    
                    # Check if we already have a 'please do it fast testing' comment
                    existing_comments = get_task_comments(task['task_id'])
                    has_late_comment = any('please do it fast testing' in str(comment) for comment in existing_comments)
                    
                    if not has_late_comment:
                        if add_comment_to_task(task['task_id'], "please do it fast testing"):
                            comments_added += 1
                            print("      💬 Added 'please do it fast testing' comment")
                        else:
                            print("      ⚠️ Could not add comment")
                    else:
                        print("      ℹ️ 'please do it fast testing' comment already exists")
                else:
                    print("      ⏳ Task not yet completed")
    
    # Summary
    print(f"\n🎉 ANALYSIS COMPLETE!")
    print(f"📊 Projects analyzed: {len(projects)}")
    print(f"📋 Total tasks found: {total_tasks}")
    print(f"✅ Tasks completed on time: {completed_on_time}")
    print(f"⚠️ Tasks completed late: {len([t for p in projects for t in get_project_tasks(p['project_id'], staff_id) if t['completed_date'] and not is_task_completed_on_time(t)])}")
    print(f"💬 Comments added: {comments_added}")
    print(f"   - 'Keep it up testing' for on-time tasks")
    print(f"   - 'please do it fast testing' for late tasks")

if __name__ == "__main__":
    analyze_hamza_tasks()