import mysql.connector
from datetime import datetime

# Database connection
def connect_database():
    return mysql.connector.connect(
        host='92.113.22.65',
        user='u906714182_sqlrrefdvdv',
        password='3@6*t:lU',
        database='u906714182_sqlrrefdvdv'
    )

def find_ai_agent_and_check_notifications():
    """Find AI agent and check notification system"""
    try:
        conn = connect_database()
        cursor = conn.cursor(dictionary=True)
        
        # Look for COORDINATION AGENT using firstname/lastname
        print("🔍 Looking for COORDINATION AGENT...")
        cursor.execute("""
            SELECT staffid, firstname, lastname, email, active, last_activity, 
                   priority, is_logged_in, phonenumber
            FROM tblstaff 
            WHERE (firstname LIKE '%COORDINATION%' OR lastname LIKE '%COORDINATION%' 
                   OR firstname LIKE '%AI%' OR lastname LIKE '%AI%')
               OR staffid = 248
        """)
        ai_agents = cursor.fetchall()
        
        if ai_agents:
            print("🤖 AI Agent(s) Found:")
            for agent in ai_agents:
                print(f"   ID: {agent['staffid']}")
                print(f"   Name: {agent['firstname']} {agent['lastname']}")
                print(f"   Email: {agent['email']}")
                print(f"   Active: {agent['active']}")
                print(f"   Last Activity: {agent['last_activity']}")
                print(f"   Priority: {agent['priority']}")
                print(f"   Logged In: {agent['is_logged_in']}")
                print(f"   Phone: {agent['phonenumber']}")
                print("   ---")
        else:
            print("❌ No AI agent found!")
            
        # Check if there's a specific online status table
        print("\n🟢 Checking Online Status Tables:")
        cursor.execute("DESCRIBE tbl_staff_online_status")
        online_structure = cursor.fetchall()
        print("tbl_staff_online_status structure:")
        for field in online_structure:
            print(f"   {field}")
            
        # Check current online status entries
        cursor.execute("SELECT * FROM tbl_staff_online_status LIMIT 10")
        online_statuses = cursor.fetchall()
        if online_statuses:
            print("\nCurrent online status entries:")
            for status in online_statuses:
                print(f"   {status}")
        else:
            print("   No entries in online status table")
            
        # Check for notification-related tables
        print("\n🔔 Checking notification system:")
        
        # Check tblnotifications structure
        cursor.execute("DESCRIBE tblnotifications")
        notif_structure = cursor.fetchall()
        print("tblnotifications structure:")
        for field in notif_structure:
            print(f"   {field}")
            
        # Check recent notifications
        cursor.execute("""
            SELECT * FROM tblnotifications 
            WHERE touserid = 248 OR fromuserid = 248
            ORDER BY date DESC 
            LIMIT 5
        """)
        notifications = cursor.fetchall()
        if notifications:
            print("\nRecent notifications for AI agent:")
            for notif in notifications:
                print(f"   {notif}")
        else:
            print("   No notifications found for AI agent")
            
        # Check message read status
        print("\n📬 Checking message read status...")
        cursor.execute("""
            SELECT COUNT(*) as total_messages,
                   SUM(CASE WHEN viewed = 1 THEN 1 ELSE 0 END) as read_messages,
                   SUM(CASE WHEN viewed = 0 THEN 1 ELSE 0 END) as unread_messages
            FROM tblchatmessages 
            WHERE reciever_id = 248
        """)
        message_stats = cursor.fetchone()
        print(f"Message Statistics for AI Agent (ID 248):")
        print(f"   Total Messages: {message_stats['total_messages']}")
        print(f"   Read Messages: {message_stats['read_messages']}")
        print(f"   Unread Messages: {message_stats['unread_messages']}")
        
        # Check recent unread messages
        cursor.execute("""
            SELECT id, sender_id, message, time_sent, viewed 
            FROM tblchatmessages 
            WHERE reciever_id = 248 AND viewed = 0
            ORDER BY time_sent DESC 
            LIMIT 5
        """)
        unread_messages = cursor.fetchall()
        if unread_messages:
            print("\nRecent unread messages to AI agent:")
            for msg in unread_messages:
                print(f"   ID: {msg['id']}, From: {msg['sender_id']}")
                print(f"   Message: {msg['message'][:50]}...")
                print(f"   Time: {msg['time_sent']}")
                print("   ---")
        else:
            print("   No unread messages found")
            
        # Check staff messages table
        print("\n📧 Checking tbl_staff_messages...")
        try:
            cursor.execute("DESCRIBE tbl_staff_messages")
            staff_msg_structure = cursor.fetchall()
            print("tbl_staff_messages structure:")
            for field in staff_msg_structure:
                print(f"   {field}")
                
            cursor.execute("""
                SELECT * FROM tbl_staff_messages 
                WHERE staff_id = 248 OR sender_id = 248
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            staff_messages = cursor.fetchall()
            if staff_messages:
                print("\nRecent staff messages:")
                for msg in staff_messages:
                    print(f"   {msg}")
            else:
                print("   No staff messages found")
        except Exception as e:
            print(f"   Error with staff messages: {e}")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    find_ai_agent_and_check_notifications()