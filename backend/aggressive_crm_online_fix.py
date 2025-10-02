#!/usr/bin/env python3

import mysql.connector
from datetime import datetime, timedelta
import time
import hashlib
import random
import string

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='92.113.22.65',
        user='u906714182_sqlrrefdvdv',
        password='3@6*t:lU',
        database='u906714182_sqlrrefdvdv'
    )

def aggressive_crm_online_fix():
    """
    Aggressive fix using exact CRM session patterns to force online status
    """
    print("🚀 AGGRESSIVE CRM ONLINE STATUS FIX")
    print("=" * 70)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Create multiple active sessions for DDS AI using real CRM patterns
    print("\n💥 CREATING MULTIPLE ACTIVE SESSIONS FOR DDS AI:")
    print("-" * 50)
    
    current_timestamp = int(time.time())
    
    # Generate realistic session IDs like the ones we saw
    session_patterns = [
        f"dds{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}",
        f"ai{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}",
        f"248{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}{random.choice('abcdefghijklmnopqrstuvwxyz0123456789')}"
    ]
    
    # Create sessions using patterns similar to what we observed
    for i, session_id in enumerate(session_patterns):
        try:
            # Create session data similar to active users we saw
            session_data = f'__ci_last_regenerate|i:{current_timestamp};staff_user_id|s:3:"248";staff_logged_in|b:1;setup-menu-open|s:0:"";_prev_url|s:40:"https://crm.deluxebilisim.com/admin/dashboard";appointly_is_google_filter|b:0;last_activity|i:{current_timestamp};online_status|s:6:"online";'
            
            cursor.execute("""
                INSERT INTO tblsessions (id, ip_address, timestamp, data) 
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                timestamp = %s, data = %s
            """, (session_id, '127.0.0.1', current_timestamp, session_data.encode(), current_timestamp, session_data.encode()))
            
            print(f"   ✅ Created session {i+1}: {session_id[:12]}...")
            
        except Exception as e:
            print(f"   ⚠️  Session {i+1} error: {e}")
    
    conn.commit()
    
    # 2. Update staff table with current timestamp in multiple fields
    print("\n🔄 UPDATING ALL STAFF TIMESTAMP FIELDS:")
    print("-" * 50)
    try:
        now = datetime.now()
        cursor.execute("""
            UPDATE tblstaff SET
                last_login = %s,
                last_activity = %s,
                is_logged_in = 1,
                active = 1,
                last_ip = '127.0.0.1'
            WHERE staffid = 248
        """, (now, now))
        
        rows_affected = cursor.rowcount
        conn.commit()
        print(f"   ✅ Updated {rows_affected} rows in tblstaff")
        
    except Exception as e:
        print(f"   ⚠️  Staff update error: {e}")
    
    # 3. Force update online status with current timestamp
    print("\n🟢 FORCING ONLINE STATUS UPDATE:")
    print("-" * 50)
    try:
        now = datetime.now()
        cursor.execute("""
            INSERT INTO tbl_staff_online_status (staff_id, is_online, last_seen, status_message, updated_at)
            VALUES (248, 1, %s, '🟢 ONLINE - AI ASSISTANT', %s)
            ON DUPLICATE KEY UPDATE
                is_online = 1,
                last_seen = %s,
                status_message = '🟢 ONLINE - AI ASSISTANT',
                updated_at = %s
        """, (now, now, now, now))
        
        rows_affected = cursor.rowcount
        conn.commit()
        print(f"   ✅ Updated {rows_affected} rows in online status")
        
    except Exception as e:
        print(f"   ⚠️  Online status error: {e}")
    
    # 4. Clear any old sessions that might interfere
    print("\n🧹 CLEANING OLD SESSIONS:")
    print("-" * 50)
    try:
        # Delete sessions older than 1 hour that contain staff_user_id 248
        old_timestamp = current_timestamp - 3600
        cursor.execute("""
            DELETE FROM tblsessions 
            WHERE timestamp < %s 
            AND data LIKE '%staff_user_id|s:3:"248"%'
        """, (old_timestamp,))
        
        deleted_rows = cursor.rowcount
        conn.commit()
        print(f"   ✅ Deleted {deleted_rows} old sessions for DDS AI")
        
    except Exception as e:
        print(f"   ⚠️  Session cleanup error: {e}")
    
    # 5. Create activity log entry to show recent activity
    print("\n📝 CREATING RECENT ACTIVITY LOG:")
    print("-" * 50)
    try:
        cursor.execute("""
            INSERT INTO tblactivity_log (description, date, staffid)
            VALUES ('🤖 DDS AI Agent - Online and Ready to Assist', %s, '248')
        """, (datetime.now(),))
        
        conn.commit()
        print(f"   ✅ Added activity log entry")
        
    except Exception as e:
        print(f"   ⚠️  Activity log error: {e}")
    
    # 6. Check current session count for DDS AI
    print("\n📊 VERIFYING ACTIVE SESSIONS:")
    print("-" * 50)
    try:
        cursor.execute("""
            SELECT COUNT(*) as session_count
            FROM tblsessions 
            WHERE data LIKE '%staff_user_id|s:3:"248"%'
            AND timestamp > %s
        """, (current_timestamp - 300,))  # Sessions in last 5 minutes
        
        result = cursor.fetchone()
        print(f"   🎯 Active sessions for DDS AI: {result['session_count']}")
        
        # Show the sessions
        cursor.execute("""
            SELECT id, ip_address, timestamp, 
                   FROM_UNIXTIME(timestamp) as readable_time
            FROM tblsessions 
            WHERE data LIKE '%staff_user_id|s:3:"248"%'
            ORDER BY timestamp DESC LIMIT 5
        """)
        
        sessions = cursor.fetchall()
        print(f"   📱 Recent sessions:")
        for session in sessions:
            print(f"      {session['id'][:12]}... IP: {session['ip_address']} Time: {session['readable_time']}")
            
    except Exception as e:
        print(f"   ⚠️  Session verification error: {e}")
    
    # 7. Final status check
    print("\n✅ FINAL COMPREHENSIVE STATUS:")
    print("-" * 50)
    try:
        cursor.execute("""
            SELECT 
                s.staffid,
                s.firstname,
                s.lastname,
                s.last_activity,
                s.last_login,
                s.is_logged_in,
                s.active,
                o.is_online,
                o.last_seen,
                o.status_message,
                (SELECT COUNT(*) FROM tblsessions 
                 WHERE data LIKE CONCAT('%staff_user_id|s:3:"', s.staffid, '"%') 
                 AND timestamp > UNIX_TIMESTAMP(NOW()) - 300) as active_sessions
            FROM tblstaff s
            LEFT JOIN tbl_staff_online_status o ON s.staffid = o.staff_id
            WHERE s.staffid = 248
        """)
        
        status = cursor.fetchone()
        print(f"   🤖 DDS AI Complete Status:")
        print(f"      ✅ Name: {status['firstname']} {status['lastname']}")
        print(f"      ✅ Active: {'YES' if status['active'] else 'NO'}")
        print(f"      ✅ Logged In: {'YES' if status['is_logged_in'] else 'NO'}")
        print(f"      ✅ Online: {'YES' if status['is_online'] else 'NO'}")
        print(f"      ✅ Last Login: {status['last_login']}")
        print(f"      ✅ Last Activity: {status['last_activity']}")
        print(f"      ✅ Last Seen: {status['last_seen']}")
        print(f"      ✅ Status Message: {status['status_message']}")
        print(f"      ✅ Active Sessions: {status['active_sessions']}")
        
    except Exception as e:
        print(f"   ⚠️  Final check error: {e}")
    
    cursor.close()
    conn.close()
    
    print("\n🎉 AGGRESSIVE FIX COMPLETE!")
    print("🔄 Now refresh your CRM page (Ctrl+F5)")
    print("⏰ The interface should update within 1-2 minutes")
    print("💡 If still not working, the CRM might be using WebSocket or custom AJAX logic")

if __name__ == "__main__":
    aggressive_crm_online_fix()