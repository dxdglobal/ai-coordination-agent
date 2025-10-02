#!/usr/bin/env python3
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def analyze_projects():
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        cursor = conn.cursor()
        
        # First, let's see the table structure
        print("🔍 Table structure for tblprojects:")
        cursor.execute("DESCRIBE tblprojects")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        
        print("\n" + "="*50)
        
        # Check different filtering scenarios
        print("\n📊 Project filtering analysis:")
        
        # Total projects
        cursor.execute("SELECT COUNT(*) FROM tblprojects")
        total = cursor.fetchone()[0]
        print(f"  Total projects: {total}")
        
        # Check if there's a status field and filter by active/open status
        cursor.execute("SELECT DISTINCT status FROM tblprojects")
        statuses = cursor.fetchall()
        print(f"  Available statuses: {[s[0] for s in statuses]}")
        
        # Count by status
        for status in statuses:
            cursor.execute(f"SELECT COUNT(*) FROM tblprojects WHERE status = %s", (status[0],))
            count = cursor.fetchone()[0]
            print(f"    - Status '{status[0]}': {count} projects")
        
        # Check for date-based filtering (recent projects)
        print(f"\n📅 Date-based analysis:")
        cursor.execute("SELECT COUNT(*) FROM tblprojects WHERE date_created >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
        recent_30 = cursor.fetchone()[0]
        print(f"  Projects created in last 30 days: {recent_30}")
        
        cursor.execute("SELECT COUNT(*) FROM tblprojects WHERE date_created >= DATE_SUB(NOW(), INTERVAL 90 DAY)")
        recent_90 = cursor.fetchone()[0]
        print(f"  Projects created in last 90 days: {recent_90}")
        
        # Check if there are exactly 18 active projects
        cursor.execute("SELECT COUNT(*) FROM tblprojects WHERE status IN ('1', 'active', 'open', 'in_progress')")
        active_count = cursor.fetchone()[0]
        print(f"  Active/Open projects (common statuses): {active_count}")
        
        # Show first 20 projects with their status and dates
        print(f"\n📋 First 20 projects with details:")
        cursor.execute("""
            SELECT id, name, status, date_created, date_finished 
            FROM tblprojects 
            ORDER BY id DESC 
            LIMIT 20
        """)
        projects = cursor.fetchall()
        
        for i, (pid, name, status, created, finished) in enumerate(projects, 1):
            name_short = (name[:50] + '...') if len(name) > 50 else name
            print(f"  {i:2}. ID:{pid:3} | Status:{status:1} | {name_short}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    analyze_projects()