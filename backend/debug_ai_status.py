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

def check_ai_agent_status():
    """Check current status of AI agent in database"""
    try:
        conn = connect_database()
        cursor = conn.cursor(dictionary=True)
        
        # Get AI agent details
        print("🔍 Checking AI Agent Status...")
        cursor.execute("""
            SELECT id, name, email, role, status, online_status, priority, 
                   last_activity, created_at, updated_at
            FROM tblstaff 
            WHERE id = 248 OR name LIKE '%COORDINATION%'
        """)
        ai_agent = cursor.fetchall()
        
        if ai_agent:
            for agent in ai_agent:
                print(f"\n📋 AI Agent Details:")
                for key, value in agent.items():
                    print(f"   {key}: {value}")
        else:
            print("❌ AI Agent not found in database!")
            
        # Check recent messages to/from AI agent
        print("\n💬 Recent Messages involving AI Agent:")
        cursor.execute("""
            SELECT id, sender_id, reciever_id, message, timestamp, status, read_status
            FROM tblchatmessages 
            WHERE sender_id = 248 OR reciever_id = 248
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        messages = cursor.fetchall()
        
        if messages:
            for msg in messages:
                print(f"   ID: {msg['id']}, From: {msg['sender_id']}, To: {msg['reciever_id']}")
                print(f"   Message: {msg['message'][:50]}...")
                print(f"   Time: {msg['timestamp']}, Status: {msg['status']}, Read: {msg['read_status']}")
                print("   ---")
        else:
            print("   No messages found for AI agent")
            
        # Check staff list ordering
        print("\n📊 Staff List Top 5 (with priority):")
        cursor.execute("""
            SELECT id, name, status, online_status, priority, last_activity
            FROM tblstaff 
            ORDER BY 
                CASE WHEN priority IS NOT NULL THEN priority ELSE 999 END ASC,
                name ASC
            LIMIT 5
        """)
        top_staff = cursor.fetchall()
        
        for i, staff in enumerate(top_staff, 1):
            online_indicator = "🟢" if staff.get('online_status') == 'online' else "🔴"
            print(f"   #{i}: {online_indicator} {staff['name']} (ID: {staff['id']}, Priority: {staff.get('priority', 'None')})")
            
        # Check if there are notification settings or triggers
        print("\n🔔 Checking for notification-related tables...")
        cursor.execute("SHOW TABLES LIKE '%notification%'")
        notification_tables = cursor.fetchall()
        
        cursor.execute("SHOW TABLES LIKE '%alert%'")
        alert_tables = cursor.fetchall()
        
        cursor.execute("SHOW TABLES LIKE '%message%'")
        message_tables = cursor.fetchall()
        
        if notification_tables:
            print(f"   Notification tables found: {notification_tables}")
        if alert_tables:
            print(f"   Alert tables found: {alert_tables}")
        if message_tables:
            print(f"   Message tables found: {message_tables}")
            
        # Check tblchatmessages structure for notification fields
        print("\n🏗️ tblchatmessages Table Structure:")
        cursor.execute("DESCRIBE tblchatmessages")
        structure = cursor.fetchall()
        for field in structure:
            print(f"   {field}")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking AI agent status: {str(e)}")

if __name__ == "__main__":
    check_ai_agent_status()