#!/usr/bin/env python3
"""
Database Connection Verification
===============================
Test script to verify we're connecting to the correct CRM database
and can access real task data.
"""

import mysql.connector
from datetime import datetime

# Database configuration (same as monitor)
db_config = {
    'host': '92.113.22.65',
    'user': 'u906714182_sqlrrefdvdv',
    'password': '3@6*t:lU',
    'database': 'u906714182_sqlrrefdvdv'
}

def test_database_connection():
    """Test database connection and show basic stats"""
    try:
        print("🔍 TESTING DATABASE CONNECTION")
        print("=" * 50)
        print(f"📡 Connecting to: {db_config['host']}")
        print(f"🗄️  Database: {db_config['database']}")
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        print("✅ Database connection successful!")
        
        # Test 1: Check if tables exist
        print("\n📋 CHECKING TABLES...")
        cursor.execute("SHOW TABLES LIKE 'tbltasks'")
        if cursor.fetchone():
            print("✅ tbltasks table found")
        else:
            print("❌ tbltasks table NOT found")
            
        cursor.execute("SHOW TABLES LIKE 'tbltask_comments'")
        if cursor.fetchone():
            print("✅ tbltask_comments table found")
        else:
            print("❌ tbltask_comments table NOT found")
            
        cursor.execute("SHOW TABLES LIKE 'tblstaff'")
        if cursor.fetchone():
            print("✅ tblstaff table found")
        else:
            print("❌ tblstaff table NOT found")
        
        # Test 2: Count total tasks
        print("\n📊 TASK STATISTICS...")
        cursor.execute("SELECT COUNT(*) as total_tasks FROM tbltasks")
        result = cursor.fetchone()
        print(f"📝 Total tasks in database: {result['total_tasks']}")
        
        # Test 3: Count tasks by status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM tbltasks 
            GROUP BY status 
            ORDER BY status
        """)
        statuses = cursor.fetchall()
        print("\n📋 Tasks by status:")
        for status in statuses:
            print(f"   Status {status['status']}: {status['count']} tasks")
        
        # Test 4: Get recent tasks
        print("\n🕐 RECENT TASKS (Last 10)...")
        cursor.execute("""
            SELECT id, name, duedate, status, dateadded
            FROM tbltasks 
            ORDER BY id DESC 
            LIMIT 10
        """)
        recent_tasks = cursor.fetchall()
        for task in recent_tasks:
            due_str = task['duedate'].strftime('%Y-%m-%d') if task['duedate'] else 'No due date'
            print(f"   Task {task['id']}: {task['name'][:40]}... (Due: {due_str}, Status: {task['status']})")
        
        # Test 5: Check task assignments
        print("\n👥 TASK ASSIGNMENTS...")
        cursor.execute("SELECT COUNT(*) as assigned_count FROM tbltask_assigned")
        result = cursor.fetchone()
        print(f"📌 Total task assignments: {result['assigned_count']}")
        
        # Test 6: Check comments
        print("\n💬 TASK COMMENTS...")
        cursor.execute("SELECT COUNT(*) as comment_count FROM tbltask_comments")
        result = cursor.fetchone()
        print(f"💭 Total comments: {result['comment_count']}")
        
        # Test 7: Check our AI agent
        cursor.execute("SELECT * FROM tblstaff WHERE id = 248")
        agent = cursor.fetchone()
        if agent:
            print(f"\n🤖 AI AGENT FOUND:")
            print(f"   ID: {agent['id']}")
            print(f"   Name: {agent['firstname']} {agent['lastname']}")
        else:
            print("\n❌ AI Agent (ID 248) not found in tblstaff")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Database verification complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()