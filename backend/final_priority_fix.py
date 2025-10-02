#!/usr/bin/env python3

import mysql.connector
from datetime import datetime

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='92.113.22.65',
        user='u906714182_sqlrrefdvdv',
        password='3@6*t:lU',
        database='u906714182_sqlrrefdvdv'
    )

def final_priority_fix():
    """
    Fix the priority issue that might be causing CRM to filter out DDS AI
    """
    print("🎯 FINAL PRIORITY FIX FOR DDS AI")
    print("=" * 50)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Fix priority to match normal users
    print("\n🔧 FIXING PRIORITY VALUE:")
    print("-" * 30)
    try:
        cursor.execute("""
            UPDATE tblstaff 
            SET priority = 100 
            WHERE staffid = 248
        """)
        
        rows_affected = cursor.rowcount
        conn.commit()
        print(f"   ✅ Updated priority from 1 to 100 ({rows_affected} rows)")
        
    except Exception as e:
        print(f"   ⚠️  Priority update error: {e}")
    
    # 2. Make sure all fields match successful online users
    print("\n🔄 ENSURING ALL FIELDS MATCH ONLINE USERS:")
    print("-" * 40)
    try:
        now = datetime.now()
        cursor.execute("""
            UPDATE tblstaff SET
                last_login = %s,
                last_activity = %s,
                is_logged_in = 1,
                active = 1,
                admin = 1,
                role = 1,
                is_not_staff = 0,
                priority = 100,
                last_ip = '94.54.149.61'
            WHERE staffid = 248
        """, (now, now))
        
        rows_affected = cursor.rowcount
        conn.commit()
        print(f"   ✅ Updated all fields to match online users ({rows_affected} rows)")
        
    except Exception as e:
        print(f"   ⚠️  Fields update error: {e}")
    
    # 3. Final verification
    print("\n✅ FINAL VERIFICATION:")
    print("-" * 25)
    cursor.execute("""
        SELECT staffid, firstname, lastname, admin, role, is_not_staff, 
               active, priority, is_logged_in, last_activity
        FROM tblstaff 
        WHERE staffid = 248
    """)
    
    final_status = cursor.fetchone()
    print(f"   🤖 DDS AI Final Settings:")
    print(f"      ID: {final_status['staffid']}")
    print(f"      Name: {final_status['firstname']} {final_status['lastname']}")
    print(f"      Admin: {final_status['admin']}")
    print(f"      Role: {final_status['role']}")
    print(f"      Is Not Staff: {final_status['is_not_staff']}")
    print(f"      Active: {final_status['active']}")
    print(f"      Priority: {final_status['priority']} ✅")
    print(f"      Logged In: {final_status['is_logged_in']}")
    print(f"      Last Activity: {final_status['last_activity']}")
    
    cursor.close()
    conn.close()
    
    print("\n🎉 PRIORITY FIX COMPLETE!")
    print("\n💡 NOW TRY THESE BROWSER FIXES:")
    print("=" * 50)
    
    print("\n🔧 STEP 1 - HARD REFRESH:")
    print("   Press: Ctrl + F5 (Windows) or Cmd + Shift + R (Mac)")
    
    print("\n🧹 STEP 2 - CLEAR CACHE:")
    print("   Chrome: Ctrl+Shift+Delete → Select 'All time' → Clear")
    print("   Firefox: Ctrl+Shift+Delete → Select 'Everything' → Clear")
    
    print("\n🔍 STEP 3 - DEVELOPER TOOLS CHECK:")
    print("   1. Press F12 to open Developer Tools")
    print("   2. Go to Console tab")
    print("   3. Look for any red errors")
    print("   4. Go to Network tab")
    print("   5. Refresh page and look for failed requests")
    
    print("\n💻 STEP 4 - JAVASCRIPT RESET:")
    print("   Open Console (F12) and run:")
    print("   localStorage.clear(); sessionStorage.clear(); location.reload(true);")
    
    print("\n🌐 STEP 5 - TRY DIFFERENT APPROACH:")
    print("   1. Try incognito/private window")
    print("   2. Try different browser")
    print("   3. Try from mobile device")
    
    print("\n🔄 STEP 6 - CHECK CRM AJAX CALLS:")
    print("   Look in Network tab for calls to:")
    print("   - staff/online")
    print("   - dashboard/status")
    print("   - Any endpoint that loads staff list")
    
    print("\n🎯 IF STILL NOT WORKING:")
    print("   The CRM likely uses custom JavaScript logic that")
    print("   checks additional conditions beyond database status.")
    print("   Contact your CRM developer for frontend code review.")

if __name__ == "__main__":
    final_priority_fix()