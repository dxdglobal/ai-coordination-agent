#!/usr/bin/env python3
"""
Task Monitor Diagnostics - Debug why comments aren't being added
"""

import mysql.connector
import sqlite3
import os
from datetime import datetime

def test_mysql_connection():
    """Test MySQL database connection and structure"""
    print("🔍 Testing MySQL Database Connection...")
    
    try:
        conn = mysql.connector.connect(
            host='92.113.22.65',
            user='u906714182_sqlrrefdvdv',
            password='3@6*t:lU',
            database='u906714182_sqlrrefdvdv'
        )
        cursor = conn.cursor()
        
        # Check if tbltasks exists
        cursor.execute("SHOW TABLES LIKE 'tbltasks'")
        if cursor.fetchone():
            print("  ✅ tbltasks table exists")
            
            # Check table structure
            cursor.execute("DESCRIBE tbltasks")
            columns = cursor.fetchall()
            print("  📋 Column structure:")
            for col in columns:
                print(f"     - {col[0]} ({col[1]})")
            
            # Try to get some tasks
            cursor.execute("SELECT id, name, duedate, status FROM tbltasks LIMIT 5")
            tasks = cursor.fetchall()
            print(f"  📊 Found {len(tasks)} tasks")
            
            for task in tasks:
                print(f"     Task: {task}")
                
        else:
            print("  ❌ tbltasks table not found")
            
        # Check for comments table
        cursor.execute("SHOW TABLES LIKE 'tbltask_comments'")
        if cursor.fetchone():
            print("  ✅ tbltask_comments table exists")
            cursor.execute("SELECT COUNT(*) FROM tbltask_comments")
            count = cursor.fetchone()[0]
            print(f"     Contains {count} comments")
        else:
            print("  ❌ tbltask_comments table not found")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ MySQL Error: {e}")
        return False

def test_sqlite_connection():
    """Test SQLite database connection"""
    print("\n🔍 Testing SQLite Database Connection...")
    
    db_path = 'project_management.db'
    if not os.path.exists(db_path):
        print("  ❌ SQLite database not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if task table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task'")
        if cursor.fetchone():
            print("  ✅ task table exists")
            
            # Get some tasks
            cursor.execute("SELECT id, title, status, end_time FROM task LIMIT 5")
            tasks = cursor.fetchall()
            print(f"  📊 Found {len(tasks)} tasks")
            
            for task in tasks:
                print(f"     Task: {task}")
        else:
            print("  ❌ task table not found")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ SQLite Error: {e}")
        return False

def test_monitor_process():
    """Check if the monitor process is actually running"""
    print("\n🔍 Testing Monitor Process...")
    
    log_file = 'human_like_monitor.log'
    if os.path.exists(log_file):
        print(f"  ✅ Monitor log file exists")
        
        # Read recent entries
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-20:] if len(lines) >= 20 else lines
            
        print("  📄 Recent log entries:")
        for line in recent_lines:
            if line.strip():
                print(f"     {line.strip()}")
    else:
        print("  ❌ No monitor log file found")

def manual_comment_test():
    """Try to manually add a comment to test the system"""
    print("\n🔍 Manual Comment Test...")
    
    try:
        conn = mysql.connector.connect(
            host='92.113.22.65',
            user='u906714182_sqlrrefdvdv',
            password='3@6*t:lU',
            database='u906714182_sqlrrefdvdv'
        )
        cursor = conn.cursor()
        
        # Try to add a test comment
        test_comment = f"🤖 Test comment from AI Agent - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Get first task to test with
        cursor.execute("SELECT id FROM tbltasks LIMIT 1")
        task_result = cursor.fetchone()
        
        if task_result:
            task_id = task_result[0]
            print(f"  📝 Attempting to add comment to task {task_id}")
            
            cursor.execute("""
                INSERT INTO tbltask_comments (taskid, staffid, dateadded, comment)
                VALUES (%s, %s, %s, %s)
            """, (task_id, 248, datetime.now(), test_comment))
            
            conn.commit()
            print("  ✅ Test comment added successfully!")
        else:
            print("  ❌ No tasks found to comment on")
            
        conn.close()
        
    except Exception as e:
        print(f"  ❌ Comment test failed: {e}")

def main():
    print("🤖 TASK MONITOR DIAGNOSTICS")
    print("=" * 50)
    
    mysql_ok = test_mysql_connection()
    sqlite_ok = test_sqlite_connection()
    test_monitor_process()
    
    if mysql_ok:
        manual_comment_test()
    
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSIS COMPLETE!")
    
    if mysql_ok or sqlite_ok:
        print("✅ Database connections work")
        print("💡 If no comments are appearing, the issue might be:")
        print("   1. Monitor is not running the scan loop")
        print("   2. Tasks don't meet commenting criteria")
        print("   3. 24-hour cooldown preventing comments")
        print("   4. Query issues in task fetching")
    else:
        print("❌ Database connection issues found")
        print("💡 Fix database connections first")

if __name__ == "__main__":
    main()