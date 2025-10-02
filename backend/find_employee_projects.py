#!/usr/bin/env python3
"""
Employee Projects Finder
Handles queries like "Show me Hamza's projects", "Nawaz projects", etc.
"""

import mysql.connector
import os
from dotenv import load_dotenv
import re

def find_employee_projects(employee_name):
    """
    Find projects associated with any employee by name
    """
    print(f"🔍 SEARCHING FOR {employee_name.upper()}'S PROJECTS")
    print("=" * 60)
    
    load_dotenv()
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        cursor = conn.cursor(dictionary=True)
        print("✅ Database connection successful!")
        
        # Step 1: Find the employee in different tables
        employee_found = False
        employee_ids = {}
        
        # Search in employees table
        print(f"\n📊 Searching for '{employee_name}' in employees table:")
        cursor.execute("SELECT * FROM employees WHERE name LIKE %s", (f"%{employee_name}%",))
        emp_results = cursor.fetchall()
        
        if emp_results:
            employee_found = True
            for emp in emp_results:
                employee_ids['employees'] = emp['id']
                print(f"✅ Found: ID {emp['id']} | {emp['name']} | {emp['email']} | {emp['department']} ({emp['position']})")
        
        # Search in tblstaff table
        print(f"\n📊 Searching for '{employee_name}' in tblstaff:")
        cursor.execute("SELECT * FROM tblstaff WHERE firstname LIKE %s OR lastname LIKE %s OR CONCAT(firstname, ' ', lastname) LIKE %s", 
                      (f"%{employee_name}%", f"%{employee_name}%", f"%{employee_name}%"))
        staff_results = cursor.fetchall()
        
        if staff_results:
            employee_found = True
            for staff in staff_results:
                employee_ids['tblstaff'] = staff['staffid']
                full_name = f"{staff.get('firstname', '')} {staff.get('lastname', '')}".strip()
                print(f"✅ Found: Staff ID {staff['staffid']} | {full_name} | {staff.get('email', 'No email')}")
        
        if not employee_found:
            print(f"❌ No employee named '{employee_name}' found in the database")
            return
        
        # Step 2: Search for projects associated with this employee
        print(f"\n🔍 SEARCHING FOR PROJECTS:")
        print("-" * 40)
        
        projects_found = []
        
        # Method 1: Check project members table
        if 'tblstaff' in employee_ids:
            print(f"📋 Checking tblproject_members for staff ID {employee_ids['tblstaff']}:")
            try:
                cursor.execute("""
                    SELECT p.*, pm.* FROM tblprojects p 
                    JOIN tblproject_members pm ON p.id = pm.project_id 
                    WHERE pm.staff_id = %s
                """, (employee_ids['tblstaff'],))
                project_members = cursor.fetchall()
                
                if project_members:
                    for proj in project_members:
                        projects_found.append({
                            'source': 'project_members',
                            'project_id': proj['id'],
                            'name': proj['name'],
                            'description': proj.get('description', ''),
                            'status': proj['status'],
                            'client_id': proj.get('clientid', ''),
                            'cost': proj.get('project_cost', '0'),
                            'created': proj.get('project_created', ''),
                            'role': 'Team Member'
                        })
                        print(f"✅ Project Member: {proj['name']} (ID: {proj['id']})")
            except Exception as e:
                print(f"⚠️ Error checking project members: {e}")
        
        # Method 2: Check tasks assigned to the employee
        if 'tblstaff' in employee_ids:
            print(f"\n📋 Checking tasks assigned to staff ID {employee_ids['tblstaff']}:")
            try:
                cursor.execute("""
                    SELECT DISTINCT p.*, 'Task Assignment' as role 
                    FROM tblprojects p 
                    JOIN tbltasks t ON p.id = t.rel_id 
                    WHERE t.addedfrom = %s OR JSON_CONTAINS(t.assignees, %s, '$')
                """, (employee_ids['tblstaff'], f'"{employee_ids["tblstaff"]}"'))
                task_projects = cursor.fetchall()
                
                for proj in task_projects:
                    # Avoid duplicates
                    if not any(p['project_id'] == proj['id'] for p in projects_found):
                        projects_found.append({
                            'source': 'tasks',
                            'project_id': proj['id'],
                            'name': proj['name'],
                            'description': proj.get('description', ''),
                            'status': proj['status'],
                            'client_id': proj.get('clientid', ''),
                            'cost': proj.get('project_cost', '0'),
                            'created': proj.get('project_created', ''),
                            'role': 'Task Assignment'
                        })
                        print(f"✅ Task Assignment: {proj['name']} (ID: {proj['id']})")
            except Exception as e:
                print(f"⚠️ Error checking task assignments: {e}")
        
        # Method 3: Check if employee created/manages projects
        if 'tblstaff' in employee_ids:
            print(f"\n📋 Checking projects created by staff ID {employee_ids['tblstaff']}:")
            try:
                cursor.execute("SELECT * FROM tblprojects WHERE addedfrom = %s", (employee_ids['tblstaff'],))
                created_projects = cursor.fetchall()
                
                for proj in created_projects:
                    if not any(p['project_id'] == proj['id'] for p in projects_found):
                        projects_found.append({
                            'source': 'creator',
                            'project_id': proj['id'],
                            'name': proj['name'],
                            'description': proj.get('description', ''),
                            'status': proj['status'],
                            'client_id': proj.get('clientid', ''),
                            'cost': proj.get('project_cost', '0'),
                            'created': proj.get('project_created', ''),
                            'role': 'Project Creator'
                        })
                        print(f"✅ Project Creator: {proj['name']} (ID: {proj['id']})")
            except Exception as e:
                print(f"⚠️ Error checking created projects: {e}")
        
        # Method 4: Check tasks table for direct association
        print(f"\n📋 Checking tasks table for '{employee_name}' projects:")
        try:
            cursor.execute("""
                SELECT DISTINCT p.*, t.name as task_name 
                FROM tblprojects p 
                JOIN tbltasks t ON p.id = t.rel_id 
                WHERE t.name LIKE %s OR t.description LIKE %s
            """, (f"%{employee_name}%", f"%{employee_name}%"))
            name_based_projects = cursor.fetchall()
            
            for proj in name_based_projects:
                if not any(p['project_id'] == proj['id'] for p in projects_found):
                    projects_found.append({
                        'source': 'task_mention',
                        'project_id': proj['id'],
                        'name': proj['name'],
                        'description': proj.get('description', ''),
                        'status': proj['status'],
                        'client_id': proj.get('clientid', ''),
                        'cost': proj.get('project_cost', '0'),
                        'created': proj.get('project_created', ''),
                        'role': 'Task Mention',
                        'task': proj.get('task_name', '')
                    })
                    print(f"✅ Mentioned in Task: {proj['name']} (ID: {proj['id']}) - Task: {proj.get('task_name', '')}")
        except Exception as e:
            print(f"⚠️ Error checking task mentions: {e}")
        
        # Display Results
        print(f"\n{'='*60}")
        print(f"📋 {employee_name.upper()}'S PROJECTS SUMMARY")
        print('='*60)
        
        if projects_found:
            print(f"✅ Found {len(projects_found)} project(s) associated with {employee_name}:")
            print()
            
            for i, project in enumerate(projects_found, 1):
                print(f"{i}. 📁 {project['name']}")
                print(f"   - Project ID: {project['project_id']}")
                print(f"   - Role: {project['role']}")
                print(f"   - Status: {project['status']}")
                print(f"   - Cost: ${project['cost']}")
                print(f"   - Created: {project['created']}")
                if project.get('task'):
                    print(f"   - Related Task: {project['task']}")
                if project['description']:
                    print(f"   - Description: {project['description'][:100]}...")
                print(f"   - Source: {project['source']}")
                print()
        else:
            print(f"❌ No projects found associated with {employee_name}")
            print("This could mean:")
            print("- The employee is not assigned to any projects")
            print("- The employee has no tasks in the system") 
            print("- The employee is not in the project members table")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def parse_employee_name_from_query(query):
    """
    Extract employee name from queries like "Show me Hamza's projects", "Nawaz projects", etc.
    """
    query = query.lower()
    
    # Patterns to match
    patterns = [
        r"show me (\w+)'s projects",
        r"(\w+)'s projects", 
        r"(\w+) projects",
        r"projects for (\w+)",
        r"(\w+) project list",
        r"what projects does (\w+) work on",
        r"find (\w+) projects"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return match.group(1).capitalize()
    
    return None

def test_employee_projects():
    """Test function with various employee queries"""
    
    test_queries = [
        "Please show me Hamza's projects",
        "Show me Nawaz's projects", 
        "Haseeb projects",
        "What projects does Sarah work on",
        "Find Deniz projects"
    ]
    
    print("🧪 TESTING EMPLOYEE PROJECTS QUERIES")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        employee_name = parse_employee_name_from_query(query)
        if employee_name:
            print(f"👤 Extracted name: {employee_name}")
            find_employee_projects(employee_name)
        else:
            print("❌ Could not extract employee name from query")
        
        print("\n" + "-"*50)

if __name__ == "__main__":
    # Test with Hamza specifically
    find_employee_projects("Hamza")