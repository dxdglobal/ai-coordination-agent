#!/usr/bin/env python3
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def find_hamza_projects():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        cursor = conn.cursor()
        
        print('🔍 Finding Hamza-related projects:')
        
        # First, let's find Hamza in the staff table
        cursor.execute("SELECT id, firstname, lastname, email FROM tblstaff WHERE firstname LIKE %s OR lastname LIKE %s OR email LIKE %s", ('%hamza%', '%hamza%', '%hamza%'))
        hamza_staff = cursor.fetchall()
        
        if hamza_staff:
            print('📋 Found Hamza in staff:')
            for staff in hamza_staff:
                print(f'  Staff ID: {staff[0]}, Name: {staff[1]} {staff[2]}, Email: {staff[3]}')
                hamza_id = staff[0]
                
                # Find projects where Hamza is a member
                cursor.execute("""
                    SELECT DISTINCT p.id, p.name, p.status, p.project_created
                    FROM tblprojects p
                    JOIN tblproject_members pm ON p.id = pm.project_id  
                    WHERE pm.staff_id = %s
                    ORDER BY p.project_created DESC
                    LIMIT 25
                """, (hamza_id,))
                
                projects = cursor.fetchall()
                print(f'\n📊 Projects assigned to {staff[1]} ({len(projects)} found):')
                for i, (pid, name, status, created) in enumerate(projects, 1):
                    name_short = (name[:50] + '...') if len(name) > 50 else name
                    print(f'  {i:2}. ID:{pid:3} | Status:{status} | {created} | {name_short}')
                    
                # Count active projects (status 2)
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM tblprojects p
                    JOIN tblproject_members pm ON p.id = pm.project_id  
                    WHERE pm.staff_id = %s AND p.status = 2
                """, (hamza_id,))
                active_count = cursor.fetchone()[0]
                print(f'\n🎯 Active projects (Status 2) for {staff[1]}: {active_count}')
        else:
            # Search in project names and descriptions for Hamza
            print('🔍 No staff named Hamza found. Searching project names and descriptions...')
            cursor.execute("""
                SELECT id, name, status, project_created 
                FROM tblprojects 
                WHERE name LIKE %s OR description LIKE %s
                ORDER BY project_created DESC
                LIMIT 20
            """, ('%hamza%', '%hamza%'))
            projects = cursor.fetchall()
            print(f'Found {len(projects)} projects mentioning Hamza:')
            for i, (pid, name, status, created) in enumerate(projects, 1):
                name_short = (name[:50] + '...') if len(name) > 50 else name
                print(f'  {i:2}. ID:{pid:3} | Status:{status} | {created} | {name_short}')
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_hamza_projects()