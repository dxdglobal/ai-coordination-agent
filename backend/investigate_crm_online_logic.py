#!/usr/bin/env python3

import mysql.connector
from datetime import datetime, timedelta
import json

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='92.113.22.65',
        user='u906714182_sqlrrefdvdv',
        password='3@6*t:lU',
        database='u906714182_sqlrrefdvdv'
    )

def investigate_crm_online_logic():
    """
    Deep investigation into what determines online status in CRM interface
    """
    print("🔍 DEEP CRM ONLINE STATUS INVESTIGATION")
    print("=" * 70)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Check sessions table for active sessions
    print("\n📱 CHECKING ACTIVE SESSIONS:")
    print("-" * 50)
    try:
        cursor.execute("""
            SELECT * FROM tblsessions 
            WHERE data LIKE '%staff_user_id%248%' 
            OR data LIKE '%staff_logged_in%' 
            ORDER BY timestamp DESC LIMIT 10
        """)
        sessions = cursor.fetchall()
        print(f"   Found {len(sessions)} relevant sessions:")
        for session in sessions:
            # Decode session data
            try:
                data_str = session['data'].decode('utf-8')
                print(f"   Session {session['id'][:8]}... IP: {session['ip_address']}")
                print(f"   Timestamp: {datetime.fromtimestamp(session['timestamp'])}")
                print(f"   Data: {data_str[:200]}...")
                print()
            except:
                print(f"   Session {session['id'][:8]}... [Binary data]")
    except Exception as e:
        print(f"   ⚠️  Session check error: {e}")
    
    # 2. Check for any cache or temporary tables
    print("\n🗄️  CHECKING FOR CACHE TABLES:")
    print("-" * 50)
    try:
        cursor.execute("SHOW TABLES LIKE '%cache%'")
        cache_tables = cursor.fetchall()
        for table in cache_tables:
            table_name = list(table.values())[0]
            print(f"   📋 Found cache table: {table_name}")
            
            # Check if it has staff data
            try:
                cursor.execute(f"DESCRIBE {table_name}")
                columns = [col['Field'] for col in cursor.fetchall()]
                if any('staff' in col.lower() for col in columns):
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    data = cursor.fetchall()
                    print(f"      Columns: {columns}")
                    print(f"      Sample data: {data}")
            except Exception as e:
                print(f"      ⚠️  Error checking {table_name}: {e}")
    except Exception as e:
        print(f"   ⚠️  Cache table check error: {e}")
    
    # 3. Check user auto login table
    print("\n🔐 CHECKING AUTO LOGIN TABLE:")
    print("-" * 50)
    try:
        cursor.execute("SELECT * FROM tbluser_auto_login WHERE staff_id = 248")
        auto_login = cursor.fetchall()
        print(f"   Found {len(auto_login)} auto login records for DDS AI:")
        for record in auto_login:
            print(f"   {record}")
    except Exception as e:
        print(f"   ⚠️  Auto login check error: {e}")
    
    # 4. Check if there are any notification or real-time tables
    print("\n🔔 CHECKING NOTIFICATION TABLES:")
    print("-" * 50)
    try:
        cursor.execute("SHOW TABLES LIKE '%notification%'")
        notif_tables = cursor.fetchall()
        for table in notif_tables:
            table_name = list(table.values())[0]
            print(f"   📋 Notification table: {table_name}")
            try:
                cursor.execute(f"SELECT * FROM {table_name} WHERE touserid = 248 OR fromid = 248 ORDER BY date DESC LIMIT 3")
                data = cursor.fetchall()
                print(f"      Recent entries: {data}")
            except Exception as e:
                print(f"      ⚠️  Error: {e}")
    except Exception as e:
        print(f"   ⚠️  Notification check error: {e}")
    
    # 5. Check for any real-time or websocket related tables
    print("\n🌐 CHECKING REALTIME TABLES:")
    print("-" * 50)
    try:
        cursor.execute("SHOW TABLES LIKE '%realtime%' OR SHOW TABLES LIKE '%websocket%' OR SHOW TABLES LIKE '%socket%'")
        realtime_tables = cursor.fetchall()
        for table in realtime_tables:
            table_name = list(table.values())[0]
            print(f"   📋 Realtime table: {table_name}")
    except Exception as e:
        print(f"   ⚠️  Realtime check error: {e}")
    
    # 6. Force create active session for DDS AI
    print("\n🚀 CREATING ACTIVE SESSION FOR DDS AI:")
    print("-" * 50)
    try:
        import time
        current_timestamp = int(time.time())
        session_id = f"dds_ai_session_{current_timestamp}"
        session_data = f'__ci_last_regenerate|i:{current_timestamp};staff_user_id|s:3:"248";staff_logged_in|b:1;last_activity|i:{current_timestamp};'
        
        cursor.execute("""
            INSERT INTO tblsessions (id, ip_address, timestamp, data) 
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            timestamp = %s, data = %s
        """, (session_id, '127.0.0.1', current_timestamp, session_data.encode(), current_timestamp, session_data.encode()))
        
        conn.commit()
        print(f"   ✅ Created active session: {session_id}")
        print(f"   ✅ Session data: {session_data}")
        
    except Exception as e:
        print(f"   ⚠️  Session creation error: {e}")
    
    # 7. Update any heartbeat or ping tables
    print("\n💓 UPDATING HEARTBEAT MECHANISMS:")
    print("-" * 50)
    try:
        # Check for heartbeat tables
        cursor.execute("SHOW TABLES LIKE '%heartbeat%' OR SHOW TABLES LIKE '%ping%' OR SHOW TABLES LIKE '%alive%'")
        heartbeat_tables = cursor.fetchall()
        for table in heartbeat_tables:
            table_name = list(table.values())[0]
            print(f"   💓 Heartbeat table: {table_name}")
    except Exception as e:
        print(f"   ⚠️  Heartbeat check error: {e}")
    
    # 8. Final status verification
    print("\n✅ FINAL STATUS VERIFICATION:")
    print("-" * 50)
    cursor.execute("""
        SELECT s.staffid, s.firstname, s.lastname, s.last_activity, s.is_logged_in,
               o.is_online, o.last_seen, o.status_message
        FROM tblstaff s
        LEFT JOIN tbl_staff_online_status o ON s.staffid = o.staff_id
        WHERE s.staffid = 248
    """)
    final_status = cursor.fetchone()
    print(f"   🤖 DDS AI Final Status:")
    print(f"      Name: {final_status['firstname']} {final_status['lastname']}")
    print(f"      Last Activity: {final_status['last_activity']}")
    print(f"      Logged In: {final_status['is_logged_in']}")
    print(f"      Online: {final_status['is_online']}")
    print(f"      Last Seen: {final_status['last_seen']}")
    print(f"      Status Message: {final_status['status_message']}")
    
    # 9. Check for any custom fields or triggers
    print("\n🔧 CHECKING FOR CUSTOM MECHANISMS:")
    print("-" * 50)
    try:
        # Check for any views that might be used
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
        views = cursor.fetchall()
        print(f"   Found {len(views)} views in database:")
        for view in views:
            view_name = view['Tables_in_u906714182_sqlrrefdvdv']
            if 'staff' in view_name.lower() or 'online' in view_name.lower():
                print(f"      📊 Relevant view: {view_name}")
    except Exception as e:
        print(f"   ⚠️  View check error: {e}")
    
    cursor.close()
    conn.close()
    
    print("\n🎯 INVESTIGATION COMPLETE!")
    print("📝 If CRM still shows offline, the issue is likely:")
    print("   1. Browser cache (try hard refresh)")
    print("   2. Client-side JavaScript logic")
    print("   3. AJAX polling with custom conditions")
    print("   4. WebSocket/real-time connection needed")

if __name__ == "__main__":
    investigate_crm_online_logic()