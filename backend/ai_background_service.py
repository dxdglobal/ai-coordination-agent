"""
AI Agent Background Service
Keeps the AI agent online and responsive to messages
"""

import mysql.connector
from datetime import datetime
import time
import threading
import sys
import signal

class AIAgentBackgroundService:
    def __init__(self):
        self.ai_staff_id = 248
        self.running = False
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
    
    def keep_online(self):
        """Keep AI agent online with updated timestamps"""
        conn = self.get_database_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Update AI agent status
            cursor.execute("""
                UPDATE tblstaff 
                SET is_logged_in = 1, 
                    last_activity = NOW(),
                    active = 1
                WHERE staffid = %s
            """, (self.ai_staff_id,))
            
            # Update online status
            cursor.execute("""
                INSERT INTO tbl_staff_online_status 
                (staff_id, is_online, last_seen, status_message, updated_at)
                VALUES (%s, 1, NOW(), 'Always Online - AI Assistant 🟢🤖', NOW())
                ON DUPLICATE KEY UPDATE 
                is_online = 1,
                last_seen = NOW(),
                status_message = 'Always Online - AI Assistant 🟢🤖',
                updated_at = NOW()
            """, (self.ai_staff_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error keeping AI online: {e}")
            if conn:
                conn.close()
            return False
    
    def process_new_messages(self):
        """Process any new unread messages"""
        conn = self.get_database_connection()
        if not conn:
            return 0
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get unread messages
            cursor.execute("""
                SELECT cm.id, cm.sender_id, cm.message, cm.time_sent,
                       CONCAT(s.firstname, ' ', s.lastname) as sender_name
                FROM tblchatmessages cm
                LEFT JOIN tblstaff s ON cm.sender_id = s.staffid
                WHERE cm.reciever_id = %s AND cm.viewed = 0
                ORDER BY cm.time_sent ASC
                LIMIT 10
            """, (self.ai_staff_id,))
            
            unread_messages = cursor.fetchall()
            
            for message in unread_messages:
                # Mark as read
                cursor.execute("""
                    UPDATE tblchatmessages 
                    SET viewed = 1, viewed_at = NOW() 
                    WHERE id = %s
                """, (message['id'],))
                
                # Create notification for sender
                cursor.execute("""
                    INSERT INTO tblnotifications 
                    (isread, isread_inline, date, description, fromuserid, fromclientid, 
                     from_fullname, touserid, link, additional_data)
                    VALUES 
                    (0, 0, NOW(), 'Message read by AI Agent', %s, 0, 
                     '!COORDINATION AGENT DXD AI', %s, 
                     CONCAT('#chatmessage=', %s), 
                     'Your message was received and processed by the AI agent')
                """, (self.ai_staff_id, message['sender_id'], message['id']))
                
                print(f"📨 Processed message from {message['sender_name']}: {message['message'][:50]}...")
            
            if unread_messages:
                conn.commit()
                
            cursor.close()
            conn.close()
            return len(unread_messages)
            
        except Exception as e:
            print(f"❌ Error processing messages: {e}")
            if conn:
                conn.close()
            return 0
    
    def run_service(self):
        """Run the background service"""
        print("🚀 Starting AI Agent Background Service...")
        print(f"🤖 Monitoring AI Agent ID: {self.ai_staff_id}")
        print(f"⏰ Service started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📡 Service will check every 30 seconds")
        print("🛑 Press Ctrl+C to stop")
        print("-" * 60)
        
        self.running = True
        message_count = 0
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\n🛑 Shutdown signal received...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while self.running:
                # Keep AI agent online
                if self.keep_online():
                    status = "🟢 Online"
                else:
                    status = "🔴 Error"
                
                # Process new messages
                new_messages = self.process_new_messages()
                message_count += new_messages
                
                # Log status
                current_time = datetime.now().strftime('%H:%M:%S')
                if new_messages > 0:
                    print(f"[{current_time}] {status} | 📨 Processed {new_messages} new messages")
                else:
                    print(f"[{current_time}] {status} | 📭 No new messages")
                
                # Wait 30 seconds
                for i in range(30):
                    if not self.running:
                        break
                    time.sleep(1)
                
        except Exception as e:
            print(f"❌ Service error: {e}")
        
        print("\n" + "-" * 60)
        print(f"🏁 Service stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Total messages processed: {message_count}")
        print("✅ AI Agent Background Service shutdown complete")

def main():
    """Main function to run the service"""
    service = AIAgentBackgroundService()
    
    print("🤖 AI Agent Background Service")
    print("=" * 50)
    
    # Check if AI agent exists first
    conn = service.get_database_connection()
    if not conn:
        print("❌ Cannot connect to database. Exiting.")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT firstname, lastname FROM tblstaff WHERE staffid = %s", (service.ai_staff_id,))
        ai_agent = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not ai_agent:
            print(f"❌ AI Agent with ID {service.ai_staff_id} not found. Exiting.")
            return
        
        print(f"✅ Found AI Agent: {ai_agent['firstname']} {ai_agent['lastname']}")
        
    except Exception as e:
        print(f"❌ Error checking AI agent: {e}")
        return
    
    # Start the service
    service.run_service()

if __name__ == "__main__":
    main()