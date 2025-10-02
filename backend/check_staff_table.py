#!/usr/bin/env python3
"""
Check tblstaff table structure to find correct AI agent
"""

import mysql.connector

db_config = {
    'host': '92.113.22.65',
    'user': 'u906714182_sqlrrefdvdv',
    'password': '3@6*t:lU',
    'database': 'u906714182_sqlrrefdvdv'
}

def check_staff_table():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        print("🔍 CHECKING TBLSTAFF TABLE STRUCTURE...")
        cursor.execute("DESCRIBE tblstaff")
        columns = cursor.fetchall()
        
        print("📋 Table columns:")
        for col in columns:
            print(f"   {col['Field']} ({col['Type']})")
        
        print("\n🔍 LOOKING for AI AGENT...")
        # Try different possible column names for ID
        cursor.execute("SELECT * FROM tblstaff WHERE staffid = 248")
        agent = cursor.fetchone()
        
        if agent:
            print(f"✅ AI Agent found with staffid = 248:")
            for key, value in agent.items():
                print(f"   {key}: {value}")
        else:
            print("❌ AI Agent not found with staffid = 248")
            print("🔍 Let's see all staff with 'AI' or 'COORDINATION':")
            cursor.execute("""
                SELECT * FROM tblstaff 
                WHERE firstname LIKE '%AI%' 
                   OR firstname LIKE '%COORDINATION%'
                   OR lastname LIKE '%AI%'
                   OR lastname LIKE '%COORDINATION%'
                LIMIT 5
            """)
            ai_staff = cursor.fetchall()
            for staff in ai_staff:
                print(f"   Staff {staff.get('staffid', 'unknown')}: {staff.get('firstname', '')} {staff.get('lastname', '')}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_staff_table()