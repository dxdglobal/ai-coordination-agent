#!/usr/bin/env python3
"""
Database Inspector - Check what the task monitor is actually scanning
"""

import sqlite3
import os
from datetime import datetime

def inspect_database():
    """Inspect the local SQLite database"""
    db_path = 'project_management.db'
    
    if not os.path.exists(db_path):
        print("❌ No local database found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("🔍 DATABASE INSPECTION REPORT")
        print("=" * 40)
        print(f"📋 Available tables: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            print(f"\n📊 Table: {table_name}")
            
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print("   Columns:")
            for col in columns:
                print(f"     - {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📝 Rows: {count}")
            
            # If it's the task table, show some data
            if 'task' in table_name.lower():
                print("   Sample data:")
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                for row in rows:
                    print(f"     {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def check_monitor_status():
    """Check if the task monitor is running and what it's doing"""
    log_file = 'human_like_monitor.log'
    
    print(f"\n🔍 TASK MONITOR STATUS")
    print("=" * 40)
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-10:] if len(lines) >= 10 else lines
            
            print("📄 Recent monitor activity:")
            for line in recent_lines:
                print(f"   {line.strip()}")
    else:
        print("❌ No monitor log file found")

def main():
    print("🤖 AI COORDINATION AGENT - DATABASE & MONITOR INSPECTOR")
    print("=" * 60)
    
    inspect_database()
    check_monitor_status()
    
    print("\n" + "=" * 60)
    print("✨ Inspection complete!")

if __name__ == "__main__":
    main()