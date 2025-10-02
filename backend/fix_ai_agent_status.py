import mysql.connector
from datetime import datetime

class AIAgentStatusFixer:
    def __init__(self):
        self.ai_staff_id = 248
        self.db_config = {
            'host': '92.113.22.65',
            'user': 'u906714182_sqlrrefdvdv',
            'password': '3@6*t:lU',
            'database': 'u906714182_sqlrrefdvdv'
        }
    
    def get_database_connection(self):
        """Get MySQL database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return None
    
    def fix_ai_agent_status(self):
        """Fix AI agent online status and logged in status"""
        conn = self.get_database_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            print("🔧 Fixing AI Agent Status...")
            
            # 1. Set AI agent as logged in
            cursor.execute("""
                UPDATE tblstaff 
                SET is_logged_in = 1, 
                    last_activity = NOW(),
                    active = 1
                WHERE staffid = %s
            """, (self.ai_staff_id,))
            
            print("✅ Updated AI agent login status")
            
            # 2. Ensure online status is properly set
            cursor.execute("""
                INSERT INTO tbl_staff_online_status 
                (staff_id, is_online, last_seen, status_message, updated_at)
                VALUES (%s, 1, NOW(), 'Always Online - AI Assistant', NOW())
                ON DUPLICATE KEY UPDATE 
                is_online = 1,
                last_seen = NOW(),
                status_message = 'Always Online - AI Assistant',
                updated_at = NOW()
            """, (self.ai_staff_id,))
            
            print("✅ Updated online status")
            
            # 3. Mark all existing messages as read to clear the backlog
            cursor.execute("""
                UPDATE tblchatmessages 
                SET viewed = 1, viewed_at = NOW() 
                WHERE reciever_id = %s AND viewed = 0
            """, (self.ai_staff_id,))
            
            read_count = cursor.rowcount
            print(f"✅ Marked {read_count} messages as read")
            
            # 4. Mark notifications as read
            cursor.execute("""
                UPDATE tblnotifications 
                SET isread = 1, isread_inline = 1 
                WHERE touserid = %s AND isread = 0
            """, (self.ai_staff_id,))
            
            notif_count = cursor.rowcount
            print(f"✅ Marked {notif_count} notifications as read")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("🎉 AI Agent status fixed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error fixing AI agent status: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def create_notification_listener(self):
        """Create a system to automatically handle incoming messages"""
        conn = self.get_database_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            print("📡 Setting up message notification system...")
            
            # Create a trigger to automatically notify when new messages arrive
            # Note: This creates a stored procedure that can be called by the application
            cursor.execute("""
                DROP PROCEDURE IF EXISTS handle_ai_message_notification;
            """)
            
            cursor.execute("""
                CREATE PROCEDURE handle_ai_message_notification(
                    IN message_id INT,
                    IN sender_id INT,
                    IN message_text TEXT
                )
                BEGIN
                    DECLARE sender_name VARCHAR(200);
                    
                    -- Get sender name
                    SELECT CONCAT(firstname, ' ', lastname) INTO sender_name 
                    FROM tblstaff 
                    WHERE staffid = sender_id;
                    
                    -- Create notification
                    INSERT INTO tblnotifications 
                    (isread, isread_inline, date, description, fromuserid, fromclientid, 
                     from_fullname, touserid, link, additional_data)
                    VALUES 
                    (0, 0, NOW(), 'New message received', sender_id, 0, 
                     sender_name, 248, CONCAT('#message=', message_id), 
                     CONCAT('Message: ', LEFT(message_text, 50)));
                    
                    -- Update AI agent activity
                    UPDATE tblstaff 
                    SET last_activity = NOW() 
                    WHERE staffid = 248;
                    
                    -- Ensure online status is maintained
                    UPDATE tbl_staff_online_status 
                    SET last_seen = NOW(), updated_at = NOW() 
                    WHERE staff_id = 248;
                    
                END
            """)
            
            print("✅ Created message notification procedure")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating notification system: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def test_notification_system(self):
        """Test the notification system by checking current status"""
        conn = self.get_database_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            print("🧪 Testing notification system...")
            
            # Check current AI agent status
            cursor.execute("""
                SELECT staffid, firstname, lastname, is_logged_in, last_activity, active
                FROM tblstaff 
                WHERE staffid = %s
            """, (self.ai_staff_id,))
            ai_status = cursor.fetchone()
            
            print(f"🤖 AI Agent Status:")
            print(f"   Name: {ai_status['firstname']} {ai_status['lastname']}")
            print(f"   Logged In: {'✅ Yes' if ai_status['is_logged_in'] else '❌ No'}")
            print(f"   Active: {'✅ Yes' if ai_status['active'] else '❌ No'}")
            print(f"   Last Activity: {ai_status['last_activity']}")
            
            # Check online status
            cursor.execute("""
                SELECT is_online, last_seen, status_message, updated_at
                FROM tbl_staff_online_status 
                WHERE staff_id = %s
            """, (self.ai_staff_id,))
            online_status = cursor.fetchone()
            
            if online_status:
                print(f"🟢 Online Status:")
                print(f"   Online: {'✅ Yes' if online_status['is_online'] else '❌ No'}")
                print(f"   Status Message: {online_status['status_message']}")
                print(f"   Last Seen: {online_status['last_seen']}")
                print(f"   Updated At: {online_status['updated_at']}")
            else:
                print("❌ No online status record found")
            
            # Check unread messages
            cursor.execute("""
                SELECT COUNT(*) as unread_count
                FROM tblchatmessages 
                WHERE reciever_id = %s AND viewed = 0
            """, (self.ai_staff_id,))
            unread_result = cursor.fetchone()
            
            print(f"📧 Unread Messages: {unread_result['unread_count']}")
            
            # Check unread notifications
            cursor.execute("""
                SELECT COUNT(*) as unread_notif_count
                FROM tblnotifications 
                WHERE touserid = %s AND isread = 0
            """, (self.ai_staff_id,))
            unread_notif = cursor.fetchone()
            
            print(f"🔔 Unread Notifications: {unread_notif['unread_notif_count']}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing notification system: {e}")
            if conn:
                conn.close()
            return False

if __name__ == "__main__":
    fixer = AIAgentStatusFixer()
    
    print("🚀 Starting AI Agent Status Fix...")
    print("=" * 50)
    
    # Fix the status issues
    if fixer.fix_ai_agent_status():
        print("\n" + "=" * 50)
        
        # Set up notification system
        if fixer.create_notification_listener():
            print("\n" + "=" * 50)
            
            # Test the system
            fixer.test_notification_system()
            
            print("\n" + "=" * 50)
            print("🎉 All fixes completed successfully!")
            print("The AI agent should now appear online and notifications should work.")
        else:
            print("❌ Failed to create notification system")
    else:
        print("❌ Failed to fix AI agent status")