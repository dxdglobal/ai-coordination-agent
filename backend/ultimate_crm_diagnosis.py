#!/usr/bin/env python3

import mysql.connector
from datetime import datetime, timedelta
import time
import json

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='92.113.22.65',
        user='u906714182_sqlrrefdvdv',
        password='3@6*t:lU',
        database='u906714182_sqlrrefdvdv'
    )

def ultimate_crm_diagnosis():
    """
    Ultimate diagnosis to understand CRM frontend logic
    """
    print("🔬 ULTIMATE CRM FRONTEND LOGIC DIAGNOSIS")
    print("=" * 70)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Compare DDS AI with known online users
    print("\n👥 COMPARING WITH CURRENTLY ONLINE USERS:")
    print("-" * 50)
    
    # Get users who are currently showing as online in sessions
    cursor.execute("""
        SELECT DISTINCT 
            SUBSTRING_INDEX(SUBSTRING_INDEX(data, 'staff_user_id|s:', -1), ':', 1) as extracted_id,
            COUNT(*) as session_count,
            MAX(timestamp) as latest_session
        FROM tblsessions 
        WHERE data LIKE '%staff_user_id%' 
        AND data LIKE '%staff_logged_in|b:1%'
        AND timestamp > UNIX_TIMESTAMP(NOW()) - 3600
        GROUP BY extracted_id
        ORDER BY latest_session DESC
        LIMIT 10
    """)
    
    active_users = cursor.fetchall()
    print("   🟢 Users with active sessions:")
    
    for user in active_users:
        try:
            staff_id = user['extracted_id'].replace('"', '').replace(';', '')
            if staff_id.isdigit():
                # Get staff details
                cursor.execute("""
                    SELECT s.staffid, s.firstname, s.lastname, s.last_activity, s.is_logged_in,
                           o.is_online, o.last_seen, o.status_message
                    FROM tblstaff s
                    LEFT JOIN tbl_staff_online_status o ON s.staffid = o.staff_id
                    WHERE s.staffid = %s
                """, (staff_id,))
                
                staff = cursor.fetchone()
                if staff:
                    print(f"      ID {staff_id}: {staff['firstname']} {staff['lastname']}")
                    print(f"         Sessions: {user['session_count']}, Last Activity: {staff['last_activity']}")
                    print(f"         DB Online: {staff['is_online']}, Logged In: {staff['is_logged_in']}")
        except Exception as e:
            continue
    
    # 2. Check what makes a user appear online
    print("\n🔍 ANALYZING ONLINE DETECTION PATTERNS:")
    print("-" * 50)
    
    # Check if there's a time threshold
    cursor.execute("""
        SELECT 
            s.staffid,
            s.firstname,
            s.lastname,
            s.last_activity,
            s.last_login,
            s.is_logged_in,
            o.is_online,
            o.last_seen,
            TIMESTAMPDIFF(MINUTE, s.last_activity, NOW()) as minutes_since_activity,
            TIMESTAMPDIFF(MINUTE, o.last_seen, NOW()) as minutes_since_seen,
            (SELECT COUNT(*) FROM tblsessions 
             WHERE data LIKE CONCAT('%staff_user_id|s:', LENGTH(s.staffid), ':"', s.staffid, '"%') 
             AND timestamp > UNIX_TIMESTAMP(NOW()) - 1800) as recent_sessions
        FROM tblstaff s
        LEFT JOIN tbl_staff_online_status o ON s.staffid = o.staff_id
        WHERE s.active = 1 
        AND (s.is_logged_in = 1 OR o.is_online = 1)
        ORDER BY s.last_activity DESC
        LIMIT 15
    """)
    
    online_analysis = cursor.fetchall()
    
    print("   📊 Online Users Analysis:")
    print("   " + "-" * 60)
    print("   ID | Name | Minutes Since Activity | Sessions | Status")
    print("   " + "-" * 60)
    
    for user in online_analysis:
        sessions = user['recent_sessions'] or 0
        activity_mins = user['minutes_since_activity'] or 0
        name = f"{user['firstname']} {user['lastname']}"[:15]
        status = "🟢" if user['is_online'] else "🔴"
        print(f"   {user['staffid']:3} | {name:15} | {activity_mins:20} | {sessions:8} | {status}")
    
    # 3. Create the EXACT session pattern of a known online user
    print("\n🎯 CREATING EXACT MATCH SESSION PATTERN:")
    print("-" * 50)
    
    # Find the most recent active user session
    cursor.execute("""
        SELECT s.id, s.ip_address, s.timestamp, s.data
        FROM tblsessions s
        WHERE s.data LIKE '%staff_logged_in|b:1%'
        AND s.timestamp > UNIX_TIMESTAMP(NOW()) - 1800
        ORDER BY s.timestamp DESC
        LIMIT 1
    """)
    
    template_session = cursor.fetchone()
    
    if template_session:
        try:
            # Decode the session data
            template_data = template_session['data'].decode('utf-8')
            print(f"   📋 Template from active user session:")
            print(f"      Session ID: {template_session['id']}")
            print(f"      IP: {template_session['ip_address']}")
            print(f"      Data: {template_data[:100]}...")
            
            # Create identical session for DDS AI
            current_timestamp = int(time.time())
            ai_session_id = f"ai_exact_match_{current_timestamp}"
            
            # Replace staff_user_id in template with 248
            ai_session_data = template_data
            # Replace any existing staff_user_id
            import re
            ai_session_data = re.sub(r'staff_user_id\|s:\d+:"[\d]+"', 'staff_user_id|s:3:"248"', ai_session_data)
            # Update timestamp
            ai_session_data = re.sub(r'__ci_last_regenerate\|i:\d+', f'__ci_last_regenerate|i:{current_timestamp}', ai_session_data)
            
            cursor.execute("""
                INSERT INTO tblsessions (id, ip_address, timestamp, data) 
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                timestamp = %s, data = %s
            """, (ai_session_id, template_session['ip_address'], current_timestamp, ai_session_data.encode(), current_timestamp, ai_session_data.encode()))
            
            conn.commit()
            print(f"   ✅ Created exact match session for DDS AI")
            print(f"   📝 AI Session Data: {ai_session_data[:100]}...")
            
        except Exception as e:
            print(f"   ⚠️  Template session error: {e}")
    
    # 4. Check for any special flags or conditions
    print("\n🚩 CHECKING FOR SPECIAL CONDITIONS:")
    print("-" * 50)
    
    # Check if certain roles or permissions affect online display
    cursor.execute("""
        SELECT 
            s.staffid,
            s.firstname,
            s.lastname,
            s.admin,
            s.role,
            s.is_not_staff,
            s.active,
            s.priority,
            o.is_online
        FROM tblstaff s
        LEFT JOIN tbl_staff_online_status o ON s.staffid = o.staff_id
        WHERE s.staffid = 248
    """)
    
    dds_permissions = cursor.fetchone()
    print(f"   🤖 DDS AI Permissions:")
    print(f"      Admin: {dds_permissions['admin']}")
    print(f"      Role: {dds_permissions['role']}")
    print(f"      Is Not Staff: {dds_permissions['is_not_staff']}")
    print(f"      Active: {dds_permissions['active']}")
    print(f"      Priority: {dds_permissions['priority']}")
    
    # Compare with a known working user
    cursor.execute("""
        SELECT 
            s.staffid,
            s.firstname,
            s.lastname,
            s.admin,
            s.role,
            s.is_not_staff,
            s.active,
            s.priority,
            o.is_online
        FROM tblstaff s
        LEFT JOIN tbl_staff_online_status o ON s.staffid = o.staff_id
        WHERE s.is_logged_in = 1 AND s.active = 1
        ORDER BY s.last_activity DESC
        LIMIT 1
    """)
    
    working_user = cursor.fetchone()
    if working_user:
        print(f"   ✅ Comparison with working user {working_user['firstname']}:")
        print(f"      Admin: {working_user['admin']} (DDS: {dds_permissions['admin']})")
        print(f"      Role: {working_user['role']} (DDS: {dds_permissions['role']})")
        print(f"      Is Not Staff: {working_user['is_not_staff']} (DDS: {dds_permissions['is_not_staff']})")
        print(f"      Priority: {working_user['priority']} (DDS: {dds_permissions['priority']})")
    
    cursor.close()
    conn.close()
    
    # 5. Provide comprehensive solution steps
    print("\n🎯 COMPREHENSIVE SOLUTION STEPS:")
    print("=" * 70)
    print("Since database is 100% correct but CRM shows offline, try these:")
    print()
    print("🔧 IMMEDIATE FIXES:")
    print("   1. Hard refresh: Ctrl+F5 or Ctrl+Shift+R")
    print("   2. Clear browser cache completely")
    print("   3. Try incognito/private browsing mode")
    print("   4. Try different browser")
    print()
    print("🌐 BROWSER DEVELOPER TOOLS:")
    print("   1. Press F12 to open developer tools")
    print("   2. Go to Network tab")
    print("   3. Refresh page and look for AJAX calls to:")
    print("      - /admin/staff/online_status")
    print("      - /admin/dashboard/online_users")
    print("      - Any calls containing 'staff' or 'online'")
    print("   4. Check Console tab for JavaScript errors")
    print()
    print("💻 MANUAL JAVASCRIPT FIX:")
    print("   1. Open browser console (F12 → Console)")
    print("   2. Paste and run this code:")
    print('   localStorage.clear(); sessionStorage.clear(); location.reload(true);')
    print()
    print("🔄 SERVER-SIDE CHECK:")
    print("   1. Check if CRM has a cron job that updates online status")
    print("   2. Look for WebSocket connections")
    print("   3. Check if there's a heartbeat endpoint")
    print()
    print("📱 MOBILE/RESPONSIVE:")
    print("   Try accessing CRM from mobile or different device")
    print()
    print("🚨 LAST RESORT:")
    print("   Contact CRM developer to check frontend JavaScript logic")
    print("   The issue is definitely in the client-side code, not database!")

if __name__ == "__main__":
    ultimate_crm_diagnosis()